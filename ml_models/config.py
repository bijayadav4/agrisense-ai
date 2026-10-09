import os

# Base Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data Paths
CROP_DATASET_PATH = os.path.join(BASE_DIR, "datasets", "Crop_recommendation.csv")
FERTILIZER_DATASET_PATH = os.path.join(BASE_DIR, "datasets", "Fertilizer Prediction.csv")

# Directory for Saved Models & Artifacts
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "saved_models")

# Output Model Artifact Paths
CROP_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "crop_recommendation_model.pkl")
CROP_SCALER_PATH = os.path.join(SAVED_MODELS_DIR, "crop_scaler.pkl")

FERTILIZER_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "fertilizer_model.pkl")
FERTILIZER_SCALER_PATH = os.path.join(SAVED_MODELS_DIR, "fertilizer_scaler.pkl")
FERTILIZER_ENCODER_PATH = os.path.join(SAVED_MODELS_DIR, "fertilizer_encoder.pkl")

# Crop Recommendation Schema
CROP_FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
CROP_TARGET_COLUMN = "label"

# Fertilizer Recommendation Schema
# Adjust these column names if your Fertilizer Prediction.csv uses slightly different headers
FERTILIZER_FEATURE_COLUMNS = [
    "Temparature",
    "Humidity",
    "Moisture",
    "Soil Type",
    "Crop Type",
    "Nitrogen",
    "Potassium",
    "Phosphorous",
]
FERTILIZER_TARGET_COLUMN = "Fertilizer Name"

# Soil Classification Vision Schema
SOIL_DATASET_DIR = os.path.join(BASE_DIR, "datasets", "soil_images")
SOIL_CNN_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "soil_cnn_model.pth")
SOIL_CLASSES = ["Black", "Clayey", "Loamy", "Red", "Sandy"]

# Spatio-Temporal LSTM & Bottleneck Fusion Model
FUSION_LSTM_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "fusion_lstm_model.pth")
