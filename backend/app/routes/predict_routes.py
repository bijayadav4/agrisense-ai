import json
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.services.ml_service import ml_engine
from app.services.weather_service import get_weather_data

predict_bp = Blueprint("predict", __name__)


# -------------------------------------------------------------
# 1. Crop Recommendation Endpoints
# -------------------------------------------------------------
@predict_bp.route("/api/recommend/crop", methods=["POST"])
@predict_bp.route("/api/crop/recommend", methods=["POST"])
@predict_bp.route("/recommend-crop", methods=["POST"])
def recommend_crop():
    data = request.get_json() or {}

    # Required soil attributes
    required_fields = ["N", "P", "K", "ph"]
    for f in required_fields:
        if f not in data or data[f] is None or str(data[f]).strip() == "":
            return jsonify({"success": False, "error": "Enter N, P, K and pH values from your Soil Health Card or lab test."}), 400

    try:
        try:
            data["N"] = float(data["N"])
            data["P"] = float(data["P"])
            data["K"] = float(data["K"])
            data["ph"] = float(data["ph"])
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Enter numeric N, P, K and pH values from your Soil Health Card or lab test."}), 400

        # Validate physiological bounds
        if not (0 <= data["ph"] <= 14):
            return jsonify({"success": False, "error": "Soil pH must be between 0.0 and 14.0"}), 400
        if data["N"] < 0 or data["P"] < 0 or data["K"] < 0:
            return jsonify({"success": False, "error": "Soil nutrients (N, P, K) cannot be negative"}), 400

        location = str(data.get("location", "")).strip() or "Coimbatore"
        lat = data.get("lat")
        lon = data.get("lon")
        lat_val = float(lat) if lat is not None and str(lat).strip() != "" else None
        lon_val = float(lon) if lon is not None and str(lon).strip() != "" else None

        # Respect user-provided climate parameters (e.g. from Season or manual field test), fallback to live weather
        has_temp = data.get("temperature") is not None and str(data.get("temperature")).strip() != ""
        has_hum = data.get("humidity") is not None and str(data.get("humidity")).strip() != ""
        has_rain = data.get("rainfall") is not None and str(data.get("rainfall")).strip() != ""

        # Only fetch weather if needed (instant sub-millisecond execution when parameters provided)
        if not (has_temp and has_hum and has_rain):
            weather = get_weather_data(location, lat=lat_val, lon=lon_val) if location else {}
        else:
            weather = {}

        data["temperature"] = (
            float(data["temperature"])
            if has_temp
            else float(weather.get("temperature_last_30_days", weather.get("temperature", 25.0)))
        )
        data["humidity"] = (
            float(data["humidity"])
            if has_hum
            else float(weather.get("humidity_last_30_days", weather.get("humidity", 65.0)))
        )
        data["rainfall"] = (
            float(data["rainfall"])
            if has_rain
            else float(weather.get("rainfall_last_30_days", 85.0))
        )

        # Predict crop + alternatives + soil health analysis
        result = ml_engine.predict_crop(data)

        return jsonify(
            {
                "success": True,
                "crop": result["crop"],
                "confidence": result["confidence"],
                "profile": result["profile"],
                "top_crops": result.get("top_crops", []),
                "is_ambiguous": result.get("is_ambiguous", False),
                "ambiguity_warning": result.get("ambiguity_warning"),
                "confidence_gap": result.get("confidence_gap"),
                "is_out_of_season": result.get("is_out_of_season", False),
                "season_warning": result.get("season_warning"),
                "season_info": result.get("season_info"),
                "provenance_note": result.get("provenance_note"),
                "data_source": result.get("data_source", "User entered"),
                "is_estimated": result.get("is_estimated", False),
                "ambiguous_tag": result.get("ambiguous_tag"),
                "estimated_warning": result.get("estimated_warning"),
                "alternatives": result["alternatives"],
                "soil_health": result["soil_health"],
                "soil_amendments": result["soil_amendments"],
                "environmental_conditions": {
                    "city": weather.get("city", location),
                    "temperature": data["temperature"],
                    "humidity": data["humidity"],
                    "rainfall": data["rainfall"],
                    "condition": weather.get("condition", "Partly Cloudy"),
                    "advisory": weather.get("advisory", []),
                },
            }
        ), 200

    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "error": f"Invalid parameter value: {e!s}"}), 400
    except Exception as e:
        print(f"❌ Error in recommend_crop: {e!s}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# 2. Fertilizer Recommendation Endpoints
# -------------------------------------------------------------
@predict_bp.route("/api/recommend/fertilizer", methods=["POST"])
@predict_bp.route("/api/fertilizer/recommend", methods=["POST"])
@predict_bp.route("/recommend-fertilizer", methods=["POST"])
def recommend_fertilizer():
    try:
        data = request.get_json() or {}

        # Validate inputs
        required = ["N", "P", "K"]
        for f in required:
            if f not in data or data[f] is None or str(data[f]).strip() == "":
                return jsonify({"success": False, "error": "Enter N, P and K values from your Soil Health Card or lab test."}), 400

        try:
            data["N"] = float(data["N"])
            data["P"] = float(data["P"])
            data["K"] = float(data["K"])
            data["temperature"] = float(data.get("temperature", 25.0))
            data["humidity"] = float(data.get("humidity", 55.0))
            data["moisture"] = float(data.get("moisture", 40.0))
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Soil nutrients (N, P, K) and environmental parameters must be valid numbers."}), 400

        if data["N"] < 0 or data["P"] < 0 or data["K"] < 0:
            return jsonify({"success": False, "error": "Soil nutrients (N, P, K) cannot be negative"}), 400
        if data["moisture"] < 0:
            return jsonify({"success": False, "error": "Soil moisture cannot be negative"}), 400

        result = ml_engine.predict_fertilizer(data)

        return jsonify(
            {
                "success": True,
                "fertilizer": result["fertilizer"],
                "confidence": result["confidence"],
                "profile": result["profile"],
                "scientific_plan": result.get("scientific_plan"),
                "data_source": result.get("data_source", "User entered"),
                "is_estimated": result.get("is_estimated", False),
                "estimated_warning": result.get("estimated_warning"),
                "input_summary": result["input_summary"],
            }
        ), 200

    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "error": f"Invalid parameter value: {e!s}"}), 400
    except Exception as e:
        print(f"❌ Error in recommend_fertilizer: {e!s}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# 3. Soil Image Classification (CNN Vision) Endpoints
# -------------------------------------------------------------
@predict_bp.route("/api/classify/soil-image", methods=["POST"])
@predict_bp.route("/api/soil/classify", methods=["POST"])
def classify_soil_image():
    """Accepts soil photograph and predicts soil type using MobileNetV2 Vision CNN."""
    try:
        # Check for uploaded file in request.files
        file = None
        if "image" in request.files:
            file = request.files["image"]
        elif "file" in request.files:
            file = request.files["file"]

        if not file or file.filename == "":
            return jsonify(
                {
                    "success": False,
                    "error": "No soil image file provided. Please upload a valid JPG/PNG photograph of the soil.",
                }
            ), 400

        # Validate allowed extensions
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            return jsonify(
                {
                    "success": False,
                    "error": f"Invalid image format '{ext}'. Allowed formats: JPG, JPEG, PNG, WEBP, BMP.",
                }
            ), 400

        # Run vision inference
        result = ml_engine.predict_soil_image(file.stream)

        return jsonify(
            {
                "success": True,
                "soil_type": result["soil_type"],
                "confidence": result["confidence"],
                "is_low_confidence": result.get("is_low_confidence", False),
                "confidence_warning": result.get("confidence_warning"),
                "profile": result["profile"],
                # Deprecated alias: consumers should migrate to demo_reference_values_not_measured
                "estimated_properties": result["estimated_properties"],
                "demo_reference_values_not_measured": result.get(
                    "demo_reference_values_not_measured", result["estimated_properties"]
                ),
                "note": result.get("note"),
                "suitable_crops": result["suitable_crops"],
                "class_probabilities": result["class_probabilities"],
            }
        ), 200

    except Exception as e:
        print(f"❌ Error in classify_soil_image: {e!s}")
        return jsonify({"success": False, "error": f"Soil classification error: {e!s}"}), 500


# -------------------------------------------------------------
# 4. Spatio-Temporal LSTM & Feature Bottleneck Fusion Endpoint
# -------------------------------------------------------------
@predict_bp.route("/api/recommend/crop/spatiotemporal-fusion", methods=["POST"])
@predict_bp.route("/api/crop/fusion", methods=["POST"])
def recommend_crop_spatiotemporal():
    """
    Multimodal Precision Crop Recommendation combining:
    - Spatial Soil Chemistry (N, P, K, pH, Soil Type)
    - 7-Day Meteorological Sequence (Temporal Bi-LSTM)
    - Feature Bottleneck Dimension Compression
    """
    try:
        data = request.get_json() or {}

        required_fields = ["N", "P", "K", "ph"]
        missing = [f for f in required_fields if f not in data or data[f] is None]
        if missing:
            return jsonify(
                {"success": False, "error": f"Please provide all required soil parameters: {', '.join(missing)}"}
            ), 400

        location = str(data.get("location", "Coimbatore")).strip()
        lat = data.get("lat")
        lon = data.get("lon")
        lat_val = float(lat) if lat is not None and str(lat).strip() != "" else None
        lon_val = float(lon) if lon is not None and str(lon).strip() != "" else None

        # Fetch 5/7-day weather forecast from high-resolution meteorological engine
        weather = get_weather_data(location, lat=lat_val, lon=lon_val) if location else {}
        forecast_seq = weather.get("forecast", [])

        # Format sequence if available
        weather_sequence = []
        for day in forecast_seq:
            weather_sequence.append(
                {
                    "temperature": day.get("max_temp", 25.0),
                    "humidity": weather.get("humidity", 65.0),
                    "rainfall": day.get("rain_mm", 5.0),
                }
            )

        # Provide current environmental conditions as fallback/supplement
        data["temperature"] = float(data.get("temperature", weather.get("temperature", 26.0)))
        data["humidity"] = float(data.get("humidity", weather.get("humidity", 65.0)))
        data["rainfall"] = float(data.get("rainfall", weather.get("rainfall", 100.0)))

        result = ml_engine.predict_crop_spatiotemporal(data, weather_sequence=weather_sequence)

        return jsonify(
            {
                "success": True,
                "is_experimental": True,
                "pipeline_status": "experimental_prototype",
                "production_notice": "ST-LSTM multimodal fusion is an experimental research prototype and is NOT used in the production recommendation pipeline. Production recommendations are served exclusively by Pillar 1 (Random Forest Classifier).",
                "crop": result["crop"],
                "confidence": result["confidence"],
                "profile": result["profile"],
                "alternatives": result["alternatives"],
                "bottleneck_features": result["bottleneck_features"],
                "fusion_architecture": result["fusion_architecture"],
                "soil_health": result["soil_health"],
                "soil_amendments": result["soil_amendments"],
                "environmental_conditions": {
                    "city": weather.get("city", location),
                    "temperature": data["temperature"],
                    "humidity": data["humidity"],
                    "rainfall": data["rainfall"],
                    "condition": weather.get("condition", "Partly Cloudy"),
                    "advisory": weather.get("advisory", []),
                },
            }
        ), 200

    except Exception as e:
        print(f"❌ Error in recommend_crop_spatiotemporal: {e!s}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# 5. Irrigation Planning Endpoints
# -------------------------------------------------------------
@predict_bp.route("/api/irrigation/plan", methods=["POST"])
@predict_bp.route("/api/irrigation/calculate", methods=["POST"])
def get_irrigation_plan():
    """
    Computes precise crop evapotranspiration (ETc), effective rain offset,
    and drip/sprinkler runtimes using Open-Meteo FAO-56 & Hargreaves principles.
    """
    try:
        data = request.get_json() or {}

        # Support regional land units or explicit area_hectares
        area = float(data.get("area", 1.0)) if data.get("area") is not None else 1.0
        unit = str(data.get("area_unit", "hectare")).strip().lower()
        if "area_hectares" in data and data["area_hectares"] is not None:
            area_ha = float(data["area_hectares"])
        elif unit in ["acre", "acres"]:
            area_ha = area * 0.404686
        elif unit in ["cent", "cents"]:
            area_ha = area * 0.00404686
        elif unit in ["guntha", "gunthas"]:
            area_ha = area * 0.010117
        elif unit in ["bigha", "bighas"]:
            area_ha = area * 0.16187
        else:
            area_ha = area

        if area_ha <= 0:
            return jsonify(
                {"success": False, "error": "Cultivated farm area must be positive and greater than 0."}
            ), 400

        data["area_hectares"] = round(area_ha, 4)

        # Synchronize live weather if location is provided and climate params are absent
        location = str(data.get("location", "")).strip()
        lat = data.get("lat")
        lon = data.get("lon")
        lat_val = float(lat) if lat is not None and str(lat).strip() != "" else None
        lon_val = float(lon) if lon is not None and str(lon).strip() != "" else None

        has_temp = data.get("temperature") is not None and str(data.get("temperature")).strip() != ""
        has_hum = data.get("humidity") is not None and str(data.get("humidity")).strip() != ""
        has_rain = data.get("rainfall") is not None and str(data.get("rainfall")).strip() != ""

        if location and not (has_temp and has_hum and has_rain):
            weather = get_weather_data(location, lat=lat_val, lon=lon_val)
            if not has_temp:
                data["temperature"] = float(weather.get("temperature", 28.0))
            if not has_hum:
                data["humidity"] = float(weather.get("humidity", 60.0))
            if not has_rain:
                data["rainfall"] = float(weather.get("rainfall", 0.0))
            if "et0" not in data and weather.get("et0_fao_evapotranspiration") is not None:
                data["et0_fao_evapotranspiration"] = float(weather["et0_fao_evapotranspiration"])
            if "forecast" not in data and weather.get("forecast"):
                data["forecast"] = weather.get("forecast")
            if "lat" not in data and weather.get("latitude"):
                data["lat"] = weather.get("latitude")
            if "temperature_max" not in data and weather.get("temperature_max"):
                data["temperature_max"] = weather.get("temperature_max")
            if "temperature_min" not in data and weather.get("temperature_min"):
                data["temperature_min"] = weather.get("temperature_min")

        plan = ml_engine.calculate_irrigation_plan(data)
        return jsonify({"success": True, **plan}), 200

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        print(f"❌ Error in get_irrigation_plan: {e!s}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# 6. Harvest Prediction & Phenological Timeline Endpoints
# -------------------------------------------------------------
@predict_bp.route("/api/harvest/predict", methods=["POST"])
@predict_bp.route("/api/harvest/timeline", methods=["POST"])
def get_harvest_prediction():
    """
    Predicts maturity timeline, phenological growth stage progress,
    and expected crop yield (quintals & 50kg bags) from sowing date.
    Strictly validates crop existence, sowing date, and positive area.
    """
    try:
        data = request.get_json() or {}

        # 1. Validate crop
        crop = str(data.get("crop", "")).strip().lower()
        if not crop:
            return jsonify({"success": False, "error": "crop parameter is required"}), 400
        supported_crops = ml_engine.crop_cycles_data.get("crops", {})
        if crop not in supported_crops:
            return jsonify(
                {
                    "success": False,
                    "error": f"Unknown crop '{crop}'. Supported crops: {', '.join(sorted(supported_crops.keys()))}",
                }
            ), 400

        # 2. Validate sowing_date
        sowing_date_str = str(data.get("sowing_date", "")).strip()
        if not sowing_date_str:
            return jsonify({"success": False, "error": "sowing_date is required in YYYY-MM-DD format"}), 400
        try:
            datetime.strptime(sowing_date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify(
                {"success": False, "error": f"Invalid sowing_date '{sowing_date_str}'. Expected YYYY-MM-DD format"}
            ), 400

        # 3. Validate area (area or area_hectares)
        area_ha_input = data.get("area_hectares")
        area_input = data.get("area")

        if area_ha_input is not None:
            try:
                area_ha = float(area_ha_input)
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "area_hectares must be a numeric value"}), 400
            if area_ha <= 0:
                return jsonify({"success": False, "error": "Area must be greater than 0"}), 400
        elif area_input is not None:
            try:
                area_val = float(area_input)
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "area must be a numeric value"}), 400
            if area_val <= 0:
                return jsonify({"success": False, "error": "Area must be greater than 0"}), 400

            unit = str(data.get("area_unit", "hectare")).strip().lower()
            if unit in ["acre", "acres"]:
                area_ha = area_val * 0.404686
            elif unit in ["cent", "cents"]:
                area_ha = area_val * 0.00404686
            elif unit in ["guntha", "gunthas"]:
                area_ha = area_val * 0.010117
            elif unit in ["bigha", "bighas"]:
                area_ha = area_val * 0.16187
            else:
                area_ha = area_val
        else:
            area_ha = 1.0

        if area_ha <= 0:
            return jsonify({"success": False, "error": "Area must be greater than 0"}), 400

        data["area_hectares"] = round(area_ha, 4)

        # 4. Optional variety_duration_days validation
        if (
            "variety_duration_days" in data
            and data["variety_duration_days"] is not None
            and str(data["variety_duration_days"]).strip() != ""
        ):
            try:
                v_days = int(data["variety_duration_days"])
                if v_days <= 0:
                    return jsonify({"success": False, "error": "variety_duration_days must be greater than 0"}), 400
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "variety_duration_days must be an integer"}), 400

        timeline = ml_engine.predict_harvest_timeline(data)
        return jsonify({"success": True, **timeline}), 200

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        print(f"❌ Error in get_harvest_prediction: {e!s}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# 7. Comprehensive Farmer Advisory Report Card PDF Endpoint
# -------------------------------------------------------------
@predict_bp.route("/api/report/generate", methods=["POST"])
def generate_report_card_pdf():
    """Generates official downloadable PDF report card covering all 4 pillars & soil diagnosis."""
    try:
        import io

        from flask import send_file

        from app.services.report_service import generate_farmer_report_card

        data = request.get_json() or {}
        pdf_bytes = generate_farmer_report_card(data)

        farmer_slug = str(data.get("farmer_name", "Farmer")).strip().replace(" ", "_") or "Farmer"
        filename = f"AgriSense_Advisory_{farmer_slug}_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"❌ Error generating report card PDF: {e!s}")
        return jsonify({"success": False, "error": f"Failed to generate PDF: {e!s}"}), 500


# -------------------------------------------------------------
# 8. Soil Crop Suitability General Guidance Endpoint (Source: UNVERIFIED)
# -------------------------------------------------------------
@predict_bp.route("/api/soil-crop-suitability", methods=["GET"])
@predict_bp.route("/api/soil/suitability", methods=["GET"])
def get_soil_crop_suitability():
    """Returns general agronomic soil crop suitability guidance (Source: UNVERIFIED)."""
    try:
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "soil_crop_suitability.json"
        )
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                suitability_data = json.load(f)
            return jsonify({"success": True, "data": suitability_data}), 200
        return jsonify({"success": False, "error": "Suitability data file not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

