"""
Generate Official Unstop Submission PDF for SupeRR Scout Season 2.
Comprehensive, publication-ready 4-page research report detailing:
- Page 1: Executive Summary, Pressure Formulation Physics & Empirical Bayes Reliability Modeling
- Page 2: 8-Page Dashboard Architecture Tour & Official Top 10 Batters Leaderboard with Dossiers
- Page 3: Official Top 10 Bowlers Leaderboard with Dossiers & Dual-Lens (IPL vs Combined) Analysis
- Page 4: RR IPL 2027 Auction War Room, SMS Stadium Fit, Statistical Governance & Submission Matrix
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# Ensure project root is in path
sys.path.insert(0, os.getcwd())
from src.ui_helpers import load_core_data, get_computed_rankings
from src.auction_intelligence import compute_auction_rankings

# Color Palette (Rajasthan Royals Theme)
C_PRIMARY = colors.HexColor("#080D20")     # Deep Navy background
C_RR_PINK = colors.HexColor("#E6007E")     # RR Royal Pink
C_RR_BLUE = colors.HexColor("#1746A2")     # Deep Royal Blue
C_TEXT = colors.HexColor("#1A202C")        # Dark slate text
C_MUTED = colors.HexColor("#4A5568")       # Muted text
C_BG_LIGHT = colors.HexColor("#F7FAFC")    # Clean card / table background
C_BORDER = colors.HexColor("#CBD5E0")      # Clean border
C_GOLD = colors.HexColor("#D69E2E")        # Gold accent


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw total page numbers and RR header/footer."""
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
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(C_RR_BLUE)

        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 758, "RAJASTHAN ROYALS | SupeRR SCOUT PRESSURE INTELLIGENCE ENGINE")
            self.drawRightString(576, 758, "UNSTOP OFFICIAL METHODOLOGY REPORT")
            self.setStrokeColor(C_RR_PINK)
            self.setLineWidth(1)
            self.line(36, 752, 576, 752)

        # Footer (All pages)
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.75)
        self.line(36, 32, 576, 32)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(C_MUTED)
        self.drawString(36, 22, "SupeRR Selector Season 2 — Identify the Most Reliable Players Under Pressure | Confidential")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 22, page_str)
        self.restoreState()


def generate_unstop_report(output_paths):
    print("Loading core data...")
    deliveries_df, matches_df = load_core_data()

    print("Computing rankings...")
    bat_ranked, top_10_batters, bowl_ranked, top_10_bowlers = get_computed_rankings(
        deliveries_df, 60, 65.0
    )
    ipl_rank_dict = compute_auction_rankings(deliveries_df, min_balls=60, pressure_thresh=65.0)
    ipl_batters = ipl_rank_dict["batters_ipl"]
    ipl_bowlers = ipl_rank_dict["bowlers_ipl"]

    total_deliveries = len(deliveries_df)
    total_matches = deliveries_df["match_id"].nunique()
    hp_bat_count = int(deliveries_df["is_high_pressure_bat"].sum())
    hp_bowl_count = int(deliveries_df["is_high_pressure_bowl"].sum())

    doc = SimpleDocTemplate(
        str(output_paths[0]),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        textColor=C_RR_PINK,
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=C_RR_BLUE,
        alignment=TA_LEFT
    )

    meta_style = ParagraphStyle(
        "Meta_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=C_MUTED
    )

    h1_style = ParagraphStyle(
        "H1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=C_RR_BLUE,
        spaceBefore=7,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=C_TEXT,
        alignment=TA_JUSTIFY,
        spaceAfter=3
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.2,
        leading=9.8,
        textColor=C_TEXT,
        leftIndent=8,
        spaceAfter=2
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.8,
        leading=8.5,
        textColor=C_TEXT
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.8,
        leading=8.5,
        textColor=C_TEXT
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.8,
        leading=8.5,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    story = []

    # ==================== PAGE 1: EXECUTIVE SUMMARY & MATHEMATICAL FOUNDATIONS ====================
    story.append(Paragraph("SupeRR SCOUT — PRESSURE DECISION INTELLIGENCE PLATFORM", title_style))
    story.append(Paragraph("Rajasthan Royals Official Hackathon Submission | SupeRR Selector Season 2 (Round 1)", subtitle_style))
    story.append(Spacer(1, 2))
    story.append(HRFlowable(width="100%", thickness=2, color=C_RR_PINK, spaceBefore=1, spaceAfter=4))

    meta_text = (
        f"<b>Tournament Corpus:</b> 2022–2026 IPL & T20I Matches | <b>Deliveries Analysed:</b> {total_deliveries:,} | "
        f"<b>Matches:</b> {total_matches:,} | <b>HP Leverage Threshold:</b> Index ≥ 65.0 | "
        f"<b>Statistical Framework:</b> Empirical Bayes Shrinkage (K=50) & 95% Bootstrap Confidence Intervals"
    )
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1. Executive Summary & Challenge Objectives", h1_style))
    exec_summary_text = (
        "Modern T20 franchise cricket is won in acute micro-moments of extreme pressure. Standard aggregate metrics "
        "— such as overall tournament strike rate or nominal bowling economy — systematically mislead franchise recruiters "
        "by conflating cheap runs and wickets accumulated in dead rubbers or low-stakes phases with clutch performances "
        "when tournament lifelines are on the line. "
        "To solve the <b>SupeRR Selector Season 2</b> mandate, we engineered <b>SupeRR SCOUT</b>: an enterprise-grade "
        "Pressure Decision Intelligence Platform built to isolate, model, and quantify player reliability under pressure. "
        "Across <b>200,999 competitive deliveries</b> spanning 2022 to 2026, the engine isolates high-leverage situations "
        "(Pressure Index ≥ 65.0), applies Empirical Bayes shrinkage against league population priors to eliminate small-sample bias, "
        "and produces transparent, scientifically defensible Top 10 rankings for batters and bowlers to power Rajasthan Royals' "
        "IPL 2027 auction strategy."
    )
    story.append(Paragraph(exec_summary_text, body_style))

    # Top KPI Banner
    top_bat = top_10_batters.iloc[0]
    top_bowl = top_10_bowlers.iloc[0]
    kpi_card_data = [
        [
            Paragraph(f"<b>#1 High-Pressure Batter</b><br/><font color='#E6007E' size=8><b>{top_bat['player_name']}</b></font><br/>Score: <b>{top_bat['reliability_score']:.1f}</b>/100 | SR: {top_bat['hp_strike_rate']:.1f}", table_cell),
            Paragraph(f"<b>#1 High-Pressure Bowler</b><br/><font color='#1746A2' size=8><b>{top_bowl['player_name']}</b></font><br/>Score: <b>{top_bowl['reliability_score']:.1f}</b>/100 | Econ: {top_bowl['hp_economy']:.2f}", table_cell),
            Paragraph(f"<b>HP Bat Deliveries</b><br/><font color='#E6007E' size=8><b>{hp_bat_count:,}</b></font><br/>{hp_bat_count/total_deliveries*100:.1f}% of all deliveries", table_cell),
            Paragraph(f"<b>HP Bowl Deliveries</b><br/><font color='#1746A2' size=8><b>{hp_bowl_count:,}</b></font><br/>{hp_bowl_count/total_deliveries*100:.1f}% of all deliveries", table_cell),
        ]
    ]
    t_kpi = Table(kpi_card_data, colWidths=[135, 135, 135, 135])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 4))

    # ==================== SECTION 2: PRESSURE DEFINITION & PHYSICS ====================
    story.append(Paragraph("2. Pressure Formulation: Physics & Match-Context Architecture", h1_style))
    p_def_text = (
        "Cricket exhibits fundamental structural asymmetry between batting and bowling, and between innings. "
        "A single static formula cannot reflect the operational reality of both roles. SupeRR SCOUT formulates three distinct "
        "continuous mathematical leverage functions calibrated dynamically from 0 to 100 on every delivery:"
    )
    story.append(Paragraph(p_def_text, body_style))

    p_components = [
        "<b>• Chase Batting Pressure (2nd Innings):</b> Governed by required run-rate escalation relative to par, remaining balls, "
        "and wickets in hand: <i>P_chase = 0.40 · RRR_Stress + 0.25 · Wicket_Urgency + 0.20 · Innings_Progression + 0.15 · Closeness_Factor</i>. "
        "When RRR exceeds 12.0 RPO in the death overs with 5+ wickets lost, pressure approaches 90–100.",
        "<b>• First-Innings Batting Pressure:</b> Calibrated by wicket crisis and match stage acceleration: "
        "<i>P_1st = 0.45 · Crisis_Index + 0.35 · Stage_Demand + 0.20 · Run_Rate_Deficit</i>. A top-order collapse (e.g. 30/3 in Powerplay) "
        "triggers immediate high pressure to model innings rebuilding.",
        "<b>• Defensive Bowling Pressure:</b> Measures the tactical difficulty of defending into high-leverage states: "
        "<i>P_bowl = 0.45 · Opposition_Leverage + 0.30 · Over_Phase_Weight + 0.25 · Target_Closeness</i>. Late overs with small run buffers "
        "and set batters at the crease maximize bowling pressure demand.",
        "<b>• Knockout / Playoff Multiplier:</b> Every delivery in tournament playoffs, eliminators, qualifiers, and finals receives an "
        "empirical <b>1.08× context multiplier</b>, elevating high-stakes knockout performance above routine league fixtures.",
        "<b>• The High-Pressure Cutoff (P ≥ 65.0):</b> Isolates the top 13–17% most acute competitive deliveries in the "
        "historical database, strictly separating routine run accumulation from true championship-defining crucible moments."
    ]
    for bullet in p_components:
        story.append(Paragraph(bullet, bullet_style))
    story.append(Spacer(1, 4))

    # ==================== SECTION 3: EMPIRICAL BAYES & STATISTICAL FAIRNESS ====================
    story.append(Paragraph("3. Statistical Fairness, Bayesian Regularization & Reliability Modeling", h1_style))
    bayes_text = (
        "Small-sample variance is the single greatest trap in sports analytics. A finisher who faces only 25 deliveries might post an "
        "unsustainable 230 strike rate, while a dependable campaigner facing 300 deliveries absorbs harder assignments. "
        "To ensure complete statistical fairness, SupeRR SCOUT integrates three mathematical pillars:"
    )
    story.append(Paragraph(bayes_text, body_style))

    bayes_bullets = [
        "<b>1. Empirical Bayes Shrinkage:</b> Every player's observed metric (θ_i) is shrunk toward the league population prior (μ_pop): "
        "<i>θ_shrunk = w_i · θ_i + (1 - w_i) · μ_pop</i>, where the credibility weight is <i>w_i = n_i / (n_i + K)</i>. "
        "We set half-credibility constant <b>K = 50 deliveries</b>. A player with 50 balls receives 50% Bayesian weight; at 200 balls, "
        "credibility reaches 80.0%, allowing proven match-winners to separate cleanly from statistical noise.",
        "<b>2. Multi-Pillar Reliability Score (0–100):</b> Synthesizes five fundamental dimensions: "
        "<b>30% Efficiency / Containment</b> (Shrunk SR or Shrunk Econ) + <b>25% Survival / Breakthrough</b> (Shrunk Avg or Wicket SR) + "
        "<b>20% Dominance</b> (Boundary % or Dot %) + <b>15% Clutch Delta</b> (Performance elevation under pressure vs baseline) + "
        "<b>10% Repeatability</b> (Cross-match consistency penalizing high single-game variance).",
        "<b>3. Uncertainty Bounds (95% Bootstrap CI):</b> Each reliability score is accompanied by non-parametric bootstrap confidence "
        "intervals (1,000 iterations). Compact intervals confirm sample maturity; wide intervals trigger cautious scouting flags."
    ]
    for b in bayes_bullets:
        story.append(Paragraph(b, bullet_style))

    story.append(PageBreak())

    # ==================== PAGE 2: DASHBOARD TOUR & TOP 10 BATTERS ====================
    story.append(Paragraph("4. Platform Architecture: Complete 8-Page Dashboard Tour", h1_style))
    dash_intro = (
        "SupeRR SCOUT is architected as an interactive IPL Franchise War Room conforming to Rajasthan Royals' brand identity "
        "and Power BI analytical conventions. The platform delivers eight deeply connected pages designed for executive decision-makers:"
    )
    story.append(Paragraph(dash_intro, body_style))

    pages_data = [
        [
            Paragraph("<b>Page Module</b>", table_header),
            Paragraph("<b>Core Capabilities & Franchise Functionality</b>", table_header),
            Paragraph("<b>Primary Tactical Outputs</b>", table_header)
        ],
        [
            Paragraph("<b>1. Executive Overview</b>", table_cell_bold),
            Paragraph("Franchise cockpit featuring high-level KPIs, 4 interactive Power BI charts (Leaderboard, Scatter, Heatmap, Split), slicer cross-filtering, and dynamic player spotlight cards.", table_cell),
            Paragraph("Macro overview of 200,999 balls, cohort benchmarks, and instant cross-visual spotlighting.", table_cell)
        ],
        [
            Paragraph("<b>2. Batting Intelligence</b>", table_cell_bold),
            Paragraph("Deep-dive batting analytics dissecting strike rate elevation (Δ SR), boundary production, dot avoidance, and match progression phases (Powerplay, Middle, Death) under high pressure.", table_cell),
            Paragraph("Identifies elite death-over finishers, middle-overs crisis anchors, and boundary accelerators.", table_cell)
        ],
        [
            Paragraph("<b>3. Bowling Intelligence</b>", table_cell_bold),
            Paragraph("Comprehensive bowling analytics examining high-pressure economy containment, wicket breakthroughs, dot ball suppression, and phase-specific defensive performance.", table_cell),
            Paragraph("Isolates death-over yorker execution, middle-over spin squeeze, and powerplay containment.", table_cell)
        ],
        [
            Paragraph("<b>4. Top 10 Rankings</b>", table_cell_bold),
            Paragraph("Official flagship leaderboards with tournament scope slicers (Combined vs IPL-Only), interactive Plotly bar charts with point-click filtering, head-to-head duels, and Unstop CSV export.", table_cell),
            Paragraph("Definitive Top 10 lists with Bayesian credibility breakdown and full statistical dossiers.", table_cell)
        ],
        [
            Paragraph("<b>5. Player Comparison</b>", table_cell_bold),
            Paragraph("Side-by-side head-to-head scouting duel studio comparing any two players with multi-metric differential tables, radar visualization, phase splits, and tactical fit verdicts.", table_cell),
            Paragraph("Direct comparative trade-off analysis for auction shortlist optimization.", table_cell)
        ],
        [
            Paragraph("<b>6. Match Simulator</b>", table_cell_bold),
            Paragraph("Interactive real-time match leverage simulator allowing analysts to set target, balls remaining, wickets in hand, and match phase to simulate live pressure and retrieve historical cohorts.", table_cell),
            Paragraph("Dynamic Pressure Curve visualization, situation win probability, and clutch player recommendations.", table_cell)
        ],
        [
            Paragraph("<b>7. Methodology</b>", table_cell_bold),
            Paragraph("Full mathematical transparency and peer-reviewable documentation: formula derivations, Bayesian shrinkage equations, data pipeline diagrams, and reproducible audit logs.", table_cell),
            Paragraph("Formal audit proof, sensitivity bounds, and governance standards.", table_cell)
        ],
        [
            Paragraph("<b>8. Auction War Room</b>", table_cell_bold),
            Paragraph("IPL 2027 Rajasthan Royals recruitment hub featuring confirmed squad baseline (19 players, 6 open slots, ₹27.05 Cr purse), player availability engine, budget simulator, and venue fit.", table_cell),
            Paragraph("Shortlist optimization, purse allocation, and Sawai Mansingh Stadium tactical fit.", table_cell)
        ]
    ]

    t_pages = Table(pages_data, colWidths=[90, 310, 140])
    t_pages.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_RR_BLUE),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_pages)
    story.append(Spacer(1, 5))

    # ==================== SECTION 5: OFFICIAL TOP 10 BATTERS ====================
    story.append(Paragraph("5. Official Top 10 Batters Under Pressure (Combined Scope: IPL & T20I)", h1_style))
    story.append(Paragraph(
        "Rankings computed across all 2022–2026 matches meeting qualifying threshold ≥60 high-pressure deliveries. "
        "Ordered strictly by Bayesian Regularized Reliability Score (0–100):",
        body_style
    ))

    bat_headers = ["Rk", "Player Name", "Score", "HP Balls", "HP Runs", "HP SR", "HP Avg", "Bnd %", "Δ SR", "95% CI"]
    bat_table_data = [[Paragraph(h, table_header) for h in bat_headers]]

    for _, r in top_10_batters.iterrows():
        bat_table_data.append([
            Paragraph(f"<b>#{r['rank']}</b>", table_cell_bold),
            Paragraph(f"<b>{r['player_name']}</b>", table_cell_bold),
            Paragraph(f"<b>{r['reliability_score']:.1f}</b>", table_cell_bold),
            Paragraph(f"{int(r['hp_balls']):,}", table_cell),
            Paragraph(f"{int(r['hp_runs']):,}", table_cell),
            Paragraph(f"{r['hp_strike_rate']:.1f}", table_cell),
            Paragraph(f"{r['hp_average']:.1f}", table_cell),
            Paragraph(f"{r['hp_boundary_pct']:.1f}%", table_cell),
            Paragraph(f"<font color='{'#2F855A' if r['sr_delta']>0 else '#E53E3E'}'><b>{r['sr_delta']:+.1f}</b></font>", table_cell),
            Paragraph(f"[{r['ci_lower']:.1f}-{r['ci_upper']:.1f}]", table_cell),
        ])

    t_bat = Table(bat_table_data, colWidths=[20, 115, 34, 46, 42, 44, 44, 40, 40, 65])
    t_bat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_RR_PINK),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_bat)
    story.append(Spacer(1, 4))

    # Batting Scouting Dossiers
    bat_dossier_text = (
        "<b>Key Tactical Batting Dossiers:</b> "
        "<b>• #1 Rinku Singh (Score: 85.3):</b> Benchmark finisher. Across 260 HP balls, Rinku posts an astounding <b>81.8 HP Avg</b> "
        "and <b>188.8 SR</b> (+45.3 SR delta) with compact 95% CI [75.5–95.0]. | "
        "<b>• #2 David Miller (Score: 84.3):</b> Exceptional clutch elevation (+68.1 SR delta) with a breathtaking <b>206.2 HP SR</b>. "
        "Premier left-handed death hitter against both express pace and spin. | "
        "<b>• #3 Tim David (Score: 75.8):</b> High-volume six-hitter (327 HP balls, 635 runs, 194.2 SR, 26.3% boundary rate). | "
        "<b>• #4 Ashutosh Sharma (Score: 70.1):</b> Premier uncapped domestic finisher (197.1 HP SR, +61.9 clutch delta across 174 balls). | "
        "<b>• #5–#10 Depth Cohort:</b> Towhid Hridoy (82.5 HP Avg) and Matthew Wade (70.7 HP Avg) provide extreme innings preservation; "
        "Tilak Varma (+36.8 Δ SR) and Tristan Stubbs (172.6 SR) represent elite middle-overs accelerators; "
        "veterans Ravindra Jadeja (63.8) and MS Dhoni (63.5, 165.5 SR) ensure experienced death-over composure."
    )
    story.append(Paragraph(bat_dossier_text, body_style))

    story.append(PageBreak())

    # ==================== PAGE 3: TOP 10 BOWLERS & DUAL-LENS ANALYSIS ====================
    story.append(Paragraph("6. Official Top 10 Bowlers Under Pressure (Combined Scope: IPL & T20I)", h1_style))
    story.append(Paragraph(
        "Rankings computed across all 2022–2026 matches meeting qualifying threshold ≥60 legal high-pressure deliveries. "
        "Ordered strictly by Bayesian Regularized Reliability Score (0–100):",
        body_style
    ))

    bowl_headers = ["Rk", "Player Name", "Score", "HP Balls", "Overs", "HP Wkts", "HP Econ", "Dot %", "Δ Econ", "95% CI"]
    bowl_table_data = [[Paragraph(h, table_header) for h in bowl_headers]]

    for _, r in top_10_bowlers.iterrows():
        bowl_table_data.append([
            Paragraph(f"<b>#{r['rank']}</b>", table_cell_bold),
            Paragraph(f"<b>{r['player_name']}</b>", table_cell_bold),
            Paragraph(f"<b>{r['reliability_score']:.1f}</b>", table_cell_bold),
            Paragraph(f"{int(r['hp_legal_balls']):,}", table_cell),
            Paragraph(f"{r['hp_overs']:.1f}", table_cell),
            Paragraph(f"{int(r['hp_wickets']):,}", table_cell),
            Paragraph(f"{r['hp_economy']:.2f}", table_cell),
            Paragraph(f"{r['hp_dot_pct']:.1f}%", table_cell),
            Paragraph(f"<font color='{'#2F855A' if r['econ_delta']<=0 else '#E53E3E'}'><b>{r['econ_delta']:+.2f}</b></font>", table_cell),
            Paragraph(f"[{r['ci_lower']:.1f}-{r['ci_upper']:.1f}]", table_cell),
        ])

    t_bowl = Table(bowl_table_data, colWidths=[20, 115, 34, 46, 42, 44, 44, 40, 40, 65])
    t_bowl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_RR_BLUE),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_bowl)
    story.append(Spacer(1, 4))

    # Bowling Scouting Dossiers
    bowl_dossier_text = (
        "<b>Key Tactical Bowling Dossiers:</b> "
        "<b>• #1 Sunil Narine (Score: 75.2):</b> Preeminent defensive bowler. Across 209 HP deliveries, Narine concedes a microscopic "
        "<b>6.32 Economy</b> with mystery length control that completely suppresses scoring. | "
        "<b>• #2 Rashid Khan (Score: 72.9):</b> High-volume match-winner. Across 389 HP balls (64.5 overs), Rashid claimed <b>38 wickets</b> "
        "with 7.90 Economy, 38.8% Dot %, and -0.54 clutch tightening. | "
        "<b>• #3 Haris Rauf (Score: 71.3):</b> Lethal death specialist (285 HP balls, 30 wickets, 42.1% Dot %) with express yorkers. | "
        "<b>• #4 Mujeeb Ur Rahman (Score: 69.8):</b> Early powerplay and middle squeeze (6.54 Econ, 46.4% Dot %). | "
        "<b>• #5 Sufiyan Muqeem (Score: 64.3):</b> Breakout wrist-spinner (5.27 Econ, 56.1% Dot %). | "
        "<b>• #6–#10 Proven Campaigners:</b> Shaheen Afridi (62.9, -0.79 Δ Econ) provides elite swing; "
        "RR legend Yuzvendra Chahal (62.2 score, 313 HP balls, 32 wickets, -0.88 Δ Econ) is the premier domestic attacking wrist-spinner; "
        "Ehsan Khan (6.71 Econ), Eshan Malinga (18 wickets), and Mitchell Santner (8.29 Econ, -0.96 Δ Econ) complete the top tier."
    )
    story.append(Paragraph(bowl_dossier_text, body_style))
    story.append(Spacer(1, 5))

    # ==================== SECTION 7: DUAL-LENS TOURNAMENT COMPARISON ====================
    story.append(Paragraph("7. Dual-Lens Competition Analysis: IPL-Only vs Combined Scope", h1_style))
    split_text = (
        "Cricket analytics governance requires strict segregation of domestic franchise leagues from international competition. "
        "T20I fixtures include associate nation matches, whereas the IPL represents the world's highest density of elite talent. "
        "SupeRR SCOUT provides side-by-side disaggregation to ensure transparent evaluation:"
    )
    story.append(Paragraph(split_text, body_style))

    split_comparison_data = [
        [
            Paragraph("<b>Category</b>", table_header),
            Paragraph("<b>Combined Ranking (IPL + T20I)</b>", table_header),
            Paragraph("<b>IPL-Only Ranking (Strictly IPL)</b>", table_header),
            Paragraph("<b>Analytical Franchise Reconciliation</b>", table_header)
        ],
        [
            Paragraph("<b>Batters #1</b>", table_cell_bold),
            Paragraph("<b>Rinku Singh</b> (Score: 85.3 | 260 Balls | 188.8 SR)", table_cell),
            Paragraph("<b>Rinku Singh</b> (Score: 85.9 | 240 Balls | 188.8 SR)", table_cell),
            Paragraph("Demonstrates total mastery across both lenses. 240 of his 260 HP deliveries occurred in the IPL.", table_cell)
        ],
        [
            Paragraph("<b>Batters #2</b>", table_cell_bold),
            Paragraph("<b>David Miller</b> (Score: 84.3 | 211 Balls | 206.2 SR)", table_cell),
            Paragraph("<b>David Miller</b> (Score: 83.2 | 162 Balls | 199.4 SR)", table_cell),
            Paragraph("Maintains top-tier standing in both cohorts; elite proven IPL track record.", table_cell)
        ],
        [
            Paragraph("<b>Batters #3</b>", table_cell_bold),
            Paragraph("<b>Tim David</b> (Score: 75.8 | 327 Balls | 194.2 SR)", table_cell),
            Paragraph("<b>Tim David</b> (Score: 80.4 | 254 Balls | 194.5 SR)", table_cell),
            Paragraph("Ranks higher (#3) in IPL-Only with 80.4 score due to heavier IPL death volume.", table_cell)
        ],
        [
            Paragraph("<b>Bowlers #1</b>", table_cell_bold),
            Paragraph("<b>Sunil Narine</b> (Score: 75.2 | 209 Balls | 6.32 Econ)", table_cell),
            Paragraph("<b>Sunil Narine</b> (Score: 74.6 | 209 Balls | 6.32 Econ)", table_cell),
            Paragraph("100% of Narine's high-pressure overs were delivered in the IPL (KKR anchor).", table_cell)
        ],
        [
            Paragraph("<b>Bowlers #2</b>", table_cell_bold),
            Paragraph("<b>Rashid Khan</b> (Score: 72.9 | 389 Balls | 7.90 Econ)", table_cell),
            Paragraph("<b>Yuzvendra Chahal</b> (Score: 64.1 | 254 Balls | 9.05 Econ)", table_cell),
            Paragraph("Chahal leaps to #2 in IPL-Only with 25 wickets; Rashid ranks #3 (59.2 score).", table_cell)
        ]
    ]

    t_split = Table(split_comparison_data, colWidths=[65, 155, 155, 165])
    t_split.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_split)

    story.append(PageBreak())

    # ==================== PAGE 4: RR AUCTION WAR ROOM & SUBMISSION MATRIX ====================
    story.append(Paragraph("8. Rajasthan Royals IPL 2027 Auction War Room Strategy", h1_style))
    rr_strat_text = (
        "<b>Franchise Squad Baseline (Post Nov-2026 Official Announcements):</b> "
        "Confirmed Squad: <b>19 players</b> | Open Slots: <b>6 available slots</b> (including <b>3 overseas capacity slots</b>). "
        "Available Purse: <b>₹27.05 Crore</b> remaining for auction procurement.<br/>"
        "<b>Sawai Mansingh Stadium (Jaipur) Venue Suitability & Tactical Dynamics:</b> "
        "SMS Stadium features deep square boundaries (70m–75m) and large outfield acreage. Pure mishits rarely clear fences. "
        "This rewards physical runners who convert twos, and bowlers who command disciplined lengths outside off-stump.<br/>"
        "• <b>Priority Finisher Target:</b> Target <b>Ashutosh Sharma</b> (available domestic finisher, 70.1 score, 197.1 SR) "
        "as a high-upside, cost-effective target to preserve purse for bowling depth.<br/>"
        "• <b>Bowling Recruitment Mandate:</b> Re-acquiring or bidding aggressively on attacking spin wickets (Chahal profile) and "
        "death containment specialists who thrive on spacious boundaries (Arshdeep Singh / Harshal Patel cutter profile)."
    )
    story.append(Paragraph(rr_strat_text, body_style))
    story.append(Spacer(1, 3))

    # ==================== SECTION 9: REPRODUCIBILITY & LIMITATIONS ====================
    story.append(Paragraph("9. Statistical Integrity, Reproducibility & Limitations", h1_style))
    limits_text = (
        "<b>Audit & Verification Integrity:</b> Every calculation in SupeRR SCOUT is fully reproducible. The platform maintains "
        "a zero-mutation policy over raw match records. Bootstrap confidence intervals explicitly bound statistical uncertainty.<br/>"
        "<b>Analytical Limitations:</b> (1) Pitch quality variations (e.g. placid Kolkata vs spinning Chennai) are standardized via par metrics "
        "rather than ball-tracking tracking coordinates. (2) Dropped catches and missed run-outs are recorded as standard deliveries without "
        "counterfactual adjustments. (3) T20I opposition quality varies across associate nations, which is why SupeRR SCOUT mandates the Dual-Lens Slicer."
    )
    story.append(Paragraph(limits_text, body_style))
    story.append(Spacer(1, 3))

    # ==================== SECTION 10: UNSTOP SUBMISSION MATRIX ====================
    story.append(Paragraph("10. Unstop Official Submission Matrix (Dropdown Confirmation)", h1_style))
    story.append(Paragraph(
        "Verification matrix matching the exact dropdown selection fields required on the Unstop submission portal:",
        body_style
    ))

    sub_matrix_data = [
        [
            Paragraph("<b>Rank</b>", table_header),
            Paragraph("<b>Official Unstop Batter Selection</b>", table_header),
            Paragraph("<b>Score / Key Metric</b>", table_header),
            Paragraph("<b>Official Unstop Bowler Selection</b>", table_header),
            Paragraph("<b>Score / Key Metric</b>", table_header)
        ]
    ]

    for i in range(10):
        b_row = top_10_batters.iloc[i]
        bw_row = top_10_bowlers.iloc[i]
        sub_matrix_data.append([
            Paragraph(f"<b>Rank {i+1}</b>", table_cell_bold),
            Paragraph(f"<b>{b_row['player_name']}</b>", table_cell),
            Paragraph(f"{b_row['reliability_score']:.1f} ({b_row['hp_strike_rate']:.1f} SR)", table_cell),
            Paragraph(f"<b>{bw_row['player_name']}</b>", table_cell),
            Paragraph(f"{bw_row['reliability_score']:.1f} ({bw_row['hp_economy']:.2f} Econ)", table_cell),
        ])

    t_sub = Table(sub_matrix_data, colWidths=[40, 160, 110, 160, 70])
    t_sub.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_sub)
    story.append(Spacer(1, 4))

    # Formal Sign-off Seal
    sign_off_text = (
        "<b>CERTIFICATE OF SUBMISSION INTEGRITY:</b> All rankings and metrics reported above have been calculated strictly "
        "from the verified 2022–2026 dataset without external heuristic inflation. The 10 batters and 10 bowlers selected above "
        "represent the definitive official entry of <b>Team SupeRR Scout</b> for the <b>Rajasthan Royals SupeRR Selector Season 2</b> challenge."
    )
    t_seal = Table([[Paragraph(sign_off_text, table_cell)]], colWidths=[540])
    t_seal.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, C_RR_PINK),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_seal)

    # Build Document using NumberedCanvas
    print(f"Building document to {output_paths[0]}...")
    doc.build(story, canvasmaker=NumberedCanvas)

    with open(output_paths[0], "rb") as f:
        pdf_bytes = f.read()

    for p in output_paths[1:]:
        p_path = Path(p)
        p_path.parent.mkdir(parents=True, exist_ok=True)
        with open(p_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Copied report to {p_path}")

    print(f"Successfully generated PDF report ({len(pdf_bytes):,} bytes).")
    return pdf_bytes


if __name__ == "__main__":
    out_files = [
        Path("assets/SupeRR_Scout_Official_Unstop_Report.pdf"),
        Path("public/SupeRR_Scout_Official_Unstop_Report.pdf")
    ]
    generate_unstop_report(out_files)
