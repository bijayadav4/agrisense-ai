import os

import joblib
import pandas as pd
from config import (
    FERTILIZER_DATASET_PATH,
    FERTILIZER_ENCODER_PATH,
    FERTILIZER_MODEL_PATH,
    FERTILIZER_SCALER_PATH,
    SAVED_MODELS_DIR,
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


def train_fertilizer_model():
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

    print("⏳ Loading fertilizer dataset...")
    df = pd.read_csv(FERTILIZER_DATASET_PATH)

    # Encode categorical features if any (e.g., Soil Type, Crop Type)
    label_encoders = {}
    for col in ["Soil Type", "Crop Type"]:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            label_encoders[col] = le

    # Define features and target
    target_col = "Fertilizer Name"
    X = df.drop(columns=[target_col])
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("🤖 Training Random Forest Classifier for Fertilizer...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n🎯 Fertilizer Model Accuracy: {acc * 100:.2f}%\n")

    # Save artifacts
    joblib.dump(model, FERTILIZER_MODEL_PATH)
    joblib.dump(scaler, FERTILIZER_SCALER_PATH)
    if label_encoders:
        joblib.dump(label_encoders, FERTILIZER_ENCODER_PATH)

    print(f"✅ Fertilizer artifacts saved successfully to {SAVED_MODELS_DIR}")


if __name__ == "__main__":
    train_fertilizer_model()
