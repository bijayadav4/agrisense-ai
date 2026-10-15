import numpy as np
import pandas as pd
import torch
import joblib

from sklearn.preprocessing import MinMaxScaler
from ml_models.train_weather_lstm_softplus import (
    WeatherForecastingLSTM,
    SequenceDataset,
    DATA_PATH,
    OUTPUT_DIR,
    FEATURES,
    SEQ_LEN,
    FORECAST_LEN,
)

MODEL_PATH = "ml_models/saved_models/weather_softplus_experiment/weather_lstm_real.pth"
SCALER_PATH = "ml_models/saved_models/weather_softplus_experiment/weather_lstm_real_scaler.pkl"

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values(["station", "date"]).reset_index(drop=True)

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

scaler = joblib.load(SCALER_PATH)

def make_test_windows(target_df, history_df):
    X, y = [], []

    for station in sorted(target_df["station"].unique()):
        history = history_df[history_df.station == station]
        targets = target_df[target_df.station == station]
        combined = pd.concat([history, targets]).drop_duplicates(
            ["station", "date"]
        ).sort_values("date").reset_index(drop=True)

        target_dates = set(targets.date)
        dates = combined.date
        values = scaler.transform(combined[FEATURES].to_numpy())

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
            y.append(values[i + SEQ_LEN:i + SEQ_LEN + FORECAST_LEN])

    return np.asarray(X, dtype=np.float32), np.asarray(y, dtype=np.float32)

X_test, y_test = make_test_windows(
    test_df, pd.concat([train_df, val_df], ignore_index=True)
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = WeatherForecastingLSTM().to(device)
state = torch.load(MODEL_PATH, map_location=device, weights_only=True)
model.load_state_dict(state)
model.eval()

with torch.no_grad():
    scaled_pred = model(torch.tensor(X_test, dtype=torch.float32).to(device)).cpu().numpy()

pred = scaler.inverse_transform(
    scaled_pred.reshape(-1, len(FEATURES))
).reshape(-1, FORECAST_LEN, len(FEATURES))

true = scaler.inverse_transform(
    y_test.reshape(-1, len(FEATURES))
).reshape(-1, FORECAST_LEN, len(FEATURES))

baseline_scaled = X_test[:, -1, :]
baseline = scaler.inverse_transform(baseline_scaled)
baseline = np.repeat(baseline[:, None, :], FORECAST_LEN, axis=1)

print("Test windows:", len(X_test))
print("\nPrediction ranges (real units):")
for i, feature in enumerate(FEATURES):
    print(
        f"{feature:15} min={pred[:, :, i].min():8.3f} "
        f"max={pred[:, :, i].max():8.3f}"
    )

humidity = pred[:, :, FEATURES.index("humidity")]
rain = pred[:, :, FEATURES.index("precipitation")]

print("\nPhysical constraint checks:")
print("Humidity outside 0–100%:", int(((humidity < 0) | (humidity > 100)).sum()))
print("Negative rainfall predictions:", int((rain < 0).sum()))

print("\nMAE comparison: experimental model vs persistence baseline")
for i, feature in enumerate(FEATURES):
    model_mae = np.mean(np.abs(pred[:, :, i] - true[:, :, i]))
    baseline_mae = np.mean(np.abs(baseline[:, :, i] - true[:, :, i]))
    print(
        f"{feature:15} model={model_mae:8.4f} "
        f"baseline={baseline_mae:8.4f} "
        f"winner={'model' if model_mae < baseline_mae else 'baseline'}"
    )
