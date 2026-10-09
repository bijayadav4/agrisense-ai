import os

import numpy as np
import pandas as pd
import torch
from config import CROP_DATASET_PATH, FUSION_LSTM_MODEL_PATH, SAVED_MODELS_DIR
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, Dataset


# ---------------------------------------------------------------------------
# 1. Spatio-Temporal LSTM & Feature Bottleneck Multimodal Fusion Model
# ---------------------------------------------------------------------------
class SoilEncoder(nn.Module):
    """Encodes soil chemistry (N, P, K, pH, Soil_Type) into a dense latent vector."""

    def __init__(self, in_features=5, hidden_dim=32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

    def forward(self, x):
        return self.net(x)


class TemporalWeatherLSTM(nn.Module):
    """Processes 7-day multi-step meteorological sequences using Bi-directional LSTM."""

    def __init__(self, in_channels=3, hidden_dim=32, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=in_channels,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.1 if num_layers > 1 else 0.0,
        )
        self.proj = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.ReLU())

    def forward(self, x):
        # x: [Batch, Seq_Len=7, Channels=3]
        lstm_out, (hn, _) = self.lstm(x)
        # Concatenate forward and backward final states
        seq_summary = torch.cat([hn[-2], hn[-1]], dim=1)  # [Batch, hidden_dim * 2]
        return self.proj(seq_summary)  # [Batch, hidden_dim]


class SpatioTemporalCropFusionModel(nn.Module):
    """
    Multimodal Agriculture Fusion Network with Feature Bottleneck:
    Fuses static spatial soil chemistry with dynamic temporal climate sequences.
    """

    def __init__(self, soil_dim=5, weather_dim=3, hidden_dim=32, bottleneck_dim=24, num_classes=23):
        super().__init__()
        self.soil_encoder = SoilEncoder(in_features=soil_dim, hidden_dim=hidden_dim)
        self.weather_lstm = TemporalWeatherLSTM(in_channels=weather_dim, hidden_dim=hidden_dim, num_layers=2)

        # Multimodal Fusion & Feature Bottleneck
        self.bottleneck = nn.Sequential(
            nn.Linear(hidden_dim * 2, bottleneck_dim), nn.BatchNorm1d(bottleneck_dim), nn.ReLU(), nn.Dropout(0.2)
        )

        # Classification Head
        self.classifier = nn.Linear(bottleneck_dim, num_classes)

    def forward(self, soil_x, weather_seq):
        soil_emb = self.soil_encoder(soil_x)
        weather_emb = self.weather_lstm(weather_seq)
        fused = torch.cat([soil_emb, weather_emb], dim=1)
        bottleneck_features = self.bottleneck(fused)
        logits = self.classifier(bottleneck_features)
        return logits

    def extract_bottleneck(self, soil_x, weather_seq):
        """Extracts low-dimensional agronomic bottleneck vector for explainability."""
        with torch.no_grad():
            soil_emb = self.soil_encoder(soil_x)
            weather_emb = self.weather_lstm(weather_seq)
            fused = torch.cat([soil_emb, weather_emb], dim=1)
            return self.bottleneck(fused)


# ---------------------------------------------------------------------------
# 2. Dataset Preparation & Temporal Sequence Synthesizer
# ---------------------------------------------------------------------------
class AgriFusionDataset(Dataset):
    def __init__(self, soil_tensors, weather_seq_tensors, labels):
        self.soil = soil_tensors
        self.weather = weather_seq_tensors
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.soil[idx], self.weather[idx], self.labels[idx]


def build_temporal_weather_sequences(df, seq_len=7):
    """
    Generates realistic 7-day meteorological trajectories (temperature, humidity, rain)
    calibrated to the physiological climate bands of each crop record in the dataset.
    """
    soil_data = []
    weather_seqs = []

    # NOTE: Historical target leakage fix:
    # Previously, soil_type was inferred via `soil_type_map.get(c_label)` which leaked the target label.
    # That code has been permanently removed. Soil vector is now independent of the target class.
    # ST-LSTM Fusion is an experimental research prototype and is NOT part of the production decision pipeline.
    neutral_soil_type = 0.25  # Neutral baseline constant (un-leaked)
    np.random.seed(42)
    for _, row in df.iterrows():
        n = row["N"] / 140.0
        p = row["P"] / 145.0
        k = row["K"] / 205.0
        ph = row["ph"] / 14.0
        soil_vec = [n, p, k, ph, neutral_soil_type]

        base_t = row["temperature"]
        base_h = row["humidity"]
        base_r = row["rainfall"]

        # Construct 7-day historical weather trajectory with realistic daily drift
        seq = []
        for d in range(seq_len):
            # Diurnal & weather wave fluctuation
            drift_t = np.sin((d / 7.0) * np.pi) * 2.5 + np.random.normal(0, 0.8)
            drift_h = np.cos((d / 7.0) * np.pi) * 4.0 + np.random.normal(0, 1.5)
            rain_factor = np.exp(-((d - 3) ** 2) / 3.0) + np.random.uniform(0.1, 0.5)

            day_t = np.clip((base_t + drift_t) / 45.0, 0.0, 1.0)
            day_h = np.clip((base_h + drift_h) / 100.0, 0.0, 1.0)
            day_r = np.clip((base_r * rain_factor / 7.0) / 60.0, 0.0, 1.0)

            seq.append([day_t, day_h, day_r])

        soil_data.append(soil_vec)
        weather_seqs.append(seq)

    return np.array(soil_data, dtype=np.float32), np.array(weather_seqs, dtype=np.float32)


# ---------------------------------------------------------------------------
# 3. Model Training Pipeline
# ---------------------------------------------------------------------------
def train_spatiotemporal_fusion_model(epochs=15, batch_size=32, lr=2e-3):
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"⚙️ Training on device: {device}")

    # Load crop dataset
    df = pd.read_csv(CROP_DATASET_PATH)
    classes = sorted(df["label"].unique())
    class_to_idx = {c: i for i, c in enumerate(classes)}
    labels = np.array([class_to_idx[c] for c in df["label"]], dtype=np.int64)

    # Build multimodal features
    soil_features, weather_sequences = build_temporal_weather_sequences(df)

    # Stratified 80:20 train/test split
    X_soil_tr, X_soil_te, X_wea_tr, X_wea_te, y_tr, y_te = train_test_split(
        soil_features, weather_sequences, labels, test_size=0.2, random_state=42, stratify=labels
    )

    train_ds = AgriFusionDataset(torch.tensor(X_soil_tr), torch.tensor(X_wea_tr), torch.tensor(y_tr))
    test_ds = AgriFusionDataset(torch.tensor(X_soil_te), torch.tensor(X_wea_te), torch.tensor(y_te))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    model = SpatioTemporalCropFusionModel(
        soil_dim=5, weather_dim=3, hidden_dim=32, bottleneck_dim=24, num_classes=len(classes)
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    print(f"🚀 Training Spatio-Temporal LSTM & Bottleneck Fusion Model across {epochs} epochs...")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for soil_b, wea_b, y_b in train_loader:
            soil_b, wea_b, y_b = soil_b.to(device), wea_b.to(device), y_b.to(device)
            optimizer.zero_grad()
            outputs = model(soil_b, wea_b)
            loss = criterion(outputs, y_b)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * len(y_b)
            _, pred = torch.max(outputs, 1)
            correct += (pred == y_b).sum().item()
            total += len(y_b)

        scheduler.step()

        # Evaluate on test set
        model.eval()
        te_correct = 0
        te_total = 0
        with torch.no_grad():
            for soil_b, wea_b, y_b in test_loader:
                soil_b, wea_b, y_b = soil_b.to(device), wea_b.to(device), y_b.to(device)
                outputs = model(soil_b, wea_b)
                _, pred = torch.max(outputs, 1)
                te_correct += (pred == y_b).sum().item()
                te_total += len(y_b)

        tr_acc = (correct / total) * 100
        te_acc = (te_correct / te_total) * 100
        print(
            f"Epoch [{epoch + 1:02d}/{epochs:02d}] Loss: {running_loss / total:.4f} | Train Acc: {tr_acc:.2f}% | Test Acc: {te_acc:.2f}%"
        )

    # Save artifact checkpoint with metadata
    checkpoint = {
        "model_state": model.state_dict(),
        "classes": classes,
        "architecture": {
            "soil_dim": 5,
            "weather_dim": 3,
            "hidden_dim": 32,
            "bottleneck_dim": 24,
            "num_classes": len(classes),
        },
    }
    torch.save(checkpoint, FUSION_LSTM_MODEL_PATH)
    print(f"\n✅ Spatio-Temporal LSTM Fusion Model successfully saved to: {FUSION_LSTM_MODEL_PATH}")
    return model, classes


if __name__ == "__main__":
    train_spatiotemporal_fusion_model()
