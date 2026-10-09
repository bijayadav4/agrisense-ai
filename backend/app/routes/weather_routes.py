from flask import Blueprint, jsonify, request

from app.services.weather_service import get_weather_data

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/api/weather", methods=["GET"])
@weather_bp.route("/weather", methods=["GET"])
def fetch_weather():
    city = request.args.get("location", "New Delhi")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    lat_val = None
    lon_val = None

    if lat is not None and lat.strip() != "":
        try:
            lat_val = float(lat)
            if not (-90.0 <= lat_val <= 90.0):
                return jsonify({"success": False, "error": "Latitude must be between -90 and 90 degrees."}), 400
        except ValueError:
            return jsonify(
                {"success": False, "error": "Invalid latitude parameter. Value must be a valid number."}
            ), 400

    if lon is not None and lon.strip() != "":
        try:
            lon_val = float(lon)
            if not (-180.0 <= lon_val <= 180.0):
                return jsonify({"success": False, "error": "Longitude must be between -180 and 180 degrees."}), 400
        except ValueError:
            return jsonify(
                {"success": False, "error": "Invalid longitude parameter. Value must be a valid number."}
            ), 400

    weather = get_weather_data(city, lat=lat_val, lon=lon_val)
    return jsonify({"success": True, "data": weather}), 200
