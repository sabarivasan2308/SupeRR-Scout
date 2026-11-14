"""
Page 2: Batting Intelligence — High-Pressure Scoring Dynamics & Clutch Engine
Power BI-Style interactive exploration of high-pressure batting efficiency,
dismissal resistance, clutch deltas, and player scouting dossiers.
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
    apply_rr_theme, plot_batting_scatter, plot_pressure_vs_normal_comparison,
    plot_phase_comparison_grouped, plot_metric_distribution_box,
    RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY, RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN
)
from src.player_profiles import build_batter_evidence_card
from src.batting_analysis import compute_batting_splits
from src.pbi_overview_helpers import build_pbi_leaderboard_chart, build_player_spotlight_card_html

st.set_page_config(page_title="Batting Intelligence | SupeRR SCOUT", page_icon="🏏", layout="wide")
inject_custom_css()

# Load Core Data
deliveries_df, matches_df = load_core_data()
global_filters = render_sidebar_filters(deliveries_df, matches_df)

# ==================== SESSION STATE FOR BATTING SLICERS ====================
if "bat_comp" not in st.session_state:
    st.session_state["bat_comp"] = "All Competitions"
if "bat_phase" not in st.session_state:
    st.session_state["bat_phase"] = "All Phases"
if "bat_seasons" not in st.session_state:
    st.session_state["bat_seasons"] = []
if "bat_min_opps" not in st.session_state:
    st.session_state["bat_min_opps"] = 60
if "bat_threshold" not in st.session_state:
    st.session_state["bat_threshold"] = 65.0
if "bat_focus_player" not in st.session_state:
    st.session_state["bat_focus_player"] = None

def handle_reset_bat_filters():
    st.session_state["bat_comp"] = "All Competitions"
    st.session_state["bat_phase"] = "All Phases"
    st.session_state["bat_seasons"] = []
    st.session_state["bat_min_opps"] = 60
    st.session_state["bat_threshold"] = 65.0
    st.session_state["bat_focus_player"] = None

def handle_clear_bat_focus():
    st.session_state["bat_focus_player"] = None


# ==================== 1. HEADER CARD WITH ACTIVE SLICER CHIPS ====================
focus_p = st.session_state.get("bat_focus_player")
focus_badge = (
    f"<span class='rr-badge' style='background:rgba(243,156,18,0.22); color:#F39C12; border:1px solid #F39C12;'>★ FOCUS: {focus_p}</span>"
    if focus_p else ""
)
seas_count = len(st.session_state["bat_seasons"]) if st.session_state["bat_seasons"] else "All"

st.markdown(f"""
<div class="rr-header-card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <div class="rr-title">2. Batting Intelligence & Reliability Engine</div>
            <div class="rr-subtitle">Evaluating high-pressure scoring efficiency, dismissal avoidance, and clutch differentials</div>
        </div>
        <div style="text-align: right; margin-top: 4px;">
            <span class="rr-badge rr-badge-pink" style="font-size: 11px; padding: 4px 12px;">RR BATTING INTEL</span>
        </div>
    </div>
    <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
        <span style="font-size: 11px; font-weight: 700; color: #A8B3CC; letter-spacing: 0.5px;">ACTIVE SLICERS:</span>
        <span class="rr-badge rr-badge-pink">Scope: {st.session_state['bat_comp']}</span>
        <span class="rr-badge rr-badge-gold">Phase: {st.session_state['bat_phase']}</span>
        <span class="rr-badge rr-badge-navy">Seasons: {seas_count}</span>
        <span class="rr-badge rr-badge-navy">Min Balls: ≥{st.session_state['bat_min_opps']}</span>
        <span class="rr-badge rr-badge-navy">Threshold: ≥{st.session_state['bat_threshold']:.0f}</span>
        {focus_badge}
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== 2. PERSISTENT POWER BI SLICER PANEL ====================
with st.container():
    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-top: 3px solid #E6007E; 
                border-radius: 12px 12px 0 0; padding: 12px 20px; margin-bottom: 0;">
        <div style="font-size: 13px; font-weight: 800; color: #F7F8FC; letter-spacing: 0.8px;">
            🎛️ BATTING COHORT SLICERS & DRILLDOWN
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns([1.3, 1.2, 1.5, 1.2, 0.8])
    with col_s1:
        comp_opts = ["All Competitions", "IPL Only", "T20I Only", "Other T20"]
        c_val = st.selectbox("Tournament Scope", comp_opts, index=comp_opts.index(st.session_state["bat_comp"]), key="sel_bat_comp")
        if c_val != st.session_state["bat_comp"]:
            st.session_state["bat_comp"] = c_val
            st.session_state["bat_focus_player"] = None
            st.rerun()

    with col_s2:
        phase_opts = ["All Phases", "Death (17-20)", "Middle (7-16)", "Powerplay (1-6)"]
        ph_val = st.selectbox("Match Phase", phase_opts, index=phase_opts.index(st.session_state["bat_phase"]), key="sel_bat_phase")
        if ph_val != st.session_state["bat_phase"]:
            st.session_state["bat_phase"] = ph_val
            st.session_state["bat_focus_player"] = None
            st.rerun()

    with col_s3:
        all_seasons = sorted(deliveries_df["season"].dropna().unique().tolist())
        s_val = st.multiselect("Seasons", all_seasons, default=st.session_state["bat_seasons"], placeholder="All (2022–2026)", key="sel_bat_seasons")
        if s_val != st.session_state["bat_seasons"]:
            st.session_state["bat_seasons"] = s_val
            st.rerun()

    with col_s4:
        opps_val = st.slider("Min HP Balls", 20, 120, int(st.session_state["bat_min_opps"]), step=10, key="slider_bat_opps")
        if opps_val != st.session_state["bat_min_opps"]:
            st.session_state["bat_min_opps"] = opps_val
            st.rerun()

    with col_s5:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        st.button("🔄 Reset", on_click=handle_reset_bat_filters, use_container_width=True, help="Reset batting slicers")

# Apply filters
filtered_df = deliveries_df.copy()
if st.session_state["bat_comp"] == "IPL Only":
    filtered_df = filtered_df[filtered_df["is_ipl"]]
elif st.session_state["bat_comp"] == "T20I Only":
    filtered_df = filtered_df[filtered_df["match_format"] == "T20I"]
elif st.session_state["bat_comp"] == "Other T20":
    filtered_df = filtered_df[filtered_df["competition_type"] == "Other T20"]

if st.session_state["bat_phase"] == "Death (17-20)":
    filtered_df = filtered_df[filtered_df["is_death"]]
elif st.session_state["bat_phase"] == "Middle (7-16)":
    filtered_df = filtered_df[filtered_df["is_middle"]]
elif st.session_state["bat_phase"] == "Powerplay (1-6)":
    filtered_df = filtered_df[filtered_df["is_powerplay"]]

if st.session_state["bat_seasons"]:
    filtered_df = filtered_df[filtered_df["season"].isin(st.session_state["bat_seasons"])]

thresh = st.session_state["bat_threshold"]
min_opps = st.session_state["bat_min_opps"]
filtered_df["is_high_pressure_bat"] = filtered_df["pressure_batting"] >= thresh

# Compute rankings
bat_ranked, top_10_batters, bowl_ranked, top_10_bowlers = get_computed_rankings(filtered_df, min_opps, thresh)
eligible_batters = bat_ranked[bat_ranked["is_eligible"]].sort_values("reliability_score", ascending=False).reset_index(drop=True)
eligible_batters["rank"] = range(1, len(eligible_batters) + 1)

# Player Spotlight Selector Row
col_sp1, col_sp2 = st.columns([2.5, 1.5])
with col_sp1:
    player_names = eligible_batters["player_name"].tolist() if not eligible_batters.empty else []
    p_opts = ["None (All Cohort)"] + sorted(player_names)
    idx = 0
    if focus_p in p_opts:
        idx = p_opts.index(focus_p)
    chosen_p = st.selectbox("Batter Spotlight Selector", p_opts, index=idx, key="sel_bat_spotlight", help="Select a player to highlight across all charts")
    if chosen_p == "None (All Cohort)" and focus_p is not None:
        st.session_state["bat_focus_player"] = None
        st.rerun()
    elif chosen_p != "None (All Cohort)" and chosen_p != focus_p:
        st.session_state["bat_focus_player"] = chosen_p
        st.rerun()

st.markdown("<br/>", unsafe_allow_html=True)


# ==================== 3. FOUR DYNAMIC BATTING KPI CARDS ====================
k1, k2, k3, k4 = st.columns(4)

total_eval_batters = len(eligible_batters)
hp_balls_total = int(filtered_df["is_high_pressure_bat"].sum())
cohort_avg_sr = eligible_batters["hp_strike_rate"].mean() if not eligible_batters.empty else 0.0
top_bat = eligible_batters.iloc[0] if not eligible_batters.empty else None

with k1:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Batters Evaluated</div>
        <div class="rr-kpi-value">{total_eval_batters}</div>
        <div class="rr-kpi-sub-pink">Qualified (≥{min_opps} HP Balls)</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">High-Pressure Balls</div>
        <div class="rr-kpi-value">{hp_balls_total:,}</div>
        <div class="rr-kpi-sub">Across {filtered_df['match_id'].nunique()} Fixtures</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Cohort Mean HP Strike Rate</div>
        <div class="rr-kpi-value">{cohort_avg_sr:.1f}</div>
        <div class="rr-kpi-sub">Pressure ≥{thresh:.0f} Baseline</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    top_name = top_bat["player_name"] if top_bat is not None else "N/A"
    top_score = top_bat["reliability_score"] if top_bat is not None else 0.0
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">#1 Ranked Batter</div>
        <div class="rr-kpi-value" style="font-size: 20px; color: #E6007E;">{top_name}</div>
        <div class="rr-kpi-sub-pink">Score: {top_score:.1f} | HP SR: {top_bat['hp_strike_rate'] if top_bat is not None else 0:.1f}</div>
    </div>
    """, unsafe_allow_html=True)


# ==================== ACTIVE PLAYER SPOTLIGHT CARD ====================
if focus_p:
    matching = eligible_batters[eligible_batters["player_name"] == focus_p]
    if not matching.empty:
        st.markdown(build_player_spotlight_card_html(matching.iloc[0], is_batter=True), unsafe_allow_html=True)
        col_c1, col_c2 = st.columns([0.85, 0.15])
        with col_c2:
            st.button("❌ Clear Focus", on_click=handle_clear_bat_focus, use_container_width=True)


# ==================== 4. THREE COMPREHENSIVE TABS ====================
tab1, tab2, tab3 = st.tabs([
    "🏆 Interactive Batting Leaderboard",
    "🎯 Efficiency & Phase Analysis",
    "👤 Player Scouting Dossier"
])

with tab1:
    st.markdown(f"#### Batting Reliability Ranking (Min {min_opps} HP Balls Faced)")
    st.caption("Click any bar on the chart to spotlight that batter and filter all subsequent analyses.")

    # Metric Sorter
    col_sort_l, col_sort_r = st.columns([1.4, 2.6])
    with col_sort_l:
        sort_metric = st.selectbox(
            "Sort Cohort Table By:",
            options=["Reliability Score", "HP Strike Rate", "HP Average", "Boundary %", "Clutch Delta (Δ SR)", "HP Balls Faced"],
            key="sel_bat_sort_metric"
        )
    
    sort_col_map = {
        "Reliability Score": ("reliability_score", False),
        "HP Strike Rate": ("hp_strike_rate", False),
        "HP Average": ("hp_average", False),
        "Boundary %": ("hp_boundary_pct", False),
        "Clutch Delta (Δ SR)": ("sr_delta", False),
        "HP Balls Faced": ("hp_balls", False)
    }
    col_to_sort, asc = sort_col_map[sort_metric]
    sorted_batters = eligible_batters.sort_values(col_to_sort, ascending=asc).reset_index(drop=True)

    c_chart, c_tbl = st.columns([1.1, 0.9])
    
    with c_chart:
        fig_bar = build_pbi_leaderboard_chart(eligible_batters, is_batter=True, selected_player=focus_p, top_n=10)
        chart_event = st.plotly_chart(fig_bar, on_select="rerun", selection_mode="points", key="bat_lead_chart", use_container_width=True)
        if chart_event and chart_event.get("selection") and chart_event["selection"].get("points"):
            pt = chart_event["selection"]["points"][0]
            c_name = pt.get("customdata", [None])[0] if "customdata" in pt else pt.get("y")
            if c_name and c_name != focus_p:
                st.session_state["bat_focus_player"] = c_name
                st.rerun()

    with c_tbl:
        st.markdown(f"##### Full Qualified Cohort (Sorted by {sort_metric})")
        disp_cols = [
            "rank", "player_name", "reliability_score", "hp_balls", "hp_runs",
            "hp_strike_rate", "hp_average", "hp_boundary_pct", "sr_delta", "ci_lower", "ci_upper"
        ]
        tbl_disp = sorted_batters[disp_cols].copy()
        tbl_disp["95% CI"] = tbl_disp.apply(lambda r: f"[{r['ci_lower']:.1f}-{r['ci_upper']:.1f}]", axis=1)
        tbl_disp.drop(columns=["ci_lower", "ci_upper"], inplace=True)
        tbl_disp.columns = ["Rank", "Player", "Score", "HP Balls", "HP Runs", "HP SR", "HP Avg", "Bnd %", "Δ SR", "95% CI"]
        st.dataframe(tbl_disp, use_container_width=True, hide_index=True)
        
        csv_data = sorted_batters.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export Batting Leaderboard (CSV)",
            data=csv_data,
            file_name=f"Batting_Leaderboard_{st.session_state['bat_comp']}.csv",
            mime="text/csv"
        )

with tab2:
    st.markdown("#### 🎯 Batting Efficiency, Phase Dynamics & Consistency Analysis")
    
    subtab_mat, subtab_comp = st.tabs(["📊 Efficiency Matrix & Phase Summary", "⏱️ Player Phase Comparison & Spread"])
    
    with subtab_mat:
        col_mat_l, col_mat_r = st.columns(2)
        with col_mat_l:
            fig_scatter = plot_batting_scatter(bat_ranked, min_balls=min_opps)
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            st.markdown("""
            <div style="background: #111A32; border: 1px solid #1D2B52; border-radius: 10px; padding: 14px 18px; font-size: 12px; color: #A8B3CC;">
                <b style="color: #F7F8FC;">Matrix Quadrant Guide:</b><br/>
                • <b style="color: #E6007E;">Top-Right (Elite Finishers):</b> High SR (>160) + High Avg (>35). Match-winners like Rinku Singh and David Miller.<br/>
                • <b style="color: #287BFF;">Top-Left (Crisis Anchors):</b> Moderate SR (125-150) + High Avg (>40). Rebuilds collapsed innings.<br/>
                • <b style="color: #F39C12;">Bottom-Right (Slashers):</b> Ultra SR (>175) + Low Avg (<25). 15-ball cameo weapons like Ashutosh Sharma.
            </div>
            """, unsafe_allow_html=True)

        with col_mat_r:
            # Phase Breakdown for Batters
            phase_df = filtered_df[filtered_df["is_high_pressure_bat"]].groupby("phase").agg(
                runs=("runs_batter", "sum"),
                balls=("is_ball_faced_batter", "sum"),
                boundaries=("is_boundary", "sum")
            ).reset_index()
            phase_df["strike_rate"] = (phase_df["runs"] / np.maximum(1, phase_df["balls"])) * 100.0
            phase_df["boundary_pct"] = (phase_df["boundaries"] / np.maximum(1, phase_df["balls"])) * 100.0

            fig_phase = px.bar(
                phase_df,
                x="phase",
                y="strike_rate",
                color="phase",
                color_discrete_map={"Death": RR_PINK, "Middle": RR_ELECTRIC, "Powerplay": RR_BLUE, "Super Over": RR_GOLD},
                title="High-Pressure Strike Rate by Match Phase"
            )
            fig_phase.update_layout(xaxis_title="Match Phase", yaxis_title="High-Pressure Strike Rate", showlegend=False)
            st.plotly_chart(apply_rr_theme(fig_phase), use_container_width=True)
            
    with subtab_comp:
        col_c_left, col_c_right = st.columns(2)
        with col_c_left:
            # Compare top 4 or focused player + top 3 across phases
            top_p_list = eligible_batters.head(4)["player_name"].tolist()
            if focus_p and focus_p not in top_p_list:
                top_p_list = [focus_p] + top_p_list[:3]
            fig_phase_grouped = plot_phase_comparison_grouped(filtered_df, top_p_list, is_batter=True)
            st.plotly_chart(fig_phase_grouped, use_container_width=True)
            
        with col_c_right:
            fig_box = plot_metric_distribution_box(
                eligible_batters,
                metric_col="hp_strike_rate",
                title="Cohort High-Pressure Strike Rate Consistency Spread",
                is_batter=True
            )
            st.plotly_chart(fig_box, use_container_width=True)

with tab3:
    st.markdown("#### 👤 Individual Batter Evidence Dossier")
    
    if player_names:
        default_idx = player_names.index(focus_p) if focus_p in player_names else 0
        sel_dossier_p = st.selectbox("Select Batter for Profile Breakdown:", options=player_names, index=default_idx)
        
        if sel_dossier_p:
            p_row = eligible_batters[eligible_batters["player_name"] == sel_dossier_p].iloc[0]
            p_id = int(p_row["player_id"])
            card = build_batter_evidence_card(p_row)
            
            c_left, c_right = st.columns([1.1, 0.9])
            with c_left:
                st.markdown(f"""
                <div class="rr-card" style="border-top: 3px solid #E6007E; padding: 22px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div>
                            <div style="font-size: 22px; font-weight: 800; color: #F7F8FC;">{card['player_name']}</div>
                            <div style="font-size: 12px; color: #A8B3CC;">Rank #{card['rank']} | ID: {card['player_id']} | {card['role']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 28px; font-weight: 900; color: #E6007E;">{card['reliability_score']:.1f}</div>
                            <div style="font-size: 10px; font-weight: 700; letter-spacing: 0.8px; color: #A8B3CC;">RELIABILITY SCORE</div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 14px;">
                        <span class="rr-badge rr-badge-pink">Strongest: {card['strongest_metric']}</span>
                        <span class="rr-badge rr-badge-blue">Confidence: {card['confidence_rating']} ({card['confidence_interval']})</span>
                        <span class="rr-badge rr-badge-gold">Consistency: {card['consistency']}</span>
                    </div>
                    
                    <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid #1D2B52;">
                        <div style="font-size: 11px; font-weight: 700; color: #E6007E; text-transform: uppercase; letter-spacing: 0.5px;">Scouting Rationale</div>
                        <div style="font-size: 12px; color: #F7F8FC; margin-top: 4px; line-height: 1.5;">{card['scouting_rationale']}</div>
                    </div>
                    
                    <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #1D2B52;">
                        <div style="font-size: 11px; font-weight: 700; color: #F39C12; text-transform: uppercase; letter-spacing: 0.5px;">Analytical Limitations / Watchpoints</div>
                        <div style="font-size: 12px; color: #A8B3CC; margin-top: 4px; line-height: 1.4;">{card['potential_limitations']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with c_right:
                st.plotly_chart(
                    plot_pressure_vs_normal_comparison(p_row, is_batter=True),
                    use_container_width=True
                )

            st.markdown("#### Performance Breakdown by Competition & Phase")
            splits = compute_batting_splits(filtered_df, p_id)
            sp1, sp2, sp3 = st.columns(3)
            with sp1:
                st.caption("By Competition")
                if "competition" in splits and not splits["competition"].empty:
                    st.dataframe(splits["competition"][["competition_type", "balls", "runs", "strike_rate", "hp_balls", "hp_strike_rate"]], hide_index=True)
            with sp2:
                st.caption("By Match Phase")
                if "phase" in splits and not splits["phase"].empty:
                    st.dataframe(splits["phase"][["phase", "balls", "runs", "strike_rate", "hp_balls", "hp_strike_rate"]], hide_index=True)
            with sp3:
                st.caption("By Season")
                if "season" in splits and not splits["season"].empty:
                    st.dataframe(splits["season"][["season", "balls", "runs", "strike_rate", "hp_balls", "hp_strike_rate"]], hide_index=True)
