import io
import unittest
from unittest import mock
from pypdf import PdfReader
from app import create_app


class SoilFlowAuditTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_crop_empty_inputs_return_400(self):
        """Empty N/P/K/pH inputs should return 400 Bad Request."""
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
        """Negative NPK or invalid pH should return 400 Bad Request."""
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
        """Empty N, P, K in fertilizer recommendation should return 400 Bad Request without crashing."""
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
        """Negative NPK should return 400 Bad Request."""
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
        """Demo estimated data source should include an estimated warning."""
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

    def test_demo_mode_fixed_input_returns_top1_rice(self):
        """STEP 3: Demo request with N=85, P=48, K=40, pH=6.4 + fixed weather (T=25, H=80, rain=200):
        - Label: 'Demo input (fixed weather)'
        - is_estimated: True
        - Fixed expected output: top-1 Rice
        """
        demo_payload = {
            "N": 85,
            "P": 48,
            "K": 40,
            "ph": 6.4,
            "temperature": 25,
            "humidity": 80,
            "rainfall": 200,
            "location": "Coimbatore, Tamil Nadu",
            "data_source": "Demo input (fixed weather)",
            "is_estimated": True,
        }
        res = self.client.post("/api/recommend/crop", json=demo_payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["crop"].lower(), "rice")
        self.assertEqual(data["top_crops"][0]["crop"].lower(), "rice")
        self.assertEqual(data["data_source"], "Demo input (fixed weather)")
        self.assertTrue(data["is_estimated"])

    def test_live_mode_weather_distinct_label_and_live_fetch(self):
        """In live mode without manual climate parameters:
        - Weather is fetched dynamically (or from cache)
        - Label remains distinct ('User entered' / 'Lab test'), NOT demo
        """
        live_payload = {
            "N": 85,
            "P": 48,
            "K": 40,
            "ph": 6.4,
            "location": "Coimbatore, Tamil Nadu",
            "data_source": "User entered",
        }
        res = self.client.post("/api/recommend/crop", json=live_payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["data_source"], "User entered")
        self.assertFalse(data["is_estimated"])

    def test_fertilizer_demo_estimated_warning(self):
        """Demo estimated values in fertilizer should have 'Estimated, not for actual application'."""
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
        """PDF report with Demo estimated source should include warning boxes and tags."""
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

        hindi_forbidden = ["kripya", "daalein", "karein", "bharein", "hai", "hoga", "nahi", "mausam", "mitti", "fasal", "kisan", "aur", "se", "ke liye", "badlein", "anivarya"]
        pdf_words = [w.strip(".,;:()[]{}<>!?\"'—–-") for w in text.lower().split()]
        for hw in hindi_forbidden:
            self.assertNotIn(hw, pdf_words, f"Found Hindi word '{hw}' in PDF text")

    def test_pdf_report_with_lab_test_source(self):
        """PDF report with Lab test source should not include the amber warning box."""
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

    def test_irrigation_drip_formula_known_input(self):
        """Audit Item 3 & 9: Known-input drip runtime test.
        Given: Net Need = 5.2 mm, Emitter = 2.0 LPH, Spacing = 0.4m x 0.8m, Efficiency = 90%.
        Application Rate = 2.0 / (0.4 * 0.8) = 6.25 mm/hr.
        Net Runtime (100% eff) = 5.2 / 6.25 = 0.832 hrs (~0.83 h).
        Gross Runtime (90% eff) = (5.2 / 6.25) / 0.90 = 5.2 / 5.625 = 0.924 hrs (~0.92 h or ~0.93 h).
        """
        payload = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "area": 2.0,
            "area_unit": "Acres",
            "irrigation_data": {
                "weekly_schedule": [
                    {
                        "day": "Day 1",
                        "rainfall_mm": 0.0,
                        "et0_mm": 5.2,
                        "temp_max": 30,
                    }
                ]
            },
        }
        res = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        reader = PdfReader(io.BytesIO(res.data))
        text = "".join([p.extract_text() for p in reader.pages])

        # Verify application rate & formula line
        self.assertIn("6.25 mm/hr", text)
        self.assertIn("0.83h @ 100% eff", text)
        self.assertIn("0.92h gross", text)

        # Check Day 1 action displays Irrigate with ~0.9h drip runtime
        self.assertIn("Irrigate (Drip 0.9h)", text)

    def test_irrigation_skip_rule(self):
        """Audit Item 2, 5 & 9: When rainfall >= ET0, net need is 0.0 mm and action is Skip (Rainfall)."""
        payload = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "irrigation_data": {
                "weekly_schedule": [
                    {
                        "day": "Rainy Day",
                        "rainfall_mm": 6.0,
                        "et0_mm": 4.8,
                        "temp_max": 28,
                    }
                ]
            },
        }
        res = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        reader = PdfReader(io.BytesIO(res.data))
        text = "".join([p.extract_text() for p in reader.pages])

        self.assertIn("Skip (Rainfall)", text)
        self.assertIn("0.0 mm", text)

    def test_weather_forecast_unavailable_in_pdf(self):
        """Audit Item 1 & 9: When weather forecast is missing/empty, PDF displays 'Weather forecast unavailable'
        instead of fabricating fake days or rainfall values.
        """
        payload = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "irrigation_data": {
                "weekly_schedule": []
            },
        }
        res = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        reader = PdfReader(io.BytesIO(res.data))
        text = "".join([p.extract_text() for p in reader.pages])

        self.assertIn("Weather forecast unavailable", text)
    def test_weather_forecast_starts_today_regression(self):
        """Regression test for Item 2: Forecast array offset bug after past_days=30.
        First date in forecast MUST equal today's calendar date in IST.
        """
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from app.services.weather_service import get_weather_data

        weather = get_weather_data("Coimbatore")
        self.assertIn("forecast", weather)
        self.assertGreaterEqual(len(weather["forecast"]), 7)

        today_ist = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
        first_date = weather["forecast"][0]["date"]
        self.assertEqual(first_date, today_ist, f"Forecast first date '{first_date}' must be today '{today_ist}'")
        self.assertEqual(weather["forecast"][0]["day"], "Today")

    def test_crop_top1_sanity_and_api_pdf_match(self):
        """Sanity test: Call /api/recommend/crop with known inputs, verify Top-1 & Top-3
        from ML API are dynamically present in the PDF without hardcoded assertions.
        """
        known_payload = {
            "N": 90,
            "P": 42,
            "K": 43,
            "ph": 6.5,
            "temperature": 24,
            "humidity": 82,
            "rainfall": 210,
        }
        crop_res = self.client.post("/api/recommend/crop", json=known_payload)
        self.assertEqual(crop_res.status_code, 200)
        c_data = crop_res.get_json()
        self.assertTrue(c_data["success"])
        top_crop_name = c_data["crop"].capitalize()
        self.assertIn("top_crops", c_data)
        self.assertGreaterEqual(len(c_data["top_crops"]), 1)

        pdf_payload = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "area": 2.0,
            "area_unit": "Acres",
            "crop_data": {
                "crop": c_data["crop"],
                "confidence": c_data["confidence"],
                "top_crops": c_data["top_crops"],
            },
        }
        res = self.client.post("/api/report/generate", json=pdf_payload)
        self.assertEqual(res.status_code, 200)
        reader = PdfReader(io.BytesIO(res.data))
        text = "".join([p.extract_text() for p in reader.pages])

        self.assertIn("1. Crop Recommendation (Machine Learning Model)", text)
        self.assertIn("Probability (%)", text)
        self.assertIn(top_crop_name, text)
        for crop_item in c_data["top_crops"][:3]:
            self.assertIn(crop_item["crop"].capitalize(), text)

    def test_crop_prediction_unavailable_when_no_data(self):
        """When crop_data is empty/missing, PDF shows '1. Crop Recommendation (Unavailable)'
        and does NOT fabricate fake ranks.
        """
        payload = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "area": 2.0,
            "area_unit": "Acres",
            "crop_data": {},
        }
        res = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        reader = PdfReader(io.BytesIO(res.data))
        text = "".join([p.extract_text() for p in reader.pages])

        self.assertIn("1. Crop Recommendation (Unavailable)", text)
        self.assertIn("Crop prediction unavailable", text)

    def test_fertilizer_bags_scaled_by_area(self):
        """Formula test: Total kg = kg/acre * area; bags = total kg / 50.
        For 2.0 acres: DAP 35.2 * 2 = 70.4 kg = 1.41 bags.
        """
        payload = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "area": 2.0,
            "area_unit": "Acres",
            "fertilizer_data": {
                "dap_kg": 35.2,
                "urea_kg": 56.6,
                "mop_kg": 16.8,
            },
        }
        res = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        reader = PdfReader(io.BytesIO(res.data))
        text = "".join([p.extract_text() for p in reader.pages])

        self.assertIn("Total for 2.0 Acres", text)
        self.assertIn("70.4 kg", text)
        self.assertIn("1.41 Bags", text)
        self.assertIn("35.2 × 2.0 = 70.4 kg = 1.41 bags", text)

    def test_irrigation_forecast_source_and_frequency_count(self):
        """Forecast source printed; frequency count matches schedule; fallback warning triggered."""
        # 1. Live source with varied days
        payload_live = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "area": 2.0,
            "area_unit": "Acres",
            "irrigation_data": {
                "forecast_source": "Open-Meteo API (Live Telemetry)",
                "weekly_schedule": [
                    {"day": "Today", "date": "2026-10-10", "rainfall_mm": 0.0, "et0_mm": 5.2, "temp_max": 30},
                    {"day": "Sun", "date": "2026-10-11", "rainfall_mm": 6.0, "et0_mm": 4.0, "temp_max": 28},
                    {"day": "Mon", "date": "2026-10-12", "rainfall_mm": 0.0, "et0_mm": 4.8, "temp_max": 29},
                ],
            },
        }
        res = self.client.post("/api/report/generate", json=payload_live)
        self.assertEqual(res.status_code, 200)
        reader = PdfReader(io.BytesIO(res.data))
        text_live = "".join([p.extract_text() for p in reader.pages])

        self.assertIn("Open-Meteo API", text_live)
        self.assertIn("Live Telemetry", text_live)
        # Day 1 and Day 3 irrigate, Day 2 skips (6mm rain >= 4mm et0) -> 2 of 3 days irrigated
        self.assertIn("Daily Water Balance", text_live)
        self.assertIn("2 of 3 days", text_live)
        self.assertIn("irrigated", text_live)

        # 2. Fallback source triggers warning banner
        payload_fallback = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "area": 2.0,
            "area_unit": "Acres",
            "irrigation_data": {
                "forecast_source": "Fallback (Agro-climatic Regional Baseline)",
                "weekly_schedule": [
                    {"day": "Today", "date": "2026-10-10", "rainfall_mm": 0.0, "et0_mm": 5.0, "temp_max": 30},
                    {"day": "Sun", "date": "2026-10-11", "rainfall_mm": 0.0, "et0_mm": 5.0, "temp_max": 30},
                ],
            },
        }
        res2 = self.client.post("/api/report/generate", json=payload_fallback)
        self.assertEqual(res2.status_code, 200)
        reader2 = PdfReader(io.BytesIO(res2.data))
        text_fallback = "".join([p.extract_text() for p in reader2.pages])
        self.assertIn("Forecast Advisory: Forecast unavailable, using estimated average", text_fallback)

    def test_harvest_sowing_date_states_and_cycle_label(self):
        """Harvest section:
        - When sowing date not provided: 'Sowing date not set; harvest date unavailable'
        - When sowing date >= today: 'Crop cycle: 125 days; harvest on <date>'
        - When sowing date < today: '<N> days remaining'
        - Source: '(Source: User entered)'
        """
        # Case A: Sowing date missing
        payload_none = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "harvest_data": {},
        }
        res_a = self.client.post("/api/report/generate", json=payload_none)
        text_a = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res_a.data)).pages])
        self.assertIn("Sowing date not set; harvest date unavailable", text_a)

        # Case B: Sowing date today/future
        payload_future = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "harvest_data": {
                "sowing_date": "2026-10-10",
                "crop_cycle_days": 125,
            },
        }
        res_b = self.client.post("/api/report/generate", json=payload_future)
        text_b = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res_b.data)).pages])
        self.assertIn("Crop cycle: 125 days; harvest on", text_b)
        self.assertIn("(Source: User entered)", text_b)

        # Case C: Sowing date in past (e.g. 2026-08-01, 70 days ago)
        payload_past = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "harvest_data": {
                "sowing_date": "2026-08-01",
                "crop_cycle_days": 125,
            },
        }
        res_c = self.client.post("/api/report/generate", json=payload_past)
        text_c = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res_c.data)).pages])
        self.assertIn("days remaining (harvest on", text_c)

    def test_crop_raw_probabilities_and_conditional_agronomic_notes(self):
        """Top-3 Crop table:
        - Raw model probabilities are displayed (share of 22 classes), sum not forced to 100%.
        - Agronomic Notes column present with header 'Agronomic Notes (General guidance)' when checks match.
        - Agronomic Notes column omitted when checks do not match.
        """
        # Case A: Matching moisture/thermal checks present
        payload_with_notes = {
            "farmer_name": "Test Farmer",
            "location": "Nashik, Maharashtra",
            "area": 2.0,
            "crop_data": {
                "crop": "Rice",
                "top_crops": [
                    {"rank": 1, "crop": "Rice", "probability": 0.55},
                    {"rank": 2, "crop": "Coconut", "probability": 0.16},
                    {"rank": 3, "crop": "Pomegranate", "probability": 0.09},
                ],
            },
            "rainfall": 200,
            "temperature": 25,
        }
        res_a = self.client.post("/api/report/generate", json=payload_with_notes)
        self.assertEqual(res_a.status_code, 200)
        text_a = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res_a.data)).pages])
        self.assertIn("Raw Probability (%)", text_a)
        self.assertIn("Agronomic Notes (General guidance)", text_a)
        self.assertIn("55.0%", text_a)
        self.assertIn("16.0%", text_a)
        self.assertIn("9.0%", text_a)

        # Case B: No agronomic checks match and no reasons provided -> column omitted
        payload_no_notes = {
            "farmer_name": "Test Farmer",
            "location": "Nashik, Maharashtra",
            "area": 2.0,
            "crop_data": {
                "crop": "Apple",
                "top_crops": [
                    {"rank": 1, "crop": "Apple", "probability": 0.50},
                    {"rank": 2, "crop": "Papaya", "probability": 0.20},
                    {"rank": 3, "crop": "Orange", "probability": 0.10},
                ],
            },
        }
        res_b = self.client.post("/api/report/generate", json=payload_no_notes)
        self.assertEqual(res_b.status_code, 200)
        text_b = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res_b.data)).pages])
        self.assertIn("Raw Probability (%)", text_b)
        self.assertNotIn("Agronomic Notes", text_b)

    def test_harvest_yield_and_msp_crop_lookup_rice_vs_jute(self):
        """Yield and MSP dynamically change based on top-1 crop lookup:
        - Rice: 48 Q/ha benchmark (~38.8 Q on 2 acres), ₹2,300 MSP, labeled UNVERIFIED and lookup table.
        - Jute: 28 Q/ha benchmark (~22.7 Q on 2 acres), 'not verified' MSP (unconfirmed source).
        """
        payload_rice = {
            "farmer_name": "Test Farmer",
            "location": "Nashik, Maharashtra",
            "area": 2.0,
            "area_unit": "Acres",
            "crop_data": {
                "crop": "Rice",
                "top_crops": [{"rank": 1, "crop": "Rice", "probability": 0.70}],
            },
        }
        res_rice = self.client.post("/api/report/generate", json=payload_rice)
        self.assertEqual(res_rice.status_code, 200)
        text_rice = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res_rice.data)).pages])
        self.assertIn("38.8", text_rice)
        self.assertIn("Quintals", text_rice)
        self.assertIn("₹2,300 / Quintal", text_rice)
        self.assertIn("lookup table", text_rice)
        self.assertIn("UNVERIFIED", text_rice)

        payload_jute = {
            "farmer_name": "Test Farmer",
            "location": "Nashik, Maharashtra",
            "area": 2.0,
            "area_unit": "Acres",
            "crop_data": {
                "crop": "Jute",
                "top_crops": [{"rank": 1, "crop": "Jute", "probability": 0.70}],
            },
        }
        res_jute = self.client.post("/api/report/generate", json=payload_jute)
        self.assertEqual(res_jute.status_code, 200)
        text_jute = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res_jute.data)).pages])
        self.assertIn("22.7", text_jute)
        self.assertIn("Quintals", text_jute)
        self.assertIn("not verified", text_jute)
        self.assertIn("lookup table", text_jute)
        self.assertIn("UNVERIFIED", text_jute)

        # Assert yield values are different
        self.assertNotEqual("38.8", "22.7")

    def test_muskmelon_top1_yield_and_msp_not_applicable(self):
        """STEP 4: Muskmelon / non-MSP crops:
        - When Muskmelon is top-1: yield displays 'Not applicable (no official yield/MSP benchmark)'
        - Muskmelon 190 Q/ha benchmark is removed and not rendered
        - MSP displays 'Not applicable (no official yield/MSP benchmark)'
        """
        payload_muskmelon = {
            "farmer_name": "Test Farmer",
            "location": "Nashik, Maharashtra",
            "area": 2.0,
            "area_unit": "Acres",
            "crop_data": {
                "crop": "Muskmelon",
                "top_crops": [{"rank": 1, "crop": "Muskmelon", "probability": 0.85}],
            },
        }
        res = self.client.post("/api/report/generate", json=payload_muskmelon)
        self.assertEqual(res.status_code, 200)
        text = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res.data)).pages])
        self.assertIn("Not applicable", text)
        self.assertIn("no official yield/MSP", text)
        self.assertNotIn("190", text)
        self.assertNotIn("153.8", text)

    def test_weather_location_coordinate_mismatch_warning(self):
        """Location mismatch test:
        - Haversine distance threshold 50 km.
        - Coimbatore text + Delhi coords produces location_mismatch: True and advisory warning.
        - Coordinates absent skips check.
        """
        from app.services.weather_service import get_weather_data

        # Coimbatore text + Delhi coordinates (28.6139, 77.2090)
        w_mismatch = get_weather_data(location="Coimbatore, Tamil Nadu", lat=28.6139, lon=77.2090)
        self.assertTrue(w_mismatch.get("location_mismatch"))
        self.assertIn("Location Advisory: Coordinate mismatch detected", w_mismatch.get("location_advisory", ""))

        # No coordinates provided -> check skipped
        w_nocoord = get_weather_data(location="Coimbatore, Tamil Nadu")
        self.assertFalse(w_nocoord.get("location_mismatch"))

        # PDF report with mismatch flag shows advisory warning box
        payload_mismatch = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "location_mismatch": True,
            "location_advisory": w_mismatch.get("location_advisory"),
        }
        res_pdf = self.client.post("/api/report/generate", json=payload_mismatch)
        text_pdf = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res_pdf.data)).pages])
        self.assertIn("Location Advisory: Coordinate mismatch detected", text_pdf)

    def test_irrigation_formula_rain_effective_rule_label(self):
        """Irrigation formula includes 'Rain counted fully as effective (no runoff loss)' label."""
        payload = {
            "farmer_name": "Test Farmer",
            "location": "Nashik, Maharashtra",
            "area": 2.0,
            "area_unit": "Acres",
            "irrigation_data": {
                "forecast_source": "Open-Meteo API (Live Telemetry)",
                "weekly_schedule": [
                    {"day": "Today", "date": "2026-10-10", "rainfall_mm": 0.0, "et0_mm": 5.2, "action": "Irrigate", "net_mm": 5.2}
                ],
            },
        }
        res = self.client.post("/api/report/generate", json=payload)
        text = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res.data)).pages])
        self.assertIn("Rain counted fully as effective (no runoff loss)", text)

    @mock.patch("app.services.weather_service.requests.get")
    def test_weather_api_429_mock_produces_fallback_in_pdf(self, mock_get):
        """When weather API returns 429 (rate-limited / error):
        - weather_service returns forecast_source: 'Fallback (Agro-climatic Regional Baseline)'
        - PDF report renders 'Fallback (Agro-climatic Regional Baseline)'
        - PDF report does NOT render 'Live Telemetry'
        - PDF report renders 'Forecast Advisory: Forecast unavailable' warning
        """
        # Mock requests.get to return 429
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        # Clear weather cache so mock takes effect
        from app.services.weather_service import WEATHER_CACHE, get_weather_data
        WEATHER_CACHE.clear()

        w_data = get_weather_data("Coimbatore")
        self.assertEqual(w_data.get("forecast_source"), "Fallback (Agro-climatic Regional Baseline)")

        # Generate PDF with this weather data
        payload = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "weather_data": w_data,
            "irrigation_data": {
                "forecast_source": w_data.get("forecast_source"),
                "weekly_schedule": w_data.get("forecast", []),
            },
        }
        res = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        text = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res.data)).pages])
        self.assertIn("Fallback", text)
        self.assertIn("Agro-climatic Regional Baseline", text)
        self.assertNotIn("Live Telemetry", text)
        self.assertIn("Forecast Advisory: Forecast unavailable", text)

    def test_live_telemetry_with_identical_7_days_triggers_forecast_advisory_warning(self):
        """When forecast_source claims 'Live Telemetry' but 7 days have identical values:
        - PDF report renders 'Forecast Advisory: Forecast unavailable' warning
        - PDF report switches label to 'Fallback (Agro-climatic Regional Baseline)'
        - PDF report does NOT claim 'Live Telemetry'
        """
        identical_schedule = [
            {"day": f"Day {i}", "date": f"2026-10-{10+i}", "rainfall_mm": 0.0, "et0_mm": 5.0, "temp_max": 30.0}
            for i in range(7)
        ]
        payload = {
            "farmer_name": "Test Farmer",
            "location": "Coimbatore, Tamil Nadu",
            "area": 2.0,
            "area_unit": "Acres",
            "irrigation_data": {
                "forecast_source": "Open-Meteo API (Live Telemetry)",
                "weekly_schedule": identical_schedule,
            },
        }
        res = self.client.post("/api/report/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        text = "".join([p.extract_text() for p in PdfReader(io.BytesIO(res.data)).pages])
        self.assertIn("Forecast Advisory: Forecast unavailable", text)
        self.assertIn("Fallback", text)
        self.assertNotIn("Live Telemetry", text)


if __name__ == "__main__":
    unittest.main()


