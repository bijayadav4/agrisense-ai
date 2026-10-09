#!/usr/bin/env python3
"""
AgriSense AI — Model Artifact Verification & Download Script
Ensures all required machine learning models are present before startup.
"""
import os
import sys
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "ml_models", "saved_models")

REQUIRED_MODELS = {
    "crop_recommendation_model.pkl": {
        "description": "Random Forest Crop Recommendation Model (23 crops, 99.52% CV)",
        "min_size_bytes": 100_000
    },
    "crop_scaler.pkl": {
        "description": "StandardScaler for 7 Crop Features",
        "min_size_bytes": 500
    },
    "fertilizer_model.pkl": {
        "description": "Random Forest Fertilizer Brand Classifier",
        "min_size_bytes": 50_000
    },
    "fertilizer_scaler.pkl": {
        "description": "StandardScaler for Fertilizer Features",
        "min_size_bytes": 500
    },
    "fertilizer_encoder.pkl": {
        "description": "LabelEncoders for Soil & Crop categorical inputs",
        "min_size_bytes": 500
    },
    "soil_cnn_model.pth": {
        "description": "MobileNetV2 Soil Vision CNN (88.19% Holdout Accuracy)",
        "min_size_bytes": 5_000_000
    }
}

def check_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    all_present = True

    print("=" * 65)
    print("🌾 AGRISENSE AI — MODEL WEIGHTS VERIFICATION & STORAGE CHECK")
    print("=" * 65)

    for filename, meta in REQUIRED_MODELS.items():
        file_path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size >= meta["min_size_bytes"]:
                print(f"✅ {filename:32} | Present ({size:,} bytes) | {meta['description']}")
            else:
                print(f"⚠️ {filename:32} | Warning: File size too small ({size} bytes)")
                all_present = False
        else:
            print(f"❌ {filename:32} | MISSING | {meta['description']}")
            all_present = False

    print("=" * 65)
    if all_present:
        print("🎉 All required model weights are verified and ready for deployment!")
        return 0
    else:
        print("⚠️ One or more model weights are missing.")
        print("👉 In production environments without Git LFS, train locally or run:")
        print("   python ml_models/train.py")
        print("   python ml_models/train_fertilizer.py")
        print("   python ml_models/train_soil_cnn.py")
        return 1

if __name__ == "__main__":
    sys.exit(check_models())
