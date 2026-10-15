import os
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error,
)

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "datasets", "weather_timeseries_real.csv")
OUT = os.path.join(BASE, "saved_models", "weather_twostage_v2")
FEATURES = ["temp_max", "temp_min", "humidity", "precipitation", "wind_speed"]
RAIN_IDX = FEATURES.index("precipitation")
SEQ_LEN, HORIZON, BATCH, SEED = 14, 7, 128, 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


class WindowDataset(Dataset):
    def __init__(self, X):
        self.X = torch.tensor(X, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i]


class SharedLSTM(nn.Module):
    def __init__(self, output_size, hidden_dim=64, dropout=0.15):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=len(FEATURES), hidden_size=hidden_dim,
            num_layers=2, batch_first=True, bidirectional=True,
            dropout=dropout,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, HORIZON * output_size),
        )
        self.output_size = output_size

    def forward(self, x):
        _, (hidden, _) = self.lstm(x)
        context = torch.cat([hidden[-2], hidden[-1]], dim=1)
        return self.head(context).view(-1, HORIZON, self.output_size)


class AmountOnlyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.base = SharedLSTM(1)

    def forward(self, x):
        return self.base(x)


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

        for i in range(len(combined) - SEQ_LEN - HORIZON + 1):
            in_dates = dates.iloc[i:i + SEQ_LEN]
            future_dates = dates.iloc[i + SEQ_LEN:i + SEQ_LEN + HORIZON]
            if not in_dates.diff().iloc[1:].eq(pd.Timedelta(days=1)).all():
                continue
            if not future_dates.diff().iloc[1:].eq(pd.Timedelta(days=1)).all():
                continue
            if not all(d in target_dates for d in future_dates):
                continue
            X.append(values[i:i + SEQ_LEN])
            Y.append(values[i + SEQ_LEN:i + SEQ_LEN + HORIZON])

    if not X:
        raise ValueError("No valid windows generated.")
    return np.asarray(X, dtype=np.float32), np.asarray(Y, dtype=np.float32)


def inverse_rain(values, scaler):
    return (
        values * (scaler.data_max_[RAIN_IDX] - scaler.data_min_[RAIN_IDX])
        + scaler.data_min_[RAIN_IDX]
    )


def predict(model, X, device):
    loader = DataLoader(WindowDataset(X), batch_size=BATCH, shuffle=False)
    outputs = []
    model.eval()
    with torch.no_grad():
        for xb in loader:
            outputs.append(model(xb.to(device)).cpu().numpy())
    return np.concatenate(outputs, axis=0)


def main():
    for name in ("rain_classifier.pth", "rain_amount.pth"):
        path = os.path.join(OUT, name)
        if not os.path.isfile(path):
            raise FileNotFoundError(path)

    df = pd.read_csv(DATA)
    required = ["date", "station"] + FEATURES
    if set(required) - set(df.columns):
        raise ValueError(f"Missing columns: {sorted(set(required) - set(df.columns))}")

    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df = df.sort_values(["station", "date"]).reset_index(drop=True)
    if df.duplicated(["station", "date"]).any():
        raise ValueError("Duplicate station-date records.")
    if df[required].isnull().any().any():
        raise ValueError("Missing required values.")
    if (df["precipitation"] < 0).any():
        raise ValueError("Negative rainfall values.")

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

    X_val, Y_val_scaled = make_windows(val_df, train_df, scaler)
    X_test, Y_test_scaled = make_windows(
        test_df, pd.concat([train_df, val_df]), scaler
    )
    val_rain = np.maximum(inverse_rain(Y_val_scaled[:, :, RAIN_IDX], scaler), 0)
    test_rain = np.maximum(inverse_rain(Y_test_scaled[:, :, RAIN_IDX], scaler), 0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    classifier = SharedLSTM(1).to(device)
    amount_model = AmountOnlyModel().to(device)

    classifier.load_state_dict(torch.load(
        os.path.join(OUT, "rain_classifier.pth"),
        map_location=device, weights_only=True,
    ))
    amount_model.load_state_dict(torch.load(
        os.path.join(OUT, "rain_amount.pth"),
        map_location=device, weights_only=True,
    ))

    val_logits = predict(classifier, X_val, device)[:, :, 0]
    val_probs = 1 / (1 + np.exp(-np.clip(val_logits, -30, 30)))
    val_actual_wet = (val_rain > 0).reshape(-1)

    best_threshold, best_f1 = 0.5, -1.0
    for threshold in np.arange(0.1, 0.91, 0.05):
        score = f1_score(
            val_actual_wet, (val_probs >= threshold).reshape(-1),
            zero_division=0,
        )
        if score > best_f1:
            best_f1, best_threshold = score, float(threshold)

    test_logits = predict(classifier, X_test, device)[:, :, 0]
    test_probs = 1 / (1 + np.exp(-np.clip(test_logits, -30, 30)))
    amount_log = predict(amount_model, X_test, device)[:, :, 0]
    amount_mm = np.maximum(np.expm1(amount_log), 0)

    # Classifier metrics use only rain/no-rain predictions.
    predicted_wet = (test_probs >= best_threshold).reshape(-1)
    actual_wet = (test_rain > 0).reshape(-1)

    # Amount metrics use the combined operational rainfall forecast.
    combined = np.where(
        test_probs >= best_threshold, amount_mm, 0.0
    ).reshape(-1)
    actual = test_rain.reshape(-1)

    last_scaled = X_test[:, -1, RAIN_IDX]
    last_mm = np.maximum(inverse_rain(last_scaled, scaler), 0)
    baseline = np.repeat(last_mm[:, None], HORIZON, axis=1).reshape(-1)

    metrics = {
        "threshold": best_threshold,
        "classifier_precision": float(precision_score(actual_wet, predicted_wet, zero_division=0)),
        "classifier_recall": float(recall_score(actual_wet, predicted_wet, zero_division=0)),
        "classifier_f1": float(f1_score(actual_wet, predicted_wet, zero_division=0)),
        "mae_mm": float(mean_absolute_error(actual, combined)),
        "rmse_mm": float(np.sqrt(mean_squared_error(actual, combined))),
        "baseline_mae_mm": float(mean_absolute_error(actual, baseline)),
        "max_predicted_rain_mm": float(combined.max()),
        "test_windows": int(len(X_test)),
    }

    print("Device:", device)
    print("Validation-selected threshold:", round(best_threshold, 2))
    print("Classifier precision:", round(metrics["classifier_precision"], 4))
    print("Classifier recall:", round(metrics["classifier_recall"], 4))
    print("Classifier F1:", round(metrics["classifier_f1"], 4))
    print("Two-stage rainfall MAE (mm):", round(metrics["mae_mm"], 4))
    print("Two-stage rainfall RMSE (mm):", round(metrics["rmse_mm"], 4))
    print("Persistence baseline MAE (mm):", round(metrics["baseline_mae_mm"], 4))
    print("Maximum predicted rainfall (mm):", round(metrics["max_predicted_rain_mm"], 3))
    print("Test windows:", metrics["test_windows"])

    # HEAVY_RAIN_AUDIT_V1
    print("\\n--- Heavy rainfall audit (test targets) ---")
    for cutoff in (10.0, 20.0):
        mask = actual >= cutoff
        count = int(mask.sum())
        print(f"Actual rainfall >= {cutoff:.0f} mm: {count} target points")
        if count:
            print(f"  Actual mean (mm): {actual[mask].mean():.3f}")
            print(f"  Predicted mean (mm): {combined[mask].mean():.3f}")
            print(f"  MAE on these points (mm): {mean_absolute_error(actual[mask], combined[mask]):.3f}")
            print(f"  Underpredicted points: {int((combined[mask] < actual[mask]).sum())}/{count}")
    print("Maximum actual rainfall (mm):", round(float(actual.max()), 3))
    print("Maximum predicted rainfall (mm):", round(float(combined.max()), 3))

    report = os.path.join(OUT, "rainfall_metrics_corrected.json")
    with open(report, "w") as f:
        import json
        json.dump(metrics, f, indent=2)
    print("Corrected metrics saved to:", report)


if __name__ == "__main__":
    main()
