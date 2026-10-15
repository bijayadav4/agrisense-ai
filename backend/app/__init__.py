import logging
import sys

from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config

try:
    from loguru import logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s")
    logger = logging.getLogger("agrisense")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for all routes across any origin
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Import Blueprints
    from app.routes.predict_routes import predict_bp
    from app.routes.weather_routes import weather_bp
    from app.services.ml_service import ml_engine
    from app.services.weather_lstm_service import weather_lstm_engine

    # Register Blueprints
    app.register_blueprint(predict_bp)
    app.register_blueprint(weather_bp)

    logger.info("AgriSense AI Backend initialized (models loaded once at startup singleton).")

    @app.route("/health", methods=["GET"])
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify(
            {
                "status": "online",
                "service": "AgriSense AI Backend",
                "version": "2.0.0",
                "models_loaded": {
                    "crop_random_forest": ml_engine.crop_model is not None,
                    "fertilizer_random_forest": ml_engine.fert_model is not None,
                    "soil_cnn_vision": ml_engine.soil_model is not None,
                    "fusion_lstm_prototype": ml_engine.fusion_model is not None,
                    "weather_forecasting_lstm": weather_lstm_engine.model is not None,
                },
                "features": [
                    "Crop Recommendation & Soil Analysis",
                    "Fertilizer Optimization & Dosage (Bags/Acre)",
                    "Live Agro-Meteorological Weather & GPS Sync",
                    "FAO-56 Penman-Monteith Irrigation Planning",
                    "Phenological Harvest Timeline & Economic Yield",
                    "Advisory Report Card PDF Generation",
                ],
            }
        ), 200

    return app
