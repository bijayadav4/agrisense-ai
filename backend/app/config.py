import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    PORT = int(os.getenv("PORT", 5000))
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    # Path to Module 1 ML artifacts
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Crop Model Paths
    MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../ml_models/saved_models/crop_recommendation_model.pkl"))
    SCALER_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../ml_models/saved_models/crop_scaler.pkl"))

    # Fertilizer Model Paths
    FERTILIZER_MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../ml_models/saved_models/fertilizer_model.pkl"))
    FERTILIZER_SCALER_PATH = os.path.abspath(
        os.path.join(BASE_DIR, "../../ml_models/saved_models/fertilizer_scaler.pkl")
    )
    FERTILIZER_ENCODER_PATH = os.path.abspath(
        os.path.join(BASE_DIR, "../../ml_models/saved_models/fertilizer_encoder.pkl")
    )

    # Plant Disease Model Path (optional Keras CNN)
    DISEASE_MODEL_PATH = os.path.abspath(
        os.path.join(BASE_DIR, "../../ml_models/saved_models/plant_disease_model.keras")
    )

    # Soil Image Classification Model (MobileNetV2 CNN)
    SOIL_CNN_MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../ml_models/saved_models/soil_cnn_model.pth"))

    # Spatio-Temporal LSTM & Bottleneck Fusion Model
    FUSION_LSTM_MODEL_PATH = os.path.abspath(
        os.path.join(BASE_DIR, "../../ml_models/saved_models/fusion_lstm_model.pth")
    )
