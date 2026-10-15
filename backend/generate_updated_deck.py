import os
import pptx
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# Initialize Presentation
prs = pptx.Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# Brand Color Palette (Professional Academic / Agro-Tech Theme)
COLOR_PRIMARY_DARK = RGBColor(15, 81, 50)      # Deep Forest Green #0F5132
COLOR_ACCENT_TEAL = RGBColor(13, 148, 136)     # Teal #0D9488
COLOR_NAVY = RGBColor(30, 58, 138)             # Deep Navy #1E3A8A
COLOR_NAVY_LIGHT = RGBColor(59, 130, 246)      # Slate Blue #3B82F6
COLOR_SLATE_DARK = RGBColor(15, 23, 42)        # Text Primary #0F172A
COLOR_SLATE_BODY = RGBColor(51, 65, 85)        # Text Secondary #334155
COLOR_SLATE_MUTED = RGBColor(100, 116, 139)    # Text Muted #64748B
COLOR_CARD_BG = RGBColor(248, 250, 252)        # Light Slate Card #F8FAFC
COLOR_CARD_BORDER = RGBColor(203, 213, 225)    # Card Border #CBD5E1
COLOR_GREEN_TINT = RGBColor(240, 253, 244)     # Emerald Tint #F0FDF4
COLOR_GREEN_BORDER = RGBColor(134, 239, 172)   # Emerald Border #86EFAC
COLOR_BLUE_TINT = RGBColor(239, 246, 255)      # Blue Tint #EFF6FF
COLOR_BLUE_BORDER = RGBColor(191, 219, 254)    # Blue Border #BFDBFE
COLOR_AMBER_TINT = RGBColor(254, 243, 199)     # Amber Tint #FEF3C7
COLOR_AMBER_BORDER = RGBColor(252, 211, 77)    # Amber Border #FCD34D
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_AMBER_TEXT = RGBColor(180, 83, 9)

FONT_HEADING = "Calibri"
FONT_BODY = "Calibri"

def add_header_footer(slide, title_text, category_badge="AGRISENSE AI • ACADEMIC REVIEW"):
    """Adds a standardized college header and footer to any slide."""
    # Top banner card
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.95))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p_badge = tf.paragraphs[0]
    p_badge.text = category_badge.upper()
    p_badge.font.size = Pt(9.5)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_ACCENT_TEAL
    
    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_NAVY
    p_title.space_before = Pt(2)
    
    # Header divider line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.42), Inches(11.733), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_ACCENT_TEAL
    line.line.fill.background()
    
    # Footer text
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.08), Inches(11.733), Inches(0.32))
    tff = footer_box.text_frame
    tff.margin_left = tff.margin_top = tff.margin_right = tff.margin_bottom = 0
    pf = tff.paragraphs[0]
    pf.text = "KPR Institute of Engineering and Technology, Coimbatore • Dept of Computer Science and Engineering"
    pf.font.size = Pt(9)
    pf.font.color.rgb = COLOR_SLATE_MUTED

def create_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.2)
    return shape

def add_bullet(tf, label, value, pt_size=9.5, space=3, bold_label=True, label_color=COLOR_SLATE_DARK, val_color=COLOR_SLATE_BODY):
    p = tf.add_paragraph()
    p.font.size = Pt(pt_size)
    p.space_before = Pt(space)
    if bold_label:
        r1 = p.add_run()
        r1.text = "• " + label + (" " if label else "")
        r1.font.bold = True
        r1.font.color.rgb = label_color
    else:
        r1 = p.add_run()
        r1.text = "• " + label + (" " if label else "")
        r1.font.color.rgb = label_color
    r2 = p.add_run()
    r2.text = value
    r2.font.color.rgb = val_color
    return p

# ==============================================================================
# SLIDE 1: TITLE SLIDE
# ==============================================================================
s1 = prs.slides.add_slide(blank_layout)

# Background Accent Box
bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = RGBColor(245, 247, 250)
bg1.line.fill.background()

# Top accent bar
top_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
top_bar.fill.solid()
top_bar.fill.fore_color.rgb = COLOR_PRIMARY_DARK
top_bar.line.fill.background()

# Main Title Card
create_card(s1, Inches(1.0), Inches(0.9), Inches(11.333), Inches(5.7), COLOR_WHITE, COLOR_CARD_BORDER)

tb1 = s1.shapes.add_textbox(Inches(1.4), Inches(1.2), Inches(10.533), Inches(5.1))
tf1 = tb1.text_frame
tf1.word_wrap = True

p_inst = tf1.paragraphs[0]
p_inst.text = "KPR INSTITUTE OF ENGINEERING AND TECHNOLOGY"
p_inst.font.size = Pt(12)
p_inst.font.bold = True
p_inst.font.color.rgb = COLOR_ACCENT_TEAL
p_inst.alignment = PP_ALIGN.CENTER

p_subinst = tf1.add_paragraph()
p_subinst.text = "Department of Computer Science and Engineering • B.E. CSE (Class: CSE-A)"
p_subinst.font.size = Pt(10.5)
p_subinst.font.color.rgb = COLOR_SLATE_MUTED
p_subinst.alignment = PP_ALIGN.CENTER

p_t = tf1.add_paragraph()
p_t.text = "AgriSense AI: Hybrid Deep Learning Framework for Weather &\nSoil-Based Multi-Crop Precision Agriculture"
p_t.font.size = Pt(23)
p_t.font.bold = True
p_t.font.color.rgb = COLOR_NAVY
p_t.alignment = PP_ALIGN.CENTER
p_t.space_before = Pt(18)

p_tagline = tf1.add_paragraph()
p_tagline.text = "An Integrated Multi-Module Decision Support System with Stoichiometric Fertilizer Dosage & Hydrological Guidance"
p_tagline.font.size = Pt(12)
p_tagline.font.italic = True
p_tagline.font.color.rgb = COLOR_PRIMARY_DARK
p_tagline.alignment = PP_ALIGN.CENTER
p_tagline.space_before = Pt(8)

# Details Box inside Title
tb_details = s1.shapes.add_textbox(Inches(1.8), Inches(4.3), Inches(9.733), Inches(1.8))
tf_d = tb_details.text_frame
tf_d.word_wrap = True

p_rev = tf_d.paragraphs[0]
p_rev.text = "Project Review Evaluation Presentation"
p_rev.font.size = Pt(11.5)
p_rev.font.bold = True
p_rev.font.color.rgb = COLOR_NAVY
p_rev.alignment = PP_ALIGN.CENTER

p_meta = tf_d.add_paragraph()
p_meta.text = "Guided By: Mr. M. Mohan (Assistant Professor - Sr.G, Dept. of CSE)\nTeam Members: Hareram Kushwaha (23CS054) • Ashok Pajiyar (23CS022) • Bijaya Kumar Yadav (23CS030) • Bishal Raut Kurmi (23CS031)"
p_meta.font.size = Pt(11)
p_meta.font.color.rgb = COLOR_SLATE_DARK
p_meta.alignment = PP_ALIGN.CENTER
p_meta.space_before = Pt(6)


# ==============================================================================
# SLIDE 2: PROJECT TEAM & GUIDE DETAILS
# ==============================================================================
s2 = prs.slides.add_slide(blank_layout)
add_header_footer(s2, "Project Team & Academic Mentorship")

# Team Card (Left)
create_card(s2, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_t = s2.shapes.add_textbox(Inches(1.05), Inches(1.85), Inches(5.2), Inches(4.7))
tft = tb_t.text_frame
tft.word_wrap = True
tft.paragraphs[0].text = "STUDENT INVESTIGATORS (CSE-A)"
tft.paragraphs[0].font.size = Pt(14)
tft.paragraphs[0].font.bold = True
tft.paragraphs[0].font.color.rgb = COLOR_NAVY

team = [
    ("Hareram Kushwaha", "23CS054", "Team Lead / Full-Stack & System Integration"),
    ("Ashok Pajiyar", "23CS022", "Agronomic Engines & Mathematical Stoichiometry"),
    ("Bijaya Kumar Yadav", "23CS030", "Deep Learning Pipeline & Vision Model Optimization"),
    ("Bishal Raut Kurmi", "23CS031", "Meteorological API Pipelines & Unit Testing Suite")
]
for name, regno, role in team:
    p = tft.add_paragraph()
    p.space_before = Pt(10)
    r1 = p.add_run()
    r1.text = f"{name} ({regno})\n"
    r1.font.bold = True
    r1.font.size = Pt(11)
    r1.font.color.rgb = COLOR_PRIMARY_DARK
    r2 = p.add_run()
    r2.text = f"Role: {role}"
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = COLOR_SLATE_BODY

# Guide Card (Right)
create_card(s2, Inches(6.8), Inches(1.65), Inches(5.7), Inches(5.1), COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_g = s2.shapes.add_textbox(Inches(7.05), Inches(1.85), Inches(5.2), Inches(4.7))
tfg = tb_g.text_frame
tfg.word_wrap = True
tfg.paragraphs[0].text = "PROJECT SUPERVISOR & RESEARCH MENTOR"
tfg.paragraphs[0].font.size = Pt(14)
tfg.paragraphs[0].font.bold = True
tfg.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

p_gname = tfg.add_paragraph()
p_gname.text = "Mr. M. Mohan, M.E., (Ph.D.)\nAssistant Professor (Sr.G), Department of CSE\nKPR Institute of Engineering and Technology, Coimbatore"
p_gname.font.size = Pt(11.5)
p_gname.font.bold = True
p_gname.font.color.rgb = COLOR_NAVY
p_gname.space_before = Pt(8)

p_gdesc = tfg.add_paragraph()
p_gdesc.text = "Research Foundation & Mentorship Scope:"
p_gdesc.font.size = Pt(11)
p_gdesc.font.bold = True
p_gdesc.font.color.rgb = COLOR_SLATE_DARK
p_gdesc.space_before = Pt(12)

guide_pts = [
    ("Base Paper Reference: ", "Author of 'Hybrid deep learning with a fusion model of weather and soil-based multi-crop recommendations for improving crop sustainability' (Theor. Appl. Climatol. 2025, Springer)."),
    ("Theoretical Framing: ", "Mentoring the adaptation of DTBRCNN and SPLSTMGNN deep learning concepts into AgriSense AI's decision platform."),
    ("Scientific Rigor: ", "Enforcing holdout validation integrity, leakage elimination, and real-world farm deployability standards.")
]
for lbl, val in guide_pts:
    add_bullet(tfg, lbl, val, pt_size=9.5, space=6, label_color=COLOR_PRIMARY_DARK)


# ==============================================================================
# SLIDE 3: ABSTRACT
# ==============================================================================
s3 = prs.slides.add_slide(blank_layout)
add_header_footer(s3, "Abstract & Executive Summary")

create_card(s3, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_abs = s3.shapes.add_textbox(Inches(1.1), Inches(1.85), Inches(11.133), Inches(4.7))
tf_abs = tb_abs.text_frame
tf_abs.word_wrap = True

p_abs0 = tf_abs.paragraphs[0]
p_abs0.text = "EXECUTIVE SCIENTIFIC ABSTRACT"
p_abs0.font.size = Pt(13)
p_abs0.font.bold = True
p_abs0.font.color.rgb = COLOR_NAVY

abs_text = (
    "Agriculture remains the cornerstone of socio-economic sustenance, yet smallholder farmers face severe "
    "yield uncertainties due to climate change, declining soil fertility, improper crop choice, and guesswork in fertilizer application. "
    "While modern research offers isolated AI models for either crop recommendation or soil classification, no unified system "
    "bridges high-level deep learning with end-to-end practical agronomy.\n\n"
    "This work presents AgriSense AI, an intelligent precision agriculture decision-support platform grounded in the hybrid deep "
    "learning architecture established by Mohan & Anandamurugan (2025). The system integrates: (1) Soil vision classification "
    "via Deep Twin Bottleneck Residual CNN (DTBRCNN) achieving 88.2% leakage-free holdout accuracy across 144 real field photographs; "
    "(2) Robust data handling using Developed Random Forest & Local Least Squares (DRFLLS); (3) Dynamic meteorological modeling "
    "backed by Pufferfish-optimized temporal sequence learning; (4) Multi-class crop prediction utilizing an audited 100-tree Random Forest "
    "(99.52% ± 0.25% 5-fold CV) alongside an experimental Spatio-Temporal LSTM Cross-Attention Fusion module; and (5) A deterministic "
    "ICAR stoichiometric fertilizer engine computing commercial 50kg bag quantities (Urea, DAP, MOP) with FAO-56 Penman-Monteith irrigation hydrology.\n\n"
    "Validated with 39+ automated unit tests and regional cadastral integration (Cents/Gunthas), AgriSense AI delivers verifiable, "
    "transparent, and scientifically audited farm advisories to maximize sustainable crop yields."
)
p_body = tf_abs.add_paragraph()
p_body.text = abs_text
p_body.font.size = Pt(10.5)
p_body.font.color.rgb = COLOR_SLATE_BODY
p_body.space_before = Pt(8)


# ==============================================================================
# SLIDE 4: INTRODUCTION & PROBLEM STATEMENT
# ==============================================================================
s4 = prs.slides.add_slide(blank_layout)
add_header_footer(s4, "Introduction & Agricultural Motivation")

c_w = Inches(3.68)
c_h = Inches(5.1)
gap = Inches(0.34)
c1_x = Inches(0.8)
c2_x = c1_x + c_w + gap
c3_x = c2_x + c_w + gap

# Col 1: Smallholder Farming Crisis
create_card(s4, c1_x, Inches(1.65), c_w, c_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_c1 = s4.shapes.add_textbox(c1_x + Inches(0.2), Inches(1.85), c_w - Inches(0.4), c_h - Inches(0.4))
tf_c1 = tb_c1.text_frame
tf_c1.word_wrap = True
tf_c1.paragraphs[0].text = "SMALLHOLDER CHALLENGES"
tf_c1.paragraphs[0].font.size = Pt(12)
tf_c1.paragraphs[0].font.bold = True
tf_c1.paragraphs[0].font.color.rgb = COLOR_NAVY

c1_pts = [
    ("Monoculture Vulnerability: ", "Continuous single-crop cultivation depletes specific soil micronutrients and increases pest susceptibility."),
    ("Unpredictable Climate Drift: ", "Erratic monsoon onset and sudden dry spells invalidate traditional farmer intuition and calendar practices."),
    ("Fertilizer Guesswork: ", "Over-application of Urea causes soil acidification, nitrogen runoff, and heavy financial burdens on smallholders."),
    ("Water Inefficiency: ", "Arbitrary flood irrigation depletes groundwater reserves without matching crop phenological stages.")
]
for lbl, val in c1_pts:
    add_bullet(tf_c1, lbl, val, pt_size=9.2, space=6)

# Col 2: Need for Smart Hybrid AI
create_card(s4, c2_x, Inches(1.65), c_w, c_h, COLOR_BLUE_TINT, COLOR_BLUE_BORDER)
tb_c2 = s4.shapes.add_textbox(c2_x + Inches(0.2), Inches(1.85), c_w - Inches(0.4), c_h - Inches(0.4))
tf_c2 = tb_c2.text_frame
tf_c2.word_wrap = True
tf_c2.paragraphs[0].text = "ROLE OF HYBRID AI & DL"
tf_c2.paragraphs[0].font.size = Pt(12)
tf_c2.paragraphs[0].font.bold = True
tf_c2.paragraphs[0].font.color.rgb = COLOR_NAVY_LIGHT

c2_pts = [
    ("Multimodal Synergy: ", "Coupling spatial visual features (soil color/texture) with tabular soil chemistry and dynamic climate time-series."),
    ("Spatio-Temporal Modeling: ", "Capturing complex environmental dynamics using Graph Neural Networks and recurrent temporal cells."),
    ("Explainable AI (XAI): ", "Black-box predictions fail in the field; farmers require SHAP/LIME feature insights to trust AI advisories."),
    ("Scientific Optimization: ", "Metaheuristic optimizers (POA) reduce parameter convergence time and avoid local error minima.")
]
for lbl, val in c2_pts:
    add_bullet(tf_c2, lbl, val, pt_size=9.2, space=6)

# Col 3: The AgriSense AI Solution
create_card(s4, c3_x, Inches(1.65), c_w, c_h, COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_c3 = s4.shapes.add_textbox(c3_x + Inches(0.2), Inches(1.85), c_w - Inches(0.4), c_h - Inches(0.4))
tf_c3 = tb_c3.text_frame
tf_c3.word_wrap = True
tf_c3.paragraphs[0].text = "AGRISENSE AI SOLUTION"
tf_c3.paragraphs[0].font.size = Pt(12)
tf_c3.paragraphs[0].font.bold = True
tf_c3.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

c3_pts = [
    ("End-to-End Decision Suite: ", "Unifies soil diagnosis, crop recommendation, fertilizer calculation, and irrigation planning in one responsive platform."),
    ("Practical Farm Units: ", "Outputs commercial 50kg bags (DAP, Urea, MOP) rather than abstract kg/ha; natively supports Cents and Gunthas."),
    ("Scientifically Audited: ", "Zero data leakage, Wilson 95% confidence intervals, and 39+ automated regression test cases."),
    ("Zero-Downtime Resilience: ", "3-tier weather fallback (ECMWF -> OpenWeather -> Climatic Normals) ensures 100% field availability.")
]
for lbl, val in c3_pts:
    add_bullet(tf_c3, lbl, val, pt_size=9.2, space=6)


# ==============================================================================
# SLIDE 5: OBJECTIVES
# ==============================================================================
s5 = prs.slides.add_slide(blank_layout)
add_header_footer(s5, "Project Objectives & Scope of Work")

card_w = Inches(5.72)
card_h = Inches(2.35)
col1_l = Inches(0.8)
col2_l = Inches(6.81)
row1_t = Inches(1.65)
row2_t = Inches(4.35)

objs = [
    (
        col1_l, row1_t, "1. Visual Soil Texture Classification",
        "Deep Learning Vision with Holdout Integrity",
        [
            ("Architecture: ", "Deploy DTBRCNN / MobileNetV2 transfer learning to categorize field soil photos into 5 classes (Black, Red, Sandy, Clayey, Loamy)."),
            ("Data Integrity: ", "Evaluate on 144 real field photographs with perceptual hash deduplication to eliminate CycleGAN leakage."),
            ("Target Benchmark: ", "Attain 88.2% holdout test accuracy with calibrated temperature scaling (T=0.811).")
        ],
        COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_NAVY
    ),
    (
        col2_l, row1_t, "2. High-Accuracy Multi-Crop Recommendation",
        "Ensemble Tabular & Multimodal Decision Engine",
        [
            ("Supervised Learning: ", "Deploy a 100-tree Random Forest classifier across 23 crop varieties trained on 2,300 standardized agronomic records."),
            ("Rigorous Validation: ", "Achieve 99.52% ± 0.25% accuracy across 5-Fold Stratified Cross-Validation on benchmark data."),
            ("Research Prototype: ", "Formulate Spatio-Temporal LSTM Cross-Attention Fusion (ST-LSTM) for dynamic climate sequences.")
        ],
        COLOR_GREEN_TINT, COLOR_GREEN_BORDER, COLOR_PRIMARY_DARK
    ),
    (
        col1_l, row2_t, "3. Stoichiometric Fertilizer Dosage Engine",
        "Deterministic Chemistry & Indian Agronomic Guidelines",
        [
            ("Chemical Mass Balance: ", "Formulate exact nutrient equations satisfying deficits via DAP (18% N, 46% P2O5), Urea (46% N), and MOP (60% K2O)."),
            ("Commercial Bag Output: ", "Convert net nutrient requirements into commercial 50kg bags tailored to local field sizes (Cents/Gunthas/Acres)."),
            ("Split Application Schedule: ", "Generate 3-stage crop growth timeline (Basal sowing, Tillering, Panicle initiation).")
        ],
        COLOR_GREEN_TINT, COLOR_GREEN_BORDER, COLOR_PRIMARY_DARK
    ),
    (
        col2_l, row2_t, "4. Hydrology, Harvest & Transparent Advisory",
        "FAO-56 Irrigation, IASRI Phenology & Explainable AI",
        [
            ("FAO-56 Dual Hydrology: ", "Compute daily reference evapotranspiration (ET0) and crop water demand (ETc = ET0 * Kc) using live weather telemetry."),
            ("Harvest Modeling: ", "Project harvest maturity windows and economic valuations using IASRI crop calendars and MSP tables."),
            ("Model Transparency: ", "Incorporate SHAP & LIME interpretability and Top-3 ambiguity alerts for farmer trust.")
        ],
        COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_NAVY
    )
]

for l, t, title, sub, pts, bg_c, bdr_c, h_c in objs:
    create_card(s5, l, t, card_w, card_h, bg_c, bdr_c)
    tb = s5.shapes.add_textbox(l + Inches(0.18), t + Inches(0.12), card_w - Inches(0.36), card_h - Inches(0.24))
    tf = tb.text_frame
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = h_c
    p_sub = tf.add_paragraph()
    p_sub.text = sub
    p_sub.font.size = Pt(9.5)
    p_sub.font.bold = True
    p_sub.font.color.rgb = COLOR_SLATE_MUTED
    for lbl, val in pts:
        add_bullet(tf, lbl, val, pt_size=8.8, space=2.5)


# ==============================================================================
# SLIDE 6: BLOCK DIAGRAM / SYSTEM FLOWCHART
# ==============================================================================
s6 = prs.slides.add_slide(blank_layout)
add_header_footer(s6, "System Architecture & Unified Multi-Module Workflow")

# 5 Sequential Workflow Panels
step_w = Inches(2.23)
step_h = Inches(5.1)
step_gap = Inches(0.14)
start_x = Inches(0.8)
step_y = Inches(1.65)

steps = [
    (
        "PHASE 01: SURVEY",
        "Cadastral & Soil Input",
        [
            ("Regional Setup: ", "Select State & District (Coimbatore, Tamil Nadu)."),
            ("Cadastral Units: ", "Input farm area in native South Indian units (Cents / Gunthas / Acres)."),
            ("Soil Image: ", "Upload field photograph for automated visual texture diagnosis (DTBRCNN)."),
            ("Chemical Test: ", "Optionally enter Soil Health Card (SHC) N-P-K & pH values.")
        ],
        COLOR_CARD_BG, COLOR_CARD_BORDER
    ),
    (
        "PHASE 02: CLIMATE",
        "Spatio-Temporal Weather",
        [
            ("Live Telemetry: ", "Auto-sync GPS weather via Open-Meteo ECMWF API."),
            ("Preprocessing: ", "DRFLLS cleans sensor anomalies and imputes missing weather variables."),
            ("Sequence Model: ", "SPLSTMGNN models 7-day temperature, humidity & rainfall dynamics."),
            ("Fallback Mesh: ", "Automated failover to OpenWeather and historical agro-climatic normals.")
        ],
        COLOR_BLUE_TINT, COLOR_BLUE_BORDER
    ),
    (
        "PHASE 03: AI FUSION",
        "Crop Decision Engine",
        [
            ("Production RF: ", "100-Tree Random Forest delivers instant, audited classification (99.52% CV)."),
            ("Research Fusion: ", "Experimental ST-LSTM fuses visual soil embeddings with climate sequences."),
            ("Ambiguity Check: ", "Top-3 candidate analysis; flags ambiguity if Rank-1 vs Rank-2 gap < 15%."),
            ("Explainable AI: ", "SHAP & LIME interpretability highlights critical limiting factors.")
        ],
        COLOR_GREEN_TINT, COLOR_GREEN_BORDER
    ),
    (
        "PHASE 04: ICAR ENGINE",
        "Stoichiometric Fertilizer",
        [
            ("Chemical Balance: ", "DAP satisfies P2O5; elemental N from DAP deducted; Urea balances residual N; MOP provides K2O."),
            ("Commercial Bags: ", "Outputs integer & decimal 50kg bags needed for the exact farm parcel."),
            ("Growth Schedule: ", "Splits dosages across 3 key growth stages (Basal, Tillering, Panicle)."),
            ("Zero Waste Alert: ", "Alerts farmer if native soil reserves are already sufficient.")
        ],
        COLOR_GREEN_TINT, COLOR_GREEN_BORDER
    ),
    (
        "PHASE 05: ADVISORY",
        "Hydrology & Reporting",
        [
            ("FAO-56 Irrigation: ", "Penman-Monteith ET0 multiplied by crop Kc curves yields daily liter requirements."),
            ("Harvest Modeler: ", "IASRI phenological duration predicts maturity date and MSP gross returns."),
            ("Printable Dossier: ", "One-click generation of comprehensive, bilingual farmer advisory PDF."),
            ("Field Ready: ", "Zero-dependency browser interface usable on mobile, tablet, and PC.")
        ],
        COLOR_CARD_BG, COLOR_CARD_BORDER
    )
]

for i, (p_title, p_sub, pts, bg_c, bdr_c) in enumerate(steps):
    x_pos = start_x + i * (step_w + step_gap)
    create_card(s6, x_pos, step_y, step_w, step_h, bg_c, bdr_c)
    tb = s6.shapes.add_textbox(x_pos + Inches(0.12), step_y + Inches(0.14), step_w - Inches(0.24), step_h - Inches(0.28))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.text = p_title
    p0.font.size = Pt(10)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_NAVY
    
    ps = tf.add_paragraph()
    ps.text = p_sub
    ps.font.size = Pt(9.5)
    ps.font.bold = True
    ps.font.color.rgb = COLOR_PRIMARY_DARK
    ps.space_before = Pt(2)
    
    for lbl, val in pts:
        add_bullet(tf, lbl, val, pt_size=8.2, space=4)


# ==============================================================================
# SLIDE 7: LITERATURE SURVEY (PART 1/2) - PAPERS 1 TO 8
# ==============================================================================
s7 = prs.slides.add_slide(blank_layout)
add_header_footer(s7, "Literature Survey (Part 1/2: Crop Recommendation & Platforms)")

# Table covering 8 papers
rows, cols = 9, 6
tbl_shape7 = s7.shapes.add_table(rows, cols, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.15))
tbl7 = tbl_shape7.table

# Set Column Widths
tbl7.columns[0].width = Inches(0.55)   # Ref
tbl7.columns[1].width = Inches(2.25)   # Author & Year
tbl7.columns[2].width = Inches(2.35)   # Methodology
tbl7.columns[3].width = Inches(2.05)   # Advantages (As Reported)
tbl7.columns[4].width = Inches(2.25)   # Disadvantages
tbl7.columns[5].width = Inches(2.28)   # Inference for AgriSense

headers = ["#", "Author & Year", "Methodology", "Advantages (As Reported)", "Disadvantages / Limitations", "Inference for AgriSense AI"]
for j, h in enumerate(headers):
    cell = tbl7.cell(0, j)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_NAVY
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.bold = True
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_WHITE
    p.alignment = PP_ALIGN.CENTER

lit_part1 = [
    ("[1]", "Mohan & Anandamurugan (2025) [Base Paper]", "DTBRCNN (Soil) + SPLSTMGNN (Weather) + Cross-Attention Fusion + POA", "99% soil acc, 99.1% weather acc, XAI (SHAP/LIME)", "Complex multi-stage deep learning pipeline", "Foundational theoretical framework; AgriSense adds practical farm execution"),
    ("[2]", "Mahmud et al. (2024)", "Genetic Algorithm (GA) feature selection + Random Forest", "98.35% accuracy, 22 crop classification", "GA tuning sensitive, potential overfitting on small datasets", "Proves Random Forest is an industry-standard baseline for 22+ Indian crops"),
    ("[3]", "Garg & Alam (2023)", "Wrapper Part Grid Search (WPGA) on benchmark data", "97.78% accuracy, lightweight & interpretable", "Lacks deep spatial/temporal feature extraction", "Simple tabular models achieve high accuracy with minimal inference latency"),
    ("[4]", "Kiruthika & Karthika (2023)", "IDCSO-WLSTM on IoT sensor time-series data", "98.35% accuracy, captures temporal trends", "Compute-heavy, high training latency", "Confirms temporal modeling value; justifies isolating heavy LSTM as experimental"),
    ("[5]", "Thilakarathne et al. (2022)", "Cloud-hosted IoT-ML precision agriculture pipeline*", "Centralized farmer access via browser*", "Fails in zero-connectivity rural zones without offline cache*", "Backs AgriSense AI's web-first responsive dashboard and lightweight API design"),
    ("[6]", "Madhuri & Indiramma (2021)", "Artificial Neural Networks (ANN) on soil & climate*", "Directly utilizes N, P, K, pH + weather parameters*", "Black-box model; sensitive to raw feature scaling*", "Confirms our 7-dimensional agronomic feature vector (N, P, K, pH, T, H, R)"),
    ("[7]", "Akkem et al. (2024)", "Streamlit Web App + ML + Explainable AI (LIME & SHAP)*", "Transparent local decision boundaries for farmers*", "Limited to crop choice; no fertilizer or water guidance*", "Strongly justifies AgriSense's XAI explainability and Top-3 ambiguity alerts"),
    ("[8]", "Shastri et al. (2025)", "Gradient Boosting on soil NPK + Explainable AI", "96.45% accuracy, farmer trust via explanation", "Explainability constraint causes slight accuracy trade-off", "Validates showing agronomic explanations alongside crop predictions")
]

for i, row in enumerate(lit_part1):
    for j, val in enumerate(row):
        cell = tbl7.cell(i+1, j)
        cell.fill.solid()
        if i == 0:
            cell.fill.fore_color.rgb = COLOR_GREEN_TINT
        else:
            cell.fill.fore_color.rgb = COLOR_WHITE if i % 2 == 0 else COLOR_CARD_BG
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.size = Pt(7.5)
        p.font.color.rgb = COLOR_PRIMARY_DARK if i == 0 else COLOR_SLATE_DARK
        if j == 0:
            p.alignment = PP_ALIGN.CENTER
            p.font.bold = True
        elif i == 0:
            p.font.bold = True


# ==============================================================================
# SLIDE 8: LITERATURE SURVEY (PART 2/2) - PAPERS 9 TO 16
# ==============================================================================
s8 = prs.slides.add_slide(blank_layout)
add_header_footer(s8, "Literature Survey (Part 2/2: Vision, Fertilizer & Hydrology)")

tbl_shape8 = s8.shapes.add_table(rows, cols, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.15))
tbl8 = tbl_shape8.table

tbl8.columns[0].width = Inches(0.55)
tbl8.columns[1].width = Inches(2.25)
tbl8.columns[2].width = Inches(2.35)
tbl8.columns[3].width = Inches(2.05)
tbl8.columns[4].width = Inches(2.25)
tbl8.columns[5].width = Inches(2.28)

for j, h in enumerate(headers):
    cell = tbl8.cell(0, j)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_PRIMARY_DARK
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.bold = True
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_WHITE
    p.alignment = PP_ALIGN.CENTER

lit_part2 = [
    ("[9]", "Banoth & Murthy (2024)", "MobileNetV2 Transfer Learning with custom CNN head", "98.45% accuracy, lightweight, mobile-deployable", "Small dataset (n=108), high risk of domain overfitting", "Validates MobileNetV2 backbone; justifies our leakage-free holdout evaluation"),
    ("[10]", "Pandiri et al. (2024)", "Lightweight CNN (LCNN) on 5 soil classes", "97.2% accuracy, low computational overhead", "Severe class imbalance impacts rare soil types", "Aligns with our 5 soil classes; justifies class-weighted loss for Loamy soil"),
    ("[11]", "Lanjewar & Gurav (2022)", "Deep Convolutional Neural Network (DCNN)", "97–98% validation accuracy, robust features", "High compute & memory footprint, slow on edge devices", "Confirms why lightweight architectures (MobileNetV2) are superior for web inference"),
    ("[12]", "Bhola & Kumar (2024)", "ML-CSFR: Multi-model ML for crop + fertilizer", "Dual-objective recommendation framework", "Low accuracy (89.45%), limited real-farm validation", "Closest prior art; highlights why AgriSense uses deterministic ICAR stoichiometry"),
    ("[13]", "Sambhe et al. (2024)", "DeepNet230 classifier on nutrient & temperature data", "93.7% accuracy, predicts season-wise crop & yield", "Large feature-heavy model requiring continuous sensors", "Directly supports AgriSense AI's Harvest & Yield duration projection module"),
    ("[14]", "Acharya et al. (2021)", "ML on soil texture and nearby weather station data*", "Accurately models field soil water retention*", "Dependent on external weather station telemetry*", "Provides baseline justification for AgriSense's FAO-56 Irrigation Engine"),
    ("[15]", "Anand et al. (2024)", "RESRNN-MR (weather) + CCGAN-CH (crop selection)", "97.45% accuracy, spatio-temporal weather adaptation", "Highly localized to Hooghly, West Bengal; low transferability", "Highlights necessity of local microclimate sync (Coimbatore / regional agro-zones)"),
    ("[16]", "Sravanthi & Moparthi (2024)", "MKGPCNN + CGSAAN on IoT data for crop & disease", "98.0% accuracy, unifies crop & disease prediction", "Extreme architectural complexity; limited real-farm testing", "Supports AgriSense AI's modular roadmap for future leaf disease detection")
]

for i, row in enumerate(lit_part2):
    for j, val in enumerate(row):
        cell = tbl8.cell(i+1, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_WHITE if i % 2 == 0 else COLOR_CARD_BG
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.size = Pt(7.5)
        p.font.color.rgb = COLOR_SLATE_DARK
        if j == 0:
            p.alignment = PP_ALIGN.CENTER
            p.font.bold = True


# ==============================================================================
# SLIDE 9: RESEARCH GAP & OUR CONTRIBUTION
# ==============================================================================
s9 = prs.slides.add_slide(blank_layout)
add_header_footer(s9, "Research Gap Analysis & Novel Contributions")

create_card(s9, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_gap = s9.shapes.add_textbox(col1_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_gap = tb_gap.text_frame
tf_gap.word_wrap = True
tf_gap.paragraphs[0].text = "IDENTIFIED RESEARCH GAPS"
tf_gap.paragraphs[0].font.size = Pt(13)
tf_gap.paragraphs[0].font.bold = True
tf_gap.paragraphs[0].font.color.rgb = COLOR_NAVY

gaps = [
    ("Lifecycle Disconnection: ", "While Bhola & Kumar [12] recently attempted combined crop and fertilizer selection, NO reviewed system integrates the complete agronomic lifecycle — Crop Selection, Stoichiometric Fertilizer, FAO-56 Hydrological Irrigation, Harvest Projection, and Cadastral Units into a unified farmer-facing platform."),
    ("Unaddressed Data Leakage: ", "Existing soil vision papers (e.g. Banoth [9], Pandiri [10]) frequently use synthetic GAN clones or random image splitting, resulting in inflated accuracies (>98%) without true field generalization."),
    ("Impractical Dosage Outputs: ", "Literature provides abstract fertilizer dosages in kg/ha without converting to commercial 50kg bags (DAP, Urea, MOP) or factoring in basal/top-dressing growth stages."),
    ("Black-Box Mistrust & Lack of Limitations: ", "Prior models deliver point predictions without explainability (XAI), uncertainty confidence gaps, or documented model failure boundaries (e.g., loamy soil weaknesses).")
]
for lbl, val in gaps:
    add_bullet(tf_gap, lbl, val, pt_size=9.2, space=6)

create_card(s9, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_con = s9.shapes.add_textbox(col2_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_con = tb_con.text_frame
tf_con.word_wrap = True
tf_con.paragraphs[0].text = "AGRISENSE AI NOVEL CONTRIBUTIONS"
tf_con.paragraphs[0].font.size = Pt(13)
tf_con.paragraphs[0].font.bold = True
tf_con.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

contributions = [
    ("Unified Full-Cycle Platform: ", "First system to bridge theoretical DL architecture from Mohan & Anandamurugan [1] with practical ground-level agronomic engines (Crop, Fertilizer, Water, Harvest)."),
    ("Scientifically Audited Vision: ", "Evaluated strictly on 144 real field photos with exact perceptual hash deduplication; achieves 88.2% holdout accuracy with Wilson 95% confidence intervals."),
    ("Commercial Stoichiometric Balancing: ", "Deterministic ICAR mass-balance engine computing exact commercial 50kg bag quantities (Urea, DAP, MOP) across South Indian regional cadastral units (Cents & Gunthas)."),
    ("Dual Engine Decision Architecture: ", "Deploys a robust, audited Random Forest in production (<1ms latency) while isolating multimodal Spatio-Temporal LSTM Fusion as an advanced experimental research prototype."),
    ("Explainable Farmer Dossier: ", "Integrates SHAP/LIME decision transparency and auto-generates printable field advisory reports.")
]
for lbl, val in contributions:
    add_bullet(tf_con, lbl, val, pt_size=9.2, space=5.5)


# ==============================================================================
# SLIDE 10: EXISTING SYSTEM VS PROPOSED SYSTEM
# ==============================================================================
s10 = prs.slides.add_slide(blank_layout)
add_header_footer(s10, "Comparative Analysis: Existing vs. Proposed System")

tbl_shape10 = s10.shapes.add_table(7, 3, Inches(0.8), Inches(1.7), Inches(11.733), Inches(5.0))
tbl10 = tbl_shape10.table
tbl10.columns[0].width = Inches(2.733)
tbl10.columns[1].width = Inches(4.5)
tbl10.columns[2].width = Inches(4.5)

comp_headers = ["Functional Dimension", "Existing Systems & Traditional Methods", "AgriSense AI (Proposed Solution)"]
for j, h in enumerate(comp_headers):
    cell = tbl10.cell(0, j)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_NAVY if j != 2 else COLOR_PRIMARY_DARK
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.bold = True
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_WHITE
    p.alignment = PP_ALIGN.CENTER

comparisons = [
    ("Soil Health Assessment", "Manual lab testing delays (1-3 weeks) or basic guesswork based on topsoil appearance.", "Instant visual soil diagnosis via MobileNetV2 CNN (88.2% acc) + 1-Click ICAR regional presets."),
    ("Crop Selection Strategy", "Monoculture tradition; unscientific crop choice leading to crop failure during weather shifts.", "Supervised Random Forest (99.52% CV) across 23 crops with Top-3 candidate ranking & ambiguity flags."),
    ("Fertilizer Dosage Calculation", "Blind broad-acre spreading of Urea; severe chemical imbalance and groundwater leaching.", "Stoichiometric chemical balancing yielding exact 50kg commercial bags (DAP, Urea, MOP) in 3 split stages."),
    ("Irrigation Water Management", "Arbitrary flood watering or continuous pump operation wasting groundwater reserves.", "FAO-56 Penman-Monteith dual hydrology; daily evapotranspiration (ET0) & dynamic Kc volumetric liter output."),
    ("Meteorological Telemetry", "Generic TV/newspaper forecasts; no farm-specific microclimate integration.", "Automated live GPS agro-weather sync (Open-Meteo ECMWF) with 3-tier zero-downtime fallback."),
    ("Cadastral Units & Reporting", "Only standard Hectares/Acres supported; no localized farmer documentation.", "Native South Indian cadastral units (Cents & Gunthas) + One-Click printable bilingual advisory dossier.")
]

for i, (dim, exist, prop) in enumerate(comparisons):
    cell0 = tbl10.cell(i+1, 0)
    cell0.fill.solid()
    cell0.fill.fore_color.rgb = COLOR_CARD_BG
    p0 = cell0.text_frame.paragraphs[0]
    p0.text = dim
    p0.font.bold = True
    p0.font.size = Pt(8.5)
    p0.font.color.rgb = COLOR_NAVY

    cell1 = tbl10.cell(i+1, 1)
    cell1.fill.solid()
    cell1.fill.fore_color.rgb = COLOR_WHITE
    p1 = cell1.text_frame.paragraphs[0]
    p1.text = exist
    p1.font.size = Pt(8.2)
    p1.font.color.rgb = COLOR_SLATE_BODY

    cell2 = tbl10.cell(i+1, 2)
    cell2.fill.solid()
    cell2.fill.fore_color.rgb = COLOR_GREEN_TINT
    p2 = cell2.text_frame.paragraphs[0]
    p2.text = prop
    p2.font.size = Pt(8.2)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_PRIMARY_DARK


# ==============================================================================
# SLIDE 11: TECHNICAL REQUIREMENTS & ENVIRONMENT
# ==============================================================================
s11 = prs.slides.add_slide(blank_layout)
add_header_footer(s11, "Hardware & Software Specifications")

create_card(s11, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_hw = s11.shapes.add_textbox(col1_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_hw = tb_hw.text_frame
tf_hw.word_wrap = True
tf_hw.paragraphs[0].text = "HARDWARE INFRASTRUCTURE"
tf_hw.paragraphs[0].font.size = Pt(13)
tf_hw.paragraphs[0].font.bold = True
tf_hw.paragraphs[0].font.color.rgb = COLOR_NAVY

hw_specs = [
    ("Development Workstation: ", "Intel Core i7 / AMD Ryzen 7 (8-Core, 16-Threads), 16GB / 32GB DDR4/DDR5 RAM."),
    ("GPU Acceleration: ", "NVIDIA GeForce RTX (CUDA 12.x enabled) for PyTorch neural network training and validation."),
    ("Production Server: ", "Linux (Ubuntu 22.04 LTS / Containerized Docker), 4GB Minimum RAM, Dual-Core vCPU (Sub-50ms latency)."),
    ("Edge / Client Devices: ", "Zero hardware dependencies; accessible via any standard mobile smartphone, tablet, or desktop PC browser."),
    ("Network Connectivity: ", "Active HTTP/HTTPS connection for live Open-Meteo GPS weather sync; cached offline mode supported.")
]
for lbl, val in hw_specs:
    add_bullet(tf_hw, lbl, val, pt_size=9.2, space=7)

create_card(s11, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_BLUE_TINT, COLOR_BLUE_BORDER)
tb_sw = s11.shapes.add_textbox(col2_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_sw = tb_sw.text_frame
tf_sw.word_wrap = True
tf_sw.paragraphs[0].text = "SOFTWARE & FRAMEWORK STACK"
tf_sw.paragraphs[0].font.size = Pt(13)
tf_sw.paragraphs[0].font.bold = True
tf_sw.paragraphs[0].font.color.rgb = COLOR_NAVY_LIGHT

sw_specs = [
    ("Frontend Layer: ", "React.js 18, Vite build tool, Tailwind CSS, Lucide Icons, responsive single-page architecture (SPA)."),
    ("Backend API Layer: ", "Python (Flask RESTful API, Flask-CORS, Gunicorn WSGI production server)."),
    ("Machine Learning & Vision: ", "PyTorch 2.x, Torchvision, Scikit-learn, Pandas, NumPy, Joblib model serialization."),
    ("Meteorological API: ", "Open-Meteo High-Resolution ECMWF Live Forecast API (with OpenWeather fallback & Ra normals)."),
    ("Agronomic Core: ", "ICAR Stoichiometric Fertilizer Dosage Engine & South India Cadastral Revenue Unit Converter."),
    ("Testing Suite: ", "Python Unittest Framework comprising 39+ automated integration, mathematical, and boundary tests.")
]
for lbl, val in sw_specs:
    add_bullet(tf_sw, lbl, val, pt_size=9.2, space=5.5)


# ==============================================================================
# SLIDE 12: MODULE 1 - SOIL VISION CLASSIFICATION (DTBRCNN)
# ==============================================================================
s12 = prs.slides.add_slide(blank_layout)
add_header_footer(s12, "Module 1: Soil Vision Classification (DTBRCNN / MobileNetV2)")

create_card(s12, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_m1a = s12.shapes.add_textbox(col1_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m1a = tb_m1a.text_frame
tf_m1a.word_wrap = True
tf_m1a.paragraphs[0].text = "MODEL ARCHITECTURE & SCIENTIFIC RIGOR"
tf_m1a.paragraphs[0].font.size = Pt(12)
tf_m1a.paragraphs[0].font.bold = True
tf_m1a.paragraphs[0].font.color.rgb = COLOR_NAVY

m1a_pts = [
    ("Deep Backbone: ", "MobileNetV2 feature extractor / DTBRCNN dual bottleneck residual blocks with custom classification head."),
    ("Head Formulation: ", "Dropout(0.2) -> Linear(128) -> BatchNorm1d -> ReLU -> Dropout(0.2) -> Linear(5)."),
    ("Dataset Composition: ", "987 original field photographs across Indian soil zones (Black, Red, Sandy, Clayey, Loamy)."),
    ("Leakage Elimination: ", "Connected-component perceptual hash clustering (d <= 6); CycleGAN synthetic clones removed due to verified -9.72% real-world domain degradation."),
    ("Probability Calibration: ", "Post-hoc temperature scaling (T = 0.811) reducing Expected Calibration Error (ECE) from 12.4% to 5.2%.")
]
for lbl, val in m1a_pts:
    add_bullet(tf_m1a, lbl, val, pt_size=9.2, space=6)

create_card(s12, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_m1b = s12.shapes.add_textbox(col2_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m1b = tb_m1b.text_frame
tf_m1b.word_wrap = True
tf_m1b.paragraphs[0].text = "HOLDOUT METRICS & DOCUMENTED BOUNDARIES"
tf_m1b.paragraphs[0].font.size = Pt(12)
tf_m1b.paragraphs[0].font.bold = True
tf_m1b.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

m1b_pts = [
    ("Holdout Accuracy: ", "88.19% (127 / 144 correct) [Wilson 95% CI: 82.64% – 93.07%]."),
    ("Macro F1-Score: ", "0.809 [Wilson 95% Confidence Interval: 0.708 – 0.884]."),
    ("Class-Wise Breakdown: ", "Black: F1 0.946 (n=37) • Red: F1 0.925 (n=47) • Sandy: F1 0.900 (n=43) • Clayey: F1 0.800 (n=9)."),
    ("Documented Loamy Weakness: ", "Loamy F1: 0.476 (n=8, Precision 38.5%) due to natural textural overlap and limited training samples."),
    ("Fail-Safe Design: ", "If vision confidence < 70%, the system flags an uncertainty notice and allows manual 1-click soil texture override in the UI.")
]
for lbl, val in m1b_pts:
    add_bullet(tf_m1b, lbl, val, pt_size=9.2, space=6)


# ==============================================================================
# SLIDE 13: MODULE 2 - DATA PREPROCESSING & CLEANING (DRFLLS)
# ==============================================================================
s13 = prs.slides.add_slide(blank_layout)
add_header_footer(s13, "Module 2: Data Preprocessing & Cleaning (DRFLLS)")

create_card(s13, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_m2a = s13.shapes.add_textbox(col1_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m2a = tb_m2a.text_frame
tf_m2a.word_wrap = True
tf_m2a.paragraphs[0].text = "THE DRFLLS METHODOLOGY"
tf_m2a.paragraphs[0].font.size = Pt(12)
tf_m2a.paragraphs[0].font.bold = True
tf_m2a.paragraphs[0].font.color.rgb = COLOR_NAVY

m2a_pts = [
    ("Ensemble Foundation: ", "Combines Random Forest Algorithm (RFA) with Local Least Squares (LLS) as formulated by Mohan & Anandamurugan (2025)."),
    ("Outlier & Noise Mitigation: ", "Reduces bias from sensor noise and mislabeled farm samples by aggregating randomized decision trees and bootstrap samples."),
    ("Localized Linear Modeling: ", "Fits localized linear models to capture underlying spatial data correlations across micro-climates."),
    ("Missing Value Imputation: ", "Predicts missing agricultural features using weighted nearest neighbor averages: Y_missing = (1/K) * sum(Y_nearer_neighbour)."),
    ("Data Quality Guarantee: ", "Ensures high data integrity and stability before passing parameters into downstream inference models.")
]
for lbl, val in m2a_pts:
    add_bullet(tf_m2a, lbl, val, pt_size=9.2, space=6)

create_card(s13, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_BLUE_TINT, COLOR_BLUE_BORDER)
tb_m2b = s13.shapes.add_textbox(col2_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m2b = tb_m2b.text_frame
tf_m2b.word_wrap = True
tf_m2b.paragraphs[0].text = "AGRISENSE DATA INTEGRATION & VALIDATION"
tf_m2b.paragraphs[0].font.size = Pt(12)
tf_m2b.paragraphs[0].font.bold = True
tf_m2b.paragraphs[0].font.color.rgb = COLOR_NAVY_LIGHT

m2b_pts = [
    ("Physiological Boundary Checks: ", "Enforces strict chemical bounds (pH in [0, 14], N/P/K >= 0 kg/ha); prevents out-of-range sensor crash."),
    ("StandardScaler Feature Normalization: ", "Standardizes 7 continuous features (N, P, K, Temp, Humidity, pH, Rainfall) into zero-mean, unit-variance distributions."),
    ("Sensor Noise Stress Testing: ", "System audited under simulated ±10% NPK noise, ±2°C temperature shifts, and ±15% rainfall perturbations (maintains 95.91% ± 0.37% accuracy)."),
    ("Regional Presets: ", "Provides calibrated 1-click agronomic presets (Kharif Wetland, Rabi Loam, Arid Gram, Cotton Black) for rapid farmer demonstration.")
]
for lbl, val in m2b_pts:
    add_bullet(tf_m2b, lbl, val, pt_size=9.2, space=6)


# ==============================================================================
# SLIDE 14: MODULE 3 - WEATHER FORECASTING (SPLSTMGNN & POA)
# ==============================================================================
s14 = prs.slides.add_slide(blank_layout)
add_header_footer(s14, "Module 3: Spatio-Temporal Weather Forecasting (SPLSTMGNN & POA)")

create_card(s14, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_m3a = s14.shapes.add_textbox(col1_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m3a = tb_m3a.text_frame
tf_m3a.word_wrap = True
tf_m3a.paragraphs[0].text = "THEORETICAL MODELING (MOHAN ET AL. 2025)"
tf_m3a.paragraphs[0].font.size = Pt(12)
tf_m3a.paragraphs[0].font.bold = True
tf_m3a.paragraphs[0].font.color.rgb = COLOR_NAVY

m3a_pts = [
    ("Spatial-Temporal Architecture: ", "Combines Graph Neural Networks (GNN) for spatial station correlations with LSTM cells for temporal sequence dependencies."),
    ("Spatial-Temporal Fusion Graph (STFG): ", "Generates sliced temporal tensors Y in R^(T x N x d x C) with multi-head graph self-attention."),
    ("Pufferfish Optimization Algorithm (POA): ", "Bio-inspired metaheuristic optimizing model hyperparameters via simulated predator-prey exploration & exploitation."),
    ("Loss Minimization: ", "Directly minimizes F(x) = RMSE + MAE error function, achieving rapid convergence without local minima traps."),
    ("Reported Benchmark: ", "Attains 99.1% accuracy and 0.254s latency (as reported in base research).")
]
for lbl, val in m3a_pts:
    add_bullet(tf_m3a, lbl, val, pt_size=9.2, space=6)

create_card(s14, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_m3b = s14.shapes.add_textbox(col2_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m3b = tb_m3b.text_frame
tf_m3b.word_wrap = True
tf_m3b.paragraphs[0].text = "AGRISENSE PRODUCTION WEATHER PIPELINE"
tf_m3b.paragraphs[0].font.size = Pt(12)
tf_m3b.paragraphs[0].font.bold = True
tf_m3b.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

m3b_pts = [
    ("Tier 1: High-Res Open-Meteo: ", "Live GPS sync with ECMWF 0.1° atmospheric numerical models fetching 7-day temperature, humidity, rainfall, and solar radiation."),
    ("Tier 2: OpenWeather Fallback: ", "Automatic secondary failover if primary gateway fails, ensuring continuous live weather sync."),
    ("Tier 3: Agro-Climatic Normals: ", "Failsafe Hargreaves extraterrestrial radiation (Ra) equations using latitude and day-of-year if totally offline."),
    ("In-Memory Caching: ", "Sub-millisecond API response times via 15-minute TTL coordinates cache to avoid redundant API hits."),
    ("Real-Time Advisory: ", "Wind speed spray drift alerts (<12 km/h safe threshold) and precipitation warnings.")
]
for lbl, val in m3b_pts:
    add_bullet(tf_m3b, lbl, val, pt_size=9.2, space=6)


# ==============================================================================
# SLIDE 15: MODULE 4 - MULTI-CROP RECOMMENDATION & FUSION
# ==============================================================================
s15 = prs.slides.add_slide(blank_layout)
add_header_footer(s15, "Module 4: Multi-Crop Recommendation & Cross-Attention Fusion")

create_card(s15, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_m4a = s15.shapes.add_textbox(col1_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m4a = tb_m4a.text_frame
tf_m4a.word_wrap = True
tf_m4a.paragraphs[0].text = "PRODUCTION: AUDITED RANDOM FOREST (PILLAR 1)"
tf_m4a.paragraphs[0].font.size = Pt(12)
tf_m4a.paragraphs[0].font.bold = True
tf_m4a.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

m4a_pts = [
    ("Core Model: ", "RandomForestClassifier(n_estimators=100, random_state=42) trained on 2,300 standardized records across 23 Indian crops."),
    ("Benchmark Rigor: ", "99.52% ± 0.25% accuracy across 5-Fold Stratified Cross-Validation on benchmark data."),
    ("Transparent Data Provenance: ", "Classes 1-22 sourced from Kaggle benchmark; Class 23 (Wheat) generated via calibrated ICAR Gaussian envelopes with clear UI badging."),
    ("Ambiguity Safeguard: ", "Outputs Top-3 ranked candidate crops; automatically flags 'is_ambiguous: true' if probability gap between Rank-1 and Rank-2 is < 15%."),
    ("Zero Latency: ", "Sub-millisecond inference (<1ms) enables instantaneous interactive UI updates.")
]
for lbl, val in m4a_pts:
    add_bullet(tf_m4a, lbl, val, pt_size=9.2, space=6)

create_card(s15, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_m4b = s15.shapes.add_textbox(col2_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m4b = tb_m4b.text_frame
tf_m4b.word_wrap = True
tf_m4b.paragraphs[0].text = "RESEARCH: CROSS-ATTENTION FUSION (EXPERIMENTAL)"
tf_m4b.paragraphs[0].font.size = Pt(12)
tf_m4b.paragraphs[0].font.bold = True
tf_m4b.paragraphs[0].font.color.rgb = COLOR_NAVY

m4b_pts = [
    ("Cross-Attention Formulation: ", "Fuses visual soil representation (del_A,B) with temporal weather predictions (g'_j(Q)): Fusion' = LayerNorm(del_A,B + g'_j(Q))."),
    ("Temporal Bi-LSTM: ", "Encodes 7-day multi-step meteorological sequences into a compressed latent bottleneck vector."),
    ("Scientific Governance & Audit: ", "Historical fusion model identified with target lookup leakage during training audit; responsibly isolated under /api/crop/fusion as an Experimental Research Prototype."),
    ("Multi-Crop Portfolios: ", "Supports Agro-Ecological Zone (AEZ) multi-crop combinations (e.g., Mung bean + Coffee for Southern Dry Zone; Chickpea for North-Eastern Dry Zone).")
]
for lbl, val in m4b_pts:
    add_bullet(tf_m4b, lbl, val, pt_size=9.2, space=6)


# ==============================================================================
# SLIDE 16: MODULE 5 - STOICHIOMETRIC FERTILIZER & IRRIGATION HYDROLOGY
# ==============================================================================
s16 = prs.slides.add_slide(blank_layout)
add_header_footer(s16, "Module 5: Agronomic Fertilizer Stoichiometry & Irrigation Hydrology")

create_card(s16, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_m5a = s16.shapes.add_textbox(col1_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m5a = tb_m5a.text_frame
tf_m5a.word_wrap = True
tf_m5a.paragraphs[0].text = "ICAR STOICHIOMETRIC FERTILIZER ENGINE"
tf_m5a.paragraphs[0].font.size = Pt(12)
tf_m5a.paragraphs[0].font.bold = True
tf_m5a.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

m5a_pts = [
    ("Deterministic Conservation Laws: ", "No black-box ML used in production; relies on physical mass balance of commercial fertilizers per Fertilizer Control Order (FCO)."),
    ("Chemical Formulations: ", "DAP (18% N, 46% P2O5) • Urea (46% N) • MOP (60% K2O)."),
    ("Step-by-Step Chemistry: ", "1. DAP satisfies P2O5 deficit -> 2. Nitrogen supplied by DAP is deducted -> 3. Remaining N satisfied via Urea -> 4. MOP satisfies K2O deficit."),
    ("Commercial 50kg Bags: ", "Outputs exact bags needed for farm plot area (e.g. 0.26 bags Urea, 0.18 bags DAP, 0.11 bags MOP for 25 Cents)."),
    ("Growth Stage Timing: ", "Provides 3-stage application schedule (100% DAP & 50% MOP basal at sowing; Urea split 50/25/25 at tillering & panicle).")
]
for lbl, val in m5a_pts:
    add_bullet(tf_m5a, lbl, val, pt_size=9.2, space=5.5)

create_card(s16, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_BLUE_TINT, COLOR_BLUE_BORDER)
tb_m5b = s16.shapes.add_textbox(col2_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m5b = tb_m5b.text_frame
tf_m5b.word_wrap = True
tf_m5b.paragraphs[0].text = "FAO-56 DUAL HYDROLOGY & HARVEST MODEL"
tf_m5b.paragraphs[0].font.size = Pt(12)
tf_m5b.paragraphs[0].font.bold = True
tf_m5b.paragraphs[0].font.color.rgb = COLOR_NAVY_LIGHT

m5b_pts = [
    ("FAO-56 Penman-Monteith: ", "Computes daily reference evapotranspiration (ET0) using net solar radiation, temperature, wind speed, and humidity."),
    ("Crop Water Need: ", "Multiplies ET0 by empirical single-crop coefficient: ETc = ET0 * Kc across 4 phenological stages (Initial, Dev, Mid, Late)."),
    ("Volumetric Water Depth: ", "Converts mm/day into liters/day based on parcel area (1 mm = 10,000 L/ha); factors irrigation efficiency (Drip 90%, Sprinkler 75%, Flood 60%)."),
    ("Harvest Phenology & MSP: ", "Projects maturity calendar dates using IASRI duration tables; estimates economic yields based on Government Minimum Support Prices (MSP).")
]
for lbl, val in m5b_pts:
    add_bullet(tf_m5b, lbl, val, pt_size=9.2, space=5.5)


# ==============================================================================
# SLIDE 17: MODULE 6 - EXPLAINABLE AI (SHAP & LIME)
# ==============================================================================
s17 = prs.slides.add_slide(blank_layout)
add_header_footer(s17, "Module 6: Explainable AI & Model Transparency (SHAP & LIME)")

create_card(s17, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_m6a = s17.shapes.add_textbox(col1_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m6a = tb_m6a.text_frame
tf_m6a.word_wrap = True
tf_m6a.paragraphs[0].text = "SHAP: GLOBAL FEATURE ATTRIBUTION"
tf_m6a.paragraphs[0].font.size = Pt(12)
tf_m6a.paragraphs[0].font.bold = True
tf_m6a.paragraphs[0].font.color.rgb = COLOR_NAVY

m6a_pts = [
    ("Game-Theoretic Foundation: ", "Computes Shapley additive explanations (f(x) = phi_0 + sum(phi_i)) assigning fair contribution values to each input feature."),
    ("Key Empirical Drivers: ", "As demonstrated in Mohan et al. (2025), Temperature (~±0.004), Nitrogen (~±0.003), and Humidity (~±0.003) exert the highest positive impacts on crop suitability."),
    ("Nutrient Deficit Penalties: ", "Suboptimal Potassium (K) and severe Phosphorus (P) deficiencies negatively skew suitability scores below decision thresholds."),
    ("Agronomic Interpretability: ", "Enables agricultural extension officers to verify whether predictions align with biological plant requirements.")
]
for lbl, val in m6a_pts:
    add_bullet(tf_m6a, lbl, val, pt_size=9.2, space=6)

create_card(s17, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_m6b = s17.shapes.add_textbox(col2_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_m6b = tb_m6b.text_frame
tf_m6b.word_wrap = True
tf_m6b.paragraphs[0].text = "LIME: LOCAL DECISION BOUNDARIES & USER TRUST"
tf_m6b.paragraphs[0].font.size = Pt(12)
tf_m6b.paragraphs[0].font.bold = True
tf_m6b.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

m6b_pts = [
    ("Local Surrogate Explanations: ", "Fits interpretable linear decision boundaries around individual farm input instances to explain specific crop outcomes."),
    ("Rule Traversal: ", "Explains decisions via explicit thresholds (e.g. Humidity > 83%, pH <= 6.8, Temp between 21-27°C selects Rice over Grapes)."),
    ("Top-3 Ambiguity Alerts: ", "When candidate crops have overlapping probabilities, the system issues an actionable advisory explaining why an alternative is viable."),
    ("Eliminating Black-Box Skepticism: ", "Builds farmer confidence by demystifying why a specific fertilizer dosage or crop rotation was prescribed.")
]
for lbl, val in m6b_pts:
    add_bullet(tf_m6b, lbl, val, pt_size=9.2, space=6)


# ==============================================================================
# SLIDE 18: EXPERIMENTAL RESULTS & BENCHMARKING
# ==============================================================================
s18 = prs.slides.add_slide(blank_layout)
add_header_footer(s18, "Experimental Benchmarking & Ablation Analysis")

# Top Comparison Table (from Mohan Table 11 as reported)
tbl_s18 = s18.shapes.add_table(5, 5, Inches(0.8), Inches(1.65), Inches(11.733), Inches(2.2))
t18 = tbl_s18.table
t18.columns[0].width = Inches(3.2)
t18.columns[1].width = Inches(1.8)
t18.columns[2].width = Inches(2.0)
t18.columns[3].width = Inches(2.0)
t18.columns[4].width = Inches(2.733)

b_hdrs = ["Evaluated Metric", "Baseline Literature", "Mohan et al. (2025) [As Reported]", "Net Improvement", "Significance in AgriSense AI"]
for j, h in enumerate(b_hdrs):
    cell = t18.cell(0, j)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_NAVY
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.bold = True
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_WHITE
    p.alignment = PP_ALIGN.CENTER

bench_rows = [
    ("Weather Prediction Accuracy", "96.12%", "99.10%", "+3.10%", "Reliable microclimate input for irrigation & crop planning"),
    ("Soil Classification Accuracy", "95.25%", "99.00%", "+3.94%", "High-precision texture diagnosis via bottleneck residual blocks"),
    ("Model Error Rate (Loss)", "4.88%", "1.32%", "-72.95%", "Substantial error minimization via neural attention & POA"),
    ("Inference Latency", "0.360 s", "0.250 s", "-30.56%", "Sub-second execution enables real-time responsive web interface")
]
for i, r in enumerate(bench_rows):
    for j, val in enumerate(r):
        cell = t18.cell(i+1, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_WHITE if i % 2 == 0 else COLOR_CARD_BG
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.size = Pt(8.0)
        p.font.color.rgb = COLOR_SLATE_DARK
        if j in [0, 2, 3]:
            p.font.bold = True
        if j in [1, 2, 3]:
            p.alignment = PP_ALIGN.CENTER

# Bottom 2 Cards: AgriSense Audit & Model Comparison
create_card(s18, col1_l, Inches(4.1), card_w, Inches(2.65), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_b1 = s18.shapes.add_textbox(col1_l + Inches(0.18), Inches(4.2), card_w - Inches(0.36), Inches(2.45))
tf_b1 = tb_b1.text_frame
tf_b1.word_wrap = True
tf_b1.paragraphs[0].text = "AGRISENSE SCIENTIFIC AUDIT RESULTS"
tf_b1.paragraphs[0].font.size = Pt(11)
tf_b1.paragraphs[0].font.bold = True
tf_b1.paragraphs[0].font.color.rgb = COLOR_NAVY

audit_pts = [
    ("Crop RF (100 Trees): ", "99.52% ± 0.25% (5-fold stratified CV, benchmark data). Retains 95.91% under realistic sensor noise."),
    ("Soil CNN (MobileNetV2): ", "88.19% (127/144 correct) holdout accuracy on real field photos [Wilson 95% CI: 82.6% – 93.1%]."),
    ("Automated Testing: ", "39+ regression unit tests verifying chemical conservation, ET0 bounds, and API failovers.")
]
for lbl, val in audit_pts:
    add_bullet(tf_b1, lbl, val, pt_size=8.5, space=2.5)

create_card(s18, col2_l, Inches(4.1), card_w, Inches(2.65), COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_b2 = s18.shapes.add_textbox(col2_l + Inches(0.18), Inches(4.2), card_w - Inches(0.36), Inches(2.45))
tf_b2 = tb_b2.text_frame
tf_b2.word_wrap = True
tf_b2.paragraphs[0].text = "ABLATION & MODEL TRADE-OFF HIGHLIGHTS"
tf_b2.paragraphs[0].font.size = Pt(11)
tf_b2.paragraphs[0].font.bold = True
tf_b2.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

ablation_pts = [
    ("Optimizer Comparison: ", "POA converges in 10 iterations (fitness near 0) vs. 40+ iterations for PSO, ALO, and SFLA."),
    ("Computational Efficiency: ", "DTBRCNN training duration is 10.4 hrs (1.7 GB memory) vs. 22.1 hrs (2.8 GB) for standard DCNN."),
    ("Inference Speed: ", "Random Forest (<1ms) and DTBRCNN (0.165s) outperform ETASNN (20s) for real-world deployment.")
]
for lbl, val in ablation_pts:
    add_bullet(tf_b2, lbl, val, pt_size=8.5, space=2.5)


# ==============================================================================
# SLIDE 19: SYSTEM DEMO & USER INTERFACE WALKTHROUGH
# ==============================================================================
s19 = prs.slides.add_slide(blank_layout)
add_header_footer(s19, "Interactive Web Application & Field Walkthrough")

step_w_d = Inches(2.8)
step_gap_d = Inches(0.17)
start_x_d = Inches(0.8)

demo_cards = [
    (
        "1. SOIL VISION & CADASTRAL",
        "Field Survey & Texture Setup",
        [
            ("1-Click Upload: ", "Farmer captures soil photo directly via mobile camera."),
            ("Vision Analysis: ", "Model classifies soil into 5 classes with confidence score and Wilson intervals."),
            ("Cadastral Units: ", "Natively converts Cents (0.01 ac) and Gunthas (0.025 ac) to hectares."),
            ("Nutrient Lab Entry: ", "Quick entry of N-P-K from Soil Health Card or 1-click regional presets.")
        ],
        COLOR_CARD_BG, COLOR_CARD_BORDER
    ),
    (
        "2. LIVE AGRO-WEATHER",
        "ECMWF Forecast Synchronization",
        [
            ("GPS Auto-Sync: ", "Automatically detects latitude/longitude for farm district (e.g. Coimbatore)."),
            ("Live Parameters: ", "Fetches 24-hr temperature, relative humidity, wind speed, and rain probability."),
            ("Agronomic Advisory: ", "Issues safety alerts for chemical foliar spray based on wind drift (<12 km/h)."),
            ("Offline Fallback: ", "Seamless fallback to regional agro-climatic normals if offline.")
        ],
        COLOR_BLUE_TINT, COLOR_BLUE_BORDER
    ),
    (
        "3. MULTI-CROP & XAI",
        "Ranked Crops & Transparency",
        [
            ("Top-3 Candidates: ", "Displays primary recommended crop alongside viable alternative choices."),
            ("Ambiguity Alerts: ", "Flags when two crops have close suitability (<15% probability gap)."),
            ("Agronomic Profile: ", "Details ideal sowing season, water needs, growth duration, and harvest tips."),
            ("Explainable XAI: ", "Visualizes SHAP/LIME feature importance rankings for farmer trust.")
        ],
        COLOR_GREEN_TINT, COLOR_GREEN_BORDER
    ),
    (
        "4. FERTILIZER & DOSSIER",
        "Commercial 50kg Bags & PDF",
        [
            ("Commercial Bags: ", "Outputs integer & decimal 50kg bags of Urea, DAP, and MOP."),
            ("3-Stage Timeline: ", "Step-by-step application schedule (Basal Sowing, Tillering, Panicle)."),
            ("FAO-56 Irrigation: ", "Daily liters/day watering demand adjusted for drip/sprinkler efficiency."),
            ("Printable Advisory: ", "One-click generation of comprehensive, bilingual farmer report.")
        ],
        COLOR_CARD_BG, COLOR_CARD_BORDER
    )
]

for i, (p_t, p_s, pts, bg_c, bdr_c) in enumerate(demo_cards):
    x_pos = start_x_d + i * (step_w_d + step_gap_d)
    create_card(s19, x_pos, Inches(1.65), step_w_d, Inches(5.1), bg_c, bdr_c)
    tb = s19.shapes.add_textbox(x_pos + Inches(0.14), Inches(1.85), step_w_d - Inches(0.28), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.text = p_t
    p0.font.size = Pt(10.5)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_NAVY
    
    ps = tf.add_paragraph()
    ps.text = p_s
    ps.font.size = Pt(9.5)
    ps.font.bold = True
    ps.font.color.rgb = COLOR_PRIMARY_DARK
    ps.space_before = Pt(2)
    
    for lbl, val in pts:
        add_bullet(tf, lbl, val, pt_size=8.5, space=5)


# ==============================================================================
# SLIDE 20: PUBLICATION PLAN & RESEARCH ROADMAP
# ==============================================================================
s20 = prs.slides.add_slide(blank_layout)
add_header_footer(s20, "Academic Publication Plan & Conference Roadmap")

col3_w = Inches(3.68)
col3_h = Inches(5.1)
c1_x = Inches(0.8)
c2_x = c1_x + col3_w + gap
c3_x = c2_x + col3_w + gap

# Col 1: Proposed Manuscript Scope
create_card(s20, c1_x, Inches(1.65), col3_w, col3_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_p1 = s20.shapes.add_textbox(c1_x + Inches(0.18), Inches(1.85), col3_w - Inches(0.36), col3_h - Inches(0.4))
tf_p1 = tb_p1.text_frame
tf_p1.word_wrap = True
tf_p1.paragraphs[0].text = "MANUSCRIPT SPECIFICATION"
tf_p1.paragraphs[0].font.size = Pt(12)
tf_p1.paragraphs[0].font.bold = True
tf_p1.paragraphs[0].font.color.rgb = COLOR_NAVY

p_mtit = tf_p1.add_paragraph()
p_mtit.text = "Proposed Research Title:"
p_mtit.font.size = Pt(10)
p_mtit.font.bold = True
p_mtit.space_before = Pt(4)

p_mtxt = tf_p1.add_paragraph()
p_mtxt.text = '"AgriSense AI: A Hybrid Deep Learning & Cross-Attention Decision Framework with Stoichiometric Agronomy for Smallholder Precision Agriculture"'
p_mtxt.font.size = Pt(9.5)
p_mtxt.font.italic = True
p_mtxt.font.color.rgb = COLOR_PRIMARY_DARK
p_mtxt.space_before = Pt(2)

p1_items = [
    ("Core Novelty: ", "Coupling the deep learning fusion foundation of Mohan & Anandamurugan (2025) with deterministic ICAR chemical balancing and cadastral revenue units."),
    ("Empirical Breadth: ", "Stratified 5-Fold Cross-Validation (99.52% CV), 88.2% leakage-free vision holdout evaluation, and FAO-56 dual hydrology validation.")
]
for lbl, val in p1_items:
    add_bullet(tf_p1, lbl, val, pt_size=8.8, space=5)

# Col 2: Target Venues & Indexing
create_card(s20, c2_x, Inches(1.65), col3_w, col3_h, COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_p2 = s20.shapes.add_textbox(c2_x + Inches(0.18), Inches(1.85), col3_w - Inches(0.36), col3_h - Inches(0.4))
tf_p2 = tb_p2.text_frame
tf_p2.word_wrap = True
tf_p2.paragraphs[0].text = "TARGET ACADEMIC VENUES"
tf_p2.paragraphs[0].font.size = Pt(12)
tf_p2.paragraphs[0].font.bold = True
tf_p2.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

p2_items = [
    ("Primary Conference Track: ", "IEEE ICACCS 2027 (IEEE International Conference on Advanced Computing & Communication Systems, Coimbatore, Scopus / IEEE Xplore)."),
    ("Flagship Regional Track: ", "IEEE INDICON / TENSYMP (Flagship IEEE Region 10 conferences in Agro-Informatics & AI)."),
    ("Target SCI Journal Track: ", "Computers and Electronics in Agriculture (Elsevier, SCI Q1, Impact Factor: 8.9) or Smart Agricultural Technology (Elsevier)."),
    ("Institutional Affiliation: ", "KPR Institute of Engineering and Technology, Coimbatore, Tamil Nadu, India.")
]
for lbl, val in p2_items:
    add_bullet(tf_p2, lbl, val, pt_size=8.8, space=6)

# Col 3: Submission Milestones
create_card(s20, c3_x, Inches(1.65), col3_w, col3_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_p3 = s20.shapes.add_textbox(c3_x + Inches(0.18), Inches(1.85), col3_w - Inches(0.36), col3_h - Inches(0.4))
tf_p3 = tb_p3.text_frame
tf_p3.word_wrap = True
tf_p3.paragraphs[0].text = "PUBLICATION MILESTONES"
tf_p3.paragraphs[0].font.size = Pt(12)
tf_p3.paragraphs[0].font.bold = True
tf_p3.paragraphs[0].font.color.rgb = COLOR_NAVY

p3_milestones = [
    ("Phase 1: Model Training & Audit", "COMPLETED", "2,300 benchmark rows trained; leakage audits finalized; 39 unit tests verified."),
    ("Phase 2: Manuscript Drafting & Figures", "CURRENT (OCT 2026)", "Drafting Section 2 (System Architecture), Section 3 (Stoichiometry Math), and ROC/SHAP plots."),
    ("Phase 3: Plagiarism & Field Trials", "NOV 2026", "Similarity check (<10% threshold); smallholder field trial validation around Coimbatore."),
    ("Phase 4: IEEE Submission", "DEC 2026", "Final IEEE 2-column camera-ready submission to conference portal.")
]
for title, status, desc in p3_milestones:
    p = tf_p3.add_paragraph()
    p.space_before = Pt(5)
    r1 = p.add_run()
    r1.text = title + " "
    r1.font.size = Pt(9)
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = f"[{status}]\n"
    r2.font.size = Pt(8.2)
    r2.font.bold = True
    r2.font.color.rgb = COLOR_PRIMARY_DARK if "COMPLETED" in status else (COLOR_NAVY if "CURRENT" in status else COLOR_AMBER_TEXT)
    r3 = p.add_run()
    r3.text = desc
    r3.font.size = Pt(8.2)
    r3.font.color.rgb = COLOR_SLATE_BODY


# ==============================================================================
# SLIDE 21: CONCLUSION, LIMITATIONS & FUTURE SCOPE
# ==============================================================================
s21 = prs.slides.add_slide(blank_layout)
add_header_footer(s21, "Conclusion, Documented Limitations & Future Scope")

create_card(s21, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_concl = s21.shapes.add_textbox(col1_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_c = tb_concl.text_frame
tf_c.word_wrap = True
tf_c.paragraphs[0].text = "KEY PROJECT ACHIEVEMENTS"
tf_c.paragraphs[0].font.size = Pt(12)
tf_c.paragraphs[0].font.bold = True
tf_c.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

concls = [
    ("Unified Decision Platform: ", "Successfully operationalized hybrid DL concepts from Mohan et al. (2025) into an interactive, full-stack decision-support system."),
    ("High-Accuracy Crop Prediction: ", "Audited Random Forest achieves 99.52% ± 0.25% 5-fold CV accuracy across 23 crops, eliminating farmer guesswork."),
    ("Commercial Agronomic Reality: ", "Bridges the gap between research and practice by calculating commercial 50kg bags (DAP, Urea, MOP) rather than theoretical kg/ha."),
    ("Full-Cycle Hydrology: ", "Integrated FAO-56 Penman-Monteith daily irrigation calculation with IASRI harvest phenology."),
    ("Engineering Robustness: ", "39+ automated tests ensure zero regression, robust API failover, and strict mathematical conservation.")
]
for lbl, val in concls:
    add_bullet(tf_c, lbl, val, pt_size=9.0, space=5.5)

create_card(s21, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_AMBER_TINT, COLOR_AMBER_BORDER)
tb_lim = s21.shapes.add_textbox(col2_l + Inches(0.2), Inches(1.85), card_w - Inches(0.4), Inches(4.7))
tf_l = tb_lim.text_frame
tf_l.word_wrap = True
tf_l.paragraphs[0].text = "DOCUMENTED LIMITATIONS & FUTURE ROADMAP"
tf_l.paragraphs[0].font.size = Pt(12)
tf_l.paragraphs[0].font.bold = True
tf_l.paragraphs[0].font.color.rgb = COLOR_AMBER_TEXT

lims = [
    ("Loamy Soil Sample Size: ", "Current vision holdout has lower Loamy accuracy (62.5% recall, n=8); expanding original Indian field photos to >3,000 samples."),
    ("Sensor Noise Drift: ", "Accuracy degrades to 95.9% under ±10% NPK noise; future work incorporates Kalman filtering for edge sensor streams."),
    ("Crop Disease Add-On: ", "Future Phase: Integrating computer vision (YOLOv8 / CNN) for automated leaf pest & fungal disease detection from leaf photos."),
    ("Edge / Offline PWA: ", "Developing an offline-first Progressive Web App (PWA) with ONNX Runtime for deployment on low-cost Android smartphones without internet.")
]
for lbl, val in lims:
    add_bullet(tf_l, lbl, val, pt_size=9.0, space=5.5)


# ==============================================================================
# SLIDE 22: REFERENCES (FULL IEEE FORMAT [1] TO [16])
# ==============================================================================
s22 = prs.slides.add_slide(blank_layout)
add_header_footer(s22, "Scholarly References (IEEE Standard)")

create_card(s22, col1_l, Inches(1.65), card_w, Inches(5.1), COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_r1 = s22.shapes.add_textbox(col1_l + Inches(0.18), Inches(1.8), card_w - Inches(0.36), Inches(4.8))
tf_r1 = tb_r1.text_frame
tf_r1.word_wrap = True
tf_r1.paragraphs[0].text = "CORE HYBRID DL & CROP PLATFORMS"
tf_r1.paragraphs[0].font.size = Pt(11)
tf_r1.paragraphs[0].font.bold = True
tf_r1.paragraphs[0].font.color.rgb = COLOR_NAVY

refs_1 = [
    ("[1] ", "M. Mohan and S. Anandamurugan, 'Hybrid deep learning with a fusion model of weather and soil-based multi-crop recommendations for improving crop sustainability,' Theor. Appl. Climatol., vol. 156, art. 637, 2025."),
    ("[2] ", "T. Mahmud et al., 'An approach for crop prediction in agriculture: integrating genetic algorithms and machine learning,' IEEE Access, vol. 12, pp. 173583–173598, 2024."),
    ("[3] ", "D. Garg and M. Alam, 'An effective crop recommendation method using machine learning techniques,' Int. J. Adv. Technol. Eng. Explor., vol. 10, p. 498, 2023."),
    ("[4] ", "S. Kiruthika and D. Karthika, 'IoT-based professional crop recommendation system using a weight-based long-term memory approach,' Meas. Sensors, vol. 27, 100722, 2023."),
    ("[5] ", "N. N. Thilakarathne et al., 'A cloud enabled crop recommendation platform for machine learning-driven precision farming,' Sensors, vol. 22, 6299, 2022."),
    ("[6] ", "J. Madhuri and M. Indiramma, 'Artificial neural networks based integrated crop recommendation system using soil and climatic parameters,' Indian J. Sci. Technol., vol. 14, pp. 1587–1597, 2021."),
    ("[7] ", "Y. Akkem, S. K. Biswas, and A. Varanasi, 'Streamlit-based enhancing crop recommendation systems with advanced explainable artificial intelligence for smart farming,' Neural Comput. Appl., vol. 36, pp. 20011–20025, 2024."),
    ("[8] ", "S. Shastri et al., 'Advancing crop recommendation system with supervised machine learning and explainable artificial intelligence,' Sci. Rep., vol. 15, 25498, 2025.")
]

for tag, citation in refs_1:
    p = tf_r1.add_paragraph()
    p.font.size = Pt(7.8)
    p.space_before = Pt(3.5)
    r_tag = p.add_run()
    r_tag.text = tag
    r_tag.font.bold = True
    r_tag.font.color.rgb = COLOR_NAVY
    r_cit = p.add_run()
    r_cit.text = citation
    r_cit.font.color.rgb = COLOR_SLATE_BODY

create_card(s22, col2_l, Inches(1.65), card_w, Inches(5.1), COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_r2 = s22.shapes.add_textbox(col2_l + Inches(0.18), Inches(1.8), card_w - Inches(0.36), Inches(4.8))
tf_r2 = tb_r2.text_frame
tf_r2.word_wrap = True
tf_r2.paragraphs[0].text = "SOIL VISION, FERTILIZER & HYDROLOGY"
tf_r2.paragraphs[0].font.size = Pt(11)
tf_r2.paragraphs[0].font.bold = True
tf_r2.paragraphs[0].font.color.rgb = COLOR_PRIMARY_DARK

refs_2 = [
    ("[9] ", "R. K. Banoth and B. V. Murthy, 'Soil image classification using transfer learning approach: MobileNetV2 with CNN,' SN Comput. Sci., vol. 5, 199, 2024."),
    ("[10] ", "D. N. Kiran Pandiri, R. Murugan, and T. Goel, 'Smart soil image classification system using lightweight convolutional neural network,' Expert Syst. Appl., vol. 238, 122185, 2024."),
    ("[11] ", "M. G. Lanjewar and O. L. Gurav, 'Convolutional neural networks based classifications of soil images,' Multimedia Tools Appl., vol. 81, pp. 10313–10336, 2022."),
    ("[12] ", "A. Bhola and P. Kumar, 'ML-CSFR: a unified crop selection and fertilizer recommendation framework based on machine learning,' Scalable Comput. Pract. Exp., vol. 25, pp. 4111–4127, 2024."),
    ("[13] ", "N. U. Sambhe et al., 'Mcyp-deepnet: nutrition and temperature-based season-wise multi-crop yield prediction using DeepNet 230 classifier,' Opt. Mem. Neural Netw., vol. 33, pp. 236–253, 2024."),
    ("[14] ", "U. Acharya, A. L. Daigh, and P. G. Oduor, 'Machine learning for predicting field soil moisture using soil, crop, and nearby weather station data in the Red River Valley of the north,' Soil Syst., vol. 5, 57, 2021."),
    ("[15] ", "M. Anand, A. Jain, and M. K. Shukla, 'Deep learning: crop selection based on weather conditions in Tarakeswar village of Hooghly district in West Bengal,' Multimedia Tools Appl., vol. 83, pp. 29715–29740, 2024."),
    ("[16] ", "G. Sravanthi and N. R. Moparthi, 'An efficient IoT based crop disease prediction and crop recommendation for precision agriculture,' Cluster Comput., vol. 27, pp. 5755–5782, 2024.")
]

for tag, citation in refs_2:
    p = tf_r2.add_paragraph()
    p.font.size = Pt(7.8)
    p.space_before = Pt(3.5)
    r_tag = p.add_run()
    r_tag.text = tag
    r_tag.font.bold = True
    r_tag.font.color.rgb = COLOR_PRIMARY_DARK
    r_cit = p.add_run()
    r_cit.text = citation
    r_cit.font.color.rgb = COLOR_SLATE_BODY


# ==============================================================================
# SLIDE 23: THANK YOU & DISCUSSION
# ==============================================================================
s23 = prs.slides.add_slide(blank_layout)

bg23 = s23.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg23.fill.solid()
bg23.fill.fore_color.rgb = RGBColor(245, 247, 250)
bg23.line.fill.background()

top_bar23 = s23.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
top_bar23.fill.solid()
top_bar23.fill.fore_color.rgb = COLOR_PRIMARY_DARK
top_bar23.line.fill.background()

create_card(s23, Inches(1.4), Inches(0.9), Inches(10.533), Inches(5.7), COLOR_WHITE, COLOR_CARD_BORDER)

tb_ty = s23.shapes.add_textbox(Inches(1.8), Inches(1.3), Inches(9.733), Inches(4.9))
tf_ty = tb_ty.text_frame
tf_ty.word_wrap = True

p_ty0 = tf_ty.paragraphs[0]
p_ty0.text = "KPR INSTITUTE OF ENGINEERING AND TECHNOLOGY"
p_ty0.font.size = Pt(12)
p_ty0.font.bold = True
p_ty0.font.color.rgb = COLOR_ACCENT_TEAL
p_ty0.alignment = PP_ALIGN.CENTER

p_ty1 = tf_ty.add_paragraph()
p_ty1.text = "Thank You!"
p_ty1.font.size = Pt(38)
p_ty1.font.bold = True
p_ty1.font.color.rgb = COLOR_NAVY
p_ty1.alignment = PP_ALIGN.CENTER
p_ty1.space_before = Pt(14)

p_ty2 = tf_ty.add_paragraph()
p_ty2.text = "AgriSense AI: Hybrid Deep Learning Decision Support System for Precision Agriculture"
p_ty2.font.size = Pt(13)
p_ty2.font.bold = True
p_ty2.font.color.rgb = COLOR_PRIMARY_DARK
p_ty2.alignment = PP_ALIGN.CENTER
p_ty2.space_before = Pt(8)

p_ty3 = tf_ty.add_paragraph()
p_ty3.text = "Project Review Team: Hareram Kushwaha • Ashok Pajiyar • Bijaya Kumar Yadav • Bishal Raut Kurmi\nGuided By: Mr. M. Mohan (Dept. of CSE, KPRIET)"
p_ty3.font.size = Pt(11)
p_ty3.font.color.rgb = COLOR_SLATE_DARK
p_ty3.alignment = PP_ALIGN.CENTER
p_ty3.space_before = Pt(8)

# Deliverables summary box
tb_deliv = s23.shapes.add_textbox(Inches(2.2), Inches(4.3), Inches(8.933), Inches(1.8))
tf_del = tb_deliv.text_frame
tf_del.word_wrap = True

del_items = [
    ("Verified Codebase: ", "Full-stack React SPA frontend + Python Flask REST backend ready for live viva demonstration."),
    ("Scientific Rigor: ", "39+ automated regression unit tests passing green; audited against leakage & domain shift."),
    ("Ready for Review Panel: ", "Open for technical questions, evaluation comments, and feedback.")
]
for lbl, val in del_items:
    add_bullet(tf_del, lbl, val, pt_size=10, space=4, bold_label=True, label_color=COLOR_PRIMARY_DARK, val_color=COLOR_SLATE_BODY)

# Save Presentation
output_path = "/home/bijayadav/Project/agrisense-ai/AgriSense_AI_Updated_Presentation.pptx"
prs.save(output_path)
print(f"SUCCESS: Generated 23 slides at: {output_path}")
