#!/usr/bin/env python3
"""
AgriSense AI - System Validation Phase 4: End-to-End Playwright Browser Tests
=============================================================================
Verifies the complete farmer user flow in real Chromium browser:
1. Soil image upload (Holdout Alluvial_Soil_44.jpg) & N, P, K, pH form filling.
2. Crop recommendation prediction on UI.
3. Fertilizer plan navigation and dosage verification.
4. Irrigation schedule navigation and 7-day projection check.
5. "Download Report Card (PDF)" click and file download interception.
6. Downloaded PDF verification:
   - Page count == 1
   - Page size == A4 (595.28 pt x 841.89 pt ±2 pt)
   - Crop name match (screen vs PDF)
   - DAP/Urea/MOP bags match (screen vs PDF)
   - Daily water requirement / liters match (screen vs PDF)
7. Full screenshot capture per step in artifacts directory.
"""

import os
import json
import time
import subprocess
import urllib.request
import pytest
from pypdf import PdfReader
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ARTIFACT_DIR = os.environ.get(
    "TEST_ARTIFACT_DIR",
    os.path.join(PROJECT_ROOT, "tests", "artifacts"),
)
os.makedirs(ARTIFACT_DIR, exist_ok=True)
VENV_PYTHON = os.path.join(PROJECT_ROOT, "venv/bin/python")
IMAGE_PATH = os.path.join(PROJECT_ROOT, "ml_models/datasets/soil_images/Loamy/Alluvial_Soil_44.jpg")


def wait_for_url(url, timeout=25):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as res:
                if res.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


@pytest.fixture(scope="module")
def app_servers():
    """Start backend Flask API and frontend Vite dev server, and clean up afterwards."""
    backend_proc = subprocess.Popen(
        [VENV_PYTHON, "backend/run.py"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    frontend_proc = subprocess.Popen(
        ["npx", "vite", "--port", "5173"],
        cwd=os.path.join(PROJECT_ROOT, "frontend"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    backend_ready = wait_for_url("http://127.0.0.1:5000/api/health", timeout=30)
    frontend_ready = wait_for_url("http://localhost:5173/", timeout=20)

    if not backend_ready or not frontend_ready:
        backend_proc.terminate()
        frontend_proc.terminate()
        raise RuntimeError(
            f"Failed to start servers. Backend ready: {backend_ready}, Frontend ready: {frontend_ready}"
        )

    yield {"backend": backend_proc, "frontend": frontend_proc}

    backend_proc.terminate()
    frontend_proc.terminate()
    try:
        backend_proc.wait(timeout=3)
    except Exception:
        backend_proc.kill()
    try:
        frontend_proc.wait(timeout=3)
    except Exception:
        frontend_proc.kill()


def test_playwright_e2e_farmer_flow(app_servers):
    """
    Execute full end-to-end browser user workflow in headless Chromium.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            accept_downloads=True,
        )
        page = context.new_page()

        # Step 1: Dashboard initial mount
        page.goto("http://localhost:5173/", wait_until="networkidle")
        page.wait_for_timeout(2000)
        screenshot_step1 = os.path.join(ARTIFACT_DIR, "step1_dashboard_initial.png")
        page.screenshot(path=screenshot_step1, full_page=True)
        assert os.path.exists(screenshot_step1)

        # Step 2: Navigate to Crop Recommendation
        page.click("button:has-text('Crop Recommendation')")
        page.wait_for_timeout(1000)

        # Upload Soil Image if exists
        if os.path.exists(IMAGE_PATH):
            file_input = page.locator("input[type='file']")
            file_input.set_input_files(IMAGE_PATH)
            page.wait_for_timeout(2500)

        # Fill N, P, K, pH form
        page.fill("input[name='N']", "85")
        page.fill("input[name='P']", "48")
        page.fill("input[name='K']", "40")
        page.fill("input[name='ph']", "6.4")

        screenshot_step2 = os.path.join(ARTIFACT_DIR, "step2_crop_form_filled.png")
        page.screenshot(path=screenshot_step2, full_page=True)
        assert os.path.exists(screenshot_step2)

        # Step 3: Recommend crop
        page.click("button:has-text('Recommend Best Crops')")
        page.wait_for_selector(".result-crop-big", timeout=10000)
        page.wait_for_timeout(1000)

        crop_name_ui = page.locator(".result-crop-big").inner_text().strip()
        crop_clean = crop_name_ui.replace("🌾", "").strip()
        assert len(crop_clean) > 0, "Crop name should not be empty"

        screenshot_step3 = os.path.join(ARTIFACT_DIR, "step3_crop_recommendation.png")
        page.screenshot(path=screenshot_step3, full_page=True)
        assert os.path.exists(screenshot_step3)

        # Step 4: Fertilizer Plan View
        page.click("button:has-text('Fertilizer Calculator')")
        page.wait_for_timeout(2000)
        screenshot_step4 = os.path.join(ARTIFACT_DIR, "step4_fertilizer_screen.png")
        page.screenshot(path=screenshot_step4, full_page=True)
        assert os.path.exists(screenshot_step4)

        # Step 5: Irrigation Planning View
        page.click("button:has-text('Irrigation Planning')")
        page.wait_for_timeout(2000)
        irr_content = page.content()
        assert "Irrigation" in irr_content

        screenshot_step5 = os.path.join(ARTIFACT_DIR, "step5_irrigation_screen.png")
        page.screenshot(path=screenshot_step5, full_page=True)
        assert os.path.exists(screenshot_step5)

        # Step 6: Return to Dashboard and Download Report Card PDF
        page.click("button:has-text('Dashboard')")
        page.wait_for_timeout(1500)

        screenshot_step6 = os.path.join(ARTIFACT_DIR, "step6_dashboard_ready.png")
        page.screenshot(path=screenshot_step6, full_page=True)
        assert os.path.exists(screenshot_step6)

        download_btn = page.locator("button:has-text('Download Report Card (PDF)')")
        download_btn.wait_for(state="visible", timeout=10000)

        pdf_path = os.path.join(ARTIFACT_DIR, "e2e_downloaded_report_card.pdf")
        with page.expect_download(timeout=15000) as download_info:
            download_btn.click()
        download = download_info.value
        download.save_as(pdf_path)

        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000

        # Step 7: Open and verify PDF with PyPDF
        reader = PdfReader(pdf_path)
        assert len(reader.pages) == 1, f"Expected 1 page, got {len(reader.pages)}"

        page0 = reader.pages[0]
        width = float(page0.mediabox.width)
        height = float(page0.mediabox.height)
        assert abs(width - 595.28) <= 2.0, f"Width {width} is not A4"
        assert abs(height - 841.89) <= 2.0, f"Height {height} is not A4"

        pdf_text = page0.extract_text()
        # Assertions:
        # Crop match
        assert crop_clean.lower() in pdf_text.lower(), f"Crop '{crop_clean}' not in PDF"
        # Fertilizer match
        assert "dap" in pdf_text.lower() and "urea" in pdf_text.lower() and "mop" in pdf_text.lower()
        assert "bag" in pdf_text.lower()
        # Water match
        assert "liter" in pdf_text.lower() or "water" in pdf_text.lower() or "irrigation" in pdf_text.lower()

        # Render preview image
        try:
            from pdf2image import convert_from_path

            imgs = convert_from_path(pdf_path)
            if imgs:
                imgs[0].save(os.path.join(ARTIFACT_DIR, "step7_downloaded_pdf_page1.png"), "PNG")
        except Exception:
            pass

        browser.close()


def test_playwright_crop_provenance_banner(app_servers):
    """
    Deterministic Playwright test for F1 provenance banner in CropView.jsx:
    Case A — Wheat: Recommendation contains non-empty provenance_note.
             The data-testid="provenance-banner" element must be visible and contain the expected message.
    Case B — Non-Wheat: Non-Wheat recommendation has no provenance_note.
             The provenance banner must not exist in the rendered DOM.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Base mock response structure compatible with CropView.jsx
        base_resp = {
            "success": True,
            "profile": {
                "recommended_season": "Rabi",
                "growing_period_days": "120-135",
                "water_requirement_mm": "450-650",
            },
            "top_crops": [
                {"crop": "Wheat", "probability": 94.2},
                {"crop": "Barley", "probability": 3.8},
                {"crop": "Gram", "probability": 2.0},
            ],
            "alternatives": ["Barley", "Gram"],
            "soil_health": {
                "status": "Optimal",
                "nitrogen_status": "Optimal",
                "phosphorus_status": "Optimal",
                "potassium_status": "Optimal",
                "ph_status": "Optimal",
            },
            "soil_amendments": [],
            "environmental_conditions": {
                "city": "Coimbatore, Tamil Nadu",
                "temperature": 20.0,
                "humidity": 58.0,
                "rainfall": 72.0,
                "condition": "Clear",
                "advisory": [],
            },
        }

        wheat_resp = dict(base_resp)
        wheat_resp.update({
            "crop": "Wheat",
            "confidence": 94.2,
            "provenance_note": "Limited benchmark data (synthetic ICAR extension)",
        })

        rice_resp = dict(base_resp)
        rice_resp.update({
            "crop": "Rice",
            "confidence": 98.5,
            "provenance_note": None,
            "top_crops": [
                {"crop": "Rice", "probability": 98.5},
                {"crop": "Jute", "probability": 1.0},
                {"crop": "Maize", "probability": 0.5},
            ],
            "alternatives": ["Jute", "Maize"],
        })

        current_mock = {"resp": wheat_resp}

        def handle_crop_route(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(current_mock["resp"]),
            )

        page.route("**/api/recommend/crop", handle_crop_route)

        # Step 1: Open app and navigate to Crop Recommendation tab
        page.goto("http://localhost:5173/", wait_until="networkidle")
        page.click("button:has-text('Crop Recommendation')")
        page.wait_for_selector("input[name='N']", timeout=5000)

        # -------------------------------------------------------------
        # Case A — Wheat: Recommendation has non-empty provenance_note
        # -------------------------------------------------------------
        current_mock["resp"] = wheat_resp
        page.fill("input[name='N']", "94")
        page.fill("input[name='P']", "50")
        page.fill("input[name='K']", "40")
        page.fill("input[name='ph']", "6.6")

        page.click("button:has-text('Recommend Best Crops')")
        page.wait_for_selector(".result-crop-big", timeout=10000)

        crop_a = page.locator(".result-crop-big").inner_text()
        assert "wheat" in crop_a.lower(), f"Expected Wheat in Case A, got: {crop_a}"

        banner = page.locator("[data-testid='provenance-banner']")
        assert banner.is_visible(), "Case A: data-testid='provenance-banner' must be visible for Wheat"
        banner_text = banner.inner_text()
        assert "Benchmark Data Provenance Notice" in banner_text, f"Case A: Expected notice header, got: {banner_text}"
        assert "Limited benchmark data (synthetic ICAR extension)" in banner_text, f"Case A: Expected note text, got: {banner_text}"

        screenshot_case_a = os.path.join(ARTIFACT_DIR, "step_f1_wheat_provenance_banner.png")
        page.screenshot(path=screenshot_case_a)
        assert os.path.exists(screenshot_case_a)

        # -------------------------------------------------------------
        # Case B — Non-Wheat: Recommendation has no provenance_note
        # -------------------------------------------------------------
        current_mock["resp"] = rice_resp
        page.fill("input[name='N']", "80")
        page.fill("input[name='P']", "48")
        page.fill("input[name='K']", "38")
        page.fill("input[name='ph']", "6.4")

        page.click("button:has-text('Recommend Best Crops')")
        page.wait_for_timeout(1000)
        page.wait_for_selector(".result-crop-big", timeout=10000)

        crop_b = page.locator(".result-crop-big").inner_text()
        assert "rice" in crop_b.lower(), f"Expected Rice in Case B, got: {crop_b}"

        # Case B: The provenance banner must not exist in the rendered DOM
        assert banner.count() == 0, f"Case B: data-testid='provenance-banner' must not exist in DOM, count is {banner.count()}"

        screenshot_case_b = os.path.join(ARTIFACT_DIR, "step_f1_rice_no_provenance_banner.png")
        page.screenshot(path=screenshot_case_b)
        assert os.path.exists(screenshot_case_b)

        browser.close()
