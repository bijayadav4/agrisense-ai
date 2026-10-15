import os
import json
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    f1_score,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "datasets", "weather_timeseries_real.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "saved_models", "weather_twostage_v2")

FEATURES = ["temp_max", "temp_min", "humidity", "precipitation", "wind_speed"]
RAIN_IDX = FEATURES.index("precipitation")

SEQ_LEN = 14
FORECAST_LEN = 7
BATCH_SIZE = 64
EPOCHS = 25
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


class WindowDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, index):
        return self.X[index], self.y[index]


class SharedLSTM(nn.Module):
    def __init__(self, output_size, hidden_dim=64, dropout=0.15):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=len(FEATURES),
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=dropout,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, FORECAST_LEN * output_size),
        )
        self.output_size = output_size

    def forward(self, x):
        _, (hidden, _) = self.lstm(x)
        context = torch.cat([hidden[-2], hidden[-1]], dim=1)
        out = self.head(context)
        return out.view(-1, FORECAST_LEN, self.output_size)


def make_windows(target_df, history_df, scaler):
    X, Y = [], []

    for station in sorted(target_df["station"].unique()):
        history = history_df[history_df.station == station]
        target = target_df[target_df.station == station]

        combined = (
            pd.concat([history, target])
            .drop_duplicates(["station", "date"])
            .sort_values("date")
            .reset_index(drop=True)
        )

        dates = combined["date"]
        values = scaler.transform(combined[FEATURES].to_numpy())
        target_dates = set(target["date"])

        for i in range(len(combined) - SEQ_LEN - FORECAST_LEN + 1):
            input_dates = dates.iloc[i:i + SEQ_LEN]
            future_dates = dates.iloc[i + SEQ_LEN:i + SEQ_LEN + FORECAST_LEN]

            if not input_dates.diff().iloc[1:].eq(pd.Timedelta(days=1)).all():
                continue
            if not future_dates.diff().iloc[1:].eq(pd.Timedelta(days=1)).all():
                continue
            if not all(d in target_dates for d in future_dates):
                continue

            X.append(values[i:i + SEQ_LEN])
            Y.append(values[i + SEQ_LEN:i + SEQ_LEN + FORECAST_LEN])

    if not X:
        raise ValueError("No valid windows found.")

    return np.asarray(X, dtype=np.float32), np.asarray(Y, dtype=np.float32)


def inverse_rain(scaled_rain, scaler):
    # MinMaxScaler inverse transform for rainfall feature only.
    return scaled_rain * (
        scaler.data_max_[RAIN_IDX] - scaler.data_min_[RAIN_IDX]
    ) + scaler.data_min_[RAIN_IDX]


def train_model(model, train_loader, val_loader, criterion, device, path):
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=3
    )
    best_val = float("inf")

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total = 0.0

        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total += loss.item() * len(xb)

        train_loss = total / len(train_loader.dataset)
        model.eval()
        val_total = 0.0

        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                val_total += criterion(model(xb), yb).item() * len(xb)

        val_loss = val_total / len(val_loader.dataset)
        scheduler.step(val_loss)

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), path)

        if epoch == 1 or epoch % 5 == 0 or epoch == EPOCHS:
            print(
                f"Epoch {epoch:02d}/{EPOCHS} | "
                f"train={train_loss:.5f} | val={val_loss:.5f}"
            )

    model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
    model.eval()
    return model


def predict(model, X, device):
    model.eval()
    outputs = []
    loader = DataLoader(WindowDataset(X, np.zeros((len(X), FORECAST_LEN, 1))), batch_size=128)

    with torch.no_grad():
        for xb, _ in loader:
            outputs.append(model(xb.to(device)).cpu().numpy())

    return np.concatenate(outputs, axis=0)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    required = ["date", "station"] + FEATURES
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df = df.sort_values(["station", "date"]).reset_index(drop=True)

    if df.duplicated(["station", "date"]).any():
        raise ValueError("Duplicate station-date records.")
    if df[required].isnull().any().any():
        raise ValueError("Missing values in required columns.")
    if (df["precipitation"] < 0).any():
        raise ValueError("Negative rainfall values found.")

    train_parts, val_parts, test_parts = [], [], []
    for _, group in df.groupby("station", sort=True):
        group = group.sort_values("date")
        n = len(group)
        a, b = int(n * 0.70), int(n * 0.85)
        train_parts.append(group.iloc[:a])
        val_parts.append(group.iloc[a:b])
        test_parts.append(group.iloc[b:])

    train_df = pd.concat(train_parts, ignore_index=True)
    val_df = pd.concat(val_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)

    scaler = MinMaxScaler()
    scaler.fit(train_df[FEATURES].to_numpy())

    X_train, y_train_scaled = make_windows(train_df, train_df, scaler)
    X_val, y_val_scaled = make_windows(val_df, train_df, scaler)
    X_test, y_test_scaled = make_windows(
        test_df, pd.concat([train_df, val_df]), scaler
    )

    # Rain occurrence targets use original millimetre values.
    train_rain = inverse_rain(y_train_scaled[:, :, RAIN_IDX], scaler)
    val_rain = inverse_rain(y_val_scaled[:, :, RAIN_IDX], scaler)
    test_rain = inverse_rain(y_test_scaled[:, :, RAIN_IDX], scaler)

    y_cls_train = (train_rain > 0).astype(np.float32)[..., None]
    y_cls_val = (val_rain > 0).astype(np.float32)[..., None]

    # Amount target is log1p(mm); dry days are masked out of the loss.
    y_amt_train = np.log1p(np.maximum(train_rain, 0))[..., None].astype(np.float32)
    y_amt_val = np.log1p(np.maximum(val_rain, 0))[..., None].astype(np.float32)

    train_cls_loader = DataLoader(
        WindowDataset(X_train, y_cls_train), batch_size=BATCH_SIZE, shuffle=True
    )
    val_cls_loader = DataLoader(
        WindowDataset(X_val, y_cls_val), batch_size=128, shuffle=False
    )
    train_amt_loader = DataLoader(
        WindowDataset(X_train, np.concatenate([y_amt_train, y_cls_train], axis=-1)),
        batch_size=BATCH_SIZE, shuffle=True
    )
    val_amt_loader = DataLoader(
        WindowDataset(X_val, np.concatenate([y_amt_val, y_cls_val], axis=-1)),
        batch_size=128, shuffle=False
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)
    print("Windows:", X_train.shape, X_val.shape, X_test.shape)
    print("Rainy target rate (train):", round(float(y_cls_train.mean()), 4))

    classifier = SharedLSTM(1)
    classifier = train_model(
        classifier, train_cls_loader, val_cls_loader,
        nn.BCEWithLogitsLoss(), device,
        os.path.join(OUTPUT_DIR, "rain_classifier.pth")
    )

    class MaskedAmountLoss(nn.Module):
        def forward(self, pred, target):
            amount = target[:, :, :1]
            mask = target[:, :, 1:2]
            loss = nn.functional.smooth_l1_loss(pred, amount, reduction="none")
            return (loss * mask).sum() / mask.sum().clamp_min(1.0)

    class AmountOnlyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.base = SharedLSTM(1)

        def forward(self, x):
            return self.base(x)

    amount_model = AmountOnlyModel()

    # Adapter ensures amount loss receives both amount and rain mask.
    class AmountTrainingModel(nn.Module):
        def __init__(self, base):
            super().__init__()
            self.base = base

        def forward(self, x):
            return self.base(x)

    # Train amount model with a custom loop because target includes the mask.
    amount_model.to(device)
    optimizer = torch.optim.AdamW(amount_model.parameters(), lr=0.003, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=3
    )
    criterion = MaskedAmountLoss()
    best_val = float("inf")
    amount_path = os.path.join(OUTPUT_DIR, "rain_amount.pth")

    for epoch in range(1, EPOCHS + 1):
        amount_model.train()
        total = 0.0

        for xb, yb in train_amt_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            pred = amount_model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(amount_model.parameters(), 1.0)
            optimizer.step()
            total += loss.item() * len(xb)

        train_loss = total / len(train_amt_loader.dataset)
        amount_model.eval()
        val_total = 0.0

        with torch.no_grad():
            for xb, yb in val_amt_loader:
                xb, yb = xb.to(device), yb.to(device)
                val_total += criterion(amount_model(xb), yb).item() * len(xb)

        val_loss = val_total / len(val_amt_loader.dataset)
        scheduler.step(val_loss)

        if val_loss < best_val:
            best_val = val_loss
            torch.save(amount_model.state_dict(), amount_path)

        if epoch == 1 or epoch % 5 == 0 or epoch == EPOCHS:
            print(f"Amount epoch {epoch:02d} | train={train_loss:.5f} | val={val_loss:.5f}")

    amount_model.load_state_dict(torch.load(amount_path, map_location=device, weights_only=True))
    amount_model.eval()

    # Select the probability threshold on validation only.
    val_logits = predict(classifier, X_val, device)[:, :, 0]
    val_probs = 1 / (1 + np.exp(-np.clip(val_logits, -30, 30)))
    best_threshold, best_f1 = 0.5, -1.0

    for threshold in np.arange(0.1, 0.91, 0.05):
        score = f1_score(
            (val_rain > 0).reshape(-1),
            (val_probs >= threshold).reshape(-1),
            zero_division=0,
        )
        if score > best_f1:
            best_f1, best_threshold = score, float(threshold)

    test_logits = predict(classifier, X_test, device)[:, :, 0]
    test_probs = 1 / (1 + np.exp(-np.clip(test_logits, -30, 30)))
    test_rain_logits = predict(amount_model, X_test, device)[:, :, 0]
    test_amount = np.maximum(np.expm1(test_rain_logits), 0)

    predicted_wet = test_probs >= best_threshold
    combined_rain = np.where(predicted_wet, test_amount, 0.0)

    actual = test_rain.reshape(-1)
    predicted = combined_rain.reshape(-1)
    # Fair persistence baseline: repeat the last observed input rainfall
    # for each of the seven forecast days. Do not use future test targets.
    last_observed_scaled = X_test[:, -1, RAIN_IDX]
    last_observed_mm = np.maximum(inverse_rain(last_observed_scaled, scaler), 0)
    baseline = np.repeat(last_observed_mm[:, None], FORECAST_LEN, axis=1).reshape(-1)

    print("\nTest rainfall results (mm):")
    print("Threshold selected on validation:", round(best_threshold, 2))
    print("Rain classifier precision:", round(precision_score(actual > 0, predicted_wet.reshape(-1), zero_division=0), 4))
    print("Rain classifier recall:", round(recall_score(actual > 0, predicted_wet.reshape(-1), zero_division=0), 4))
    print("Rain classifier F1:", round(f1_score(actual > 0, predicted_wet.reshape(-1), zero_division=0), 4))
    print("Two-stage rainfall MAE:", round(mean_absolute_error(actual, predicted), 4))
    print("Two-stage rainfall RMSE:", round(float(np.sqrt(mean_squared_error(actual, predicted))), 4))

    print("\nRainfall persistence baseline MAE:", round(mean_absolute_error(actual, baseline), 4))
    print("Predicted rainfall range:", round(float(predicted.min()), 3), "to", round(float(predicted.max()), 3), "mm")

    metrics = {
        "threshold": best_threshold,
        "precision": float(precision_score(actual > 0, predicted_wet.reshape(-1), zero_division=0)),
        "recall": float(recall_score(actual > 0, predicted_wet.reshape(-1), zero_division=0)),
        "f1": float(f1_score(actual > 0, predicted_wet.reshape(-1), zero_division=0)),
        "mae_mm": float(mean_absolute_error(actual, predicted)),
        "rmse_mm": float(np.sqrt(mean_squared_error(actual, predicted))),
        "baseline_mae_mm": float(mean_absolute_error(actual, baseline)),
    }

    with open(os.path.join(OUTPUT_DIR, "rainfall_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nSaved experiment to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
