"""
SupeRR SCOUT — Pressure Intelligence Platform
Rajasthan Royals IPL 2027 Auction Research
Main Streamlit Application Entry Point
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from src.ui_helpers import (
    inject_custom_css, load_core_data, render_sidebar_filters, filter_deliveries, get_computed_rankings
)
from src.visualizations import plot_pressure_distribution, plot_top_10_horizontal_bar
from src.report_generator import build_pdf_report

st.set_page_config(
    page_title="SupeRR SCOUT | Rajasthan Royals Intel",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_custom_css()

# Load Data
deliveries_df, matches_df = load_core_data()
filters = render_sidebar_filters(deliveries_df, matches_df)
filtered_df = filter_deliveries(deliveries_df, filters)

# Compute Rankings
bat_ranked, top_10_batters, bowl_ranked, top_10_bowlers = get_computed_rankings(
    filtered_df, filters["min_opportunities"], filters["pressure_threshold"]
)

# Header Banner
st.markdown("""
<div class="rr-header-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="rr-title">SupeRR SCOUT — Pressure Intelligence Engine</div>
            <div class="rr-subtitle">Rajasthan Royals IPL 2027 Auction Research | Confidential Intelligence Platform</div>
        </div>
        <div style="text-align: right;">
            <span class="rr-badge rr-badge-pink">SEASON 2 HACKATHON</span>
            <span class="rr-badge rr-badge-blue">2022–2026 ARCHIVE</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Executive KPI Grid
total_deliveries = len(filtered_df)
total_matches = filtered_df["match_id"].nunique()
hp_bat_deliveries = filtered_df["is_high_pressure_bat"].sum()
hp_bowl_deliveries = filtered_df["is_high_pressure_bowl"].sum()
eligible_batters = (bat_ranked["hp_balls"] >= filters["min_opportunities"]).sum()
eligible_bowlers = (bowl_ranked["hp_legal_balls"] >= filters["min_opportunities"]).sum()

top_batter = top_10_batters.iloc[0] if not top_10_batters.empty else None
top_bowler = top_10_bowlers.iloc[0] if not top_10_bowlers.empty else None

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Matches Analysed</div>
        <div class="rr-kpi-value">{total_matches:,}</div>
        <div class="rr-kpi-sub">Across {len(filters['seasons'])} Seasons</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Deliveries Processed</div>
        <div class="rr-kpi-value">{total_deliveries:,}</div>
        <div class="rr-kpi-sub-pink">{hp_bat_deliveries:,} HP Bat Balls ({hp_bat_deliveries/max(1, total_deliveries)*100:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    bat_name = top_batter["player_name"] if top_batter is not None else "N/A"
    bat_score = top_batter["reliability_score"] if top_batter is not None else 0.0
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Top Rated Batter</div>
        <div class="rr-kpi-value" style="font-size: 19px; color: #E6007E;">{bat_name}</div>
        <div class="rr-kpi-sub-pink">Score: {bat_score:.1f}/100 (CI: {top_batter['confidence_interval'] if top_batter is not None else ''})</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    bowl_name = top_bowler["player_name"] if top_bowler is not None else "N/A"
    bowl_score = top_bowler["reliability_score"] if top_bowler is not None else 0.0
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Top Rated Bowler</div>
        <div class="rr-kpi-value" style="font-size: 19px; color: #287BFF;">{bowl_name}</div>
        <div class="rr-kpi-sub-blue">Score: {bowl_score:.1f}/100 (CI: {top_bowler['confidence_interval'] if top_bowler is not None else ''})</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# Overview Showcase Columns
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.markdown("### 🏆 Top 5 Clutch Batters & Bowlers")
    tab_bat, tab_bowl = st.tabs(["Top Batters under Pressure", "Top Bowlers under Pressure"])

    with tab_bat:
        if not top_10_batters.empty:
            st.plotly_chart(
                plot_top_10_horizontal_bar(top_10_batters.head(5), "Top 5 Batters by Pressure Reliability", is_batter=True),
                use_container_width=True
            )
            # Mini table
            disp_bat = top_10_batters.head(5)[["rank", "player_name", "reliability_score", "hp_runs", "hp_strike_rate", "hp_average", "sr_delta"]]
            disp_bat.columns = ["Rank", "Player", "Score", "HP Runs", "HP SR", "HP Avg", "SR Delta"]
            st.dataframe(disp_bat, use_container_width=True, hide_index=True)

    with tab_bowl:
        if not top_10_bowlers.empty:
            st.plotly_chart(
                plot_top_10_horizontal_bar(top_10_bowlers.head(5), "Top 5 Bowlers by Pressure Reliability", is_batter=False),
                use_container_width=True
            )
            disp_bowl = top_10_bowlers.head(5)[["rank", "player_name", "reliability_score", "hp_wickets", "hp_economy", "hp_dot_pct", "econ_delta"]]
            disp_bowl.columns = ["Rank", "Player", "Score", "HP Wkts", "HP Econ", "Dot %", "Econ Delta"]
            st.dataframe(disp_bowl, use_container_width=True, hide_index=True)

with col_right:
    st.markdown("### 📈 Match Pressure Dynamics")
    st.plotly_chart(
        plot_pressure_distribution(filtered_df, threshold=filters["pressure_threshold"]),
        use_container_width=True
    )

    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-radius: 10px; padding: 16px 20px; box-shadow: 0 4px 14px rgba(8,13,32,0.6);">
        <div style="font-weight: 700; color: #E6007E; font-size: 13px; margin-bottom: 6px; letter-spacing: 0.5px;">
            PLATFORM CAPABILITIES & NAVIGATION
        </div>
        <div style="font-size: 12px; color: #A8B3CC; line-height: 1.5;">
            Explore the pages in the sidebar for in-depth intelligence:<br/>
            • <b>1. Executive Overview:</b> Macro indicators, tournament splits, methodology summary.<br/>
            • <b>2. Batting Intelligence:</b> Complete leaderboard, efficiency scatter plots, match logs.<br/>
            • <b>3. Bowling Intelligence:</b> Containment vs strike-rate matrix, economy deltas.<br/>
            • <b>4. Top 10 Rankings:</b> Official leaderboards, scouting dossiers, and Unstop export.<br/>
            • <b>5. Player Comparison:</b> Head-to-head radar comparison across 5 dimensions.<br/>
            • <b>6. Match Situations:</b> Phase splits, required run-rate stress, turning points.<br/>
            • <b>7. Methodology:</b> Complete mathematical formulations and sensitivity controls.<br/>
            • <b>8. Auction Intelligence:</b> IPL-only rankings, competition splits, role fingerprints, and RR tactical dossiers.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Quick Exports Bar
st.markdown("### 📥 Quick Intelligence Exports")
exp_c1, exp_c2, exp_c3, exp_c4 = st.columns(4)

with exp_c1:
    bat_csv = top_10_batters.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📄 Export Top 10 Batters (CSV)",
        data=bat_csv,
        file_name="RR_Top_10_Batters_Pressure.csv",
        mime="text/csv",
        use_container_width=True
    )

with exp_c2:
    bowl_csv = top_10_bowlers.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📄 Export Top 10 Bowlers (CSV)",
        data=bowl_csv,
        file_name="RR_Top_10_Bowlers_Pressure.csv",
        mime="text/csv",
        use_container_width=True
    )

with exp_c3:
    summary_stats = {
        "total_deliveries": total_deliveries,
        "total_matches": total_matches,
        "hp_bat_balls": hp_bat_deliveries,
        "hp_bowl_balls": hp_bowl_deliveries
    }
    pdf_bytes = build_pdf_report(top_10_batters, top_10_bowlers, summary_stats)
    st.download_button(
        "📑 Download Research Report (PDF)",
        data=pdf_bytes,
        file_name="SupeRR_SCOUT_Pressure_Intelligence_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )

with exp_c4:
    auction_pdf_path = Path("assets/RR_IPL_2027_Auction_Intelligence_Report.pdf")
    if auction_pdf_path.exists():
        with open(auction_pdf_path, "rb") as f:
            auc_pdf_bytes = f.read()
    else:
        auc_pdf_bytes = pdf_bytes
    st.download_button(
        "🏰 Download Auction Dossier (PDF)",
        data=auc_pdf_bytes,
        file_name="RR_IPL_2027_Auction_Intelligence_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )


# Vercel serverless function entrypoint compatibility
def handler(request=None, response=None):
    """Fallback entrypoint for serverless runtimes (e.g. Vercel)."""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": "<h1>SupeRR SCOUT</h1><p>Live platform running. Please visit the web portal.</p>"
    }

app = handler
application = handler
