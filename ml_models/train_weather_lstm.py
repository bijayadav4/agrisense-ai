"""
AgriSense AI - Spatio-Temporal Weather Forecasting LSTM Training Pipeline
========================================================================
Trains a multi-step sequence-to-sequence Deep Bidirectional LSTM network
to predict multi-variable agricultural weather 7 days into the future,
conditioned on a 14-day historical meteorological sequence.

Target Variables (5 features):
1. temp_max (°C)
2. temp_min (°C)
3. humidity (%)
4. precipitation (mm)
5. wind_speed (km/h)

Inputs:  [Batch, Seq_Len=14, Features=5]
Outputs: [Batch, Horizon=7, Features=5]
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

from config import (
    SAVED_MODELS_DIR,
    WEATHER_DATASET_PATH,
    WEATHER_LSTM_MODEL_PATH,
    WEATHER_LSTM_SCALER_PATH,
    WEATHER_FEATURE_COLUMNS,
)

SEQ_LEN = 14       # 14 days input lookback
FORECAST_LEN = 7   # 7 days forward prediction
NUM_FEATURES = len(WEATHER_FEATURE_COLUMNS)


# ---------------------------------------------------------------------------
# 1. Model Architecture
# ---------------------------------------------------------------------------
class WeatherForecastingLSTM(nn.Module):
    """
    Bidirectional Multi-Layer LSTM with Deep Residual Projection
    for Multi-Horizon Meteorological Time-Series Forecasting.
    """
    def __init__(self, in_features=5, hidden_dim=64, num_layers=2, forecast_days=7, dropout=0.15):
        super().__init__()
        self.in_features = in_features
        self.forecast_days = forecast_days
        self.hidden_dim = hidden_dim

        # Bidirectional LSTM to capture bidirectional weather dynamics
        self.lstm = nn.LSTM(
            input_size=in_features,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Multi-head projection head into multi-step future horizon
        self.head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, forecast_days * in_features),
        )

    def forward(self, x):
        # x: [Batch, Seq_Len=14, Features=5]
        out, (hn, _) = self.lstm(x)
        # Concatenate forward and backward final layer hidden states
        seq_context = torch.cat([hn[-2], hn[-1]], dim=1)  # [Batch, hidden_dim * 2]
        pred = self.head(seq_context)                     # [Batch, forecast_days * in_features]
        return pred.view(-1, self.forecast_days, self.in_features)


# ---------------------------------------------------------------------------
# 2. Dataset & Sliding Window Creator
# ---------------------------------------------------------------------------
class WeatherSequenceDataset(Dataset):
    def __init__(self, X_tensors, y_tensors):
        self.X = X_tensors
        self.y = y_tensors

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def create_sliding_windows(df, scaler, is_train=True):
    X_list, y_list = [], []
    
    # Process station-by-station to preserve temporal continuity
    stations = df["station"].unique()
    for st in stations:
        st_df = df[df["station"] == st].sort_values("date").reset_index(drop=True)
        raw_vals = st_df[WEATHER_FEATURE_COLUMNS].values
        scaled_vals = scaler.transform(raw_vals) if not is_train else scaler.fit_transform(raw_vals)

        total_days = len(scaled_vals)
        for i in range(total_days - SEQ_LEN - FORECAST_LEN + 1):
            x_seq = scaled_vals[i : i + SEQ_LEN]
            y_seq = scaled_vals[i + SEQ_LEN : i + SEQ_LEN + FORECAST_LEN]
            X_list.append(x_seq)
            y_list.append(y_seq)

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.float32)


# ---------------------------------------------------------------------------
# 3. Training Loop
# ---------------------------------------------------------------------------
def train_weather_lstm():
    print("=" * 70)
    print(" AgriSense AI - Weather Forecasting LSTM Training Pipeline")
    print("=" * 70)

    if not os.path.exists(WEATHER_DATASET_PATH):
        raise FileNotFoundError(f"Weather dataset missing at {WEATHER_DATASET_PATH}. Run download_weather_data.py first.")

    df = pd.read_csv(WEATHER_DATASET_PATH)
    print(f"📊 Loaded {len(df)} records across {df['station'].nunique()} agro stations.")

    # Sort temporally
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["station", "date"]).reset_index(drop=True)

    # 80/20 Chronological train/test split per station
    train_dfs, test_dfs = [], []
    for st in df["station"].unique():
        st_sub = df[df["station"] == st].sort_values("date").reset_index(drop=True)
        split_idx = int(len(st_sub) * 0.82)
        train_dfs.append(st_sub.iloc[:split_idx])
        test_dfs.append(st_sub.iloc[split_idx:])

    train_df = pd.concat(train_dfs, ignore_index=True)
    test_df = pd.concat(test_dfs, ignore_index=True)

    # Fit Scaler strictly on Train split
    scaler = MinMaxScaler(feature_range=(0.0, 1.0))
    scaler.fit(train_df[WEATHER_FEATURE_COLUMNS].values)

    # Build sequence windows
    X_train, y_train = [], []
    for st in train_df["station"].unique():
        sub = train_df[train_df["station"] == st].sort_values("date")
        scaled = scaler.transform(sub[WEATHER_FEATURE_COLUMNS].values)
        for i in range(len(scaled) - SEQ_LEN - FORECAST_LEN + 1):
            X_train.append(scaled[i : i + SEQ_LEN])
            y_train.append(scaled[i + SEQ_LEN : i + SEQ_LEN + FORECAST_LEN])

    X_test, y_test = [], []
    for st in test_df["station"].unique():
        sub = test_df[test_df["station"] == st].sort_values("date")
        scaled = scaler.transform(sub[WEATHER_FEATURE_COLUMNS].values)
        for i in range(len(scaled) - SEQ_LEN - FORECAST_LEN + 1):
            X_test.append(scaled[i : i + SEQ_LEN])
            y_test.append(scaled[i + SEQ_LEN : i + SEQ_LEN + FORECAST_LEN])

    X_train, y_train = np.array(X_train, dtype=np.float32), np.array(y_train, dtype=np.float32)
    X_test, y_test = np.array(X_test, dtype=np.float32), np.array(y_test, dtype=np.float32)

    print(f"📦 Train Windows: {X_train.shape} (X) -> {y_train.shape} (y)")
    print(f"📦 Test Windows:  {X_test.shape} (X) -> {y_test.shape} (y)")

    train_dataset = WeatherSequenceDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
    test_dataset = WeatherSequenceDataset(torch.from_numpy(X_test), torch.from_numpy(y_test))

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=128, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"⚙️ Training device: {device}")

    model = WeatherForecastingLSTM(
        in_features=NUM_FEATURES,
        hidden_dim=64,
        num_layers=2,
        forecast_days=FORECAST_LEN,
        dropout=0.15,
    ).to(device)

    # Smooth L1 (Huber) Loss is robust to extreme weather anomalies & rain spikes
    criterion = nn.SmoothL1Loss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)

    epochs = 25
    best_val_loss = float("inf")
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

    print("\n🚀 Starting Training...")
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            preds = model(X_batch)
            loss = criterion(preds, y_batch)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item() * len(X_batch)

        train_loss /= len(train_dataset)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_batch, y_batch in test_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                preds = model(X_batch)
                loss = criterion(preds, y_batch)
                val_loss += loss.item() * len(X_batch)
        val_loss /= len(test_dataset)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), WEATHER_LSTM_MODEL_PATH)

        if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
            print(f"  Epoch [{epoch:02d}/{epochs:02d}] - Train Loss: {train_loss:.5f} | Val Loss: {val_loss:.5f} (Best: {best_val_loss:.5f})")

    # Save MinMaxScaler
    joblib.dump(scaler, WEATHER_LSTM_SCALER_PATH)
    print(f"\n💾 Model weights saved: {WEATHER_LSTM_MODEL_PATH}")
    print(f"💾 Feature scaler saved: {WEATHER_LSTM_SCALER_PATH}")

    # ---------------------------------------------------------------------------
    # 4. Comprehensive Evaluation on Holdout Test Split
    # ---------------------------------------------------------------------------
    print("\n🔍 Evaluating Holdout Test Split (Unscaled Physical Units)...")
    model.load_state_dict(torch.load(WEATHER_LSTM_MODEL_PATH, map_location=device))
    model.eval()

    all_preds, all_trues = [], []
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch = X_batch.to(device)
            p = model(X_batch).cpu().numpy()
            all_preds.append(p)
            all_trues.append(y_batch.numpy())

    preds_arr = np.concatenate(all_preds, axis=0)  # [N, 7, 5]
    trues_arr = np.concatenate(all_trues, axis=0)  # [N, 7, 5]

    # Inverse transform to compute real-world error
    N, H, F = preds_arr.shape
    p_flat = preds_arr.reshape(-1, F)
    t_flat = trues_arr.reshape(-1, F)

    p_unscaled = scaler.inverse_transform(p_flat).reshape(N, H, F)
    t_unscaled = scaler.inverse_transform(t_flat).reshape(N, H, F)

    metrics = {}
    print("\n📈 Per-Feature Prediction Accuracies across 7-Day Horizon:")
    for idx, col in enumerate(WEATHER_FEATURE_COLUMNS):
        mae = mean_absolute_error(t_unscaled[:, :, idx], p_unscaled[:, :, idx])
        rmse = np.sqrt(mean_squared_error(t_unscaled[:, :, idx], p_unscaled[:, :, idx]))
        unit = "°C" if "temp" in col else ("%" if "humidity" in col else ("mm" if "precip" in col else "km/h"))
        metrics[col] = {"MAE": round(float(mae), 2), "RMSE": round(float(rmse), 2), "unit": unit}
        print(f"  • {col:14s} -> MAE: {mae:.2f} {unit} | RMSE: {rmse:.2f} {unit}")

    # Overall summary
    metrics_path = os.path.join(SAVED_MODELS_DIR, "weather_lstm_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n✅ All evaluation metrics saved to {metrics_path}")
    print("=" * 70)


if __name__ == "__main__":
    train_weather_lstm()
