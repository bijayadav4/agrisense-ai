import unittest

from app import create_app


class IrrigationValuesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_hand_calculated_etc_and_liters(self):
        """
        Hand-calculated Test 1:
        Inputs:
          ET0 = 5.0 mm/day
          Crop = 'rice', Stage = 'flowering' (Kc = 1.25 from FAO-56 Table 12)
          Area = 1.0 ha
          Rainfall = 0.0 mm
        Expected Values:
          ETc = ET0 * Kc = 5.0 * 1.25 = 6.25 mm/day
          Rain offset = 0.0 mm
          Net Depth = 6.25 mm/day
          Net Volume = 6.25 mm * 1.0 ha * 10,000 m2/ha = 62,500.0 Liters/day
          Drip Efficiency = 0.90 -> Gross Drip Volume = 62,500 / 0.90 = ~69,444.4 Liters/day
          Flood Efficiency = 0.60 -> Gross Flood Volume = 62,500 / 0.60 = ~104,166.7 Liters/day
        """
        payload = {"crop": "rice", "growth_stage": "flowering", "area_hectares": 1.0, "rainfall": 0.0, "et0": 5.0}
        res = self.client.post("/api/irrigation/plan", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertAlmostEqual(data["crop_water_need_mm"], 6.25, places=2)
        self.assertAlmostEqual(data["net_irrigation_depth_mm"], 6.25, places=2)
        self.assertAlmostEqual(data["daily_liters"], 62500.0, places=1)
        self.assertAlmostEqual(data["gross_drip_liters"], 62500.0 / 0.90, places=0)
        self.assertAlmostEqual(data["gross_flood_liters"], 62500.0 / 0.60, places=0)

    def test_rain_exceeds_etc_skips_irrigation(self):
        """
        Hand-calculated Test 2:
        Inputs:
          ET0 = 5.0 mm/day
          Crop = 'rice', Stage = 'flowering' (Kc = 1.25 => ETc = 6.25 mm)
          Rainfall = 10.0 mm (Rain > ETc)
        Expected Values:
          Rainfall satisfies field demand -> Status contains 'Skip irrigation' (case-insensitive)
          Net Volume = 0.0 Liters
        """
        payload = {"crop": "rice", "growth_stage": "flowering", "area_hectares": 1.0, "rainfall": 10.0, "et0": 5.0}
        res = self.client.post("/api/irrigation/plan", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("skip irrigation", data["status"].lower())
        self.assertEqual(data["daily_liters"], 0.0)

    def test_unknown_crop_returns_400(self):
        """
        Hand-calculated Test 3a:
        Input: crop = 'unknown_alien_crop'
        Expected: HTTP 400 Bad Request
        """
        payload = {"crop": "unknown_alien_crop", "area_hectares": 1.0}
        res = self.client.post("/api/irrigation/plan", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])

    def test_negative_area_returns_400(self):
        """
        Hand-calculated Test 3b:
        Input: area = -2.5
        Expected: HTTP 400 Bad Request
        """
        payload = {"crop": "wheat", "area_hectares": -2.5}
        res = self.client.post("/api/irrigation/plan", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])

    def test_fallback_hargreaves_equation(self):
        """
        Hand-calculated Test 4:
        Hargreaves Formula:
          ET0 = 0.0023 * (Tmean + 17.8) * sqrt(Tmax - Tmin) * Ra
        Inputs:
          Tmean = 28.0 °C
          Tmax - Tmin = 10.0 °C (e.g., Tmax=33, Tmin=23)
          Ra = 15.0 mm/day
        Expected Value:
          0.0023 * (28 + 17.8) * sqrt(10) * 15
          = 0.0023 * 45.8 * 3.16227766 * 15
          = 5.000673... =~ 5.0 mm/day
        """
        payload = {
            "crop": "wheat",
            "growth_stage": "vegetative",
            "area_hectares": 1.0,
            "temperature": 28.0,
            "tmax": 33.0,
            "tmin": 23.0,
            "ra": 15.0,
            "rainfall": 0.0,
        }
        res = self.client.post("/api/irrigation/plan", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["et0_method"], "hargreaves-fallback")
        self.assertAlmostEqual(data["reference_et0_mm"], 5.0, delta=0.05)


if __name__ == "__main__":
    unittest.main()
