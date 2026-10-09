import os
import sys
import unittest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app


class AgriSenseAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "online")

    def test_weather_endpoint(self):
        response = self.client.get("/api/weather?location=Mumbai")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("temperature", data["data"])
        self.assertIn("humidity", data["data"])
        self.assertIn("rainfall", data["data"])
        self.assertIn("advisory", data["data"])

    def test_weather_gps_endpoint(self):
        response = self.client.get("/api/weather?lat=18.52&lon=73.85")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("temperature", data["data"])

    def test_crop_recommendation(self):
        payload = {"N": 90, "P": 42, "K": 43, "ph": 6.5, "location": "Mumbai"}
        response = self.client.post("/api/recommend/crop", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("crop", data)
        self.assertIn("confidence", data)
        self.assertIn("profile", data)
        self.assertIn("soil_health", data)
        self.assertIn("environmental_conditions", data)

    def test_crop_recommendation_validation_missing_fields(self):
        payload = {"N": 90, "P": 42}  # missing K and ph
        response = self.client.post("/api/recommend/crop", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_crop_recommendation_top3_schema(self):
        """Audit Fix #5 & #7: Response must return Top-3 crops with probabilities, ranks, and confidence gap."""
        payload = {
            "N": 90,
            "P": 42,
            "K": 43,
            "ph": 6.5,
            "temperature": 24.0,
            "humidity": 80.0,
            "rainfall": 120.0,
            "location": "Mumbai",
        }
        response = self.client.post("/api/recommend/crop", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])

        # Verify Top-3 list schema
        self.assertIn("top_crops", data)
        self.assertEqual(len(data["top_crops"]), 3)

        for idx, item in enumerate(data["top_crops"]):
            self.assertEqual(item["rank"], idx + 1)
            self.assertIn("crop", item)
            self.assertIn("probability", item)
            self.assertIn("confidence", item)
            self.assertIn("profile", item)
            self.assertGreaterEqual(item["probability"], 0.0)
            self.assertLessEqual(item["probability"], 1.0)

        # Verify probabilities are sorted descending
        self.assertGreaterEqual(data["top_crops"][0]["probability"], data["top_crops"][1]["probability"])
        self.assertGreaterEqual(data["top_crops"][1]["probability"], data["top_crops"][2]["probability"])

        # Ambiguity fields
        self.assertIn("is_ambiguous", data)
        self.assertIsInstance(data["is_ambiguous"], bool)
        self.assertIn("confidence_gap", data)

    def test_crop_recommendation_ambiguous_flag(self):
        """Audit Fix #5 & #7: If gap between top-1 and top-2 < 0.15, return is_ambiguous=True with warning banner."""
        from unittest.mock import patch

        import numpy as np
        from app.services.ml_service import ml_engine

        # Mock model predict_proba to simulate close probabilities (gap = 0.05 < 0.15)
        mock_probs = np.zeros((1, len(ml_engine.crop_model.classes_)))
        mock_probs[0, 0] = 0.42
        mock_probs[0, 1] = 0.37
        mock_probs[0, 2] = 0.10
        mock_probs[0, 3:] = (1.0 - 0.89) / max(1, len(ml_engine.crop_model.classes_) - 3)

        with patch.object(ml_engine.crop_model, "predict_proba", return_value=mock_probs):
            payload = {"N": 50, "P": 50, "K": 50, "ph": 6.5, "temperature": 25, "humidity": 60, "rainfall": 100}
            response = self.client.post("/api/recommend/crop", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data["is_ambiguous"])
            self.assertIsNotNone(data["ambiguity_warning"])
            self.assertIn("Ambiguous prediction", data["ambiguity_warning"])
            self.assertLess(data["confidence_gap"], 0.15)

    def test_crop_recommendation_invalid_inputs_400(self):
        """Audit Fix #7: Unknown/missing/invalid input formats must return 400 Bad Request."""
        # Non-numeric parameter
        res_non_num = self.client.post("/api/recommend/crop", json={"N": "invalid_str", "P": 40, "K": 40, "ph": 6.5})
        self.assertEqual(res_non_num.status_code, 400)
        self.assertFalse(res_non_num.get_json()["success"])

        # Out-of-bounds pH
        res_ph_high = self.client.post("/api/recommend/crop", json={"N": 40, "P": 40, "K": 40, "ph": 15.5})
        self.assertEqual(res_ph_high.status_code, 400)

        # Negative nutrients
        res_neg = self.client.post("/api/recommend/crop", json={"N": -10, "P": 40, "K": 40, "ph": 6.5})
        self.assertEqual(res_neg.status_code, 400)

    def test_crop_fusion_experimental_flag(self):
        """Audit Fix #2: /api/crop/fusion must return is_experimental=True and prototype disclaimer."""
        payload = {"N": 90, "P": 42, "K": 43, "ph": 6.5, "location": "Mumbai"}
        response = self.client.post("/api/crop/fusion", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data.get("is_experimental"))
        self.assertEqual(data.get("pipeline_status"), "experimental_prototype")
        self.assertIn("experimental", data.get("production_notice", "").lower())

    def test_wheat_provenance_badge(self):
        """Audit Fix #1: Wheat predictions must provide limited benchmark provenance note."""
        payload = {
            "N": 95,
            "P": 50,
            "K": 40,
            "ph": 6.6,
            "temperature": 19.5,
            "humidity": 58,
            "rainfall": 72,
            "location": "Karnal",
        }
        response = self.client.post("/api/recommend/crop", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["crop"].lower(), "wheat")
        self.assertIsNotNone(data.get("provenance_note"))
        self.assertIn("synthetic", data["provenance_note"].lower())

    def test_crop_recommendation_season_warning(self):
        """Finalization Step #3: Test seasonal suitability check and season_warning for out-of-season planting."""
        # Wheat in May (Month 5 - Off-Season for Rabi Wheat)
        payload_off_season = {
            "N": 95,
            "P": 50,
            "K": 40,
            "ph": 6.6,
            "temperature": 19.5,
            "humidity": 58,
            "rainfall": 72,
            "month": 5,
        }
        res_off = self.client.post("/api/recommend/crop", json=payload_off_season)
        self.assertEqual(res_off.status_code, 200)
        data_off = res_off.get_json()
        self.assertTrue(data_off["is_out_of_season"])
        self.assertIsNotNone(data_off["season_warning"])
        self.assertIn("Seasonal Advisory", data_off["season_warning"])
        self.assertIn("May", data_off["season_warning"])

        # Wheat in November (Month 11 - Prime Sowing Season for Rabi Wheat)
        payload_in_season = {
            "N": 95,
            "P": 50,
            "K": 40,
            "ph": 6.6,
            "temperature": 19.5,
            "humidity": 58,
            "rainfall": 72,
            "month": 11,
        }
        res_in = self.client.post("/api/recommend/crop", json=payload_in_season)
        self.assertEqual(res_in.status_code, 200)
        data_in = res_in.get_json()
        self.assertFalse(data_in["is_out_of_season"])
        self.assertIsNone(data_in["season_warning"])

    def test_fertilizer_recommendation(self):
        payload = {
            "temperature": 26,
            "humidity": 52,
            "moisture": 38,
            "soil_type": "Sandy",
            "crop_type": "Maize",
            "N": 37,
            "P": 0,
            "K": 0,
        }
        response = self.client.post("/api/recommend/fertilizer", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("fertilizer", data)
        self.assertIn("profile", data)
        self.assertIn("dosage_guidelines", data["profile"])
        self.assertIn("scientific_plan", data)

    def test_paddy_recommendation(self):
        payload = {
            "N": 85,
            "P": 48,
            "K": 40,
            "ph": 6.4,
            "temperature": 24,
            "humidity": 82,
            "rainfall": 220,
            "location": "Thanjavur",
        }
        response = self.client.post("/api/recommend/crop", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["crop"].lower(), "rice")
        self.assertGreater(data["confidence"], 80)

    def test_wheat_recommendation(self):
        payload = {
            "N": 95,
            "P": 50,
            "K": 40,
            "ph": 6.6,
            "temperature": 19.5,
            "humidity": 58,
            "rainfall": 72,
            "location": "Karnal",
        }
        response = self.client.post("/api/recommend/crop", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["crop"].lower(), "wheat")
        self.assertGreater(data["confidence"], 90)

    def test_weather_invalid_lat_non_numeric(self):
        response = self.client.get("/api/weather?lat=abc&lon=73.85")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid latitude parameter", data["error"])

    def test_weather_invalid_lon_non_numeric(self):
        response = self.client.get("/api/weather?lat=18.52&lon=xyz")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid longitude parameter", data["error"])

    def test_weather_lat_out_of_range(self):
        response = self.client.get("/api/weather?lat=95.0&lon=73.85")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("between -90 and 90", data["error"])

    def test_weather_lon_out_of_range(self):
        response = self.client.get("/api/weather?lat=18.52&lon=200.0")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_fertilizer_dosage_soil_adjusted_binding(self):
        payload = {
            "crop_type": "Paddy",
            "soil_type": "Clayey",
            "temperature": 26,
            "humidity": 60,
            "moisture": 70,
            "N": 40,
            "P": 20,
            "K": 15,
        }
        response = self.client.post("/api/recommend/fertilizer", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        plan = data["scientific_plan"]
        self.assertTrue(plan["has_soil_test"])
        self.assertTrue(plan["active_rate"]["is_soil_adjusted"])
        # Strictly verify net adjusted values
        self.assertEqual(plan["active_rate"]["dap_kg"], 35.2)
        self.assertEqual(plan["active_rate"]["dap_bags"], 0.7)
        self.assertEqual(plan["active_rate"]["urea_kg"], 56.6)
        self.assertEqual(plan["active_rate"]["urea_bags"], 1.13)
        self.assertIn(plan["active_rate"]["mop_kg"], [16.8, 16.9])
        self.assertEqual(plan["active_rate"]["mop_bags"], 0.34)

    def test_fertilizer_dosage_blanket_binding(self):
        payload = {
            "crop_type": "Paddy",
            "soil_type": "Clayey",
            "temperature": 26,
            "humidity": 60,
            "moisture": 70,
            "N": 0,
            "P": 0,
            "K": 0,
        }
        response = self.client.post("/api/recommend/fertilizer", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        plan = data["scientific_plan"]
        self.assertFalse(plan["has_soil_test"])
        self.assertFalse(plan["active_rate"]["is_soil_adjusted"])
        # Strictly verify baseline blanket values
        self.assertEqual(plan["active_rate"]["dap_kg"], 52.8)
        self.assertEqual(plan["active_rate"]["dap_bags"], 1.06)
        self.assertIn(plan["active_rate"]["urea_kg"], [84.9, 85.0])
        self.assertEqual(plan["active_rate"]["mop_kg"], 27.0)

    def test_classify_soil_image_valid(self):
        import io

        from PIL import Image

        # Create small test in-memory JPEG image
        img = Image.new("RGB", (100, 100), color=(120, 80, 50))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        response = self.client.post(
            "/api/classify/soil-image", content_type="multipart/form-data", data={"image": (img_bytes, "test_soil.jpg")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn(data["soil_type"], ["Black", "Clayey", "Loamy", "Red", "Sandy"])
        self.assertGreater(data["confidence"], 0)
        self.assertIn("estimated_properties", data)
        self.assertIn("suitable_crops", data)

    def test_classify_soil_image_missing_file(self):
        response = self.client.post("/api/classify/soil-image")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_recommend_crop_spatiotemporal_valid(self):
        payload = {"N": 85, "P": 48, "K": 40, "ph": 6.4, "soil_type": "Clayey", "location": "Coimbatore"}
        response = self.client.post("/api/recommend/crop/spatiotemporal-fusion", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("crop", data)
        self.assertGreater(data["confidence"], 0)
        self.assertIn("bottleneck_features", data)
        self.assertEqual(len(data["bottleneck_features"]), 8)
        self.assertIn("fusion_architecture", data)
        self.assertIn("bottleneck_layer", data["fusion_architecture"])

    def test_recommend_crop_spatiotemporal_missing_param(self):
        payload = {"N": 85, "P": 48}  # missing K and ph
        response = self.client.post("/api/recommend/crop/spatiotemporal-fusion", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_irrigation_plan_endpoint(self):
        payload = {
            "crop": "rice",
            "growth_stage": "flowering",
            "soil_type": "Clayey",
            "area": 2.5,
            "area_unit": "acres",
            "temperature": 32,
            "humidity": 65,
            "rainfall": 0,
        }
        response = self.client.post("/api/irrigation/plan", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("crop_water_need_mm", data)
        self.assertIn("daily_liters", data)
        self.assertIn("drip_runtime_hours", data)
        self.assertIn("weekly_schedule", data)
        self.assertEqual(len(data["weekly_schedule"]), 7)
        self.assertGreater(data["daily_liters"], 0)

    def test_harvest_prediction_endpoint(self):
        payload = {"crop": "wheat", "sowing_date": "2026-09-01", "area": 2, "area_unit": "acres"}
        response = self.client.post("/api/harvest/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("expected_harvest_date", data)
        self.assertIn("days_remaining", data)
        self.assertIn("progress_percentage", data)
        self.assertIn("stages_timeline", data)
        self.assertEqual(len(data["stages_timeline"]), 5)
        self.assertIn("yield_prediction", data)
        self.assertGreater(data["yield_prediction"]["total_expected_quintals"], 0)

    def test_generate_report_card_pdf(self):
        """Finalization Step #5: Test PDF generation endpoint, size > 0, and verify text contents."""
        import io

        from pypdf import PdfReader

        payload = {
            "farmer_name": "Ramesh Patel",
            "location": "Coimbatore, Tamil Nadu",
            "area": 2.5,
            "area_unit": "Acres",
            "soil_type": "Clayey",
            "soil_source": "AI CNN Vision (94.3% Confidence)",
            "crop_data": {
                "crop": "Rice",
                "confidence": 92.5,
                "is_ambiguous": False,
                "top_crops": [
                    {"rank": 1, "crop": "rice", "probability": 0.925, "confidence": 92.5},
                    {"rank": 2, "crop": "maize", "probability": 0.045, "confidence": 4.5},
                    {"rank": 3, "crop": "jute", "probability": 0.015, "confidence": 1.5},
                ],
            },
            "fertilizer_data": {
                "fertilizer": "Urea / DAP Balanced",
                "dap_kg": 35.2,
                "dap_bags": 0.70,
                "urea_kg": 56.6,
                "urea_bags": 1.13,
                "mop_kg": 16.8,
                "mop_bags": 0.34,
            },
            "irrigation_data": {
                "et0_method": "open-meteo-fao56",
                "interval_days": 4,
                "daily_liters": 47512,
                "drip_runtime_hours": 0.6,
                "weekly_schedule": [
                    {
                        "day": "Day 1",
                        "temp_max": 30,
                        "rainfall_mm": 0,
                        "et0_mm": 5.8,
                        "net_mm": 5.8,
                        "action": "Irrigate (Drip 0.6h)",
                    }
                ],
            },
            "harvest_data": {
                "harvest_date": "December 18, 2026",
                "days_remaining": 70,
                "yield_quintals": 38.9,
                "msp_year": "2024-25",
                "msp_rs_per_quintal": 2300,
                "msp_type": "UNVERIFIED (Pending Official Gazette)",
            },
        }

        response = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertGreater(len(response.data), 1000)  # PDF size > 0

        # Verify PDF contents with PdfReader
        reader = PdfReader(io.BytesIO(response.data))
        self.assertGreater(len(reader.pages), 0)
        pdf_text = ""
        for page in reader.pages:
            pdf_text += page.extract_text()

        self.assertIn("Rice", pdf_text)
        self.assertIn("Ramesh Patel", pdf_text)
        self.assertIn("Local agriculture officer", pdf_text)
        self.assertIn("UNVERIFIED", pdf_text)


if __name__ == "__main__":
    unittest.main()
