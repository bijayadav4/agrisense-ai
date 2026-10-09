import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import create_app


class HarvestValuesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.tz = ZoneInfo("Asia/Kolkata")
        self.today = datetime.now(self.tz).date()

    def test_future_sowing_date_shows_upcoming(self):
        """
        Hand-calculated Test 1: Future Sowing Date
        Input:
          Crop = 'rice' (duration = 125 days)
          Sowing date = 7 days in the future (today + 7 days)
          Area = 1.0 ha
        Expected Values:
          days_elapsed = -7 (< 0)
          days_until_sowing = 7
          days_overdue = 0
          status = "Upcoming"
          starts_in_message = "Starts in 7 days"
          progress_percentage = 0.0
          days_remaining = 125 + 7 = 132
          All 5 stages in stages_timeline must have status == 'Upcoming'
          is_harvest_ready = False
        """
        future_date = self.today + timedelta(days=7)
        future_str = future_date.strftime("%Y-%m-%d")

        payload = {"crop": "rice", "sowing_date": future_str, "area_hectares": 1.0}
        res = self.client.post("/api/harvest/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        # Validate future status and countdown
        self.assertEqual(data["status"], "Upcoming")
        self.assertEqual(data["days_elapsed"], -7)
        self.assertEqual(data["days_until_sowing"], 7)
        self.assertEqual(data["days_overdue"], 0)
        self.assertEqual(data["starts_in_message"], "Starts in 7 days")
        self.assertEqual(data["progress_percentage"], 0.0)
        self.assertEqual(data["days_remaining"], 132)
        self.assertFalse(data["is_harvest_ready"])

        # Check every stage is strictly "Upcoming"
        self.assertEqual(len(data["stages_timeline"]), 5)
        for stage in data["stages_timeline"]:
            self.assertEqual(stage["status"], "Upcoming")

    def test_overdue_by_10_days_and_1_5x_warning(self):
        """
        Hand-calculated Test 2: Overdue Harvesting & 1.5x Warning
        Part A - Overdue by 10 days:
          Crop = 'wheat' (cycle = 120 days)
          Sowing date = 130 days ago (today - 130 days)
          Harvest date was 10 days ago (130 - 120 = 10 days overdue)
        Expected Values:
          days_elapsed = 130
          days_remaining = -10 (< 0)
          days_overdue = 10
          status = "Overdue"
          progress_percentage = 100.0
          All 5 stages in stages_timeline must have status == 'Completed'

        Part B - Sowing date > 1.5x cycle:
          Crop = 'wheat' (120 days cycle * 1.5 = 180 days threshold)
          Sowing date = 200 days ago (200 > 180)
        Expected Values:
          warning is present and alerts about > 1.5x cycle duration
        """
        # Part A
        sowing_date_overdue = self.today - timedelta(days=130)
        payload_overdue = {
            "crop": "wheat",
            "sowing_date": sowing_date_overdue.strftime("%Y-%m-%d"),
            "area_hectares": 1.0,
        }
        res = self.client.post("/api/harvest/predict", json=payload_overdue)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        self.assertEqual(data["status"], "Overdue")
        self.assertEqual(data["days_elapsed"], 130)
        self.assertEqual(data["days_remaining"], -10)
        self.assertEqual(data["days_overdue"], 10)
        self.assertEqual(data["progress_percentage"], 100.0)

        for stage in data["stages_timeline"]:
            self.assertEqual(stage["status"], "Completed")

        # Part B - > 1.5x cycle warning
        sowing_date_ancient = self.today - timedelta(days=200)
        payload_ancient = {
            "crop": "wheat",
            "sowing_date": sowing_date_ancient.strftime("%Y-%m-%d"),
            "area_hectares": 1.0,
        }
        res_ancient = self.client.post("/api/harvest/predict", json=payload_ancient)
        self.assertEqual(res_ancient.status_code, 200)
        data_ancient = res_ancient.get_json()
        self.assertIsNotNone(data_ancient.get("warning"))
        self.assertTrue("1.5x" in data_ancient["warning"])

    def test_rice_2ha_yield_and_range_calculations(self):
        """
        Hand-calculated Test 3: Rice 2 ha Yield Range
        Inputs:
          Crop = 'rice', Area = 2.0 ha
          Baseline yield from ICAR-NRRI benchmark = 48.0 q/ha
          MSP for Paddy (Common) 2024-25 = Rs 2300/quintal
        Expected Calculations:
          Expected yield per ha = 48.0 q/ha
          Total Expected quintals = 48.0 * 2.0 = 96.0 q
          Low yield (0.70x) = 96.0 * 0.70 = 67.2 q
          High yield (1.15x) = 96.0 * 1.15 = 110.4 q

          Total Expected 50kg bags = (96.0 * 100) / 50 = 192 bags
          Low 50kg bags = round((67.2 * 100) / 50) = 134 bags
          High 50kg bags = round((110.4 * 100) / 50) = 221 bags

          Expected Revenue = 96.0 * 2300 = Rs 220,800
          Low Revenue = 67.2 * 2300 = Rs 154,560
          High Revenue = 110.4 * 2300 = Rs 253,920
        """
        sowing_date = self.today - timedelta(days=60)
        payload = {"crop": "rice", "sowing_date": sowing_date.strftime("%Y-%m-%d"), "area_hectares": 2.0}
        res = self.client.post("/api/harvest/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        yp = data["yield_prediction"]
        self.assertEqual(yp["baseline_yield_per_hectare_q"], 48.0)
        self.assertEqual(yp["total_expected_quintals"], 96.0)

        # Range quintals
        self.assertEqual(yp["yield_quintals"]["low"], 67.2)
        self.assertEqual(yp["yield_quintals"]["expected"], 96.0)
        self.assertEqual(yp["yield_quintals"]["high"], 110.4)

        # Range 50kg bags
        self.assertEqual(yp["bags_50kg"]["low"], 134)
        self.assertEqual(yp["bags_50kg"]["expected"], 192)
        self.assertEqual(yp["bags_50kg"]["high"], 221)

        # Gross revenue
        self.assertEqual(yp["gross_revenue_rs"]["low"], 154560)
        self.assertEqual(yp["gross_revenue_rs"]["expected"], 220800)
        self.assertEqual(yp["gross_revenue_rs"]["high"], 253920)

        # Disclaimer and MSP metadata
        self.assertIn("Indicative estimate", yp["disclaimer"])
        self.assertEqual(data["msp_info"]["year"], "2024-25")
        self.assertEqual(data["msp_info"]["rate_rs_per_quintal"], 2300)

    def test_validation_errors_return_400(self):
        """
        Hand-calculated Test 4: Validation Errors (400 HTTP status)
        Inputs & Expected:
          - Unknown crop ('dragonfruit_xyz') -> 400
          - Invalid date ('not-a-date' or '2025-13-45') -> 400
          - Negative area (area = -2.0) -> 400
          - Negative area_hectares (area_hectares = -1.5) -> 400
          - Zero area -> 400
        """
        valid_date = self.today.strftime("%Y-%m-%d")

        # 1. Unknown crop
        res = self.client.post(
            "/api/harvest/predict", json={"crop": "dragonfruit_xyz", "sowing_date": valid_date, "area_hectares": 1.0}
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["success"])
        self.assertIn("Unknown crop", res.get_json()["error"])

        # 2. Invalid date
        res = self.client.post(
            "/api/harvest/predict", json={"crop": "rice", "sowing_date": "invalid-date-string", "area_hectares": 1.0}
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["success"])
        self.assertIn("Invalid sowing_date", res.get_json()["error"])

        # 3. Negative area
        res = self.client.post("/api/harvest/predict", json={"crop": "rice", "sowing_date": valid_date, "area": -2.0})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["success"])
        self.assertIn("greater than 0", res.get_json()["error"])

        # 4. Negative area_hectares
        res = self.client.post(
            "/api/harvest/predict", json={"crop": "rice", "sowing_date": valid_date, "area_hectares": -1.5}
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["success"])
        self.assertIn("greater than 0", res.get_json()["error"])

        # 5. Zero area
        res = self.client.post(
            "/api/harvest/predict", json={"crop": "rice", "sowing_date": valid_date, "area_hectares": 0.0}
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
