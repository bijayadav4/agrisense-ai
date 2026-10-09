import joblib
import pandas as pd

# Import the updated configuration variable names
from config import (
    CROP_DATASET_PATH,
    CROP_FEATURE_COLUMNS,
    CROP_SCALER_PATH,
    CROP_TARGET_COLUMN,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_and_preprocess_data():
    # Load dataset
    df = pd.read_csv(CROP_DATASET_PATH)

    X = df[CROP_FEATURE_COLUMNS]
    y = df[CROP_TARGET_COLUMN]

    # Split dataset (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Standardize numerical features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save scaler artifact
    joblib.dump(scaler, CROP_SCALER_PATH)
    print(f"✅ Scaler saved successfully to {CROP_SCALER_PATH}")

    return X_train_scaled, X_test_scaled, y_train, y_test
