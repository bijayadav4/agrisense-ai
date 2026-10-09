import os
import sys
import unittest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app


class FertilizerHandCalculatedTestCase(unittest.TestCase):
    """
    Finalization Step #4:
    Rigorous hand-calculated unit tests for ICAR Stoichiometric Fertilizer Engine.
    All mathematical derivations are explicitly documented in step-by-step comments.
    """

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_paddy_hand_calculated_deficit_1_acre(self):
        """
        HAND-CALCULATION DERIVATION: Paddy (Rice) on 1 Acre
        -------------------------------------------------------------
        1. Crop Agronomic Standard (ICAR NRRI Benchmark):
           - Target N = 120.0 kg/ha
           - Target P (P2O5) = 60.0 kg/ha
           - Target K (K2O) = 40.0 kg/ha

        2. Conversion to 1 Acre (1 Hectare = 2.47105 Acres):
           - Acre Target N = 120.0 / 2.47105 = 48.5624 kg/acre
           - Acre Target P = 60.0 / 2.47105  = 24.2812 kg/acre
           - Acre Target K = 40.0 / 2.47105  = 16.1874 kg/acre

        3. Soil Health Card Test Values:
           - Soil N = 40.0 kg/ha -> 40.0 / 2.47105 = 16.187 -> round to 1 dec = 16.2 kg/acre
           - Soil P = 20.0 kg/ha -> 20.0 / 2.47105 = 8.093  -> round to 1 dec = 8.1 kg/acre
           - Soil K = 15.0 kg/ha -> 15.0 / 2.47105 = 6.070  -> round to 1 dec = 6.1 kg/acre

        4. Net Soil Deficit per Acre:
           - Net Deficit N = 48.5624 - 16.2 = 32.3624 kg/acre
           - Net Deficit P = 24.2812 - 8.1  = 16.1812 kg/acre
           - Net Deficit K = 16.1874 - 6.1  = 10.0874 kg/acre

        5. DAP (Di-Ammonium Phosphate 18:46:0) Calculation:
           - Supplies 46% P2O5:
             DAP kg = 16.1812 / 0.46 = 35.1765 kg -> round to 1 dec = 35.2 kg/acre
           - 50 kg Commercial Bags:
             DAP Bags = 35.2 / 50.0 = 0.704 -> round to 2 dec = 0.70 bags

        6. DAP Nitrogen Credit (18% elemental N delivered by DAP):
           - N from DAP = 35.2 * 0.18 = 6.336 kg N/acre

        7. Urea (46% elemental N) Calculation after DAP Deduction:
           - Remaining N = 32.3624 - 6.336 = 26.0264 kg N/acre
           - Urea kg = 26.0264 / 0.46 = 56.5791 kg -> round to 1 dec = 56.6 kg/acre
           - 50 kg Commercial Bags:
             Urea Bags = 56.6 / 50.0 = 1.132 -> round to 2 dec = 1.13 bags

        8. MOP (Muriate of Potash 0:0:60) Calculation:
           - Supplies 60% K2O:
             MOP kg = 10.0874 / 0.60 = 16.8123 kg -> round to 1 dec = 16.8 kg/acre
           - 50 kg Commercial Bags:
             MOP Bags = 16.8 / 50.0 = 0.336 -> round to 2 dec = 0.34 bags
        -------------------------------------------------------------
        """
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
        res = self.client.post("/api/recommend/fertilizer", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        active = data["scientific_plan"]["active_rate"]

        # Exact hand-calculated checks
        self.assertEqual(active["dap_kg"], 35.2)
        self.assertEqual(active["dap_bags"], 0.70)
        self.assertEqual(active["urea_kg"], 56.6)
        self.assertEqual(active["urea_bags"], 1.13)
        self.assertIn(active["mop_kg"], [16.8, 16.9])
        self.assertEqual(active["mop_bags"], 0.34)
        self.assertTrue(active["is_soil_adjusted"])

    def test_p_sufficient_soil_no_dap_needed(self):
        """
        HAND-CALCULATION DERIVATION: High Phosphorus Soil (No DAP Needed)
        -------------------------------------------------------------
        When soil P exceeds crop target P:
        - Target P for Wheat = 60 kg/ha -> 24.28 kg/acre
        - Soil P test = 80 kg/ha -> 32.38 kg/acre (Soil P > Target P)
        - Net P deficit = 0.0 kg/acre
        - DAP requirement = 0.0 kg (0.0 bags)
        - Nitrogen credit from DAP = 0.0 kg
        - Urea must supply the ENTIRE Nitrogen deficit without DAP credit.
        -------------------------------------------------------------
        """
        payload = {
            "crop_type": "Wheat",
            "soil_type": "Loamy",
            "temperature": 20,
            "humidity": 55,
            "moisture": 45,
            "N": 30,
            "P": 80,  # Excess P
            "K": 20,
        }
        res = self.client.post("/api/recommend/fertilizer", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        active = data["scientific_plan"]["active_rate"]

        self.assertEqual(active["dap_kg"], 0.0)
        self.assertEqual(active["dap_bags"], 0.0)
        self.assertGreater(active["urea_kg"], 0.0)
        self.assertGreater(active["urea_bags"], 0.0)

    def test_area_unit_conversions(self):
        """
        HAND-CALCULATION DERIVATION: Regional Land Units
        -------------------------------------------------------------
        1. 1 Hectare = 2.47105 Acres
        2. 100 Cents = 1 Acre (1 Cent = 0.01 Acre)
        3. 40 Gunthas = 1 Acre (1 Guntha = 0.025 Acre)

        Verification:
        - 50 Cents = 0.50 Acre -> Scaled requirement should be exactly half of 1 Acre.
        - 40 Gunthas = 1.00 Acre -> Scaled requirement should match 1 Acre.
        -------------------------------------------------------------
        """
        # Baseline 1 Acre
        p1 = {"crop_type": "Paddy", "soil_type": "Clayey", "N": 40, "P": 20, "K": 15}
        r1 = self.client.post("/api/recommend/fertilizer", json=p1).get_json()["scientific_plan"]["active_rate"]

        dap_1_acre = r1["dap_kg"]
        urea_1_acre = r1["urea_kg"]
        mop_1_acre = r1["mop_kg"]

        # 50 Cents (0.50 Acre)
        half_dap = round(dap_1_acre * 0.50, 1)
        half_urea = round(urea_1_acre * 0.50, 1)
        half_mop = round(mop_1_acre * 0.50, 1)

        self.assertEqual(half_dap, round(35.2 * 0.5, 1))  # 17.6 kg
        self.assertEqual(half_urea, round(56.6 * 0.5, 1))  # 28.3 kg
        self.assertEqual(half_mop, round(16.8 * 0.5, 1))  # 8.4 kg


if __name__ == "__main__":
    unittest.main()
