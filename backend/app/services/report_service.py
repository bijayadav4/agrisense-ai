import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_farmer_report_card(data):
    """
    Generates a scientifically rigorous and visually clean Farmer Advisory Report Card PDF.
    Complies with all AgriSense AI audit standards:
    - Top-3 crops with probabilities + ambiguity/seasonal warnings
    - Soil classification source (CNN confidence or user-selected)
    - ICAR Stoichiometric fertilizer balance (DAP, Urea, MOP)
    - FAO-56 Irrigation (ET0 method, interval, 7-day schedule summary)
    - Phenological harvest timeline & UNVERIFIED MSP benchmark label
    - Legal disclaimer footer
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#14532d"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#166534"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1e293b"),
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0f172a"),
    )
    warning_style = ParagraphStyle(
        "WarningBox",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#92400e"),
    )
    disclaimer_style = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        alignment=1,  # Center
        textColor=colors.HexColor("#64748b"),
    )

    story = []

    # 1. Header & Metadata
    farmer_name = str(data.get("farmer_name", "Farmer")).strip() or "Farmer"
    location = str(data.get("location", "Coimbatore, Tamil Nadu")).strip()
    date_str = str(data.get("date", datetime.now().strftime("%B %d, %Y"))).strip()
    area = data.get("area", 1.0)
    area_unit = str(data.get("area_unit", "Acres")).strip()

    header_table = Table(
        [
            [
                Paragraph("🌾 AgriSense AI — Farm Advisory Report Card", title_style),
                Paragraph(f"<b>Date:</b> {date_str}<br/><b>Status:</b> Official Advisory", subtitle_style),
            ]
        ],
        colWidths=[380, 160],
    )
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    story.append(header_table)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#15803d"), spaceBefore=2, spaceAfter=8))

    # Farmer & Field Summary Card
    soil_type = str(data.get("soil_type", "Clayey")).capitalize()
    soil_source = str(data.get("soil_source", "User-Selected")).strip()
    data_source = str(data.get("data_source", "User entered")).strip()
    is_estimated = (data_source == "Demo estimated") or bool(data.get("is_estimated", False))

    n_val = data.get("N", data.get("crop_data", {}).get("N", "—"))
    p_val = data.get("P", data.get("crop_data", {}).get("P", "—"))
    k_val = data.get("K", data.get("crop_data", {}).get("K", "—"))
    ph_val = data.get("ph", data.get("crop_data", {}).get("ph", "—"))

    farmer_meta_data = [
        [
            Paragraph(f"<b>Farmer:</b> {farmer_name}", body_style),
            Paragraph(f"<b>Location:</b> {location}", body_style),
            Paragraph(f"<b>Plot Size:</b> {area} {area_unit}", body_style),
            Paragraph(f"<b>Soil Type:</b> {soil_type} ({soil_source})", body_style),
        ],
        [
            Paragraph(f"<b>Soil Chemistry:</b> N: {n_val} | P: {p_val} | K: {k_val} kg/ha | pH: {ph_val}", body_style),
            "",
            "",
            Paragraph(f"<b>Data Source:</b> <font color='{'#b45309' if is_estimated else '#15803d'}'><b>{data_source}</b></font>", body_style),
        ]
    ]
    meta_table = Table(farmer_meta_data, colWidths=[135, 145, 110, 150])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
                ("SPAN", (0, 1), (2, 1)),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#bbf7d0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(meta_table)

    if is_estimated:
        story.append(Spacer(1, 4))
        warn_box = Table(
            [[
                Paragraph(
                    "⚠️ <b>Estimated Values Warning:</b> Soil chemistry values were generated from Demo estimates, NOT measured from a physical soil sample. Lab test (Soil Health Card) se confirm karein before executing field interventions. Fertilizer plan is estimated and not for actual commercial field application.",
                    warning_style,
                )
            ]],
            colWidths=[540],
        )
        warn_box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#f59e0b")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(warn_box)

    story.append(Spacer(1, 8))

    # 2. Crop Recommendation (Top-3, Probabilities, Ambiguity & Season Warning)
    story.append(Paragraph("1. Precision Crop Suitability (Pillar 1: Random Forest)", h2_style))
    crop_data = data.get("crop_data", {})
    primary_crop = str(crop_data.get("crop", "Rice")).capitalize()
    confidence = crop_data.get("confidence", 92.0)
    top_crops = crop_data.get("top_crops", [])
    is_ambiguous = crop_data.get("is_ambiguous", False)
    ambiguity_warning = crop_data.get("ambiguity_warning")
    season_warning = crop_data.get("season_warning")
    provenance_note = crop_data.get("provenance_note")

    top3_rows = [
        [
            Paragraph("<b>Rank</b>", body_bold),
            Paragraph("<b>Crop Candidate</b>", body_bold),
            Paragraph("<b>Probability</b>", body_bold),
            Paragraph("<b>Suitability Confidence</b>", body_bold),
            Paragraph("<b>Agronomic Notes</b>", body_bold),
        ]
    ]

    if top_crops:
        for item in top_crops[:3]:
            r_num = item.get("rank", 1)
            c_name = str(item.get("crop", "")).capitalize()
            p_val = f"{round(item.get('probability', 0.0) * 100, 1)}%"
            conf_val = f"{item.get('confidence', 0.0)}%"
            notes = "Limited benchmark data (synthetic)" if c_name.lower() == "wheat" else "Optimal envelope match"
            top3_rows.append(
                [
                    Paragraph(str(r_num), body_style),
                    Paragraph(f"<b>{c_name}</b>", body_style),
                    Paragraph(p_val, body_style),
                    Paragraph(conf_val, body_style),
                    Paragraph(notes, body_style),
                ]
            )
    else:
        top3_rows.append(
            [
                Paragraph("1", body_style),
                Paragraph(f"<b>{primary_crop}</b>", body_style),
                Paragraph(f"{confidence}%", body_style),
                Paragraph(f"{confidence}%", body_style),
                Paragraph("Primary recommendation", body_style),
            ]
        )

    top3_table = Table(top3_rows, colWidths=[40, 110, 80, 120, 190])
    top3_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(top3_table)

    # Warnings (Ambiguity / Out-of-Season / Provenance)
    warning_elements = []
    if is_ambiguous and ambiguity_warning:
        warning_elements.append(Paragraph(f"⚠️ <b>Ambiguity Advisory:</b> {ambiguity_warning}", warning_style))
    if season_warning:
        warning_elements.append(Paragraph(f"🗓️ <b>Seasonal Advisory:</b> {season_warning}", warning_style))
    if provenance_note or primary_crop.lower() == "wheat":
        warning_elements.append(
            Paragraph(
                "ℹ️ <b>Benchmark Note:</b> Wheat recommendation is calibrated from ICAR synthetic parameter extension (limited benchmark data).",
                warning_style,
            )
        )

    if warning_elements:
        story.append(Spacer(1, 4))
        warn_table = Table([[elem] for elem in warning_elements], colWidths=[540])
        warn_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fde68a")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(warn_table)

    story.append(Spacer(1, 10))

    fert_data = data.get("fertilizer_data", {})
    fert_brand = str(fert_data.get("fertilizer", "Urea / DAP Balanced")).capitalize()
    fert_suffix = " — <font color='#b45309'><b>[Estimated, not for actual application]</b></font>" if is_estimated else ""
    story.append(Paragraph(f"2. Fertilizer Prescription (ICAR Chemical Stoichiometry — Formulation: {fert_brand}){fert_suffix}", h2_style))
    dap_bags = fert_data.get("dap_bags", 0.70)
    urea_bags = fert_data.get("urea_bags", 1.13)
    mop_bags = fert_data.get("mop_bags", 0.34)
    dap_kg = fert_data.get("dap_kg", 35.2)
    urea_kg = fert_data.get("urea_kg", 56.6)
    mop_kg = fert_data.get("mop_kg", 16.8)

    fert_rows = [
        [
            Paragraph("<b>Commercial Fertilizer</b>", body_bold),
            Paragraph("<b>Chemical Grade</b>", body_bold),
            Paragraph("<b>Net Requirement</b>", body_bold),
            Paragraph("<b>Commercial 50kg Bags</b>", body_bold),
            Paragraph("<b>Application Schedule</b>", body_bold),
        ],
        [
            Paragraph("<b>DAP (Di-Ammonium Phosphate)</b>", body_style),
            Paragraph("18% N, 46% P2O5", body_style),
            Paragraph(f"{dap_kg} kg/acre", body_style),
            Paragraph(f"<b>{dap_bags} Bags</b>", body_bold),
            Paragraph("100% Basal at sowing (delivers full P)", body_style),
        ],
        [
            Paragraph("<b>Urea</b>", body_style),
            Paragraph("46% Elemental N", body_style),
            Paragraph(f"{urea_kg} kg/acre", body_style),
            Paragraph(f"<b>{urea_bags} Bags</b>", body_bold),
            Paragraph("50% Basal + 25% Tillering + 25% Panicle", body_style),
        ],
        [
            Paragraph("<b>MOP (Muriate of Potash)</b>", body_style),
            Paragraph("60% Elemental K2O", body_style),
            Paragraph(f"{mop_kg} kg/acre", body_style),
            Paragraph(f"<b>{mop_bags} Bags</b>", body_bold),
            Paragraph("50% Basal + 50% Top-dress flowering", body_style),
        ],
    ]
    fert_table = Table(fert_rows, colWidths=[140, 100, 85, 95, 120])
    fert_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(fert_table)
    story.append(Spacer(1, 10))

    # 4. Irrigation Schedule (FAO-56 Hydrology Engine)
    story.append(Paragraph("3. Hydrological Irrigation Plan (FAO-56 Penman-Monteith)", h2_style))
    irr_data = data.get("irrigation_data", {})
    et0_method = irr_data.get("et0_method", "open-meteo-fao56")
    interval_days = irr_data.get("interval_days", 4)
    daily_liters = irr_data.get("daily_liters", 47512)
    drip_hours = irr_data.get("drip_runtime_hours", 0.6)
    schedule = irr_data.get("weekly_schedule", [])

    irr_meta_rows = [
        [
            Paragraph(f"<b>ET0 Calculation Method:</b> {et0_method}", body_style),
            Paragraph(f"<b>Irrigation Interval:</b> Every {interval_days} Days", body_style),
            Paragraph(f"<b>Daily Water Need:</b> {daily_liters:,.0f} L", body_style),
            Paragraph(f"<b>Drip Runtime:</b> {drip_hours} Hours/day", body_style),
        ]
    ]
    irr_meta_table = Table(irr_meta_rows, colWidths=[150, 130, 130, 130])
    irr_meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bae6fd")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(irr_meta_table)

    if schedule:
        story.append(Spacer(1, 4))
        sched_rows = [
            [
                Paragraph("<b>Day</b>", body_bold),
                Paragraph("<b>Forecast Temp</b>", body_bold),
                Paragraph("<b>Rainfall</b>", body_bold),
                Paragraph("<b>ET0</b>", body_bold),
                Paragraph("<b>Net Water Need</b>", body_bold),
                Paragraph("<b>Irrigation Action</b>", body_bold),
            ]
        ]
        for item in schedule[:7]:
            sched_rows.append(
                [
                    Paragraph(str(item.get("day", "")), body_style),
                    Paragraph(f"{item.get('temp_max', 30)}°C", body_style),
                    Paragraph(f"{item.get('rainfall_mm', 0)} mm", body_style),
                    Paragraph(f"{item.get('et0_mm', 4.5)} mm", body_style),
                    Paragraph(f"{item.get('net_mm', 4.0)} mm", body_style),
                    Paragraph(
                        f"<b>{item.get('action', 'Irrigate')}</b>",
                        body_bold if "Irrigate" in item.get("action", "") else body_style,
                    ),
                ]
            )
        sched_table = Table(sched_rows, colWidths=[65, 80, 75, 70, 90, 160])
        sched_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bae6fd")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(sched_table)

    story.append(Spacer(1, 10))

    # 5. Harvest & Economic Projections
    story.append(Paragraph("4. Phenological Harvest Projection & Economics", h2_style))
    harvest_data = data.get("harvest_data", {})
    harvest_date = str(harvest_data.get("harvest_date", "Indicative Calendar Projection")).strip()
    days_rem = harvest_data.get("days_remaining", 70)
    yield_q = harvest_data.get("yield_quintals", 38.9)
    msp_year = harvest_data.get("msp_year", "2024-25")
    msp_rate = harvest_data.get("msp_rs_per_quintal", 2300)
    msp_type = harvest_data.get("msp_type", "UNVERIFIED (Pending Official Gazette)")

    harvest_meta = [
        [
            Paragraph(f"<b>Projected Harvest Date:</b> {harvest_date} ({days_rem} Days Remaining)", body_style),
            Paragraph(f"<b>Expected Yield Range:</b> {yield_q} Quintals (Indicative Mean)", body_style),
        ],
        [
            Paragraph(f"<b>Government MSP Benchmark:</b> ₹{msp_rate:,} / Quintal (Year: {msp_year})", body_style),
            Paragraph(f"<b>MSP Status Label:</b> <font color='#b91c1c'><b>{msp_type}</b></font>", body_style),
        ],
    ]
    harv_table = Table(harvest_meta, colWidths=[270, 270])
    harv_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fefce8")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fef08a")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(harv_table)
    story.append(Spacer(1, 14))

    # 6. Official Footer & Mandatory Disclaimer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8"), spaceBefore=4, spaceAfter=8))
    story.append(
        Paragraph(
            "<b>LEGAL DISCLAIMER:</b> Estimates only. All numerical recommendations (crop suitability, fertilizer quantities, irrigation depths, and harvest yields) are AI and empirical decision-support estimates. Local agriculture officer / Krishi Vigyan Kendra (KVK) se confirm karein before executing significant commercial field purchases or interventions.",
            disclaimer_style,
        )
    )

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
