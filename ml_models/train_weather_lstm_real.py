import joblib

import os
import json
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

# --------------------------------------------------
# 1. Paths and settings
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "datasets", "weather_timeseries_real.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "saved_models", "real_weather")

MODEL_PATH = os.path.join(OUTPUT_DIR, "weather_lstm_real.pth")
SCALER_PATH = os.path.join(OUTPUT_DIR, "weather_lstm_real_scaler.pkl")
METRICS_PATH = os.path.join(OUTPUT_DIR, "weather_lstm_real_metrics.json")

FEATURES = [
    "temp_max", "temp_min", "humidity",
    "precipitation", "wind_speed"
]

SEQ_LEN = 14
FORECAST_LEN = 7
BATCH_SIZE = 64
EPOCHS = 25
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# --------------------------------------------------
# 2. Model
# --------------------------------------------------
class WeatherForecastingLSTM(nn.Module):
    def __init__(self, in_features=5, hidden_dim=64,
                 num_layers=2, forecast_days=7, dropout=0.15):
        super().__init__()
        self.forecast_days = forecast_days
        self.in_features = in_features

        self.lstm = nn.LSTM(
            input_size=in_features,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout,
        )

        self.head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, forecast_days * in_features),
        )

    def forward(self, x):
        _, (hidden, _) = self.lstm(x)
        context = torch.cat([hidden[-2], hidden[-1]], dim=1)
        output = self.head(context)
        return output.view(-1, self.forecast_days, self.in_features)


class SequenceDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, index):
        return self.X[index], self.y[index]


# --------------------------------------------------
# 3. Create windows without crossing date gaps
# --------------------------------------------------
def create_windows(df, scaler):
    X, y = [], []

    for _, station_df in df.groupby("station", sort=True):
        station_df = station_df.sort_values("date").reset_index(drop=True)

        dates = station_df["date"]
        values = scaler.transform(station_df[FEATURES].to_numpy())

        for i in range(len(station_df) - SEQ_LEN - FORECAST_LEN + 1):
            end = i + SEQ_LEN + FORECAST_LEN
            window_dates = dates.iloc[i:end]

            if not window_dates.diff().iloc[1:].eq(
                pd.Timedelta(days=1)
            ).all():
                continue

            X.append(values[i:i + SEQ_LEN])
            y.append(values[i + SEQ_LEN:end])

    if not X:
        raise ValueError("No valid sequence windows found.")

    return np.asarray(X, dtype=np.float32), np.asarray(y, dtype=np.float32)


# --------------------------------------------------
# 4. Load and split data chronologically
# --------------------------------------------------
def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(DATA_PATH)

    df = pd.read_csv(DATA_PATH)
    required = ["date", "station"] + FEATURES

    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df = df.sort_values(["station", "date"]).reset_index(drop=True)

    if df.duplicated(["station", "date"]).any():
        raise ValueError("Duplicate station-date records found.")

    if df[required].isnull().any().any():
        raise ValueError("Missing values found in required columns.")

    train_parts, val_parts, test_parts = [], [], []

    for _, group in df.groupby("station", sort=True):
        group = group.sort_values("date").reset_index(drop=True)
        n = len(group)
        train_end = int(n * 0.70)
        val_end = int(n * 0.85)

        train_parts.append(group.iloc[:train_end])
        val_parts.append(group.iloc[train_end:val_end])
        test_parts.append(group.iloc[val_end:])

    train_df = pd.concat(train_parts, ignore_index=True)
    val_df = pd.concat(val_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)

    print("Dataset:", DATA_PATH)
    print("Rows:", len(df), "| Stations:", df["station"].nunique())
    print("Train rows:", len(train_df))
    print("Validation rows:", len(val_df))
    print("Test rows:", len(test_df))

    # Fit scaler only on training rows.
    scaler = MinMaxScaler()
    scaler.fit(train_df[FEATURES].to_numpy())

    # Validation/test windows may use prior-period history as input,
    # but their target dates remain entirely within their own split.
    def split_windows(target_df, history_df):
        X, y = [], []

        for station in sorted(target_df["station"].unique()):
            history = history_df[history_df["station"] == station]
            targets = target_df[target_df["station"] == station]

            combined = pd.concat([history, targets]).drop_duplicates(
                ["station", "date"]
            ).sort_values("date").reset_index(drop=True)

            history_dates = set(history["date"])
            target_dates = set(targets["date"])

            dates = combined["date"]
            values = scaler.transform(combined[FEATURES].to_numpy())

            for i in range(len(combined) - SEQ_LEN - FORECAST_LEN + 1):
                input_dates = dates.iloc[i:i + SEQ_LEN]
                future_dates = dates.iloc[i + SEQ_LEN:i + SEQ_LEN + FORECAST_LEN]

                if not input_dates.diff().iloc[1:].eq(
                    pd.Timedelta(days=1)
                ).all():
                    continue
                if not future_dates.diff().iloc[1:].eq(
                    pd.Timedelta(days=1)
                ).all():
                    continue
                if not all(d in target_dates for d in future_dates):
                    continue

                X.append(values[i:i + SEQ_LEN])
                y.append(values[i + SEQ_LEN:i + SEQ_LEN + FORECAST_LEN])

        if not X:
            raise ValueError("No valid windows for split.")

        return np.asarray(X, dtype=np.float32), np.asarray(y, dtype=np.float32)

    X_train, y_train = create_windows(train_df, scaler)
    X_val, y_val = split_windows(val_df, train_df)
    X_test, y_test = split_windows(test_df, pd.concat([train_df, val_df]))

    print("Train windows:", X_train.shape, y_train.shape)
    print("Validation windows:", X_val.shape, y_val.shape)
    print("Test windows:", X_test.shape, y_test.shape)

    train_loader = DataLoader(
        SequenceDataset(X_train, y_train),
        batch_size=BATCH_SIZE, shuffle=True
    )
    val_loader = DataLoader(
        SequenceDataset(X_val, y_val),
        batch_size=128, shuffle=False
    )
    test_loader = DataLoader(
        SequenceDataset(X_test, y_test),
        batch_size=128, shuffle=False
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)

    model = WeatherForecastingLSTM().to(device)
    criterion = nn.SmoothL1Loss()
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=0.003, weight_decay=1e-4
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=3
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    best_val_loss = float("inf")

    # Select checkpoint using validation data only.
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0

        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            prediction = model(xb)
            loss = criterion(prediction, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item() * len(xb)

        train_loss = total_loss / len(train_loader.dataset)

        model.eval()
        val_total = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                loss = criterion(model(xb), yb)
                val_total += loss.item() * len(xb)

        val_loss = val_total / len(val_loader.dataset)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), MODEL_PATH)

        if epoch == 1 or epoch % 5 == 0 or epoch == EPOCHS:
            print(
                f"Epoch {epoch:02d}/{EPOCHS} | "
                f"Train Loss: {train_loss:.5f} | "
                f"Val Loss: {val_loss:.5f}"
            )

    # Evaluate the selected model on test data only once.
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()

    predictions, truths = [], []
    with torch.no_grad():
        for xb, yb in test_loader:
            predictions.append(model(xb.to(device)).cpu().numpy())
            truths.append(yb.numpy())

    pred = np.concatenate(predictions).reshape(-1, len(FEATURES))
    true = np.concatenate(truths).reshape(-1, len(FEATURES))

    pred = scaler.inverse_transform(pred)
    true = scaler.inverse_transform(true)

    metrics = {}
    print("\nFinal test metrics (real-world units):")

    for i, feature in enumerate(FEATURES):
        mae = mean_absolute_error(true[:, i], pred[:, i])
        rmse = np.sqrt(mean_squared_error(true[:, i], pred[:, i]))
        metrics[feature] = {
            "MAE": round(float(mae), 4),
            "RMSE": round(float(rmse), 4),
        }
        print(f"{feature}: MAE={mae:.4f}, RMSE={rmse:.4f}")

    joblib.dump(scaler, SCALER_PATH)

    with open(METRICS_PATH, "w") as file:
        json.dump(metrics, file, indent=2)

    print("\nSaved model:", MODEL_PATH)
    print("Saved scaler:", SCALER_PATH)
    print("Saved metrics:", METRICS_PATH)


if __name__ == "__main__":
    main()
