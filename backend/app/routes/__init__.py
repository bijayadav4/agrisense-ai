from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)  # Enables CORS for all routes and origin header types

    from app.routes.predict_routes import predict_bp

    app.register_blueprint(predict_bp, url_prefix="/api")

    return app
