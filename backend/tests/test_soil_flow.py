import io
import unittest
from pypdf import PdfReader
from app import create_app


class SoilFlowAuditTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_crop_empty_inputs_return_400(self):
        """Khali N/P/K/pH inputs par 400 Bad Request milna chahiye."""
        payload_empty = {
            "N": "",
            "P": 48,
            "K": 40,
            "ph": 6.4,
            "temperature": 24,
            "humidity": 80,
            "rainfall": 100,
        }
        res = self.client.post("/api/recommend/crop", json=payload_empty)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Soil Health Card", data["error"])

    def test_crop_invalid_bounds_return_400(self):
        """Negative NPK ya invalid pH par 400 milna chahiye."""
        # Negative N
        res1 = self.client.post(
            "/api/recommend/crop",
            json={"N": -5, "P": 20, "K": 20, "ph": 6.5, "temperature": 25, "humidity": 70, "rainfall": 100},
        )
        self.assertEqual(res1.status_code, 400)
        self.assertIn("negative", res1.get_json()["error"].lower())

        # Out-of-bounds pH
        res2 = self.client.post(
            "/api/recommend/crop",
            json={"N": 50, "P": 20, "K": 20, "ph": 15.2, "temperature": 25, "humidity": 70, "rainfall": 100},
        )
        self.assertEqual(res2.status_code, 400)
        self.assertIn("between 0.0 and 14.0", res2.get_json()["error"])

    def test_fertilizer_empty_inputs_return_400(self):
        """Fertilizer me khali N, P, K par 400 milna chahiye (500 crash nahi hona chahiye)."""
        payload_empty = {
            "N": "",
            "P": 20,
            "K": 15,
            "crop_type": "Paddy",
            "soil_type": "Clayey",
        }
        res = self.client.post("/api/recommend/fertilizer", json=payload_empty)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Soil Health Card", data["error"])

    def test_fertilizer_negative_inputs_return_400(self):
        """Negative NPK par 400 milna chahiye."""
        payload_neg = {
            "N": 40,
            "P": -10,
            "K": 15,
            "crop_type": "Paddy",
            "soil_type": "Clayey",
        }
        res = self.client.post("/api/recommend/fertilizer", json=payload_neg)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("negative", data["error"].lower())

    def test_crop_demo_estimated_data_source(self):
        """Demo estimated data source hone par response me warning tag aana chahiye."""
        payload = {
            "N": 90,
            "P": 50,
            "K": 45,
            "ph": 6.8,
            "temperature": 25,
            "humidity": 65,
            "rainfall": 120,
            "data_source": "Demo estimated",
        }
        res = self.client.post("/api/recommend/crop", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["data_source"], "Demo estimated")
        self.assertTrue(data["is_estimated"])
        self.assertIsNotNone(data["estimated_warning"])

    def test_fertilizer_demo_estimated_warning(self):
        """Fertilizer me demo estimated values hone par 'Estimated, not for actual application' aana chahiye."""
        payload = {
            "N": 40,
            "P": 20,
            "K": 15,
            "crop_type": "Paddy",
            "soil_type": "Clayey",
            "data_source": "Demo estimated",
        }
        res = self.client.post("/api/recommend/fertilizer", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["data_source"], "Demo estimated")
        self.assertTrue(data["is_estimated"])
        self.assertIn("not for actual application", data["estimated_warning"])
        self.assertIn("not for actual application", data["scientific_plan"]["estimated_warning"])

    def test_pdf_report_with_demo_estimated_source(self):
        """Report PDF me N, P, K, pH, Data Source aur Demo estimated warning box aana chahiye."""
        payload = {
            "farmer_name": "Ramesh Kumar",
            "location": "Varanasi, UP",
            "area": 2.5,
            "area_unit": "Acres",
            "soil_type": "Loamy",
            "soil_source": "Demo data",
            "data_source": "Demo estimated",
            "is_estimated": True,
            "N": 90,
            "P": 50,
            "K": 45,
            "ph": 6.8,
            "crop_data": {
                "crop": "Wheat",
                "confidence": 94.0,
            },
            "fertilizer_data": {
                "fertilizer": "Urea / DAP",
                "dap_kg": 40.0,
                "dap_bags": 0.8,
                "urea_kg": 50.0,
                "urea_bags": 1.0,
                "mop_kg": 20.0,
                "mop_bags": 0.4,
            },
        }
        res = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        reader = PdfReader(io.BytesIO(res.data))
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        self.assertIn("Demo estimated", text)
        self.assertIn("Estimated Values Warning", text)
        self.assertIn("Estimated, not for actual application", text)
        self.assertIn("Soil Chemistry", text)

    def test_pdf_report_with_lab_test_source(self):
        """Report PDF me Lab test hone par amber warning nahi aana chahiye."""
        payload = {
            "farmer_name": "Suresh Patel",
            "location": "Surat, Gujarat",
            "area": 3.0,
            "area_unit": "Acres",
            "soil_type": "Black",
            "soil_source": "User-Selected",
            "data_source": "Lab test",
            "is_estimated": False,
            "N": 80,
            "P": 35,
            "K": 40,
            "ph": 7.2,
            "crop_data": {
                "crop": "Cotton",
                "confidence": 95.0,
            },
            "fertilizer_data": {
                "fertilizer": "Urea / DAP",
                "dap_kg": 30.0,
                "dap_bags": 0.6,
                "urea_kg": 45.0,
                "urea_bags": 0.9,
                "mop_kg": 15.0,
                "mop_bags": 0.3,
            },
        }
        res = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        reader = PdfReader(io.BytesIO(res.data))
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        self.assertIn("Lab test", text)
        self.assertNotIn("Estimated Values Warning", text)


if __name__ == "__main__":
    unittest.main()
