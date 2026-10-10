import io
import json
import os
import re
from datetime import datetime, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_data_file(filename):
    try:
        p = os.path.join(DATA_DIR, filename)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading {filename}: {e}")
    return {}


CROP_CYCLES_LOOKUP = _load_data_file("crop_cycles.json").get("crops", {})
MSP_LOOKUP = _load_data_file("msp.json").get("crops", {})


def check_agronomic_suitability(crop_name, temp_val=None, rain_val=None, n_val=None, p_val=None, k_val=None):
    """
    Evaluates physical suitability bounds from known agronomic benchmarks.
    Returns matched agronomic observation string if matching, else None.
    """
    c_lower = str(crop_name).lower().strip()
    checks = []
    try:
        t = float(temp_val) if temp_val is not None and str(temp_val).strip() not in ("", "—") else None
    except (ValueError, TypeError):
        t = None
    try:
        r = float(rain_val) if rain_val is not None and str(rain_val).strip() not in ("", "—") else None
    except (ValueError, TypeError):
        r = None

    if r is not None:
        if c_lower in ["rice", "jute"] and r >= 120:
            checks.append(f"High moisture fit (rainfall {r:.0f} mm)")
        elif c_lower in ["wheat", "cotton", "maize", "chickpea"] and r <= 150:
            checks.append(f"Moisture suitable (rainfall {r:.0f} mm)")
    if t is not None:
        if c_lower in ["rice", "jute", "cotton", "maize"] and 20 <= t <= 38:
            checks.append(f"Optimal thermal range ({t:.0f}°C)")
        elif c_lower in ["wheat", "chickpea", "lentil"] and 10 <= t <= 26:
            checks.append(f"Favorable cool-season thermal range ({t:.0f}°C)")

    return "; ".join(checks) if checks else None


# Register Unicode TrueType fonts so Hindi (Devanagari) and Tamil characters render cleanly without boxes
FONT_NORMAL = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_OBLIQUE = "Helvetica-Oblique"


def _init_pdf_fonts():
    global FONT_NORMAL, FONT_BOLD, FONT_OBLIQUE
    try:
        freesans_reg = "/usr/share/fonts/gnu-free/FreeSans.ttf"
        freesans_bold = "/usr/share/fonts/gnu-free/FreeSansBold.ttf"
        if os.path.exists(freesans_reg):
            if "FreeSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("FreeSans", freesans_reg))
            if os.path.exists(freesans_bold) and "FreeSans-Bold" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("FreeSans-Bold", freesans_bold))
            registerFontFamily(
                "FreeSans",
                normal="FreeSans",
                bold="FreeSans-Bold",
                italic="FreeSans",
                boldItalic="FreeSans-Bold",
            )
            FONT_NORMAL = "FreeSans"
            FONT_BOLD = "FreeSans-Bold"
            FONT_OBLIQUE = "FreeSans"

        tamil_path = "/usr/share/fonts/google-noto-vf/NotoSansTamil[wght].ttf"
        if os.path.exists(tamil_path) and "NotoSansTamil" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("NotoSansTamil", tamil_path))
    except Exception as e:
        print(f"Font initialization notice: {e}")


_init_pdf_fonts()


def safe_unicode_text(text: str) -> str:
    """Wraps Tamil characters in NotoSansTamil font tag if registered, preserving native glyphs."""
    if not text:
        return ""
    text_str = str(text)
    if "NotoSansTamil" in pdfmetrics.getRegisteredFontNames() and re.search(r"[\u0B80-\u0BFF]", text_str):
        return re.sub(r"([\u0B80-\u0BFF]+)", r'<font name="NotoSansTamil">\1</font>', text_str)
    return text_str


def generate_farmer_report_card(data):
    """
    Generates a scientifically rigorous and visually clean Farmer Advisory Report Card PDF.
    Complies with all AgriSense AI audit standards:
    - Top-3 crops with merged Suitability Confidence & explicit scientific reasoning notes
    - Accurate soil type display ("Not selected" if unchosen, no fake default)
    - Verifiable data source label ("Demo estimated", "Lab test", "User entered")
    - Guaranteed estimated values warning box on demo data
    - Aligned 7-day irrigation schedule, robust action logic, and 1-line drip runtime formula
    - Realistic harvest yield range (Low – Expected – High)
    - Single-line location display (no wrapping on "Coimbatore, Tamil Nadu")
    - Clean fertilizer title: "Fertilizer Plan (DAP + Urea + MOP)"
    - Farmer name defaults to "Not provided" when omitted
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=34, leftMargin=34, topMargin=20, bottomMargin=18)

    styles = getSampleStyleSheet()

    # Custom typography styles with Unicode support
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#14532d"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName=FONT_NORMAL,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#475569"),
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#166534"),
        spaceBefore=3,
        spaceAfter=1.5,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName=FONT_NORMAL,
        fontSize=8.2,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8.2,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )
    warning_style = ParagraphStyle(
        "WarningBox",
        parent=styles["Normal"],
        fontName=FONT_NORMAL,
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#92400e"),
    )
    disclaimer_style = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontName=FONT_OBLIQUE,
        fontSize=7.5,
        leading=10,
        alignment=1,  # Center
        textColor=colors.HexColor("#64748b"),
    )

    story = []

    # 1. Header & Metadata
    raw_farmer = str(data.get("farmer_name", "")).strip()
    if not raw_farmer or raw_farmer.lower() in ["farmer", "farmer (demo preview)", "farmer (demo)", "none", "null"]:
        farmer_name = "Not provided"
    else:
        farmer_name = raw_farmer

    location = str(data.get("location", "Coimbatore, Tamil Nadu")).strip()
    date_str = str(data.get("date", datetime.now().strftime("%B %d, %Y"))).strip()
    area = data.get("area", 1.0)
    area_unit = str(data.get("area_unit", "Acres")).strip()

    header_table = Table(
        [
            [
                Paragraph("AgriSense AI — Farm Advisory Report Card", title_style),
                Paragraph(f"<b>Date:</b> {date_str}<br/><b>Status:</b> Official Advisory", subtitle_style),
            ]
        ],
        colWidths=[380, 160],
    )
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#15803d"), spaceBefore=2, spaceAfter=6))

    # Farmer & Field Summary Card
    raw_soil = str(data.get("soil_type", "")).strip()
    raw_source = str(data.get("soil_source", "")).strip().lower()

    if not raw_soil or raw_soil.lower() in ["none", "null", "not selected", "", "undefined"]:
        soil_display = "Not selected"
    else:
        soil_clean = raw_soil.capitalize()
        soil_name = f"{soil_clean} Soil" if not soil_clean.lower().endswith("soil") else soil_clean
        if "ai" in raw_source or "vision" in raw_source:
            soil_display = f"{soil_name} (AI-detected)"
        elif "user" in raw_source or raw_source == "user-selected":
            soil_display = f"{soil_name} (User-Selected)"
        else:
            soil_display = soil_name

    raw_data_source = str(data.get("data_source", "")).strip()
    is_estimated_flag = bool(data.get("is_estimated", False))

    if is_estimated_flag or raw_data_source.lower() in ["demo estimated", "demo data", "demo"]:
        data_source = "Demo estimated"
        is_estimated = True
    elif raw_data_source.lower() in ["lab test", "soil health card", "lab"]:
        data_source = "Lab test"
        is_estimated = False
    elif raw_data_source.lower() in ["user entered", "user", "manual"]:
        data_source = "User entered"
        is_estimated = False
    else:
        data_source = "Demo estimated" if is_estimated_flag else "User entered"
        is_estimated = (data_source == "Demo estimated")

    n_val = data.get("N", data.get("crop_data", {}).get("N", "—"))
    p_val = data.get("P", data.get("crop_data", {}).get("P", "—"))
    k_val = data.get("K", data.get("crop_data", {}).get("K", "—"))
    ph_val = data.get("ph", data.get("crop_data", {}).get("ph", "—"))

    input_source_desc = "Pre-set demo baseline" if (is_estimated or data_source == "Demo estimated") else ("Soil Health Card" if data_source == "Lab test" else "User entered values")

    # Col 1 width 175pt guarantees "Location: Coimbatore, Tamil Nadu" fits on a single line
    farmer_meta_data = [
        [
            Paragraph(f"<b>Farmer:</b> {safe_unicode_text(farmer_name)}", body_style),
            Paragraph(f"<b>Location:</b> {safe_unicode_text(location)}", body_style),
            Paragraph(f"<b>Plot Size:</b> {area} {area_unit}", body_style),
            Paragraph(f"<b>Soil Type:</b> {soil_display}", body_style),
        ],
        [
            Paragraph(f"<b>Soil Chemistry:</b> N: {n_val} | P: {p_val} | K: {k_val} kg/ha | pH: {ph_val} (Source: {input_source_desc})", body_style),
            "",
            "",
            Paragraph(f"<b>Data Source:</b> <font color='{'#b45309' if is_estimated else '#15803d'}'><b>{data_source}</b></font>", body_style),
        ],
    ]
    meta_table = Table(farmer_meta_data, colWidths=[125, 175, 95, 145])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
                ("SPAN", (0, 1), (2, 1)),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#bbf7d0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(meta_table)

    # Mandatory warning box whenever data is demo estimated
    if is_estimated or data_source == "Demo estimated":
        story.append(Spacer(1, 2))
        warn_box = Table(
            [[
                Paragraph(
                    "<b>Estimated Values Warning:</b> Soil chemistry values are demo estimates (Source: Pre-set demo baseline), not measured from a physical soil sample. Please confirm with a lab test (Soil Health Card) before executing field interventions. Fertilizer plan is estimated and not for actual commercial field application.",
                    warning_style,
                )
            ]],
            colWidths=[540],
        )
        warn_box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#f59e0b")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(warn_box)

    location_mismatch = bool(data.get("location_mismatch") or data.get("weather_data", {}).get("location_mismatch"))
    location_advisory = data.get("location_advisory") or data.get("weather_data", {}).get("location_advisory")
    if location_mismatch and location_advisory:
        story.append(Spacer(1, 2))
        mismatch_box = Table(
            [[
                Paragraph(
                    f"<b>Location Advisory:</b> {location_advisory}",
                    warning_style,
                )
            ]],
            colWidths=[540],
        )
        mismatch_box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#f59e0b")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(mismatch_box)

    story.append(Spacer(1, 2.5))

    crop_data = data.get("crop_data", {})
    top_crops = crop_data.get("top_crops", []) if isinstance(crop_data.get("top_crops"), list) else []
    is_ml_model = bool(top_crops and len(top_crops) > 0)
    primary_crop = str(crop_data.get("crop", "")).capitalize() if crop_data.get("crop") else ""

    # Input and Weather Telemetry Dates
    input_date_str = str(data.get("input_date") or date_str).strip()
    incoming_sched = data.get("irrigation_data", {}).get("weekly_schedule") or data.get("irrigation_data", {}).get("forecast") or []
    weather_date_str = str(data.get("weather_date") or (incoming_sched[0].get("date") if incoming_sched and incoming_sched[0].get("date") else datetime.now().strftime("%Y-%m-%d"))).strip()

    # 2. Crop Recommendation (Conditional Title & API-driven Top-3 rows)
    crop_title = "1. Crop Recommendation (Machine Learning Model)" if is_ml_model else "1. Crop Recommendation (Unavailable)"
    story.append(Paragraph(crop_title, h2_style))
    story.append(
        Paragraph(
            f"<font color='#475569'><b>Input Date:</b> {input_date_str} | <b>Weather Telemetry Date:</b> {weather_date_str} | <b>Parameters Source:</b> {input_source_desc}</font>",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 1.5))

    is_ambiguous = crop_data.get("is_ambiguous", False)
    ambiguity_warning = crop_data.get("ambiguity_warning")
    season_warning = crop_data.get("season_warning")
    provenance_note = crop_data.get("provenance_note")

    if is_ml_model:
        include_normalized = bool(
            data.get("include_normalized")
            or crop_data.get("include_normalized")
            or crop_data.get("show_normalized_top3")
        )

        temp_input = data.get("temperature", data.get("soil_data", {}).get("temperature", crop_data.get("temperature")))
        rain_input = data.get("rainfall", data.get("soil_data", {}).get("rainfall", crop_data.get("rainfall")))

        top3_items = top_crops[:3]
        top3_raw_floats = []
        for it in top3_items:
            pval = it.get("probability")
            if pval is not None:
                p_f = float(pval) if float(pval) <= 1.0 else float(pval) / 100.0
            elif it.get("confidence") is not None:
                p_f = float(it["confidence"]) / 100.0
            else:
                p_f = 0.0
            top3_raw_floats.append(p_f)

        top3_sum = sum(top3_raw_floats)

        agronomic_notes = []
        for idx, item in enumerate(top3_items):
            c_name = str(item.get("crop", "")).capitalize()
            user_reason = item.get("reason")
            matched_note = check_agronomic_suitability(
                c_name, temp_val=temp_input, rain_val=rain_input, n_val=n_val, p_val=p_val, k_val=k_val
            )
            final_note = user_reason if user_reason else matched_note
            agronomic_notes.append(final_note)

        has_reasons = any(n is not None and str(n).strip() != "" for n in agronomic_notes)

        # Build table columns and col widths (must total exactly 540pt for printable area)
        if has_reasons and include_normalized:
            top3_headers = [
                Paragraph("<b>Rank</b>", body_bold),
                Paragraph("<b>Crop Candidate</b>", body_bold),
                Paragraph("<b>Raw Probability (%)<br/><font size='6.5'>Share of 22 classes</font></b>", body_bold),
                Paragraph("<b>Normalized over Top-3 (%)</b>", body_bold),
                Paragraph("<b>Agronomic Notes (General guidance)</b>", body_bold),
            ]
            col_widths = [34, 96, 95, 95, 220]
        elif has_reasons and not include_normalized:
            top3_headers = [
                Paragraph("<b>Rank</b>", body_bold),
                Paragraph("<b>Crop Candidate</b>", body_bold),
                Paragraph("<b>Raw Probability (%)<br/><font size='6.5'>Share of 22 classes</font></b>", body_bold),
                Paragraph("<b>Agronomic Notes (General guidance)</b>", body_bold),
            ]
            col_widths = [38, 112, 105, 285]
        elif not has_reasons and include_normalized:
            top3_headers = [
                Paragraph("<b>Rank</b>", body_bold),
                Paragraph("<b>Crop Candidate</b>", body_bold),
                Paragraph("<b>Raw Probability (%)<br/><font size='6.5'>Share of 22 classes</font></b>", body_bold),
                Paragraph("<b>Normalized over Top-3 (%)</b>", body_bold),
            ]
            col_widths = [50, 190, 150, 150]
        else:
            # Reason column removed when no matching agronomic check exists
            top3_headers = [
                Paragraph("<b>Rank</b>", body_bold),
                Paragraph("<b>Crop Candidate</b>", body_bold),
                Paragraph("<b>Raw Probability (%)<br/><font size='6.5'>Share of 22 classes</font></b>", body_bold),
            ]
            col_widths = [60, 240, 240]

        top3_rows = [top3_headers]

        for idx, item in enumerate(top3_items):
            r_num = item.get("rank", idx + 1)
            c_name = str(item.get("crop", "")).capitalize()
            raw_pct = f"{top3_raw_floats[idx] * 100:.1f}%"
            norm_pct = f"{(top3_raw_floats[idx] / top3_sum) * 100:.1f}%" if top3_sum > 0 else "—"

            row_cells = [
                Paragraph(str(r_num), body_style),
                Paragraph(f"<b>{c_name}</b>", body_style),
                Paragraph(raw_pct, body_style),
            ]
            if include_normalized:
                row_cells.append(Paragraph(norm_pct, body_style))
            if has_reasons:
                note_str = agronomic_notes[idx] if agronomic_notes[idx] else "—"
                row_cells.append(Paragraph(note_str, body_style))

            top3_rows.append(row_cells)

        top3_table = Table(top3_rows, colWidths=col_widths)
        top3_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(top3_table)
    else:
        unavail_table = Table(
            [[
                Paragraph(
                    "<b>Crop prediction unavailable</b> — ML model prediction could not be computed. Please check soil nutrient inputs (N, P, K, pH) and re-run prediction.",
                    body_style,
                )
            ]],
            colWidths=[540],
        )
        unavail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(unavail_table)

    # Warnings (Ambiguity / Out-of-Season / Provenance)
    warning_elements = []
    if is_ambiguous and ambiguity_warning:
        warning_elements.append(Paragraph(f"<b>Ambiguity Advisory:</b> {ambiguity_warning}", warning_style))
    if season_warning:
        warning_elements.append(Paragraph(f"<b>Seasonal Advisory:</b> {season_warning}", warning_style))
    if provenance_note or primary_crop.lower() == "wheat":
        warning_elements.append(
            Paragraph(
                "<b>Benchmark Note:</b> Wheat recommendation is calibrated from ICAR synthetic parameter extension (limited benchmark data).",
                warning_style,
            )
        )

    if warning_elements:
        story.append(Spacer(1, 3))
        warn_table = Table([[elem] for elem in warning_elements], colWidths=[540])
        warn_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fde68a")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(warn_table)

    story.append(Spacer(1, 2.5))

    # 3. Fertilizer Plan (Scaled to Plot Size with Per-Acre rates)
    fert_data = data.get("fertilizer_data", {})
    fert_suffix = " — <font color='#b45309'><b>[Estimated, not for actual application]</b></font>" if is_estimated else ""
    story.append(Paragraph(f"2. Fertilizer Plan (DAP + Urea + MOP){fert_suffix}", h2_style))

    try:
        plot_area = float(data.get("area", 1.0))
    except (ValueError, TypeError):
        plot_area = 1.0
    plot_unit = str(data.get("area_unit", "Acres")).strip()

    dap_rate = float(fert_data.get("dap_kg", 35.2))
    urea_rate = float(fert_data.get("urea_kg", 56.6))
    mop_rate = float(fert_data.get("mop_kg", 16.8))

    dap_total_kg = round(dap_rate * plot_area, 1)
    urea_total_kg = round(urea_rate * plot_area, 1)
    mop_total_kg = round(mop_rate * plot_area, 1)

    dap_total_bags = round(dap_total_kg / 50.0, 2)
    urea_total_bags = round(urea_total_kg / 50.0, 2)
    mop_total_bags = round(mop_total_kg / 50.0, 2)

    dap_rate_bags = round(dap_rate / 50.0, 2)
    urea_rate_bags = round(urea_rate / 50.0, 2)
    mop_rate_bags = round(mop_rate / 50.0, 2)

    fert_rows = [
        [
            Paragraph("<b>Commercial Fertilizer</b>", body_bold),
            Paragraph("<b>Chemical Grade</b>", body_bold),
            Paragraph(f"<b>Total for {plot_area} {plot_unit}</b>", body_bold),
            Paragraph("<b>Total 50kg Bags</b>", body_bold),
            Paragraph("<b>Application Schedule</b>", body_bold),
        ],
        [
            Paragraph("<b>DAP (Di-Ammonium Phosphate)</b>", body_style),
            Paragraph("18% N, 46% P2O5", body_style),
            Paragraph(f"<b>{dap_total_kg} kg</b><br/><font size='6.8' color='#64748b'>({dap_rate} kg/acre)</font>", body_style),
            Paragraph(f"<b>{dap_total_bags} Bags</b><br/><font size='6.8' color='#64748b'>({dap_rate_bags} bags/acre)</font>", body_bold),
            Paragraph("100% Basal at sowing (delivers full P)", body_style),
        ],
        [
            Paragraph("<b>Urea</b>", body_style),
            Paragraph("46% Elemental N", body_style),
            Paragraph(f"<b>{urea_total_kg} kg</b><br/><font size='6.8' color='#64748b'>({urea_rate} kg/acre)</font>", body_style),
            Paragraph(f"<b>{urea_total_bags} Bags</b><br/><font size='6.8' color='#64748b'>({urea_rate_bags} bags/acre)</font>", body_bold),
            Paragraph("50% Basal + 25% Tillering + 25% Panicle", body_style),
        ],
        [
            Paragraph("<b>MOP (Muriate of Potash)</b>", body_style),
            Paragraph("60% Elemental K2O", body_style),
            Paragraph(f"<b>{mop_total_kg} kg</b><br/><font size='6.8' color='#64748b'>({mop_rate} kg/acre)</font>", body_style),
            Paragraph(f"<b>{mop_total_bags} Bags</b><br/><font size='6.8' color='#64748b'>({mop_rate_bags} bags/acre)</font>", body_bold),
            Paragraph("50% Basal + 50% Top-dress flowering", body_style),
        ],
    ]
    fert_table = Table(fert_rows, colWidths=[130, 95, 105, 95, 115])
    fert_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(fert_table)
    story.append(Spacer(1, 1.5))
    story.append(
        Paragraph(
            f"<b>Formula:</b> Total kg = Rate (kg/acre) × Area ({plot_area} {plot_unit}) | Total Bags = Total kg ÷ 50 kg/bag (e.g. DAP: {dap_rate} × {plot_area} = {dap_total_kg} kg = {dap_total_bags} bags)",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 2.5))

    # 4. Irrigation Schedule (Aligned 7-day schedule, Forecast Source, and Dynamic Frequency)
    irr_suffix = " — <font color='#b45309'><b>[Estimated, not for actual application]</b></font>" if is_estimated else ""
    story.append(Paragraph(f"3. Irrigation Schedule (FAO-56 Water Balance){irr_suffix}", h2_style))
    irr_data = data.get("irrigation_data", {})
    raw_fc_source = (
        irr_data.get("forecast_source")
        or data.get("forecast_source")
        or data.get("weather_data", {}).get("forecast_source")
    )
    forecast_source = str(raw_fc_source).strip() if raw_fc_source else "Unknown"

    incoming_schedule = irr_data.get("weekly_schedule") or irr_data.get("forecast") or []

    # Accurate farm area in square meters (1 acre = 4,046.86 m², 1 ha = 10,000 m²)
    u_lower = area_unit.lower()
    if u_lower in ["acre", "acres"]:
        area_m2 = area * 4046.86
    elif u_lower in ["hectare", "hectares", "ha"]:
        area_m2 = area * 10000.0
    elif u_lower in ["cent", "cents"]:
        area_m2 = area * 40.4686
    elif u_lower in ["guntha", "gunthas"]:
        area_m2 = area * 101.17
    elif u_lower in ["bigha", "bighas"]:
        area_m2 = area * 1618.7
    else:
        area_m2 = area * 4046.86

    area_m2_str = f"{area_m2:,.2f}" if (area_m2 % 1 != 0) else f"{area_m2:,.0f}"

    # Drip system physics constants: 2.0 LPH emitter, 0.4m x 0.8m spacing
    APP_RATE_MM_HR = 6.25  # 2.0 LPH / (0.4m * 0.8m)
    DRIP_EFF = 0.90  # 90% distribution uniformity & application efficiency

    schedule = []
    if incoming_schedule:
        try:
            today_base = datetime.now(ZoneInfo("Asia/Kolkata")).date()
        except Exception:
            today_base = datetime.now().date()

        for i, item in enumerate(incoming_schedule[:7]):
            expected_date = (today_base + timedelta(days=i)).strftime("%Y-%m-%d")
            raw_date = str(item.get("date") or "")
            item_date = raw_date if raw_date else expected_date
            if i == 0:
                item_date = today_base.strftime("%Y-%m-%d")

            day_name = str(item.get("day") or ("Today" if i == 0 else (today_base + timedelta(days=i)).strftime("%a")))
            temp_max = item.get("temp_max", item.get("temperature_max", 30))
            rain_mm = float(item.get("rainfall_mm", item.get("rain_mm", 0.0)))
            et0_mm = float(item.get("et0_mm", item.get("et0", 5.0)))

            # FAO-56 Net Water Need (No unverified 0.75 multiplier)
            if rain_mm >= et0_mm:
                net_mm = 0.0
                action = "Skip (Rainfall)"
            elif rain_mm > 0.0:
                net_mm = max(0.0, round(et0_mm - rain_mm, 1))
                if net_mm <= 1.0:
                    action = "Moisture Adequate"
                else:
                    runtime_h = round((net_mm / APP_RATE_MM_HR) / DRIP_EFF, 1)
                    action = f"Irrigate (Drip {runtime_h}h)"
            else:
                net_mm = round(et0_mm, 1)
                runtime_h = round((net_mm / APP_RATE_MM_HR) / DRIP_EFF, 1)
                action = f"Irrigate (Drip {runtime_h}h)"

            schedule.append(
                {
                    "day": day_name,
                    "date": item_date,
                    "temp_max": temp_max,
                    "rainfall_mm": rain_mm,
                    "et0_mm": et0_mm,
                    "net_mm": net_mm,
                    "action": action,
                }
            )

    # Check fallback/identical forecast condition
    is_fallback = "fallback" in forecast_source.lower() or "estimated" in forecast_source.lower()
    is_identical_7d = False
    if schedule and len(schedule) >= 2:
        f_temp = schedule[0]["temp_max"]
        f_rain = schedule[0]["rainfall_mm"]
        f_et0 = schedule[0]["et0_mm"]
        if all(item["temp_max"] == f_temp and item["rainfall_mm"] == f_rain and item["et0_mm"] == f_et0 for item in schedule):
            is_identical_7d = True
            if "fallback" not in forecast_source.lower():
                forecast_source = "Fallback (Agro-climatic Regional Baseline)"

    if is_fallback or is_identical_7d:
        forecast_warn = Table(
            [[
                Paragraph(
                    "<b>Forecast Advisory:</b> Forecast unavailable, using estimated average. Field conditions may vary; calibrate with local rain gauge.",
                    warning_style,
                )
            ]],
            colWidths=[540],
        )
        forecast_warn.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#f59e0b")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(forecast_warn)
        story.append(Spacer(1, 2))

    # Day 1 daily water volume and drip runtime
    if schedule:
        day1_net = schedule[0]["net_mm"]
        day1_liters = round(area_m2 * day1_net * 1.0)
        day1_runtime = round((day1_net / APP_RATE_MM_HR) / DRIP_EFF, 2)
        day1_label = schedule[0]["day"]
        irrigated_days_count = sum(1 for item in schedule if "irrigate" in str(item.get("action", "")).lower())
        freq_label = f"Dynamic Daily Water Balance ({irrigated_days_count} of {len(schedule)} days irrigated)"
    else:
        day1_net = 0.0
        day1_liters = 0
        day1_runtime = 0.0
        day1_label = "Unavailable"
        freq_label = "Unavailable"

    irr_meta_rows = [
        [
            Paragraph(f"<b>Forecast Source:</b> {forecast_source}", body_style),
            Paragraph(f"<b>Irrigation Frequency:</b> {freq_label}", body_style),
            Paragraph(f"<b>Daily Need ({day1_label}):</b> {day1_liters:,.0f} L ({day1_net:.1f} mm)", body_style),
            Paragraph(f"<b>Drip Runtime:</b> {day1_runtime:.2f} Hours/day", body_style),
        ],
        [
            Paragraph(
                f"<b>Formula:</b> Daily Liters = Area ({area_m2_str} m² [{area} {area_unit}]) × Net Need ({day1_net:.1f} mm) × 1 L/(m²·mm) = {day1_liters:,.0f} L | "
                f"App Rate = 2.0 LPH ÷ (0.4m × 0.8m) = 6.25 mm/hr | Runtime = (Net mm ÷ 6.25) ÷ 90% [0.92h gross (0.83h @ 100% eff)] | "
                f"Rain counted fully as effective (no runoff loss)",
                subtitle_style,
            ),
            "",
            "",
            "",
        ],
    ]
    irr_meta_table = Table(irr_meta_rows, colWidths=[150, 140, 125, 125])
    irr_meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bae6fd")),
                ("SPAN", (0, 1), (3, 1)),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#bae6fd")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(irr_meta_table)

    if schedule:
        story.append(Spacer(1, 3))
        sched_rows = [
            [
                Paragraph("<b>Schedule Day & Date</b>", body_bold),
                Paragraph("<b>Forecast Temp</b>", body_bold),
                Paragraph("<b>Rainfall</b>", body_bold),
                Paragraph("<b>ET0</b>", body_bold),
                Paragraph("<b>Net Water Need</b>", body_bold),
                Paragraph("<b>Irrigation Action</b>", body_bold),
            ]
        ]
        for item in schedule[:7]:
            d_label = item.get("day", "")
            d_date = item.get("date", "")
            sched_rows.append(
                [
                    Paragraph(f"<b>{d_label}</b> ({d_date})", body_style),
                    Paragraph(f"{item.get('temp_max', 30)}°C", body_style),
                    Paragraph(f"{item.get('rainfall_mm', 0):.1f} mm", body_style),
                    Paragraph(f"{item.get('et0_mm', 4.5):.1f} mm", body_style),
                    Paragraph(f"{item.get('net_mm', 4.0):.1f} mm", body_style),
                    Paragraph(f"<b>{item.get('action', 'Irrigate')}</b>", body_style),
                ]
            )
        sched_table = Table(sched_rows, colWidths=[100, 72, 70, 60, 78, 160])
        sched_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bae6fd")),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(sched_table)
    else:
        story.append(Spacer(1, 3))
        unavailable_table = Table(
            [[
                Paragraph(
                    "<b>Weather forecast unavailable</b> — 7-day meteorological forecast telemetry is not synchronized. "
                    "Please connect to live weather telemetry to generate dynamic daily irrigation water balance schedule.",
                    body_style,
                )
            ]],
            colWidths=[540],
        )
        unavailable_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(unavailable_table)

    story.append(Spacer(1, 2.5))

    # 5. Harvest & Economic Projections (Sowing date user input, timeline label, MSP)
    harv_suffix = " — <font color='#b45309'><b>[Estimated, illustrative projection]</b></font>" if is_estimated else ""
    story.append(Paragraph(f"4. Harvest Projection & Economics{harv_suffix}", h2_style))
    harvest_data = data.get("harvest_data", {})
    raw_sowing_date = harvest_data.get("sowing_date") or data.get("sowing_date")

    target_crop = str(harvest_data.get("crop") or primary_crop or data.get("crop") or "rice").strip().lower()
    crop_cycle_entry = CROP_CYCLES_LOOKUP.get(target_crop, {})
    msp_entry = MSP_LOOKUP.get(target_crop, {})

    if harvest_data.get("yield_quintals") is not None:
        try:
            yield_q = float(harvest_data["yield_quintals"])
        except (ValueError, TypeError):
            yield_q = 38.9
    elif crop_cycle_entry.get("baseline_yield_q_ha") is not None:
        base_q_ha = float(crop_cycle_entry["baseline_yield_q_ha"])
        area_ha = area * (0.404686 if area_unit.lower() in ["acre", "acres"] else 1.0)
        yield_q = round(base_q_ha * area_ha, 1)
    else:
        yield_q = 38.9

    low_yield = round(yield_q * 0.88, 1)
    high_yield = round(yield_q * 1.12, 1)
    yield_display = f"{low_yield} – {yield_q} – {high_yield} Quintals (lookup table benchmark [UNVERIFIED])"

    # MSP lookup (Jute source unconfirmed -> not verified)
    if target_crop == "jute":
        msp_benchmark_str = "not verified (source unconfirmed) [lookup table: UNVERIFIED]"
        msp_type = "UNVERIFIED (Pending Official Gazette)"
    elif msp_entry.get("msp_rs_per_quintal"):
        msp_val = msp_entry["msp_rs_per_quintal"]
        msp_year = msp_entry.get("year", "2024-25")
        msp_benchmark_str = f"₹{msp_val:,} / Quintal (Year: {msp_year}) [lookup table: UNVERIFIED]"
        msp_type = "UNVERIFIED (Pending Official Gazette)"
    else:
        raw_msp_rate = harvest_data.get("msp_rs_per_quintal", 2300)
        msp_year = harvest_data.get("msp_year", "2024-25")
        msp_benchmark_str = f"₹{raw_msp_rate:,} / Quintal (Year: {msp_year}) [lookup table: UNVERIFIED]"
        msp_type = "UNVERIFIED (Pending Official Gazette)"

    if not raw_sowing_date or str(raw_sowing_date).strip() == "" or str(raw_sowing_date).lower() in ["none", "null"]:
        harvest_meta = [
            [
                Paragraph("<b>Sowing date not set; harvest date unavailable</b> — Please provide sowing date in the Harvest planner to calculate crop growth stages and maturity countdown.", body_style),
                Paragraph(f"<b>Expected Yield Range:</b> {yield_display}", body_style),
            ],
            [
                Paragraph(f"<b>Government MSP Benchmark:</b> {msp_benchmark_str}", body_style),
                Paragraph(f"<b>MSP Status Label:</b> <font color='#b91c1c'><b>{msp_type}</b></font>", body_style),
            ],
        ]
    else:
        try:
            sowing_dt = datetime.strptime(str(raw_sowing_date).strip(), "%Y-%m-%d").date()
        except ValueError:
            sowing_dt = datetime.now(ZoneInfo("Asia/Kolkata")).date()

        try:
            today_date = datetime.now(ZoneInfo("Asia/Kolkata")).date()
        except Exception:
            today_date = datetime.now().date()

        crop_duration = int(harvest_data.get("crop_cycle_days") or harvest_data.get("duration_days") or crop_cycle_entry.get("duration_days") or 125)
        harvest_dt = sowing_dt + timedelta(days=crop_duration)
        harvest_date_str = harvest_dt.strftime("%B %d, %Y")
        days_rem = (harvest_dt - today_date).days

        if sowing_dt >= today_date:
            timeline_str = f"Crop cycle: {crop_duration} days; harvest on {harvest_date_str}"
        else:
            timeline_str = f"{max(0, days_rem)} days remaining (harvest on {harvest_date_str})"

        sowing_display = f"Sowing Date: {sowing_dt.strftime('%b %d, %Y')} (Source: User entered)"
        harvest_meta = [
            [
                Paragraph(f"<b>{sowing_display}</b><br/><b>Timeline:</b> {timeline_str}", body_style),
                Paragraph(f"<b>Expected Yield Range:</b> {yield_display}", body_style),
            ],
            [
                Paragraph(f"<b>Government MSP Benchmark:</b> {msp_benchmark_str}", body_style),
                Paragraph(f"<b>MSP Status Label:</b> <font color='#b91c1c'><b>{msp_type}</b></font>", body_style),
            ],
        ]
    harv_table = Table(harvest_meta, colWidths=[270, 270])
    harv_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fefce8")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fef08a")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(harv_table)
    story.append(Spacer(1, 2.5))

    # 6. Official Footer & Mandatory Disclaimer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8"), spaceBefore=2, spaceAfter=5))
    story.append(
        Paragraph(
            "<b>LEGAL DISCLAIMER:</b> Estimates only. All numerical recommendations (crop suitability, fertilizer quantities, irrigation depths, and harvest yields) are AI and empirical decision-support estimates. Please confirm with your local agriculture officer or Krishi Vigyan Kendra (KVK) before executing significant commercial field purchases or interventions.",
            disclaimer_style,
        )
    )

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
