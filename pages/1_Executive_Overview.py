"""
Page 1: Executive Overview — Power BI-Style Interactive Analytics War Room
Reference Design for SupeRR Scout 3.0 Platform.
Features cross-filtering, 6 responsive Plotly visuals, dynamic KPI cards,
and persistent multi-dimensional slicers.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.ui_helpers import (
    inject_custom_css, load_core_data, render_sidebar_filters, filter_deliveries, get_computed_rankings
)
from src.visualizations import (
    apply_rr_theme, plot_role_distribution, RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY,
    RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN, GRID_COLOR
)
from src.pbi_overview_helpers import (
    build_pbi_leaderboard_chart, build_pbi_scatter_chart, build_pbi_heatmap_chart,
    build_pbi_comp_comparison_chart, build_pbi_distribution_chart, build_pbi_season_trends_chart,
    build_player_spotlight_card_html, generate_executive_insights
)
from src.auction_intelligence import generate_all_auction_assets
from pathlib import Path

st.set_page_config(
    page_title="Executive Overview | SupeRR SCOUT",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_custom_css()

# Load Core Datasets
deliveries_df, matches_df = load_core_data()

# Render Global Sidebar Filters
global_filters = render_sidebar_filters(deliveries_df, matches_df)

# ==================== SESSION STATE FOR POWER BI SLICERS ====================
if "pbi_category" not in st.session_state:
    st.session_state["pbi_category"] = "🏏 Batters"
if "pbi_comp" not in st.session_state:
    st.session_state["pbi_comp"] = "All Competitions"
if "pbi_phase" not in st.session_state:
    st.session_state["pbi_phase"] = "All Phases"
if "pbi_seasons" not in st.session_state:
    st.session_state["pbi_seasons"] = []
if "pbi_threshold" not in st.session_state:
    st.session_state["pbi_threshold"] = 65.0
if "pbi_min_opps" not in st.session_state:
    st.session_state["pbi_min_opps"] = 60
if "pbi_focus_player" not in st.session_state:
    st.session_state["pbi_focus_player"] = None

# Slicer callbacks
def handle_reset_filters():
    st.session_state["pbi_category"] = "🏏 Batters"
    st.session_state["pbi_comp"] = "All Competitions"
    st.session_state["pbi_phase"] = "All Phases"
    st.session_state["pbi_seasons"] = []
    st.session_state["pbi_threshold"] = 65.0
    st.session_state["pbi_min_opps"] = 60
    st.session_state["pbi_focus_player"] = None

def handle_clear_focus():
    st.session_state["pbi_focus_player"] = None


# ==================== 1. PREMIUM EXECUTIVE HEADER ====================
is_batter = (st.session_state["pbi_category"] == "🏏 Batters")
focus_player = st.session_state.get("pbi_focus_player")

focus_badge = (
    f"<span class='rr-badge' style='background:rgba(243,156,18,0.22); color:#F39C12; border:1px solid #F39C12;'>★ FOCUS: {focus_player}</span>"
    if focus_player else ""
)

season_count = len(st.session_state["pbi_seasons"]) if st.session_state["pbi_seasons"] else "All"

st.markdown(f"""
<div class="rr-header-card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <div class="rr-title">1. Executive Overview — Pressure Intelligence Platform</div>
            <div class="rr-subtitle">Power BI-Style Franchise Analytics War Room | Cross-Filtered Tournament Dynamics</div>
        </div>
        <div style="text-align: right; margin-top: 4px;">
            <span class="rr-badge rr-badge-pink" style="font-size: 11px; padding: 4px 12px;">RR IPL 2027 WAR ROOM</span>
        </div>
    </div>
    <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
        <span style="font-size: 11px; font-weight: 700; color: #A8B3CC; letter-spacing: 0.5px;">ACTIVE SLICERS:</span>
        <span class="rr-badge {'rr-badge-pink' if is_batter else 'rr-badge-blue'}">{st.session_state['pbi_category']}</span>
        <span class="rr-badge rr-badge-navy">Scope: {st.session_state['pbi_comp']}</span>
        <span class="rr-badge rr-badge-gold">Phase: {st.session_state['pbi_phase']}</span>
        <span class="rr-badge rr-badge-navy">Seasons: {season_count}</span>
        <span class="rr-badge rr-badge-navy">Threshold: ≥{st.session_state['pbi_threshold']:.0f}</span>
        {focus_badge}
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== 2. PERSISTENT POWER BI-STYLE FILTER PANEL ====================
with st.container():
    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-top: 3px solid #1746A2; 
                border-radius: 12px 12px 0 0; padding: 12px 20px; margin-bottom: 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 13px; font-weight: 800; color: #F7F8FC; letter-spacing: 0.8px;">
                🎛️ POWER BI INTERACTIVE SLICER PANEL
            </div>
            <div style="font-size: 11px; color: #A8B3CC;">
                Multi-dimensional cross-filtering | Real-time synchronized visuals
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    slicer_box = st.container()
    with slicer_box:
        # Slicer Row 1: Primary Dimensions
        col_cat, col_comp, col_phase, col_seas = st.columns([1.1, 1.2, 1.2, 1.5])
        
        with col_cat:
            cat_choice = st.radio(
                "Player Role",
                options=["🏏 Batters", "🎯 Bowlers"],
                index=0 if st.session_state["pbi_category"] == "🏏 Batters" else 1,
                horizontal=True,
                key="radio_pbi_cat"
            )
            if cat_choice != st.session_state["pbi_category"]:
                st.session_state["pbi_category"] = cat_choice
                st.session_state["pbi_focus_player"] = None
                st.rerun()

        with col_comp:
            comp_options = ["All Competitions", "IPL Only", "T20I Only", "Other T20"]
            comp_choice = st.selectbox(
                "Competition Slicer",
                options=comp_options,
                index=comp_options.index(st.session_state["pbi_comp"]),
                key="sel_pbi_comp"
            )
            if comp_choice != st.session_state["pbi_comp"]:
                st.session_state["pbi_comp"] = comp_choice
                st.session_state["pbi_focus_player"] = None
                st.rerun()

        with col_phase:
            phase_options = ["All Phases", "Death (17-20)", "Middle (7-16)", "Powerplay (1-6)"]
            phase_choice = st.selectbox(
                "Match Phase Slicer",
                options=phase_options,
                index=phase_options.index(st.session_state["pbi_phase"]),
                key="sel_pbi_phase"
            )
            if phase_choice != st.session_state["pbi_phase"]:
                st.session_state["pbi_phase"] = phase_choice
                st.session_state["pbi_focus_player"] = None
                st.rerun()

        with col_seas:
            available_seasons = sorted(deliveries_df["season"].dropna().unique().tolist())
            seas_choice = st.multiselect(
                "Seasons Slicer",
                options=available_seasons,
                default=st.session_state["pbi_seasons"],
                placeholder="All Available Seasons (2022–2026)",
                key="sel_pbi_seasons"
            )
            if seas_choice != st.session_state["pbi_seasons"]:
                st.session_state["pbi_seasons"] = seas_choice
                st.rerun()

        # Slicer Row 2: Thresholds, Player Drill-Through & Reset
        col_thresh, col_opps, col_player, col_action = st.columns([1.3, 1.2, 1.7, 0.8])
        
        with col_thresh:
            thresh_choice = st.slider(
                "Pressure Threshold (HP Index)",
                min_value=50.0,
                max_value=85.0,
                value=float(st.session_state["pbi_threshold"]),
                step=5.0,
                key="slider_pbi_thresh",
                help="Defines high-pressure deliveries. Default benchmark: 65.0."
            )
            if thresh_choice != st.session_state["pbi_threshold"]:
                st.session_state["pbi_threshold"] = thresh_choice
                st.rerun()

        with col_opps:
            opps_choice = st.slider(
                "Min HP Deliveries",
                min_value=20,
                max_value=120,
                value=int(st.session_state["pbi_min_opps"]),
                step=10,
                key="slider_pbi_opps",
                help="Minimum high-pressure balls faced/bowled for qualification."
            )
            if opps_choice != st.session_state["pbi_min_opps"]:
                st.session_state["pbi_min_opps"] = opps_choice
                st.rerun()

# Apply Filters to deliveries_df
filtered_df = deliveries_df.copy()
if st.session_state["pbi_comp"] == "IPL Only":
    filtered_df = filtered_df[filtered_df["is_ipl"]]
elif st.session_state["pbi_comp"] == "T20I Only":
    filtered_df = filtered_df[filtered_df["match_format"] == "T20I"]
elif st.session_state["pbi_comp"] == "Other T20":
    filtered_df = filtered_df[filtered_df["competition_type"] == "Other T20"]

if st.session_state["pbi_phase"] == "Death (17-20)":
    filtered_df = filtered_df[filtered_df["is_death"]]
elif st.session_state["pbi_phase"] == "Middle (7-16)":
    filtered_df = filtered_df[filtered_df["is_middle"]]
elif st.session_state["pbi_phase"] == "Powerplay (1-6)":
    filtered_df = filtered_df[filtered_df["is_powerplay"]]

if st.session_state["pbi_seasons"]:
    filtered_df = filtered_df[filtered_df["season"].isin(st.session_state["pbi_seasons"])]

# Re-apply threshold
thresh = st.session_state["pbi_threshold"]
min_opps = st.session_state["pbi_min_opps"]
filtered_df["is_high_pressure_bat"] = filtered_df["pressure_batting"] >= thresh
filtered_df["is_high_pressure_bowl"] = filtered_df["pressure_bowling"] >= thresh

# Compute rankings for filtered slice
bat_ranked, top_10_batters, bowl_ranked, top_10_bowlers = get_computed_rankings(
    filtered_df, min_opps, thresh
)
active_ranked = bat_ranked if is_batter else bowl_ranked

# Populate player search options based on current qualified cohort
eligible_players = active_ranked[active_ranked["is_eligible"]]["player_name"].tolist()
if not eligible_players:
    eligible_players = active_ranked.head(30)["player_name"].tolist()

with col_player:
    player_options = ["None (All Cohort)"] + sorted(eligible_players)
    current_player_idx = 0
    if st.session_state["pbi_focus_player"] in player_options:
        current_player_idx = player_options.index(st.session_state["pbi_focus_player"])
        
    p_select = st.selectbox(
        "Player Spotlight Slicer",
        options=player_options,
        index=current_player_idx,
        key="sel_pbi_player",
        help="Select a specific player to highlight across all 6 visualizations."
    )
    if p_select == "None (All Cohort)" and st.session_state["pbi_focus_player"] is not None:
        st.session_state["pbi_focus_player"] = None
        st.rerun()
    elif p_select != "None (All Cohort)" and p_select != st.session_state["pbi_focus_player"]:
        st.session_state["pbi_focus_player"] = p_select
        st.rerun()

with col_action:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    st.button("🔄 Reset", on_click=handle_reset_filters, use_container_width=True, help="Reset all slicers and drill-throughs")

st.markdown("<br/>", unsafe_allow_html=True)


# ==================== 3. FOUR DYNAMIC KPI CARDS ====================
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

qualified_cohort = active_ranked[active_ranked["is_eligible"]]
players_eval = len(qualified_cohort)
deliveries_eval = len(filtered_df)
avg_reliability = qualified_cohort["reliability_score"].mean() if not qualified_cohort.empty else 0.0
hp_sample_size = int(filtered_df["is_high_pressure_bat" if is_batter else "is_high_pressure_bowl"].sum())
hp_pct = (hp_sample_size / max(1, deliveries_eval)) * 100.0

with kpi1:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Players Evaluated</div>
        <div class="rr-kpi-value">{players_eval:,}</div>
        <div class="{'rr-kpi-sub-pink' if is_batter else 'rr-kpi-sub-blue'}">
            Qualified (≥{min_opps} HP Balls)
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Deliveries Evaluated</div>
        <div class="rr-kpi-value">{deliveries_eval:,}</div>
        <div class="rr-kpi-sub">
            Across {filtered_df['match_id'].nunique()} Reconstructed Fixtures
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Average Reliability Score</div>
        <div class="rr-kpi-value">{avg_reliability:.1f}<span style="font-size:16px; color:#A8B3CC;">/100</span></div>
        <div class="rr-kpi-sub">
            Bayesian Credibility Cohort Mean
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">High-Pressure Sample Size</div>
        <div class="rr-kpi-value">{hp_sample_size:,}</div>
        <div class="{'rr-kpi-sub-pink' if is_batter else 'rr-kpi-sub-blue'}">
            {hp_pct:.1f}% of Slice (Pressure ≥{thresh:.0f})
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==================== DYNAMIC EXECUTIVE INSIGHTS PANEL ====================
exec_insights = generate_executive_insights(active_ranked, is_batter, filtered_df)
if exec_insights:
    insights_html = "<br/>".join([f"• {ins}" for ins in exec_insights])
    st.markdown(f"""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-left: 4px solid {'#E6007E' if is_batter else '#287BFF'}; 
                border-radius: 10px; padding: 14px 20px; margin-top: 14px; margin-bottom: 10px; box-shadow: 0 4px 16px rgba(8,13,32,0.6);">
        <div style="font-size: 13px; font-weight: 800; color: #F7F8FC; margin-bottom: 6px; letter-spacing: 0.5px;">
            🧠 EVIDENCE-BASED EXECUTIVE INTELLIGENCE
        </div>
        <div style="font-size: 12px; color: #A8B3CC; line-height: 1.6;">
            {insights_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==================== ACTIVE PLAYER SPOTLIGHT (IF CROSS-FILTERED) ====================
if focus_player:
    matching_rows = active_ranked[active_ranked["player_name"] == focus_player]
    if not matching_rows.empty:
        focus_row = matching_rows.iloc[0]
        st.markdown(build_player_spotlight_card_html(focus_row, is_batter), unsafe_allow_html=True)
        col_sp_left, col_sp_right = st.columns([0.85, 0.15])
        with col_sp_right:
            st.button("❌ Clear Focus", on_click=handle_clear_focus, use_container_width=True)


# ==================== 4. SIX MAIN EXECUTIVE VISUALIZATIONS ====================
# Layout: Professional Two-Column Interactive Grid
st.markdown("### 📊 Interactive Visual Intelligence Grid")
st.caption("Click any bar in the Leaderboard to cross-filter compatible charts and highlight player trajectories across the war room.")

# ROW 1: Visual A (Leaderboard) & Visual B (Scatter Plot)
col_r1_left, col_r1_right = st.columns(2)

with col_r1_left:
    fig_lead = build_pbi_leaderboard_chart(
        active_ranked,
        is_batter=is_batter,
        selected_player=focus_player,
        top_n=10
    )
    # Native Streamlit 1.67+ selection handling
    lead_select = st.plotly_chart(
        fig_lead,
        on_select="rerun",
        selection_mode="points",
        key="pbi_lead_chart",
        use_container_width=True
    )
    
    # Process bar chart clicks
    if lead_select and lead_select.get("selection") and lead_select["selection"].get("points"):
        clicked_pt = lead_select["selection"]["points"][0]
        clicked_name = None
        if "customdata" in clicked_pt and len(clicked_pt["customdata"]) > 0:
            clicked_name = clicked_pt["customdata"][0]
        elif "y" in clicked_pt:
            clicked_name = clicked_pt["y"]
            
        if clicked_name and clicked_name != focus_player:
            st.session_state["pbi_focus_player"] = clicked_name
            st.rerun()

with col_r1_right:
    fig_scat = build_pbi_scatter_chart(
        active_ranked,
        is_batter=is_batter,
        selected_player=focus_player
    )
    st.plotly_chart(fig_scat, use_container_width=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ROW 2: Visual C (Pressure Heatmap) & Visual D (Competition Comparison)
col_r2_left, col_r2_right = st.columns(2)

with col_r2_left:
    fig_heat = build_pbi_heatmap_chart(
        filtered_df,
        active_ranked,
        is_batter=is_batter,
        selected_player=focus_player,
        top_n=8
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with col_r2_right:
    fig_comp = build_pbi_comp_comparison_chart(
        filtered_df,
        is_batter=is_batter
    )
    st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ROW 3: Visual E (Player & Phase Distribution) & Visual F (Historical Season Trends)
col_r3_left, col_r3_right = st.columns(2)

with col_r3_left:
    tab_dist_phase, tab_dist_role = st.tabs(["⏱️ Match Phase Breakdown", "🎯 Tactical Role Breakdown"])
    with tab_dist_phase:
        fig_dist = build_pbi_distribution_chart(
            filtered_df,
            is_batter=is_batter
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    with tab_dist_role:
        assets = generate_all_auction_assets(deliveries_df, Path("assets"))
        dossier_data = assets["dossier"]
        cat_dossier = dossier_data[dossier_data["category"] == ("Batter" if is_batter else "Bowler")]
        fig_roles = plot_role_distribution(cat_dossier if not cat_dossier.empty else dossier_data)
        st.plotly_chart(fig_roles, use_container_width=True)

with col_r3_right:
    fig_trend = build_pbi_season_trends_chart(
        filtered_df,
        is_batter=is_batter,
        selected_player=focus_player
    )
    st.plotly_chart(fig_trend, use_container_width=True)


# ==================== DATA EXPORT & AUDIT FOOTER ====================
st.markdown("---")
col_exp_left, col_exp_right = st.columns([1.2, 0.8])

with col_exp_left:
    st.markdown("#### 📥 Filtered Cohort Data Export")
    export_df = active_ranked[active_ranked["is_eligible"]].head(25).copy()
    if not export_df.empty:
        if is_batter:
            cols_export = ["rank", "player_name", "player_id", "reliability_score", "hp_balls", "hp_runs", "hp_strike_rate", "hp_average", "sr_delta", "ci_lower", "ci_upper"]
        else:
            cols_export = ["rank", "player_name", "player_id", "reliability_score", "hp_legal_balls", "hp_overs", "hp_wickets", "hp_economy", "econ_delta", "ci_lower", "ci_upper"]
        
        valid_cols = [c for c in cols_export if c in export_df.columns]
        csv_data = export_df[valid_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"📥 Download Filtered {st.session_state['pbi_category']} Cohort (CSV)",
            data=csv_data,
            file_name=f"SupeRR_Scout_{'Batters' if is_batter else 'Bowlers'}_Filtered.csv",
            mime="text/csv"
        )

with col_exp_right:
    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-radius: 8px; padding: 12px 16px; font-size: 11px; color: #A8B3CC; line-height: 1.5;">
        <b style="color: #F7F8FC;">Analytical Integrity Guardrail:</b><br/>
        Interactive slicers and cross-filtering enable deep exploratory analysis without modifying the official 
        hackathon Top 10 rankings. The official benchmark leaderboards are preserved on Page 4 and Page 8.
    </div>
    """, unsafe_allow_html=True)
