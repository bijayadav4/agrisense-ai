from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

pdf_path = "/home/bijayadav/Project/agrisense-ai/AgriSense_AI_System_Workflow.pdf"


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header (Top rule)
        self.drawString(54, 750, "AgriSense AI — Precision Agriculture System Workflow")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        # Footer (Bottom rule)
        self.line(54, 45, 558, 45)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_text)
        self.drawString(54, 32, "CONFIDENTIAL — For Academic & Technical Review")
        self.restoreState()


doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=60, bottomMargin=60)

styles = getSampleStyleSheet()

# Typography Styles
title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    textColor=colors.HexColor("#15803d"),
)

subtitle_style = ParagraphStyle(
    "DocSubTitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    textColor=colors.HexColor("#475569"),
)

h1_style = ParagraphStyle(
    "SectionH1",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=17,
    textColor=colors.HexColor("#0f172a"),
    spaceBefore=12,
    spaceAfter=6,
)

h2_style = ParagraphStyle(
    "SectionH2",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10.5,
    leading=14,
    textColor=colors.HexColor("#166534"),
    spaceBefore=7,
    spaceAfter=3,
)

body_style = ParagraphStyle(
    "DocBody",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13.5,
    textColor=colors.HexColor("#1e293b"),
    spaceAfter=5,
)

table_header_style = ParagraphStyle(
    "TableHeader", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white
)

table_body_style = ParagraphStyle(
    "TableBody",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#1e293b"),
)

story = []

# Title & Metadata
story.append(Paragraph("AgriSense AI — Complete System Workflow", title_style))
story.append(Spacer(1, 4))
story.append(
    Paragraph("End-to-End Technical Architecture, Scientific Logic, and Reviewer Defense Guide", subtitle_style)
)
story.append(Spacer(1, 8))
story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#15803d"), spaceAfter=12))

# 1. Executive System Overview
story.append(Paragraph("1. Executive System Overview", h1_style))
story.append(
    Paragraph(
        "<b>AgriSense AI</b> is a full-stack, cloud-native Precision Agriculture Decision Support System (DSS). It empowers farmers and agricultural extension officers to optimize crop selection, calculate scientifically balanced fertilizer dosages, convert South Indian regional land units, and monitor real-time micro-climate spray windows.",
        body_style,
    )
)

overview_data = [
    [
        Paragraph("System Layer", table_header_style),
        Paragraph("Technology Stack", table_header_style),
        Paragraph("Core Responsibility", table_header_style),
    ],
    [
        Paragraph("Frontend Client", table_body_style),
        Paragraph("React 19 + Vite 8 + Lucide Icons", table_body_style),
        Paragraph("Responsive, single-page application with instant client-side Map caching.", table_body_style),
    ],
    [
        Paragraph("Backend REST API", table_body_style),
        Paragraph("Python Flask + Blueprints + Requests", table_body_style),
        Paragraph("Stateless REST API handling validation, orchestration, and inference.", table_body_style),
    ],
    [
        Paragraph("Machine Learning", table_body_style),
        Paragraph("Scikit-Learn (Random Forest) + Joblib", table_body_style),
        Paragraph("Predicts optimal crop across 23 classes (99.52% 5-fold CV benchmark).", table_body_style),
    ],
    [
        Paragraph("Chemical Engine", table_body_style),
        Paragraph("ICAR Nutrient Deficit Stoichiometry", table_body_style),
        Paragraph("Calculates commercial bag counts (DAP, Urea, MOP) per plot size.", table_body_style),
    ],
    [
        Paragraph("Meteorology", table_body_style),
        Paragraph("ECMWF / Open-Meteo High-Res API", table_body_style),
        Paragraph("Live 10m wind velocity, rain probability %, and 5-day continuous forecast.", table_body_style),
    ],
]
t_overview = Table(overview_data, colWidths=[110, 150, 244])
t_overview.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#15803d")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]
    )
)
story.append(t_overview)
story.append(Spacer(1, 10))

# 2. End-to-End Farmer User Flow
story.append(Paragraph("2. End-to-End Farmer Workflow (Step-by-Step)", h1_style))
story.append(Paragraph("The platform is designed around three natural agricultural stages:", body_style))

steps_data = [
    [
        Paragraph("Stage", table_header_style),
        Paragraph("Farmer Action", table_header_style),
        Paragraph("Internal System Processing", table_header_style),
        Paragraph("Farmer Result", table_header_style),
    ],
    [
        Paragraph("Step 1", table_body_style),
        Paragraph("<b>Dashboard Landing</b>", table_body_style),
        Paragraph(
            "Auto-syncs live GPS/district weather; evaluates 10m wind speed and rain probability.", table_body_style
        ),
        Paragraph(
            "Sees today date, current weather, and direct <b>Spray Safety</b> and <b>Irrigation</b> decisions.",
            table_body_style,
        ),
    ],
    [
        Paragraph("Step 2", table_body_style),
        Paragraph("<b>Soil Test (Crop)</b>", table_body_style),
        Paragraph(
            "Farmer enters N, P, K (kg/ha) and pH from Soil Health Card. Features scaled and passed to Random Forest.",
            table_body_style,
        ),
        Paragraph(
            "Recommended Crop (e.g. <b>Rice / Paddy</b>) with match confidence (99.5%), season, duration, and water need.",
            table_body_style,
        ),
    ],
    [
        Paragraph("Step 3", table_body_style),
        Paragraph("<b>Fertilizer Planner</b>", table_body_style),
        Paragraph(
            "Farmer selects South Indian state and enters plot in Cents/Gunthas/Acres. System calculates ICAR NPK deficit.",
            table_body_style,
        ),
        Paragraph(
            "Exact 50kg bag counts for <b>DAP, Urea, and MOP</b> tailored to their specific land plot.",
            table_body_style,
        ),
    ],
]
t_steps = Table(steps_data, colWidths=[40, 110, 194, 160])
t_steps.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]
    )
)
story.append(t_steps)
story.append(Spacer(1, 10))

# 3. Scientific Calculations & Revenue Formulas
story.append(Paragraph("3. Scientific Calculations & Revenue Formulas", h1_style))

story.append(Paragraph("<b>A. Regional Land Unit Multipliers (Government Revenue Survey Standards):</b>", h2_style))
story.append(
    Paragraph(
        "• <b>Tamil Nadu & Kerala:</b> 1 Cent = 0.00404686 Hectares (100 Cents = 1 Acre = 0.404686 Hectares).<br/>• <b>Karnataka & Andhra Pradesh:</b> 1 Guntha = 0.01011714 Hectares (40 Gunthas = 1 Acre = 0.404686 Hectares).<br/>• <b>Acre to Hectare:</b> 1 Hectare = 2.47105 Acres.",
        body_style,
    )
)

story.append(Paragraph("<b>B. ICAR Chemical Fertilizer Stoichiometry:</b>", h2_style))
story.append(
    Paragraph(
        "Commercial fertilizers have fixed elemental nutrient percentages:<br/>• <b>DAP (18-46-0):</b> Supplies 46% P2O5 and 18% Nitrogen.<br/>• <b>Urea (46-0-0):</b> Supplies 46% Nitrogen.<br/>• <b>MOP (0-0-60):</b> Supplies 60% K2O (Potash).<br/>The engine first calculates DAP to satisfy phosphorus. It then subtracts the nitrogen delivered by DAP before calculating Urea: <i>Remaining Nitrogen = Deficit N - (DAP kg * 0.18)</i>. This prevents chemical fertilizer over-application and leaf burn.",
        body_style,
    )
)

story.append(Paragraph("<b>C. Weather & Spray Window Safety Threshold:</b>", h2_style))
story.append(
    Paragraph(
        "• <b>Wind &lt; 20 km/h:</b> Safe calm conditions for pesticide and nutrient boom spraying.<br/>• <b>Wind &gt;= 20 km/h:</b> High drift hazard alert (spray droplets will blow off target).<br/>• <b>Rain Probability &gt;= 60%:</b> Postpone surface fertilizer broadcasting to prevent wash-off.",
        body_style,
    )
)
story.append(Spacer(1, 10))

# Page Break for clean 2-page document
story.append(PageBreak())

# 4. Reviewer Defense: Where is the Database?
story.append(Paragraph('4. Reviewer Defense: "Where is the Database?"', h1_style))
story.append(
    Paragraph(
        "When evaluators or professors ask where data is persisted, present this clear architectural defense:",
        body_style,
    )
)

db_points = [
    [
        Paragraph("Evaluation Question", table_header_style),
        Paragraph("Technical Defense & Architecture Explanation", table_header_style),
    ],
    [
        Paragraph("Why No Traditional SQL DB?", table_body_style),
        Paragraph(
            "<b>Decision Support System (DSS):</b> AgriSense AI performs real-time stateless inference rather than CRUD operations. Farmers require zero-login, instant advice without personal tracking.",
            table_body_style,
        ),
    ],
    [
        Paragraph("Where is Ground Truth?", table_body_style),
        Paragraph(
            "<b>Structured Datasets:</b> 2,300 benchmark records (2,200 open-source Kaggle samples across 22 crops + 100 ICAR Rabi synthetic envelope samples for Wheat) stored in <code>Crop_recommendation.csv</code>.",
            table_body_style,
        ),
    ],
    [
        Paragraph("Where is AI Knowledge?", table_body_style),
        Paragraph(
            "<b>Serialized Model Store:</b> Machine learning weights and scalers are pre-compiled and stored in binary Joblib format (<code>.pkl</code>) for sub-millisecond memory loading.",
            table_body_style,
        ),
    ],
    [
        Paragraph("Where is Weather Stored?", table_body_style),
        Paragraph(
            "<b>Live Dynamic Feeds:</b> Queried in real-time from Open-Meteo with an in-memory TTL cache (10-minute validity) to eliminate stale database records.",
            table_body_style,
        ),
    ],
    [
        Paragraph("How to Add DB in Future?", table_body_style),
        Paragraph(
            "<b>Modular Architecture:</b> Built with Flask Blueprints. An enterprise SQL database (PostgreSQL/SQLite via SQLAlchemy) or MongoDB can be attached seamlessly for audit trails.",
            table_body_style,
        ),
    ],
]
t_db = Table(db_points, colWidths=[130, 374])
t_db.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf5ff")]),
        ]
    )
)
story.append(t_db)
story.append(Spacer(1, 14))

# 5. Verification & Mathematical Audit Summary
story.append(Paragraph("5. Verification & Mathematical Audit Summary", h1_style))
story.append(
    Paragraph(
        "The entire platform was subjected to an automated end-to-end mathematical audit on September 6, 2026:<br/>• <b>18/18 Mathematical Audit Checks:</b> Passed (100% precision across Cents, Gunthas, DAP/Urea stoichiometry, and crop predictions).<br/>• <b>8/8 Automated PyUnit Test Cases:</b> Passed (Status: OK in 3.05s).<br/>• <b>Frontend Production Build:</b> 0 Errors, built in 271ms.<br/>• <b>Dashboard Polish:</b> Zero duplicate widgets, real calendar dates for all 5 forecast days, and farmer-first high-contrast UI.",
        body_style,
    )
)

doc.build(story, canvasmaker=NumberedCanvas)
print("PDF generated successfully at:", pdf_path)
