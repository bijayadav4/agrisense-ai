import os

import torch
from config import SAVED_MODELS_DIR, SOIL_CLASSES, SOIL_CNN_MODEL_PATH
from torch import nn
from torch.utils.data import DataLoader
from torchvision import models, transforms


class SoilCNNClassifier(nn.Module):
    """
    Lightweight, high-performance Soil Image Classifier using MobileNetV2 backbone.
    Classifies soil images into 5 categories: Black, Clayey, Loamy, Red, Sandy.
    """

    def __init__(self, num_classes=5):
        super().__init__()
        self.backbone = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        in_features = self.backbone.classifier[1].in_features

        # Custom head with Dropout & BatchNorm
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_features, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        return self.backbone(x)


def get_transforms():
    train_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    val_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    return train_transform, val_transform


def train_or_initialize_soil_model(epochs=8, batch_size=32, lr=1e-3):
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"⚙️ Using device: {device}")

    model = SoilCNNClassifier(num_classes=len(SOIL_CLASSES)).to(device)

    # Freeze pretrained MobileNetV2 feature backbone
    for param in model.backbone.features.parameters():
        param.requires_grad = False

    splits_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "splits")
    train_csv = os.path.join(splits_dir, "soil_split_train_orig.csv")
    val_csv = os.path.join(splits_dir, "soil_split_val.csv")

    if os.path.exists(train_csv):
        import pandas as pd
        from PIL import Image
        from torch.utils.data import Dataset

        class SoilDataset(Dataset):
            def __init__(self, df, transform=None):
                self.df = df.reset_index(drop=True)
                self.transform = transform
                self.class_to_idx = {c: i for i, c in enumerate(SOIL_CLASSES)}

            def __len__(self):
                return len(self.df)

            def __getitem__(self, idx):
                row = self.df.iloc[idx]
                img = Image.open(row["filepath"]).convert("RGB")
                if self.transform:
                    img = self.transform(img)
                return img, self.class_to_idx[row["soil_class"]]

        df_train = pd.read_csv(train_csv)
        df_val = pd.read_csv(val_csv)
        train_transform, val_transform = get_transforms()

        train_ds = SoilDataset(df_train, transform=train_transform)
        val_ds = SoilDataset(df_val, transform=val_transform)
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

        # Inverse Class Frequency Weighting for Imbalance
        cls_counts = df_train["soil_class"].value_counts()
        weights = [float(len(df_train) / (len(SOIL_CLASSES) * max(1, cls_counts.get(c, 1)))) for c in SOIL_CLASSES]
        criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float).to(device))
        optimizer = torch.optim.Adam(model.backbone.classifier.parameters(), lr=lr, weight_decay=1e-4)

        print(f"🚀 Training Champion Model A on {len(df_train)} pure original images ({epochs} epochs)...")
        best_val_acc = 0.0
        best_weights = None

        for epoch in range(epochs):
            model.train()
            running_loss = 0.0
            correct = 0
            total = 0
            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                running_loss += loss.item() * images.size(0)
                preds = outputs.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

            # Validation
            model.eval()
            val_correct = 0
            with torch.no_grad():
                for v_imgs, v_lbls in val_loader:
                    v_imgs, v_lbls = v_imgs.to(device), v_lbls.to(device)
                    val_correct += (model(v_imgs).argmax(dim=1) == v_lbls).sum().item()
            val_acc = (val_correct / len(df_val)) * 100
            train_acc = (correct / total) * 100

            print(
                f"Epoch [{epoch + 1}/{epochs}] Loss: {running_loss / total:.4f} | Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}%"
            )
            if val_acc >= best_val_acc:
                best_val_acc = val_acc
                best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        model.load_state_dict(best_weights)
        torch.save(model.state_dict(), SOIL_CNN_MODEL_PATH)
        print(f"✅ Champion weights saved successfully to: {SOIL_CNN_MODEL_PATH} (Best Val Acc: {best_val_acc:.2f}%)")
    else:
        print("ℹ️ Split CSVs not found. Run scratch/run_ablation.py first.")

    return model


if __name__ == "__main__":
    train_or_initialize_soil_model()
