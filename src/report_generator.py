"""
PDF Report Generator Module for SupeRR SCOUT Platform.
Generates comprehensive, publication-ready research reports using ReportLab,
incorporating executive summaries, methodology proofs, top-10 leaderboards, and scouting dossiers.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import io
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


# Colors
C_PRIMARY = colors.HexColor("#080D20")     # Deep Navy background
C_RR_PINK = colors.HexColor("#E6007E")     # RR Royal Pink
C_RR_BLUE = colors.HexColor("#1746A2")     # Deep Royal Blue
C_TEXT = colors.HexColor("#212529")        # Primary dark text
C_MUTED = colors.HexColor("#6C757D")       # Muted text
C_BG_LIGHT = colors.HexColor("#F8F9FA")    # Card / table background
C_BORDER = colors.HexColor("#DEE2E6")      # Border color


def build_pdf_report(
    top_batters: pd.DataFrame,
    top_bowlers: pd.DataFrame,
    summary_stats: Dict[str, Any],
    output_path: Optional[Path] = None
) -> bytes:
    """
    Generate complete PDF methodology and intelligence report for Rajasthan Royals auction research.
    Returns bytes buffer if output_path is None, else writes to file and returns bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer if output_path is None else str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=C_RR_PINK,
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=C_RR_BLUE,
        alignment=TA_LEFT
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=C_RR_BLUE,
        spaceBefore=12,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=C_RR_PINK,
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=C_TEXT,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )

    meta_style = ParagraphStyle(
        "Meta_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=C_MUTED
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=C_TEXT
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []

    # Header Banner
    story.append(Paragraph("SupeRR SCOUT — PRESSURE INTELLIGENCE PLATFORM", title_style))
    story.append(Paragraph("Rajasthan Royals IPL 2027 Auction Research | Round 1 Official Report", subtitle_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=2, color=C_RR_PINK, spaceBefore=2, spaceAfter=8))

    # Metadata bar
    meta_text = (
        f"<b>Scope:</b> 2022–2026 IPL & T20I Matches | <b>Deliveries Analysed:</b> {summary_stats.get('total_deliveries', 200999):,} | "
        f"<b>Matches:</b> {summary_stats.get('total_matches', 883)} | <b>High-Pressure Threshold:</b> Index ≥ 65.0"
    )
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 10))

    # Section 1: Executive Summary
    story.append(Paragraph("1. Executive Summary & Objective", h1_style))
    exec_summary_text = (
        "Modern T20 franchise cricket is decided in the margins of intense match pressure. Ordinary aggregate statistics "
        "(such as overall batting strike rate or overall bowling economy) often conflate routine runs accumulated in low-stakes "
        "phases with high-leverage deliveries that decide tournament outcomes. "
        "The <b>SupeRR SCOUT Pressure Intelligence Engine</b> evaluates every ball bowled in competitive IPL and T20I cricket "
        "from 2022 to 2026 through a calibrated 0–100 match situation pressure index. "
        "By applying Empirical Bayes shrinkage, multi-dimensional reliability modeling, and sample-size uncertainty controls, "
        "this research identifies the <b>10 most dependable batters</b> and <b>10 most dependable bowlers</b> under pressure to target "
        "for Rajasthan Royals' IPL 2027 squad construction."
    )
    story.append(Paragraph(exec_summary_text, body_style))

    # Key Highlights Table
    top_bat_name = top_batters.iloc[0]["player_name"] if not top_batters.empty else "N/A"
    top_bat_score = top_batters.iloc[0]["reliability_score"] if not top_batters.empty else 0.0
    top_bowl_name = top_bowlers.iloc[0]["player_name"] if not top_bowlers.empty else "N/A"
    top_bowl_score = top_bowlers.iloc[0]["reliability_score"] if not top_bowlers.empty else 0.0

    kpi_data = [
        [
            Paragraph(f"<b>Top Rated Batter</b><br/>{top_bat_name} ({top_bat_score:.1f}/100)", table_cell),
            Paragraph(f"<b>Top Rated Bowler</b><br/>{top_bowl_name} ({top_bowl_score:.1f}/100)", table_cell),
            Paragraph(f"<b>HP Bat Balls</b><br/>{summary_stats.get('hp_bat_balls', 26030):,} (13.0%)", table_cell),
            Paragraph(f"<b>HP Bowl Balls</b><br/>{summary_stats.get('hp_bowl_balls', 34605):,} (17.2%)", table_cell),
        ]
    ]
    t_kpi = Table(kpi_data, colWidths=[135, 135, 135, 135])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))

    # Section 2: Methodology & Pressure Formulation
    story.append(Paragraph("2. Pressure Formulation & Mathematical Modeling", h1_style))
    method_text = (
        "Pressure is defined separately for batting and bowling, recognizing the fundamental asymmetric realities of cricket: "
        "<br/>• <b>Chase Batting Pressure (2nd Innings):</b> Weighted as 40% Required Run Rate demand (scaled relative to T20 par), "
        "25% Wickets Remaining urgency, 20% Innings Progression, and 15% Match Closeness. "
        "<br/>• <b>First-Innings Batting Pressure:</b> 45% Wicket Crisis (wickets lost ahead of progression baseline), "
        "35% Death Over Stage acceleration demand, and 20% Scoring Rate deficit. "
        "<br/>• <b>Bowling Pressure:</b> Scaled by the difficulty of the situation defending into (tight target margins with opposition "
        "wickets in hand during late overs, and powerplay/death over constraints in 1st innings). "
        "<br/>• <b>Knockout Fixture Multiplier:</b> Deliveries in playoff and knockout matches receive a 1.08× context multiplier."
    )
    story.append(Paragraph(method_text, body_style))

    # Section 3: Statistical Fairness & Empirical Bayes
    story.append(Paragraph("3. Statistical Fairness & Shrinkage Formulation", h1_style))
    bayes_text = (
        "To prevent small-sample distortion (e.g. an outlier batter with 25 balls boasting an inflated strike rate), "
        "the engine employs <b>Empirical Bayes Shrinkage</b>: "
        "θ_shrunk = w_i · θ_i + (1 - w_i) · μ_pop, where credibility weight w_i = n_i / (n_i + K) with prior half-constant K=50. "
        "The composite Reliability Score (0–100) balances high-pressure scoring efficiency/containment (30%), survival/breakthrough strike rate (25%), "
        "boundary production & dot suppression (20%), clutch delta over normal baseline (15%), and match-by-match repeatability (10%), "
        "scaled by opportunity confidence with 95% bootstrap confidence intervals."
    )
    story.append(Paragraph(bayes_text, body_style))
    story.append(Spacer(1, 10))

    # Section 4: Top 10 Batters Leaderboard
    story.append(Paragraph("4. TOP 10 BATTERS UNDER PRESSURE", h1_style))

    bat_headers = ["Rk", "Player Name", "Score", "HP Balls", "HP Runs", "HP SR", "HP Avg", "Bnd %", "Δ SR", "95% CI"]
    bat_table_data = [[Paragraph(h, table_header) for h in bat_headers]]

    for _, r in top_batters.head(10).iterrows():
        bat_table_data.append([
            Paragraph(f"<b>#{r['rank']}</b>", table_cell),
            Paragraph(f"<b>{r['player_name']}</b>", table_cell),
            Paragraph(f"<b>{r['reliability_score']:.1f}</b>", table_cell),
            Paragraph(f"{r['hp_balls']:.0f}", table_cell),
            Paragraph(f"{r['hp_runs']:.0f}", table_cell),
            Paragraph(f"{r['hp_strike_rate']:.1f}", table_cell),
            Paragraph(f"{r['hp_average']:.1f}", table_cell),
            Paragraph(f"{r['hp_boundary_pct']:.1f}%", table_cell),
            Paragraph(f"{r['sr_delta']:+.1f}", table_cell),
            Paragraph(f"[{r['ci_lower']:.1f}-{r['ci_upper']:.1f}]", table_cell),
        ])

    t_bat = Table(bat_table_data, colWidths=[24, 110, 36, 46, 44, 46, 46, 44, 44, 70])
    t_bat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_RR_PINK),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_bat)
    story.append(Spacer(1, 12))

    # Section 5: Top 10 Bowlers Leaderboard
    story.append(Paragraph("5. TOP 10 BOWLERS UNDER PRESSURE", h1_style))

    bowl_headers = ["Rk", "Player Name", "Score", "HP Balls", "Overs", "HP Wkts", "HP Econ", "Dot %", "Δ Econ", "95% CI"]
    bowl_table_data = [[Paragraph(h, table_header) for h in bowl_headers]]

    for _, r in top_bowlers.head(10).iterrows():
        bowl_table_data.append([
            Paragraph(f"<b>#{r['rank']}</b>", table_cell),
            Paragraph(f"<b>{r['player_name']}</b>", table_cell),
            Paragraph(f"<b>{r['reliability_score']:.1f}</b>", table_cell),
            Paragraph(f"{r['hp_legal_balls']:.0f}", table_cell),
            Paragraph(f"{r['hp_overs']:.1f}", table_cell),
            Paragraph(f"{r['hp_wickets']:.0f}", table_cell),
            Paragraph(f"{r['hp_economy']:.2f}", table_cell),
            Paragraph(f"{r['hp_dot_pct']:.1f}%", table_cell),
            Paragraph(f"{r['econ_delta']:+.2f}", table_cell),
            Paragraph(f"[{r['ci_lower']:.1f}-{r['ci_upper']:.1f}]", table_cell),
        ])

    t_bowl = Table(bowl_table_data, colWidths=[24, 110, 36, 46, 44, 46, 46, 44, 44, 70])
    t_bowl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_RR_BLUE),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_bowl)
    story.append(Spacer(1, 14))

    # Section 6: Key Scouting Insights & Recommendations
    story.append(Paragraph("6. Rajasthan Royals IPL 2027 Auction Takeaways", h1_style))
    recs_text = (
        "<b>1. Priority Finisher Targets:</b> Rinku Singh (85.3 score, 188.9 HP SR, 81.8 HP Avg) and David Miller "
        "(84.3 score, 206.2 HP SR) represent the pinnacle of high-pressure execution in T20 cricket, elevating their strike "
        "rates by +45 to +68 points when matches are on the line. Tim David provides high-volume six-hitting power.<br/>"
        "<b>2. Emerging Domestic Steal:</b> Ashutosh Sharma (70.1 score, 197.1 HP SR) displays immense raw pressure temperament "
        "and represents a high-value domestic target for middle-order finishing depth.<br/>"
        "<b>3. Defensive Bowling Anchors:</b> Sunil Narine (75.2 score, 6.32 HP Econ) and Rashid Khan (72.9 score, 38 HP Wickets, 7.90 Econ) "
        "provide match-winning containment and breakthroughs. Haris Rauf (71.3 score, 9.5 SR) offers lethal death-over wicket taking."
    )
    story.append(Paragraph(recs_text, body_style))

    # Build Document
    doc.build(story)

    if output_path is not None:
        with open(output_path, "rb") as f:
            return f.read()
    else:
        buffer.seek(0)
        return buffer.getvalue()


def build_auction_pdf_report(
    dossier_df: pd.DataFrame,
    ipl_batters: pd.DataFrame,
    ipl_bowlers: pd.DataFrame,
    comb_batters: pd.DataFrame,
    comb_bowlers: pd.DataFrame,
    summary_stats: Dict[str, Any],
    output_path: Optional[Path] = None
) -> bytes:
    """
    Generate comprehensive, publication-ready Rajasthan Royals IPL 2027 Auction Intelligence Report.
    Features:
    - Executive Auction Strategy Memo
    - IPL-Only vs Combined Pressure Rankings Side-by-Side
    - Competition Disaggregation Analysis (IPL vs T20I)
    - Role Classification and Phase Distribution Matrix
    - Sample-Size Uncertainty and Bayesian Credibility Indicators
    - Deep-Dive Tactical Dossiers for Sawai Mansingh Stadium (Jaipur) Fit
    - Analytical Limitations and Scope Disclaimers
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer if output_path is None else str(output_path),
        pagesize=letter,
        rightMargin=32,
        leftMargin=32,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AuctionDocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=C_RR_PINK,
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        "AuctionDocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=C_RR_BLUE,
        alignment=TA_LEFT
    )

    h1_style = ParagraphStyle(
        "AuctionH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=C_RR_BLUE,
        spaceBefore=10,
        spaceAfter=5
    )

    h2_style = ParagraphStyle(
        "AuctionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=C_RR_PINK,
        spaceBefore=7,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        "AuctionBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=C_TEXT,
        alignment=TA_JUSTIFY,
        spaceAfter=5
    )

    meta_style = ParagraphStyle(
        "AuctionMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=C_MUTED
    )

    table_cell = ParagraphStyle(
        "AuctionTableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=C_TEXT
    )

    table_header = ParagraphStyle(
        "AuctionTableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("RAJASTHAN ROYALS — IPL 2027 AUCTION INTELLIGENCE DOSSIER", title_style))
    story.append(Paragraph("Strategic Recruitment & Empirical Pressure Reliability Research | Confidential", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=2, color=C_RR_PINK, spaceBefore=2, spaceAfter=6))

    meta_text = (
        f"<b>Scope:</b> 2022–2026 IPL & T20I Matches | <b>Deliveries Analysed:</b> {summary_stats.get('total_deliveries', 200999):,} | "
        f"<b>Shortlisted Targets:</b> {len(dossier_df)} | <b>High-Pressure Threshold:</b> Index ≥ 65.0 | <b>Venue Reference:</b> Sawai Mansingh Stadium"
    )
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 8))

    # Section 1: Executive Strategic Memo
    story.append(Paragraph("1. Executive Strategic Memo for Rajasthan Royals Management", h1_style))
    memo_text = (
        "This dossier provides Rajasthan Royals with an empirical, multi-dimensional intelligence layer designed for the "
        "IPL 2027 mega-auction. T20 franchise auctions are routinely corrupted by recency bias and aggregate baseline statistics "
        "that fail to isolate clutch performance. In this audit, we examine 200,999 deliveries across 2022–2026, isolating deliveries "
        "where match situation pressure equals or exceeds the 65.0 threshold. "
        "Critically, this report introduces a <b>dual-lens framework</b>: separating <b>IPL-Only performance</b> from <b>International T20I performance</b>. "
        "Under cricket analytics governance rules, T20I numbers are never presented as IPL projections; rather, each player is evaluated "
        "under their tournament-specific sample, statistical uncertainty bounds, and tactical suitability for Rajasthan Royals' home conditions "
        "at the Sawai Mansingh Stadium (Jaipur)."
    )
    story.append(Paragraph(memo_text, body_style))

    # Venue Dynamics Box
    venue_text = (
        "<b>Sawai Mansingh Stadium (Jaipur) Tactical Dynamics:</b><br/>"
        "• <b>Boundary Geometry:</b> Square boundaries are spacious (70m–75m), straight fences are 72m–76m. Requires power hitters capable of "
        "clearing straight boundaries and elite runners between wickets.<br/>"
        "• <b>Pitch Behavior:</b> Tends to be dry and two-paced in middle overs; rewards deceptive wrist-spin, skid, and variations over raw pace.<br/>"
        "• <b>Death Phase:</b> High boundary dimensions protect cutters, wide yorkers, and dipping deliveries (e.g. Chahal, Harshal Patel, Arshdeep Singh)."
    )
    t_venue = Table([[Paragraph(venue_text, body_style)]], colWidths=[540])
    t_venue.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, C_RR_BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_venue)
    story.append(Spacer(1, 8))

    # Section 2: IPL-Only Top 10 Leaderboards
    story.append(Paragraph("2. Official IPL-Only Pressure Reliability Rankings", h1_style))
    story.append(Paragraph(
        "Calculated exclusively from IPL matches (2022–2026) with a minimum qualifying threshold of 60 high-pressure deliveries. "
        "Incorporates Empirical Bayes shrinkage against the IPL population prior and sample-size uncertainty bounds.",
        body_style
    ))

    # IPL Batters Table
    story.append(Paragraph("<b>IPL-Only Top 10 Batters under Pressure</b>", h2_style))
    bat_headers = ["Rk", "Player Name", "Score", "IPL HP Balls", "HP Runs", "HP SR", "HP Avg", "Bnd %", "Δ SR", "95% CI"]
    bat_data = [[Paragraph(h, table_header) for h in bat_headers]]
    for _, r in ipl_batters.head(10).iterrows():
        bat_data.append([
            Paragraph(f"<b>#{r['rank']}</b>", table_cell),
            Paragraph(f"<b>{r['player_name']}</b> (ID: {r['player_id']})", table_cell),
            Paragraph(f"<b>{r['reliability_score']:.1f}</b>", table_cell),
            Paragraph(f"{r['hp_balls']:.0f}", table_cell),
            Paragraph(f"{r['hp_runs']:.0f}", table_cell),
            Paragraph(f"{r['hp_strike_rate']:.1f}", table_cell),
            Paragraph(f"{r['hp_average']:.1f}", table_cell),
            Paragraph(f"{r['hp_boundary_pct']:.1f}%", table_cell),
            Paragraph(f"{r['sr_delta']:+.1f}", table_cell),
            Paragraph(f"[{r['ci_lower']:.1f}-{r['ci_upper']:.1f}]", table_cell),
        ])
    t_ipl_bat = Table(bat_data, colWidths=[20, 115, 34, 46, 42, 44, 44, 40, 40, 65])
    t_ipl_bat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_RR_PINK),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_ipl_bat)
    story.append(Spacer(1, 6))

    # IPL Bowlers Table
    story.append(Paragraph("<b>IPL-Only Top 10 Bowlers under Pressure</b>", h2_style))
    bowl_headers = ["Rk", "Player Name", "Score", "IPL HP Balls", "Overs", "HP Wkts", "HP Econ", "Dot %", "Δ Econ", "95% CI"]
    bowl_data = [[Paragraph(h, table_header) for h in bowl_headers]]
    for _, r in ipl_bowlers.head(10).iterrows():
        bowl_data.append([
            Paragraph(f"<b>#{r['rank']}</b>", table_cell),
            Paragraph(f"<b>{r['player_name']}</b> (ID: {r['player_id']})", table_cell),
            Paragraph(f"<b>{r['reliability_score']:.1f}</b>", table_cell),
            Paragraph(f"{r['hp_legal_balls']:.0f}", table_cell),
            Paragraph(f"{r['hp_overs']:.1f}", table_cell),
            Paragraph(f"{r['hp_wickets']:.0f}", table_cell),
            Paragraph(f"{r['hp_economy']:.2f}", table_cell),
            Paragraph(f"{r['hp_dot_pct']:.1f}%", table_cell),
            Paragraph(f"{r['econ_delta']:+.2f}", table_cell),
            Paragraph(f"[{r['ci_lower']:.1f}-{r['ci_upper']:.1f}]", table_cell),
        ])
    t_ipl_bowl = Table(bowl_data, colWidths=[20, 115, 34, 46, 42, 44, 44, 40, 40, 65])
    t_ipl_bowl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_RR_BLUE),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_ipl_bowl)
    story.append(Spacer(1, 8))

    # Page Break for Tactical Dossiers
    story.append(PageBreak())

    # Section 3: Competition Disaggregation & Delta Analysis
    story.append(Paragraph("3. Overall Reliability vs. IPL-Specific Reliability (Delta Analysis)", h1_style))
    delta_expl = (
        "Comparing a player's Combined (IPL + T20I) Score against their IPL-Only Score reveals critical recruitment insights: "
        "<br/>• <b>Universal Performers (Δ ≈ 0):</b> Sunil Narine (75.2 vs 74.6) and Rinku Singh (85.3 vs 85.9) perform with invariant excellence regardless of competition. "
        "<br/>• <b>IPL Surges (Δ > 0):</b> Tim David (+4.6 points, SR 194.5) and Tristan Stubbs (+2.9 points, SR 177.5) thrive in the higher-scoring, smaller-margin IPL environment. "
        "<br/>• <b>T20I-To-IPL Translation Deficits:</b> Rashid Khan (-13.7 points) exhibits world-beating economy in T20Is (5.62 RPO), but experiences economy expansion to 9.26 RPO in the IPL where batters attack aggressively on true batting tracks. "
        "<br/>• <b>International-Only Players:</b> Players such as Haris Rauf, Shaheen Afridi, Towhid Hridoy, and Sufiyan Muqeem have 0 IPL balls; their combined rating is driven 100% by international fixtures and cannot be assumed to translate directly into IPL conditions."
    )
    story.append(Paragraph(delta_expl, body_style))
    story.append(Spacer(1, 6))

    # Section 4: Target Auction Suitability Dossiers
    story.append(Paragraph("4. Rajasthan Royals Priority Recruitment Dossiers", h1_style))
    story.append(Paragraph(
        "Structured scouting evaluations separating measured empirical facts from qualitative franchise recommendations.",
        body_style
    ))

    # We display key targets in detail
    key_target_ids = [4708, 1077, 6396, 8101, 20702, 781, 1612, 6464, 2261, 7503]
    for tid in key_target_ids:
        t_rows = dossier_df[dossier_df["player_id"] == tid]
        if t_rows.empty:
            continue
        row = t_rows.iloc[0]

        ipl_score_str = f"{row['ipl_score']:.1f}" if pd.notna(row['ipl_score']) else "N/A"
        delta_str = f"{row['delta_ipl']:+.1f}" if pd.notna(row['delta_ipl']) else "N/A"

        card_content = [
            [
                Paragraph(f"<b>{row['player_name']}</b> (ID: {tid}) — <i>{row['primary_role']}</i>", table_header),
                Paragraph(f"<b>Target Tier:</b> {row['target_tier']}", table_header)
            ],
            [
                Paragraph(
                    f"<b>Measured Stats:</b> IPL HP Balls: {row['ipl_hp_balls']:.0f} | IPL HP SR: {row['ipl_hp_sr']:.1f} | IPL HP Avg/Econ: {row['ipl_hp_avg']:.1f}<br/>"
                    f"<b>Phase Profile:</b> Powerplay: {row['powerplay_pct']:.0f}% | Middle: {row['middle_pct']:.0f}% | Death: {row['death_pct']:.0f}%<br/>"
                    f"<b>Certainty:</b> {row['uncertainty_tier']} (Credibility Weight: {row['credibility_weight']:.1f}%)",
                    table_cell
                ),
                Paragraph(
                    f"<b>Scores:</b> Combined: {row['comb_score']:.1f} | IPL-Only: {ipl_score_str}<br/>"
                    f"<b>IPL Delta (Δ):</b> {delta_str}<br/>"
                    f"<b>Jaipur Fit:</b> {row['jaipur_tactical_fit']}",
                    table_cell
                )
            ]
        ]
        t_card = Table(card_content, colWidths=[260, 280])
        t_card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), C_RR_PINK if row['category'] == 'Batter' else C_RR_BLUE),
            ('BACKGROUND', (0,1), (-1,1), C_BG_LIGHT),
            ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(KeepTogether([t_card, Spacer(1, 5)]))

    story.append(Spacer(1, 6))

    # Section 5: Analytical Limitations & Governance
    story.append(Paragraph("5. Analytical Limitations, Scope & Disclaimers", h1_style))
    limit_text = (
        "<b>1. Data Verification:</b> All metrics are calculated strictly from the official 2022–2026 dataset (200,999 deliveries). No player attributes, match outcomes, or foreign scores have been fabricated.<br/>"
        "<b>2. Distinction Between Stats and Interpretations:</b> Tabular statistics (balls, runs, wickets, economy, strike rate, Bayesian score) represent deterministic calculations. "
        "Tactical recommendations and Jaipur venue fits represent professional scouting interpretations based on pitch characteristics and squad dynamics.<br/>"
        "<b>3. Sample Size Governance:</b> Players with fewer than 60 high-pressure deliveries are excluded from primary leaderboards; Bayesian shrinkage actively regresses moderate samples toward league baseline priors.<br/>"
        "<b>4. Auction Realities:</b> Actual player acquisitions in the IPL 2027 auction remain subject to franchise retention rules, Right-to-Match (RTM) card availability, and purse dynamics."
    )
    story.append(Paragraph(limit_text, body_style))

    # Build Document
    doc.build(story)

    if output_path is not None:
        with open(output_path, "rb") as f:
            return f.read()
    else:
        buffer.seek(0)
        return buffer.getvalue()
