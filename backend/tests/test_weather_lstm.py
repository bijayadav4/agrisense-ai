"""
AgriSense AI - Deep Bi-LSTM Weather Forecasting Unit Tests
=========================================================
Tests the model inference engine and API endpoints for 7-day weather predictions.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app
from app.services.weather_lstm_service import weather_lstm_engine



class WeatherLSTMTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_model_loaded(self):
        self.assertIsNotNone(weather_lstm_engine.model, "Weather LSTM PyTorch model should be loaded")
        self.assertIsNotNone(weather_lstm_engine.scaler, "Weather LSTM scaler should be loaded")

    def test_lstm_inference_bounds(self):
        result = weather_lstm_engine.predict_7day_forecast(lat=18.5204, lon=73.8567)
        self.assertIsNotNone(result)
        self.assertTrue(result.get("is_ai_predicted"))
        forecast = result.get("forecast", [])
        self.assertEqual(len(forecast), 7, "Should predict exactly 7 days")

        for day in forecast:
            self.assertIn("day", day)
            self.assertIn("max_temp", day)
            self.assertIn("min_temp", day)
            self.assertIn("humidity", day)
            self.assertIn("rain_mm", day)
            self.assertIn("rain_chance", day)
            self.assertIn("wind_speed", day)
            self.assertIn("condition", day)
            self.assertIn("icon", day)
            self.assertIn("et0", day)

            # Physical validity
            self.assertGreaterEqual(day["max_temp"], day["min_temp"])
            self.assertGreaterEqual(day["humidity"], 0.0)
            self.assertLessEqual(day["humidity"], 100.0)
            self.assertGreaterEqual(day["rain_mm"], 0.0)
            self.assertGreaterEqual(day["wind_speed"], 0.0)

    def test_endpoint_lstm_forecast(self):
        resp = self.client.get("/api/weather/lstm-forecast?lat=18.5204&lon=73.8567")
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertTrue(json_data["success"])
        self.assertIn("data", json_data)
        self.assertEqual(len(json_data["data"]["forecast"]), 7)

    def test_endpoint_weather_includes_lstm(self):
        resp = self.client.get("/api/weather?location=Pune&lat=18.5204&lon=73.8567")
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertTrue(json_data["success"])
        data = json_data["data"]
        self.assertIn("lstm_forecast", data)
        self.assertEqual(len(data["lstm_forecast"]["forecast"]), 7)


if __name__ == "__main__":
    unittest.main()
