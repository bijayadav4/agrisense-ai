import os

import joblib
from config import CROP_MODEL_PATH, SAVED_MODELS_DIR
from preprocess import load_and_preprocess_data
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


def train_model():
    # Ensure saved_models directory exists
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

    print("⏳ Preprocessing dataset...")
    X_train, X_test, y_train, y_test = load_and_preprocess_data()

    print("🤖 Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n🎯 Model Accuracy: {acc * 100:.2f}%\n")
    print("Classification Report:\n", classification_report(y_test, y_pred))

    # Save Model Artifact
    joblib.dump(model, CROP_MODEL_PATH)
    print(f"✅ Trained model saved successfully to {CROP_MODEL_PATH}")


if __name__ == "__main__":
    train_model()
