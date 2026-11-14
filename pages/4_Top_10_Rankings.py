"""
Page 4: Top 10 Rankings & Unstop Submission Dossier
Power BI-Style flagship leaderboards showcasing the definitive Top 10 Batters and Top 10 Bowlers.
Features interactive horizontal bar charts, click cross-filtering, player drilldowns, and Unstop exports.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from src.ui_helpers import (
    inject_custom_css, load_core_data, render_sidebar_filters, filter_deliveries, get_computed_rankings
)
from src.visualizations import (
    apply_rr_theme, plot_top_10_horizontal_bar,
    RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY, RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN
)
from src.player_profiles import build_batter_evidence_card, build_bowler_evidence_card
from src.rankings import generate_unstop_submission_table
from src.report_generator import build_pdf_report
from src.auction_intelligence import compute_auction_rankings
from src.pbi_overview_helpers import build_pbi_leaderboard_chart, build_player_spotlight_card_html

st.set_page_config(page_title="Top 10 Rankings | SupeRR SCOUT", page_icon="🏆", layout="wide")
inject_custom_css()

# Load Core Data
deliveries_df, matches_df = load_core_data()
global_filters = render_sidebar_filters(deliveries_df, matches_df)

bat_ranked, top_10_batters, bowl_ranked, top_10_bowlers = get_computed_rankings(
    deliveries_df, global_filters["min_opportunities"], global_filters["pressure_threshold"]
)

# Compute IPL-only rankings for comparison toggle
@st.cache_data(show_spinner=False)
def get_cached_ipl_rankings(min_opps, thresh):
    rank_dict = compute_auction_rankings(deliveries_df, min_balls=min_opps, pressure_thresh=thresh)
    return rank_dict["batters_ipl"], rank_dict["bowlers_ipl"]

ipl_top_batters, ipl_top_bowlers = get_cached_ipl_rankings(
    global_filters["min_opportunities"], global_filters["pressure_threshold"]
)

# Session State for Top 10 page
if "top10_scope" not in st.session_state:
    st.session_state["top10_scope"] = "Combined (All Matches: IPL, T20I & Emerging T20)"
if "top10_role" not in st.session_state:
    st.session_state["top10_role"] = "🏏 Batters"
if "top10_focus_player" not in st.session_state:
    st.session_state["top10_focus_player"] = None

def handle_clear_top10_focus():
    st.session_state["top10_focus_player"] = None

# ==================== 1. HEADER CARD WITH ACTIVE SLICER CHIPS ====================
focus_p = st.session_state.get("top10_focus_player")
focus_badge = (
    f"<span class='rr-badge' style='background:rgba(243,156,18,0.22); color:#F39C12; border:1px solid #F39C12;'>★ FOCUS: {focus_p}</span>"
    if focus_p else ""
)

st.markdown(f"""
<div class="rr-header-card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <div class="rr-title">4. Top 10 Pressure Reliability Leaderboards</div>
            <div class="rr-subtitle">The official definitive rankings for Rajasthan Royals IPL 2027 Auction Recruitment</div>
        </div>
        <div style="text-align: right; margin-top: 4px;">
            <span class="rr-badge rr-badge-pink" style="font-size: 11px; padding: 4px 12px;">OFFICIAL RR LEADERBOARD</span>
        </div>
    </div>
    <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
        <span style="font-size: 11px; font-weight: 700; color: #A8B3CC; letter-spacing: 0.5px;">ACTIVE PARAMETERS:</span>
        <span class="rr-badge rr-badge-navy">Scope: {st.session_state['top10_scope']}</span>
        <span class="rr-badge {'rr-badge-pink' if 'Batters' in st.session_state['top10_role'] else 'rr-badge-blue'}">Category: {st.session_state['top10_role']}</span>
        <span class="rr-badge rr-badge-gold">HP Threshold: ≥65.0</span>
        <span class="rr-badge rr-badge-navy">Min Opportunities: ≥60 Balls</span>
        {focus_badge}
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== 2. PERSISTENT SLICER PANEL ====================
with st.container():
    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-top: 3px solid #E6007E; 
                border-radius: 12px 12px 0 0; padding: 12px 20px; margin-bottom: 0;">
        <div style="font-size: 13px; font-weight: 800; color: #F7F8FC; letter-spacing: 0.8px;">
            🎛️ TOURNAMENT SCOPE & ROLE SLICERS
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2, col_s3, col_s4 = st.columns([1.8, 1.1, 1.6, 0.8])
    with col_s1:
        scope_choice = st.radio(
            "Tournament Scope",
            options=["Combined (All Matches: IPL, T20I & Emerging T20)", "IPL-Only (Strictly 87,687 Balls)"],
            index=0 if "Combined" in st.session_state["top10_scope"] else 1,
            horizontal=True,
            key="radio_top10_scope"
        )
        if scope_choice != st.session_state["top10_scope"]:
            st.session_state["top10_scope"] = scope_choice
            st.session_state["top10_focus_player"] = None
            st.rerun()

    with col_s2:
        role_choice = st.radio(
            "Player Role",
            options=["🏏 Batters", "🎯 Bowlers"],
            index=0 if "Batters" in st.session_state["top10_role"] else 1,
            horizontal=True,
            key="radio_top10_role"
        )
        if role_choice != st.session_state["top10_role"]:
            st.session_state["top10_role"] = role_choice
            st.session_state["top10_focus_player"] = None
            st.rerun()

    # Determine active dataset
    is_batter = ("Batters" in st.session_state["top10_role"])
    is_combined = ("Combined" in st.session_state["top10_scope"])
    
    if is_batter:
        active_df = top_10_batters if is_combined else ipl_top_batters
    else:
        active_df = top_10_bowlers if is_combined else ipl_top_bowlers

    with col_s3:
        p_names = active_df["player_name"].tolist() if not active_df.empty else []
        p_opts = ["None (All 10)"] + sorted(p_names)
        curr_idx = 0
        if focus_p in p_opts:
            curr_idx = p_opts.index(focus_p)
        sel_spotlight = st.selectbox("Player Spotlight Slicer", p_opts, index=curr_idx, key="sel_top10_player")
        if sel_spotlight == "None (All 10)" and focus_p is not None:
            st.session_state["top10_focus_player"] = None
            st.rerun()
        elif sel_spotlight != "None (All 10)" and sel_spotlight != focus_p:
            st.session_state["top10_focus_player"] = sel_spotlight
            st.rerun()

    with col_s4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Reset", key="btn_reset_top10", use_container_width=True):
            st.session_state["top10_scope"] = "Combined (All Matches: IPL, T20I & Emerging T20)"
            st.session_state["top10_role"] = "🏏 Batters"
            st.session_state["top10_focus_player"] = None
            st.rerun()

st.markdown("<br/>", unsafe_allow_html=True)


# ==================== 3. FOUR DYNAMIC TOP 10 KPI CARDS ====================
k1, k2, k3, k4 = st.columns(4)

top_player = active_df.iloc[0] if not active_df.empty else None
avg_score = active_df["reliability_score"].mean() if not active_df.empty else 0.0
total_hp_balls = int(active_df["hp_balls" if is_batter else "hp_legal_balls"].sum()) if not active_df.empty else 0

with k1:
    top_name = top_player["player_name"] if top_player is not None else "N/A"
    top_scr = top_player["reliability_score"] if top_player is not None else 0.0
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">#1 Ranked { 'Batter' if is_batter else 'Bowler'}</div>
        <div class="rr-kpi-value" style="font-size: 20px; color: {RR_PINK if is_batter else RR_ELECTRIC};">{top_name}</div>
        <div class="{'rr-kpi-sub-pink' if is_batter else 'rr-kpi-sub-blue'}">Score: {top_scr:.1f}/100</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Top 10 Mean Reliability</div>
        <div class="rr-kpi-value">{avg_score:.1f}<span style="font-size:14px; color:#A8B3CC;">/100</span></div>
        <div class="rr-kpi-sub">Elite Cohort Benchmark</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Total HP Deliveries</div>
        <div class="rr-kpi-value">{total_hp_balls:,}</div>
        <div class="{'rr-kpi-sub-pink' if is_batter else 'rr-kpi-sub-blue'}">Delivered Across Top 10</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    if is_batter:
        best_sr_player = active_df.sort_values("hp_strike_rate", ascending=False).iloc[0] if not active_df.empty else None
        st.markdown(f"""
        <div class="rr-kpi-card">
            <div class="rr-kpi-title">Highest HP Strike Rate</div>
            <div class="rr-kpi-value" style="font-size: 19px; color: {RR_GOLD};">{best_sr_player['player_name'] if best_sr_player is not None else 'N/A'}</div>
            <div class="rr-kpi-sub">SR: {best_sr_player['hp_strike_rate']:.1f} under pressure</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        best_econ_player = active_df.sort_values("hp_economy", ascending=True).iloc[0] if not active_df.empty else None
        st.markdown(f"""
        <div class="rr-kpi-card">
            <div class="rr-kpi-title">Tightest HP Economy</div>
            <div class="rr-kpi-value" style="font-size: 19px; color: {RR_GOLD};">{best_econ_player['player_name'] if best_econ_player is not None else 'N/A'}</div>
            <div class="rr-kpi-sub">Econ: {best_econ_player['hp_economy']:.2f} RPO under pressure</div>
        </div>
        """, unsafe_allow_html=True)


# ==================== ACTIVE PLAYER SPOTLIGHT CARD ====================
if focus_p:
    matching = active_df[active_df["player_name"] == focus_p]
    if not matching.empty:
        st.markdown(build_player_spotlight_card_html(matching.iloc[0], is_batter=is_batter), unsafe_allow_html=True)
        col_c1, col_c2 = st.columns([0.85, 0.15])
        with col_c2:
            st.button("❌ Clear Focus", on_click=handle_clear_top10_focus, use_container_width=True)


# ==================== 4. MAIN LEADERBOARD TABS ====================
tab_lead, tab_dossiers, tab_unstop = st.tabs([
    f"🏆 Top 10 { 'Batters' if is_batter else 'Bowlers'} Leaderboard",
    "📁 Individual Evidence Dossiers",
    "📋 Unstop Official Submission Table"
])

with tab_lead:
    st.markdown(f"#### Top 10 { 'Batters' if is_batter else 'Bowlers'} ({st.session_state['top10_scope']})")
    st.caption("Click any bar on the chart to spotlight that player across the war room.")
    
    col_chart, col_tbl = st.columns([1.1, 0.9])
    
    with col_chart:
        fig_bar = build_pbi_leaderboard_chart(active_df, is_batter=is_batter, selected_player=focus_p, top_n=10)
        c_event = st.plotly_chart(fig_bar, on_select="rerun", selection_mode="points", key="top10_chart", use_container_width=True)
        if c_event and c_event.get("selection") and c_event["selection"].get("points"):
            pt = c_event["selection"]["points"][0]
            c_name = pt.get("customdata", [None])[0] if "customdata" in pt else pt.get("y")
            if c_name and c_name != focus_p:
                st.session_state["top10_focus_player"] = c_name
                st.rerun()

    with col_tbl:
        st.markdown("##### Detailed Metric Table")
        if is_batter:
            bat_disp = active_df[[
                "rank", "player_name", "player_id", "reliability_score", "hp_balls",
                "hp_strike_rate", "hp_average", "sr_delta", "confidence_interval"
            ]].copy()
            bat_disp.columns = ["Rank", "Player", "ID", "Score", "HP Balls", "HP SR", "HP Avg", "Δ SR", "95% CI"]
            st.dataframe(bat_disp, use_container_width=True, hide_index=True)
        else:
            bowl_disp = active_df[[
                "rank", "player_name", "player_id", "reliability_score", "hp_legal_balls", "hp_overs",
                "hp_wickets", "hp_economy", "econ_delta", "confidence_interval"
            ]].copy()
            bowl_disp.columns = ["Rank", "Player", "ID", "Score", "HP Balls", "Overs", "Wkts", "HP Econ", "Δ Econ", "95% CI"]
            st.dataframe(bowl_disp, use_container_width=True, hide_index=True)

        csv_bytes = active_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"📥 Download Top 10 { 'Batters' if is_batter else 'Bowlers'} CSV",
            data=csv_bytes,
            file_name=f"Top_10_{'Batters' if is_batter else 'Bowlers'}_{st.session_state['top10_scope'].replace(' ', '_')}.csv",
            mime="text/csv"
        )

with tab_dossiers:
    st.markdown(f"#### 🔍 Official Scouting Dossiers ({ 'Batters' if is_batter else 'Bowlers'})")
    for _, row in active_df.iterrows():
        is_highlighted = bool(focus_p and row["player_name"] == focus_p)
        border_col = RR_GOLD if is_highlighted else (RR_PINK if is_batter else RR_ELECTRIC)
        
        rk = row.get("rank", "N/A")
        pname = row["player_name"]
        score = row["reliability_score"]
        insight = row.get("best_supporting_insight", "")
        ci = row.get("confidence_interval", "")
        cr = row.get("confidence_rating", "High")
        
        with st.expander(f"Rank #{rk} — {pname} (Reliability Score: {score:.1f}) {'★ ACTIVE FOCUS' if is_highlighted else ''}", expanded=is_highlighted):
            c1, c2 = st.columns([1.2, 0.8])
            with c1:
                st.markdown(f"**Official Scouting Insight:**")
                st.markdown(f"{insight}")
                st.markdown(f"**Reliability Rating:** `{score:.1f} / 100` ({cr} — 95% CI `{ci}`)")
            with c2:
                if is_batter:
                    st.markdown(f"• **HP Balls Faced:** {int(row['hp_balls']):,}")
                    st.markdown(f"• **HP Runs:** {int(row['hp_runs']):,}")
                    st.markdown(f"• **HP Strike Rate:** {row['hp_strike_rate']:.1f}")
                    st.markdown(f"• **HP Average:** {row['hp_average']:.1f}")
                    st.markdown(f"• **Clutch Delta (Δ SR):** {row['sr_delta']:+.1f}")
                    st.markdown(f"• **95% Confidence Interval:** `{ci}`")
                else:
                    st.markdown(f"• **HP Legal Balls:** {int(row['hp_legal_balls']):,} ({row['hp_overs']:.1f} ov)")
                    st.markdown(f"• **HP Wickets:** {int(row['hp_wickets']):,}")
                    st.markdown(f"• **HP Economy Rate:** {row['hp_economy']:.2f} RPO")
                    st.markdown(f"• **Clutch Delta (Δ Econ):** {row['econ_delta']:+.2f} RPO")
                    st.markdown(f"• **95% Confidence Interval:** `{ci}`")

with tab_unstop:
    st.markdown("### 📋 Unstop Official Submission Table")
    st.caption("Standardized export format with exact column schema required by the hackathon submission portal.")
    
    unstop_df = generate_unstop_submission_table(top_10_batters, top_10_bowlers)
    st.dataframe(unstop_df, use_container_width=True, hide_index=True)
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        unstop_csv = unstop_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Official Unstop Submission (CSV)",
            data=unstop_csv,
            file_name="SupeRR_Scout_Top10_Submission.csv",
            mime="text/csv"
        )
    with col_u2:
        pdf_path = Path("assets/SupeRR_Scout_Auction_Report.pdf")
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                "📄 Download Executive PDF Dossier (ReportLab)",
                data=pdf_bytes,
                file_name="SupeRR_Scout_Executive_Report.pdf",
                mime="application/pdf"
            )
