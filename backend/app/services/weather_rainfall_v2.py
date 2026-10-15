"""Two-stage V2 rainfall inference; keeps the original weather model untouched."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler


FEATURES = ["temp_max", "temp_min", "humidity", "precipitation", "wind_speed"]
SEQ_LEN = 14
FORECAST_LEN = 7


class SharedLSTM(nn.Module):
    def __init__(self, output_size=1, hidden_dim=64, dropout=0.15):
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
        return self.head(context).view(-1, FORECAST_LEN, self.output_size)


class AmountOnlyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.base = SharedLSTM(1)

    def forward(self, x):
        return self.base(x)


class WeatherRainfallV2:
    def __init__(self):
        self.device = torch.device("cpu")
        self.classifier = None
        self.amount_model = None
        self.scaler = None
        self.threshold = 0.25
        self.metrics = {}
        self.error = None
        self._load()

    def _load(self):
        root = Path(__file__).resolve().parents[3]
        model_dir = root / "ml_models" / "saved_models" / "weather_twostage_v2"
        data_path = root / "ml_models" / "datasets" / "weather_timeseries_real.csv"

        try:
            with (model_dir / "rainfall_metrics_corrected.json").open() as f:
                self.metrics = json.load(f)
            self.threshold = float(self.metrics["threshold"])

            # Reproduce training preprocessing: chronological 70% per station.
            df = pd.read_csv(data_path, parse_dates=["date"])
            required = ["date", "station"] + FEATURES
            if df[required].isna().any().any():
                raise ValueError("Training dataset contains missing required values.")
            df = df.sort_values(["station", "date"]).reset_index(drop=True)
            train_parts = []
            for _, group in df.groupby("station", sort=True):
                group = group.sort_values("date")
                train_parts.append(group.iloc[:int(len(group) * 0.70)])
            train_df = pd.concat(train_parts, ignore_index=True)

            self.scaler = MinMaxScaler()
            self.scaler.fit(train_df[FEATURES].to_numpy())

            self.classifier = SharedLSTM(1)
            self.classifier.load_state_dict(
                torch.load(model_dir / "rain_classifier.pth", map_location=self.device)
            )
            self.amount_model = AmountOnlyModel()
            self.amount_model.load_state_dict(
                torch.load(model_dir / "rain_amount.pth", map_location=self.device)
            )
            self.classifier.eval()
            self.amount_model.eval()
        except Exception as exc:
            self.error = str(exc)
            self.classifier = None
            self.amount_model = None
            self.scaler = None
            print(f"⚠️ V2 rainfall model unavailable: {exc}")

    @property
    def is_ready(self):
        return (
            self.classifier is not None
            and self.amount_model is not None
            and self.scaler is not None
        )

    def predict(self, raw_14days):
        """Return 7 rainfall amounts (mm) and probabilities, or None if unavailable."""
        if not self.is_ready:
            return None

        raw = np.asarray(raw_14days, dtype=np.float32)
        if raw.shape != (SEQ_LEN, len(FEATURES)) or not np.isfinite(raw).all():
            return None

        scaled = self.scaler.transform(raw)
        x = torch.from_numpy(scaled.astype(np.float32)).unsqueeze(0).to(self.device)

        with torch.no_grad():
            probabilities = torch.sigmoid(self.classifier(x)).squeeze(0).squeeze(-1)
            amount_log = self.amount_model(x).squeeze(0).squeeze(-1)

        probabilities = probabilities.cpu().numpy()
        amount_log = amount_log.cpu().numpy()
        amount_mm = np.maximum(np.expm1(np.clip(amount_log, 0.0, 20.0)), 0.0)
        rainfall_mm = np.where(probabilities >= self.threshold, amount_mm, 0.0)

        return {
            "rain_mm": rainfall_mm.astype(float),
            "rain_probability": probabilities.astype(float),
            "threshold": self.threshold,
        }


weather_rainfall_v2 = WeatherRainfallV2()
