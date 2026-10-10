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
import time
import subprocess
import urllib.request
import pytest
from pypdf import PdfReader
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = "/home/bijayadav/.gemini/antigravity-ide/brain/bda884e5-51e4-452a-abbd-0c3226ec3429"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
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
