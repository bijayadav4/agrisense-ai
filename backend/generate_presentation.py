import os

import pptx
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# Initialize Presentation
prs = pptx.Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# Image backgrounds extracted from uploaded KPRIET PDF
slides_dir = "/home/bijayadav/.gemini/antigravity-ide/brain/069589ea-52ae-4dfd-9fde-b7eff4501043/scratch/slides"

# Brand Colors
COLOR_DARK_GREEN = RGBColor(15, 81, 50)  # #0F5132
COLOR_EMERALD = RGBColor(22, 101, 52)  # #166534
COLOR_NAVY = RGBColor(30, 58, 138)  # #1E3A8A
COLOR_SLATE_DARK = RGBColor(15, 23, 42)  # #0F172A
COLOR_SLATE_BODY = RGBColor(51, 65, 85)  # #334155
COLOR_SLATE_MUTED = RGBColor(100, 116, 139)  # #64748B
COLOR_CARD_BG = RGBColor(248, 250, 252)  # #F8FAFC
COLOR_CARD_BORDER = RGBColor(203, 213, 225)  # #CBD5E1
COLOR_GREEN_TINT = RGBColor(240, 253, 244)  # #F0FDF4
COLOR_GREEN_BORDER = RGBColor(134, 239, 172)  # #86EFAC
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_AMBER = RGBColor(217, 119, 6)


def add_bg(slide, page_num):
    bg_path = os.path.join(slides_dir, f"page-{page_num}.png")
    if os.path.exists(bg_path):
        slide.shapes.add_picture(bg_path, 0, 0, width=Inches(13.333), height=Inches(7.5))


def create_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.2)
    return shape


# ==============================================================================
# SLIDE 1: Slide 12 - MODULE NAME
# ==============================================================================
slide1 = prs.slides.add_slide(blank_layout)
add_bg(slide1, 1)

# Subtitle under the header
sub1 = slide1.shapes.add_textbox(Inches(0.8), Inches(1.55), Inches(11.733), Inches(0.4))
tf_sub1 = sub1.text_frame
tf_sub1.word_wrap = True
p_sub1 = tf_sub1.paragraphs[0]
p_sub1.text = "AgriSense AI — Intelligent Multi-Module Precision Agriculture Decision Support System"
p_sub1.font.size = Pt(13)
p_sub1.font.bold = True
p_sub1.font.color.rgb = COLOR_NAVY
p_sub1.alignment = PP_ALIGN.CENTER

# 4 Module Cards (2x2 Grid)
card_w = Inches(5.72)
card_h = Inches(2.25)
col1_l = Inches(0.8)
col2_l = Inches(6.81)
row1_t = Inches(1.95)
row2_t = Inches(4.35)

# Module 1 Card (Top Left)
create_card(slide1, col1_l, row1_t, card_w, card_h, COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_m1 = slide1.shapes.add_textbox(
    col1_l + Inches(0.18), row1_t + Inches(0.12), card_w - Inches(0.36), card_h - Inches(0.24)
)
tf1 = tb_m1.text_frame
tf1.word_wrap = True
p = tf1.paragraphs[0]
p.text = "MODULE 1: AI Soil Diagnosis & Crop Recommender"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_DARK_GREEN

points_m1 = [
    ("Core Algorithm: ", "Random Forest Classifier (100 Decision Trees, Ensembled Voting)"),
    ("Trained Dataset: ", "2,300 curated records across 23 distinct crops (100 samples/crop)"),
    ("Feature Vector: ", "Soil Chemistry (N, P, K, pH) + Microclimate (Temp, Humidity, Rain)"),
    ("Holdout Accuracy: ", "99.52% ± 0.25% (5-Fold Stratified CV on benchmark data)"),
]
for label, val in points_m1:
    p = tf1.add_paragraph()
    p.font.size = Pt(10)
    p.space_before = Pt(3)
    r1 = p.add_run()
    r1.text = "• " + label
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.color.rgb = COLOR_SLATE_BODY

# Module 2 Card (Top Right)
create_card(slide1, col2_l, row1_t, card_w, card_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_m2 = slide1.shapes.add_textbox(
    col2_l + Inches(0.18), row1_t + Inches(0.12), card_w - Inches(0.36), card_h - Inches(0.24)
)
tf2 = tb_m2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "MODULE 2: ICAR Stoichiometric Fertilizer Dosage Engine"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_NAVY

points_m2 = [
    ("Core Logic: ", "Stoichiometric chemical balancing replacing theoretical kg/ha ambiguity"),
    ("Elemental Balancing: ", "DAP (46% P2O5, 18% N) satisfies P & credits N; remainder via Urea (46% N) & MOP"),
    ("Commercial Bags: ", "Outputs exact standard 50 kg commercial bag counts tailored to plot size"),
    ("Organic Options: ", "Computes equivalent Farmyard Manure (FYM) & bio-fertilizer alternatives"),
]
for label, val in points_m2:
    p = tf2.add_paragraph()
    p.font.size = Pt(10)
    p.space_before = Pt(3)
    r1 = p.add_run()
    r1.text = "• " + label
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.color.rgb = COLOR_SLATE_BODY

# Module 3 Card (Bottom Left)
create_card(slide1, col1_l, row2_t, card_w, card_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_m3 = slide1.shapes.add_textbox(
    col1_l + Inches(0.18), row2_t + Inches(0.12), card_w - Inches(0.36), card_h - Inches(0.24)
)
tf3 = tb_m3.text_frame
tf3.word_wrap = True
p = tf3.paragraphs[0]
p.text = "MODULE 3: Agro-Meteorological & Spray Advisory Engine"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_NAVY

points_m3 = [
    ("Live Weather Pipeline: ", "Open-Meteo ECMWF Numerical Model (Primary) + OpenWeatherMap (Secondary)"),
    ("Fail-Safe Protection: ", "Sub-millisecond localized memory cache (<1ms) + Agricultural climate baseline"),
    ("Spray Safety Advisory: ", "Evaluates wind drift threshold (<12 km/h) & rain probability for safe spraying"),
    ("Forecast Horizon: ", "5-day daily forecast with real calendar dates & soil moisture conservation advice"),
]
for label, val in points_m3:
    p = tf3.add_paragraph()
    p.font.size = Pt(10)
    p.space_before = Pt(3)
    r1 = p.add_run()
    r1.text = "• " + label
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.color.rgb = COLOR_SLATE_BODY

# Module 4 Card (Bottom Right)
create_card(slide1, col2_l, row2_t, card_w, card_h, COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_m4 = slide1.shapes.add_textbox(
    col2_l + Inches(0.18), row2_t + Inches(0.12), card_w - Inches(0.36), card_h - Inches(0.24)
)
tf4 = tb_m4.text_frame
tf4.word_wrap = True
p = tf4.paragraphs[0]
p.text = "MODULE 4: Regional Land Survey Unit Engine (South India)"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = COLOR_DARK_GREEN

points_m4 = [
    ("State Revenue Units: ", "Tamil Nadu & Kerala (Cent, Acre, Ha) | Karnataka & AP (Guntha, Acre, Ha)"),
    ("Survey Multipliers: ", "1 Cent = 0.00404686 Hectare (435.6 sq.ft) | 1 Guntha = 0.01011714 Hectare"),
    ("Precision Decimal Engine: ", "3-decimal hectare conversion cascading directly to fertilizer dosages"),
    ("Farmer Accessibility: ", "Farmers input their native land holding without complex manual conversions"),
]
for label, val in points_m4:
    p = tf4.add_paragraph()
    p.font.size = Pt(10)
    p.space_before = Pt(3)
    r1 = p.add_run()
    r1.text = "• " + label
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.color.rgb = COLOR_SLATE_BODY

# ==============================================================================
# SLIDE 2: Slide 13 - MODULE DEMO
# ==============================================================================
slide2 = prs.slides.add_slide(blank_layout)
add_bg(slide2, 2)

sub2 = slide2.shapes.add_textbox(Inches(0.8), Inches(1.55), Inches(11.733), Inches(0.4))
tf_sub2 = sub2.text_frame
tf_sub2.word_wrap = True
p_sub2 = tf_sub2.paragraphs[0]
p_sub2.text = "End-to-End Decision Support Workflow & Real-Time Farm Execution"
p_sub2.font.size = Pt(13)
p_sub2.font.bold = True
p_sub2.font.color.rgb = COLOR_NAVY
p_sub2.alignment = PP_ALIGN.CENTER

# 5 Horizontal Process Cards
step_w = Inches(2.23)
step_h = Inches(1.85)
step_gap = Inches(0.14)
start_x = Inches(0.8)
step_y = Inches(1.95)

steps = [
    (
        "01. SURVEY & GPS",
        "Regional Cadastral Setup",
        ["State: Tamil Nadu", "Unit: Cents (e.g. 25 Cents)", "Area: 0.101 Hectare", "GPS auto-sync weather"],
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
    ),
    (
        "02. SOIL HEALTH",
        "Diagnostic Parameters",
        ["Lab N-P-K (kg/ha) & pH", "Or 1-Click SHC Presets", "N: 90, P: 42, K: 43", "Soil pH: 6.5 (Neutral)"],
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
    ),
    (
        "03. AI ML MODEL",
        "Random Forest Inference",
        ["Evaluates 7 features", "Predicts: Rice / Paddy", "Confidence: 96.8%", "Viable alternative crops"],
        COLOR_GREEN_TINT,
        COLOR_GREEN_BORDER,
    ),
    (
        "04. ICAR DOSAGE",
        "Commercial 50kg Bags",
        ["DAP 18% N deduction", "Urea: 0.26 Bags (13.2 kg)", "DAP: 0.18 Bags (8.8 kg)", "MOP: 0.11 Bags (5.4 kg)"],
        COLOR_GREEN_TINT,
        COLOR_GREEN_BORDER,
    ),
    (
        "05. FARM ADVISORY",
        "Daily Actionable Plan",
        ["Today's spray safety status", "Wind < 12 km/h (Safe)", "5-Day weather forecast", "Optimal irrigation timing"],
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
    ),
]

for idx, (s_num, s_title, s_bullets, s_bg, s_bc) in enumerate(steps):
    cur_x = start_x + idx * (step_w + step_gap)
    create_card(slide2, cur_x, step_y, step_w, step_h, s_bg, s_bc)
    tb = slide2.shapes.add_textbox(
        cur_x + Inches(0.1), step_y + Inches(0.08), step_w - Inches(0.2), step_h - Inches(0.16)
    )
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = s_num
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_GREEN if "GREEN" in str(s_bc) else COLOR_NAVY

    p2 = tf.add_paragraph()
    p2.text = s_title
    p2.font.size = Pt(9.5)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_SLATE_DARK
    p2.space_before = Pt(1)

    for b in s_bullets:
        p_b = tf.add_paragraph()
        p_b.text = "• " + b
        p_b.font.size = Pt(8.5)
        p_b.font.color.rgb = COLOR_SLATE_BODY
        p_b.space_before = Pt(2)

# Bottom Section: Two Execution Panels
panel_w = Inches(5.72)
panel_h = Inches(2.65)
panel_y = Inches(3.95)

# Panel 1: Live Calculation Proof
create_card(slide2, col1_l, panel_y, panel_w, panel_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_p1 = slide2.shapes.add_textbox(
    col1_l + Inches(0.18), panel_y + Inches(0.12), panel_w - Inches(0.36), panel_h - Inches(0.24)
)
tf_p1 = tb_p1.text_frame
tf_p1.word_wrap = True
p = tf_p1.paragraphs[0]
p.text = "LIVE EXECUTION SCENARIO: Smallholder Plot (25 Cents, Coimbatore)"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = COLOR_NAVY

scenarios_p1 = [
    ("Land Conversion: ", "25 Cents × 0.00404686 = 0.1012 Hectares (0.25 Acres)"),
    ("Target Recommendation: ", "Paddy (Rice) with 96.8% Model Confidence | Alternatives: Maize, Jute"),
    ("ICAR Nutrient Deficit: ", "Target N: 120 kg/ha, P: 40 kg/ha, K: 40 kg/ha for optimal yield"),
    ("Stoichiometric Split: ", "DAP = 40 / 0.46 = 87.0 kg/ha; N from DAP = 87.0 × 0.18 = 15.65 kg/ha"),
    ("Net Urea Required: ", "Remaining N = 120 - 15.65 = 104.35 kg/ha → Urea = 104.35 / 0.46 = 226.8 kg/ha"),
    ("Final Plot Dosage (0.101 ha): ", "Urea: 22.9 kg (0.46 Bags) | DAP: 8.8 kg (0.18 Bags) | MOP: 6.7 kg (0.13 Bags)"),
]
for label, val in scenarios_p1:
    p = tf_p1.add_paragraph()
    p.font.size = Pt(9.2)
    p.space_before = Pt(2)
    r1 = p.add_run()
    r1.text = "✔ " + label
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.color.rgb = COLOR_SLATE_BODY

# Panel 2: Farmer-Centric UI & Meteorological Safety
create_card(slide2, col2_l, panel_y, panel_w, panel_h, COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_p2 = slide2.shapes.add_textbox(
    col2_l + Inches(0.18), panel_y + Inches(0.12), panel_w - Inches(0.36), panel_h - Inches(0.24)
)
tf_p2 = tb_p2.text_frame
tf_p2.word_wrap = True
p = tf_p2.paragraphs[0]
p.text = "FARMER-CENTRIC LANDING & SPRAY ADVISORY ENGINE"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = COLOR_DARK_GREEN

scenarios_p2 = [
    ("Live Weather Sync: ", "Coimbatore District (11.0168° N, 76.9558° E) live temperature 28.4°C, RH 72%"),
    ("Spray Safety Assessment: ", "Wind Speed 8.5 km/h (< 12 km/h threshold) & Rain Chance 10% → SAFE TO SPRAY"),
    ("Chemical Drift Mitigation: ", "Advises foliar spray between 7:00 AM - 10:00 AM to prevent thermal evaporation"),
    (
        "5-Day Forecast Display: ",
        "Integrated real calendar dates (e.g. Today, Mon • 7 Sep) for intuitive farmer planning",
    ),
    ("Zero Tech Clutter: ", "Replaced complex charts with clear status badges, color alerts, and WhatsApp export"),
    ("Sub-Millisecond Response: ", "In-memory LRU coordinate caching ensures <50ms end-to-end API response time"),
]
for label, val in scenarios_p2:
    p = tf_p2.add_paragraph()
    p.font.size = Pt(9.2)
    p.space_before = Pt(2)
    r1 = p.add_run()
    r1.text = "✔ " + label
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.color.rgb = COLOR_SLATE_BODY

# ==============================================================================
# SLIDE 3: Slide 14 - PUBLICATION PLAN
# ==============================================================================
slide3 = prs.slides.add_slide(blank_layout)
add_bg(slide3, 3)

sub3 = slide3.shapes.add_textbox(Inches(0.8), Inches(1.55), Inches(11.733), Inches(0.4))
tf_sub3 = sub3.text_frame
tf_sub3.word_wrap = True
p_sub3 = tf_sub3.paragraphs[0]
p_sub3.text = "Research Manuscript Formulation, Scientific Benchmarking & Academic Target Venues"
p_sub3.font.size = Pt(13)
p_sub3.font.bold = True
p_sub3.font.color.rgb = COLOR_NAVY
p_sub3.alignment = PP_ALIGN.CENTER

# 3 Column Cards
col3_w = Inches(3.68)
col3_h = Inches(4.75)
col3_gap = Inches(0.34)
c1_x = Inches(0.8)
c2_x = c1_x + col3_w + col3_gap
c3_x = c2_x + col3_w + col3_gap
c_top = Inches(1.95)

# Column 1: Research Paper Scope
create_card(slide3, c1_x, c_top, col3_w, col3_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_c1 = slide3.shapes.add_textbox(
    c1_x + Inches(0.16), c_top + Inches(0.14), col3_w - Inches(0.32), col3_h - Inches(0.28)
)
tf_c1 = tb_c1.text_frame
tf_c1.word_wrap = True
p = tf_c1.paragraphs[0]
p.text = "RESEARCH PAPER SCOPE"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_NAVY

p_title = tf_c1.add_paragraph()
p_title.text = "Proposed Title:"
p_title.font.size = Pt(10)
p_title.font.bold = True
p_title.space_before = Pt(4)
p_title_val = tf_c1.add_paragraph()
p_title_val.text = '"AgriSense AI: An Integrated Machine Learning and Stoichiometric Decision Support Framework for Precision Smallholder Agriculture"'
p_title_val.font.size = Pt(9.5)
p_title_val.font.italic = True
p_title_val.font.color.rgb = COLOR_DARK_GREEN

c1_items = [
    ("Domain: ", "Precision Agriculture, Machine Learning & Agro-Informatics"),
    (
        "Core Novelty: ",
        "Coupling multi-class Random Forest with ICAR stoichiometric chemical balancing and cadastral revenue units (Cents/Gunthas).",
    ),
    (
        "Methodological Rigor: ",
        "Stratified 5-Fold Cross-Validation on 2,300 benchmark records across 23 crops achieving 99.52% ± 0.25% accuracy.",
    ),
    (
        "Comparative Analysis: ",
        "Benchmarking Random Forest vs SVM, Decision Trees, KNN, and XGBoost on training latency and F1-score.",
    ),
]
for lbl, vl in c1_items:
    p = tf_c1.add_paragraph()
    p.font.size = Pt(9)
    p.space_before = Pt(4)
    r1 = p.add_run()
    r1.text = "• " + lbl
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = vl
    r2.font.color.rgb = COLOR_SLATE_BODY

# Column 2: Target Venues & Indexing
create_card(slide3, c2_x, c_top, col3_w, col3_h, COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_c2 = slide3.shapes.add_textbox(
    c2_x + Inches(0.16), c_top + Inches(0.14), col3_w - Inches(0.32), col3_h - Inches(0.28)
)
tf_c2 = tb_c2.text_frame
tf_c2.word_wrap = True
p = tf_c2.paragraphs[0]
p.text = "TARGET ACADEMIC VENUES"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_DARK_GREEN

c2_items = [
    ("Primary Conference Track:", ""),
    (
        "IEEE ICACCS 2027: ",
        "IEEE International Conference on Advanced Computing & Communication Systems, Coimbatore (IEEE Xplore / Scopus Indexed).",
    ),
    ("IEEE INDICON / TENSYMP: ", "Flagship IEEE Region 10 flagship conferences in Smart Agriculture & AI."),
    ("Journal Publication Track:", ""),
    (
        "Computers and Electronics in Agriculture: ",
        "Elsevier, SCI Q1 Journal (Impact Factor: 8.9) — premier venue for agro-informatics.",
    ),
    (
        "Smart Agricultural Technology: ",
        "Elsevier, Scopus Indexed Open-Access Journal focused on applied farming systems.",
    ),
    ("Institutional Affiliation: ", "KPR Institute of Engineering and Technology, Coimbatore, Tamil Nadu, India."),
]
for lbl, vl in c2_items:
    p = tf_c2.add_paragraph()
    if vl == "":
        p.text = lbl
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_NAVY
        p.space_before = Pt(6)
    else:
        p.font.size = Pt(9)
        p.space_before = Pt(3)
        r1 = p.add_run()
        r1.text = "• " + lbl
        r1.font.bold = True
        r1.font.color.rgb = COLOR_SLATE_DARK
        r2 = p.add_run()
        r2.text = vl
        r2.font.color.rgb = COLOR_SLATE_BODY

# Column 3: Roadmap & Milestones
create_card(slide3, c3_x, c_top, col3_w, col3_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_c3 = slide3.shapes.add_textbox(
    c3_x + Inches(0.16), c_top + Inches(0.14), col3_w - Inches(0.32), col3_h - Inches(0.28)
)
tf_c3 = tb_c3.text_frame
tf_c3.word_wrap = True
p = tf_c3.paragraphs[0]
p.text = "PUBLICATION MILESTONES"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_NAVY

c3_milestones = [
    (
        "Phase 1: Dataset & Empirical Experiments",
        "COMPLETED",
        [
            "Curated 2,300 rows across 23 crops",
            "Trained & serialized models with joblib",
            "Verified 99.52% ± 0.25% 5-fold CV accuracy",
            "Passed 34 automated unit test cases",
        ],
    ),
    (
        "Phase 2: Manuscript Drafting & Figures",
        "CURRENT (OCT 2026)",
        [
            "Drafting Introduction, ICAR Stoichiometry",
            "Generating confusion matrix & ROC curves",
            "Writing system latency benchmark (<50ms)",
        ],
    ),
    (
        "Phase 3: Field Validation & Submission",
        "UPCOMING (NOV-DEC 2026)",
        [
            "Coimbatore smallholder field trials",
            "Plagiarism check (<10% similarity)",
            "Submission to IEEE conference portal",
        ],
    ),
]
for title, status, sub_pts in c3_milestones:
    p = tf_c3.add_paragraph()
    p.space_before = Pt(5)
    r1 = p.add_run()
    r1.text = title + " "
    r1.font.size = Pt(9.5)
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = f"[{status}]"
    r2.font.size = Pt(8.5)
    r2.font.bold = True
    r2.font.color.rgb = (
        COLOR_DARK_GREEN if "COMPLETED" in status else (COLOR_NAVY if "CURRENT" in status else COLOR_AMBER)
    )
    for sp in sub_pts:
        p_sp = tf_c3.add_paragraph()
        p_sp.text = "  - " + sp
        p_sp.font.size = Pt(8.2)
        p_sp.font.color.rgb = COLOR_SLATE_BODY
        p_sp.space_before = Pt(1)

# ==============================================================================
# SLIDE 4: Slide 15 - CONCLUSION / TARGET
# ==============================================================================
slide4 = prs.slides.add_slide(blank_layout)
add_bg(slide4, 4)

sub4 = slide4.shapes.add_textbox(Inches(0.8), Inches(1.55), Inches(11.733), Inches(0.4))
tf_sub4 = sub4.text_frame
tf_sub4.word_wrap = True
p_sub4 = tf_sub4.paragraphs[0]
p_sub4.text = "Project Achievements, Socio-Economic Impact & Future Technological Roadmap"
p_sub4.font.size = Pt(13)
p_sub4.font.bold = True
p_sub4.font.color.rgb = COLOR_NAVY
p_sub4.alignment = PP_ALIGN.CENTER

# Two large panels (Left: Conclusions, Right: Future Targets)
panel4_w = Inches(5.72)
panel4_h = Inches(4.75)
panel4_y = Inches(1.95)

# Left Panel: Conclusion
create_card(slide4, col1_l, panel4_y, panel4_w, panel4_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_concl = slide4.shapes.add_textbox(
    col1_l + Inches(0.18), panel4_y + Inches(0.14), panel4_w - Inches(0.36), panel4_h - Inches(0.28)
)
tf_c = tb_concl.text_frame
tf_c.word_wrap = True
p = tf_c.paragraphs[0]
p.text = "KEY PROJECT ACHIEVEMENTS & CONTRIBUTIONS"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_DARK_GREEN

conclusions = [
    (
        "1. High-Accuracy Multi-Class Crop Prediction: ",
        "Successfully engineered and deployed a Random Forest classifier with 99.52% ± 0.25% (5-fold CV) accuracy across 23 diverse crops, eliminating guesswork for smallholder farmers.",
    ),
    (
        "2. Practical Commercial Fertilizer Dosage: ",
        "Bridged the critical industry gap between theoretical scientific recommendations (kg/ha) and commercial reality by computing exact 50 kg bag quantities (Urea, DAP, MOP).",
    ),
    (
        "3. Resilient Zero-Downtime Agro-Meteorology: ",
        "Architected a robust 3-tier fallback pipeline (Open-Meteo ECMWF → OpenWeatherMap → Climate Baseline) backed by in-memory caching (<1ms response) ensuring 100% service availability.",
    ),
    (
        "4. Regional Land Cadastral Integration: ",
        "Empowered South Indian farmers (Tamil Nadu, Kerala, Karnataka, Andhra Pradesh) to input their native survey units (Cents & Gunthas) with exact 3-decimal revenue conversion.",
    ),
    (
        "5. Robust Software & Security Standards: ",
        "Passed 34 automated integration tests, implemented strict coordinate validation (HTTP 400), and secured API credentials through environment variable isolation.",
    ),
]
for lbl, val in conclusions:
    p = tf_c.add_paragraph()
    p.font.size = Pt(9.2)
    p.space_before = Pt(5)
    r1 = p.add_run()
    r1.text = lbl
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.color.rgb = COLOR_SLATE_BODY

# Right Panel: Future Targets
create_card(slide4, col2_l, panel4_y, panel4_w, panel4_h, COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_targ = slide4.shapes.add_textbox(
    col2_l + Inches(0.18), panel4_y + Inches(0.14), panel4_w - Inches(0.36), panel4_h - Inches(0.28)
)
tf_t = tb_targ.text_frame
tf_t.word_wrap = True
p = tf_t.paragraphs[0]
p.text = "FUTURE TECHNOLOGICAL ROADMAP & COMMERCIAL TARGETS"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = COLOR_NAVY

targets = [
    (
        "TARGET 1: Offline Edge AI Mobile Application (TFLite / ONNX): ",
        "Quantize Random Forest model weights to run directly on low-cost Android smartphones without requiring active internet connectivity in remote rural farmlands.",
    ),
    (
        "TARGET 2: IoT Soil Sensor Telemetry (LoRaWAN & ESP32): ",
        "Develop solar-powered low-power field probes to continuously stream real-time in-situ Nitrogen, Phosphorus, Potassium, moisture, and soil temperature telemetry directly to the DSS.",
    ),
    (
        "TARGET 3: Multilingual Vernacular Voice Assistant: ",
        "Implement Speech-to-Text and Text-to-Speech interfaces in Tamil, Telugu, Kannada, and Hindi to make actionable agro-advisories accessible to illiterate and marginal farmers.",
    ),
    (
        "TARGET 4: Computer Vision Leaf Pathology Diagnosis: ",
        "Incorporate a lightweight MobileNetV3 Convolutional Neural Network (CNN) module for instant smartphone image diagnosis of foliar diseases and pest infestations.",
    ),
    (
        "TARGET 5: Agricultural Cooperative & SHG Deployment: ",
        "Pilot deployment with Primary Agricultural Credit Societies (PACS) and Farmer Producer Organizations (FPOs) across Coimbatore and Western Tamil Nadu.",
    ),
]
for lbl, val in targets:
    p = tf_t.add_paragraph()
    p.font.size = Pt(9.2)
    p.space_before = Pt(5)
    r1 = p.add_run()
    r1.text = lbl
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.color.rgb = COLOR_SLATE_BODY

# ==============================================================================
# SLIDE 5: Slide 16 - REFERENCES
# ==============================================================================
slide5 = prs.slides.add_slide(blank_layout)
add_bg(slide5, 5)

sub5 = slide5.shapes.add_textbox(Inches(0.8), Inches(1.55), Inches(11.733), Inches(0.4))
tf_sub5 = sub5.text_frame
tf_sub5.word_wrap = True
p_sub5 = tf_sub5.paragraphs[0]
p_sub5.text = "Standard IEEE Scholarly, Agronomic & Meteorological Citations"
p_sub5.font.size = Pt(13)
p_sub5.font.bold = True
p_sub5.font.color.rgb = COLOR_NAVY
p_sub5.alignment = PP_ALIGN.CENTER

# Two Symmetrical Reference Cards
ref_col_w = Inches(5.72)
ref_col_h = Inches(4.75)
ref_top = Inches(1.95)

# Left Column: Machine Learning & Computing Core
create_card(slide5, col1_l, ref_top, ref_col_w, ref_col_h, COLOR_CARD_BG, COLOR_CARD_BORDER)
tb_ref1 = slide5.shapes.add_textbox(
    col1_l + Inches(0.18), ref_top + Inches(0.14), ref_col_w - Inches(0.36), ref_col_h - Inches(0.28)
)
tf_r1 = tb_ref1.text_frame
tf_r1.word_wrap = True
tf_r1.paragraphs[0].text = "MACHINE LEARNING & AGRO-INFORMATICS"
tf_r1.paragraphs[0].font.size = Pt(12)
tf_r1.paragraphs[0].font.bold = True
tf_r1.paragraphs[0].font.color.rgb = COLOR_NAVY

refs_part1 = [
    (
        "[1] ",
        "Indian Council of Agricultural Research (ICAR), ",
        '"Handbook of Agriculture: Facts and Figures for Farmers, Students and All Interested in Farming," ',
        "7th ed., New Delhi: Directorate of Knowledge Management in Agriculture, ICAR Publications, 2023, ISBN: 978-8171641870.\n"
        "• Foundation for nutrient deficit equations & chemical fertilizer balancing.",
    ),
    (
        "[2] ",
        "L. Breiman, ",
        '"Random Forests," ',
        "Machine Learning, vol. 45, no. 1, pp. 5–32, Oct. 2001, doi: 10.1023/A:1010933404324.\n"
        "• Theoretical basis for ensemble voting, out-of-bag error estimation & Gini impurity.",
    ),
    (
        "[3] ",
        "F. Pedregosa, G. Varoquaux, A. Gramfort, et al., ",
        '"Scikit-learn: Machine Learning in Python," ',
        "Journal of Machine Learning Research (JMLR), vol. 12, pp. 2825–2830, Nov. 2011.\n"
        "• Pipeline architecture for StandardScaler normalization & stratified data splitting.",
    ),
]

for tag, authors, paper_title, pub_details in refs_part1:
    p = tf_r1.add_paragraph()
    p.font.size = Pt(9.5)
    p.space_before = Pt(8)

    r_tag = p.add_run()
    r_tag.text = tag
    r_tag.font.bold = True
    r_tag.font.color.rgb = COLOR_NAVY

    r_auth = p.add_run()
    r_auth.text = authors
    r_auth.font.bold = True
    r_auth.font.color.rgb = COLOR_SLATE_DARK

    r_tit = p.add_run()
    r_tit.text = paper_title
    r_tit.font.italic = True
    r_tit.font.color.rgb = COLOR_DARK_GREEN

    r_pub = p.add_run()
    r_pub.text = pub_details
    r_pub.font.color.rgb = COLOR_SLATE_BODY

# Right Column: Agrometeorology & Agronomic Standards
create_card(slide5, col2_l, ref_top, ref_col_w, ref_col_h, COLOR_GREEN_TINT, COLOR_GREEN_BORDER)
tb_ref2 = slide5.shapes.add_textbox(
    col2_l + Inches(0.18), ref_top + Inches(0.14), ref_col_w - Inches(0.36), ref_col_h - Inches(0.28)
)
tf_r2 = tb_ref2.text_frame
tf_r2.word_wrap = True
tf_r2.paragraphs[0].text = "METEOROLOGY & AGRONOMIC GUIDELINES"
tf_r2.paragraphs[0].font.size = Pt(12)
tf_r2.paragraphs[0].font.bold = True
tf_r2.paragraphs[0].font.color.rgb = COLOR_DARK_GREEN

refs_part2 = [
    (
        "[4] ",
        "R. G. Allen, L. S. Pereira, D. Raes, and M. Smith, ",
        '"Crop Evapotranspiration: Guidelines for Computing Crop Water Requirements," ',
        "FAO Irrigation and Drainage Paper No. 56, Rome: Food and Agriculture Organization of the United Nations (FAO), 1998.\n"
        "• Basis for Penman-Monteith crop water coefficients & irrigation planning.",
    ),
    (
        "[5] ",
        "Tamil Nadu Agricultural University (TNAU), ",
        '"Crop Production Guide: Agriculture 2020," ',
        "Directorate of Agriculture, Government of Tamil Nadu & TNAU, Coimbatore, India, 2020.\n"
        "• Regional crop calendar, soil pH tolerance & Tamil Nadu fertilizer recommendations.",
    ),
    (
        "[6] ",
        "World Meteorological Organization (WMO), ",
        '"Guide to Agricultural Meteorological Practices," ',
        "WMO-No. 134, Geneva, Switzerland: Secretariat of the WMO, 2018.\n"
        "• Standardized wind drift (<12 km/h) & precipitation thresholds for chemical spraying.",
    ),
]

for tag, authors, paper_title, pub_details in refs_part2:
    p = tf_r2.add_paragraph()
    p.font.size = Pt(9.5)
    p.space_before = Pt(8)

    r_tag = p.add_run()
    r_tag.text = tag
    r_tag.font.bold = True
    r_tag.font.color.rgb = COLOR_DARK_GREEN

    r_auth = p.add_run()
    r_auth.text = authors
    r_auth.font.bold = True
    r_auth.font.color.rgb = COLOR_SLATE_DARK

    r_tit = p.add_run()
    r_tit.text = paper_title
    r_tit.font.italic = True
    r_tit.font.color.rgb = COLOR_NAVY

    r_pub = p.add_run()
    r_pub.text = pub_details
    r_pub.font.color.rgb = COLOR_SLATE_BODY

# ==============================================================================
# SLIDE 6: Slide 17 - Thank you.
# ==============================================================================
slide6 = prs.slides.add_slide(blank_layout)
add_bg(slide6, 6)

# Top badge above "Thank you."
tb_top6 = slide6.shapes.add_textbox(Inches(1.5), Inches(1.4), Inches(10.333), Inches(0.8))
tf_t6 = tb_top6.text_frame
tf_t6.word_wrap = True
p = tf_t6.paragraphs[0]
p.text = "AgriSense AI: Precision Agriculture Decision Support Platform"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_NAVY
p.alignment = PP_ALIGN.CENTER

p_inst = tf_t6.add_paragraph()
p_inst.text = "Department of Computer Science and Engineering / Information Technology\nKPR Institute of Engineering and Technology, Coimbatore, Tamil Nadu"
p_inst.font.size = Pt(11.5)
p_inst.font.bold = True
p_inst.font.color.rgb = COLOR_DARK_GREEN
p_inst.alignment = PP_ALIGN.CENTER
p_inst.space_before = Pt(2)

# Card placed BELOW "Thank you." (y=3.8 to 6.4)
card_ty_w = Inches(10.5)
card_ty_h = Inches(2.65)
card_ty_x = Inches(1.416)
card_ty_y = Inches(3.85)

create_card(slide6, card_ty_x, card_ty_y, card_ty_w, card_ty_h, COLOR_GREEN_TINT, COLOR_GREEN_BORDER)

tb_ty = slide6.shapes.add_textbox(
    card_ty_x + Inches(0.25), card_ty_y + Inches(0.12), card_ty_w - Inches(0.5), card_ty_h - Inches(0.24)
)
tf_ty = tb_ty.text_frame
tf_ty.word_wrap = True

p_ty0 = tf_ty.paragraphs[0]
p_ty0.text = "PROJECT REVIEW & TECHNICAL EVALUATION"
p_ty0.font.size = Pt(13)
p_ty0.font.bold = True
p_ty0.font.color.rgb = COLOR_DARK_GREEN
p_ty0.alignment = PP_ALIGN.CENTER

p_div = tf_ty.add_paragraph()
p_div.text = "────────────────────────────────────────────────────────────"
p_div.font.size = Pt(8)
p_div.font.color.rgb = COLOR_GREEN_BORDER
p_div.alignment = PP_ALIGN.CENTER
p_div.space_before = Pt(2)

points_ty = [
    (
        "Core Modules Evaluated: ",
        "Random Forest 23-Crop Engine (99.52% 5-fold CV) • ICAR 50kg Bag Stoichiometry Engine",
    ),
    (
        "Real-Time Integrations: ",
        "Zero-Downtime Agro-Meteorological Spray Advisory Pipeline • South Indian Land Survey Units",
    ),
    (
        "System Deliverables: ",
        "34/34 Green Unit Tests • Interactive Farmer-First React SPA • Python Flask REST Services",
    ),
    (
        "Ready for Live Demonstration: ",
        "Full live system demonstration available for Viva Voce & Review Panel Questions",
    ),
]

for lbl, val in points_ty:
    p = tf_ty.add_paragraph()
    p.font.size = Pt(9.5)
    p.space_before = Pt(2.5)
    r1 = p.add_run()
    r1.text = "✔ " + lbl
    r1.font.bold = True
    r1.font.color.rgb = COLOR_SLATE_DARK
    r2 = p.add_run()
    r2.text = val
    r2.font.color.rgb = COLOR_SLATE_BODY

p_ty_end = tf_ty.add_paragraph()
p_ty_end.text = "Open for Questions, Suggestions & Review Feedback"
p_ty_end.font.size = Pt(11)
p_ty_end.font.bold = True
p_ty_end.font.color.rgb = COLOR_NAVY
p_ty_end.alignment = PP_ALIGN.CENTER
p_ty_end.space_before = Pt(5)

# Save presentation
output_pptx = "/home/bijayadav/Project/agrisense-ai/AgriSense_AI_Project_Presentation.pptx"
prs.save(output_pptx)
print(f"✅ Presentation successfully generated and saved to: {output_pptx}")
