"""
Page 3: Bowling Intelligence — High-Pressure Containment & Breakthrough Engine
Power BI-Style interactive exploration of high-pressure bowling economy,
wicket taking lethality, pressure-band heatmaps, and scouting dossiers.
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
    apply_rr_theme, plot_bowling_scatter, plot_pressure_vs_normal_comparison,
    plot_phase_comparison_grouped, plot_metric_distribution_box,
    RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY, RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN
)
from src.player_profiles import build_bowler_evidence_card
from src.bowling_analysis import compute_bowling_splits
from src.pbi_overview_helpers import (
    build_pbi_leaderboard_chart, build_pbi_heatmap_chart, build_player_spotlight_card_html
)

st.set_page_config(page_title="Bowling Intelligence | SupeRR SCOUT", page_icon="🎯", layout="wide")
inject_custom_css()

# Load Core Data
deliveries_df, matches_df = load_core_data()
global_filters = render_sidebar_filters(deliveries_df, matches_df)

# ==================== SESSION STATE FOR BOWLING SLICERS ====================
if "bowl_comp" not in st.session_state:
    st.session_state["bowl_comp"] = "All Competitions"
if "bowl_phase" not in st.session_state:
    st.session_state["bowl_phase"] = "All Phases"
if "bowl_seasons" not in st.session_state:
    st.session_state["bowl_seasons"] = []
if "bowl_min_opps" not in st.session_state:
    st.session_state["bowl_min_opps"] = 60
if "bowl_threshold" not in st.session_state:
    st.session_state["bowl_threshold"] = 65.0
if "bowl_focus_player" not in st.session_state:
    st.session_state["bowl_focus_player"] = None

def handle_reset_bowl_filters():
    st.session_state["bowl_comp"] = "All Competitions"
    st.session_state["bowl_phase"] = "All Phases"
    st.session_state["bowl_seasons"] = []
    st.session_state["bowl_min_opps"] = 60
    st.session_state["bowl_threshold"] = 65.0
    st.session_state["bowl_focus_player"] = None

def handle_clear_bowl_focus():
    st.session_state["bowl_focus_player"] = None


# ==================== 1. HEADER CARD WITH ACTIVE SLICER CHIPS ====================
focus_p = st.session_state.get("bowl_focus_player")
focus_badge = (
    f"<span class='rr-badge' style='background:rgba(243,156,18,0.22); color:#F39C12; border:1px solid #F39C12;'>★ FOCUS: {focus_p}</span>"
    if focus_p else ""
)
seas_count = len(st.session_state["bowl_seasons"]) if st.session_state["bowl_seasons"] else "All"

st.markdown(f"""
<div class="rr-header-card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <div class="rr-title">3. Bowling Intelligence & Containment Engine</div>
            <div class="rr-subtitle">Evaluating high-pressure economy, wicket breakthrough rate, dot ball generation, and boundary suppression</div>
        </div>
        <div style="text-align: right; margin-top: 4px;">
            <span class="rr-badge rr-badge-blue" style="font-size: 11px; padding: 4px 12px;">RR BOWLING INTEL</span>
        </div>
    </div>
    <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
        <span style="font-size: 11px; font-weight: 700; color: #A8B3CC; letter-spacing: 0.5px;">ACTIVE SLICERS:</span>
        <span class="rr-badge rr-badge-blue">Scope: {st.session_state['bowl_comp']}</span>
        <span class="rr-badge rr-badge-gold">Phase: {st.session_state['bowl_phase']}</span>
        <span class="rr-badge rr-badge-navy">Seasons: {seas_count}</span>
        <span class="rr-badge rr-badge-navy">Min Balls: ≥{st.session_state['bowl_min_opps']}</span>
        <span class="rr-badge rr-badge-navy">Threshold: ≥{st.session_state['bowl_threshold']:.0f}</span>
        {focus_badge}
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== 2. PERSISTENT POWER BI SLICER PANEL ====================
with st.container():
    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-top: 3px solid #287BFF;
                border-radius: 12px 12px 0 0; padding: 12px 20px; margin-bottom: 0;">
        <div style="font-size: 13px; font-weight: 800; color: #F7F8FC; letter-spacing: 0.8px;">
            🎛️ BOWLING COHORT SLICERS & DRILLDOWN
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns([1.3, 1.2, 1.5, 1.2, 0.8])
    with col_s1:
        comp_opts = ["All Competitions", "IPL Only", "T20I Only", "Other T20"]
        c_val = st.selectbox("Tournament Scope", comp_opts, index=comp_opts.index(st.session_state["bowl_comp"]), key="sel_bowl_comp")
        if c_val != st.session_state["bowl_comp"]:
            st.session_state["bowl_comp"] = c_val
            st.session_state["bowl_focus_player"] = None
            st.rerun()

    with col_s2:
        phase_opts = ["All Phases", "Death (17-20)", "Middle (7-16)", "Powerplay (1-6)"]
        ph_val = st.selectbox("Match Phase", phase_opts, index=phase_opts.index(st.session_state["bowl_phase"]), key="sel_bowl_phase")
        if ph_val != st.session_state["bowl_phase"]:
            st.session_state["bowl_phase"] = ph_val
            st.session_state["bowl_focus_player"] = None
            st.rerun()

    with col_s3:
        all_seasons = sorted(deliveries_df["season"].dropna().unique().tolist())
        s_val = st.multiselect("Seasons", all_seasons, default=st.session_state["bowl_seasons"], placeholder="All (2022–2026)", key="sel_bowl_seasons")
        if s_val != st.session_state["bowl_seasons"]:
            st.session_state["bowl_seasons"] = s_val
            st.rerun()

    with col_s4:
        opps_val = st.slider("Min HP Balls", 20, 120, int(st.session_state["bowl_min_opps"]), step=10, key="slider_bowl_opps")
        if opps_val != st.session_state["bowl_min_opps"]:
            st.session_state["bowl_min_opps"] = opps_val
            st.rerun()

    with col_s5:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        st.button("🔄 Reset", on_click=handle_reset_bowl_filters, use_container_width=True, help="Reset bowling slicers")

# Apply filters
filtered_df = deliveries_df.copy()
if st.session_state["bowl_comp"] == "IPL Only":
    filtered_df = filtered_df[filtered_df["is_ipl"]]
elif st.session_state["bowl_comp"] == "T20I Only":
    filtered_df = filtered_df[filtered_df["match_format"] == "T20I"]
elif st.session_state["bowl_comp"] == "Other T20":
    filtered_df = filtered_df[filtered_df["competition_type"] == "Other T20"]

if st.session_state["bowl_phase"] == "Death (17-20)":
    filtered_df = filtered_df[filtered_df["is_death"]]
elif st.session_state["bowl_phase"] == "Middle (7-16)":
    filtered_df = filtered_df[filtered_df["is_middle"]]
elif st.session_state["bowl_phase"] == "Powerplay (1-6)":
    filtered_df = filtered_df[filtered_df["is_powerplay"]]

if st.session_state["bowl_seasons"]:
    filtered_df = filtered_df[filtered_df["season"].isin(st.session_state["bowl_seasons"])]

thresh = st.session_state["bowl_threshold"]
min_opps = st.session_state["bowl_min_opps"]
filtered_df["is_high_pressure_bowl"] = filtered_df["pressure_bowling"] >= thresh

# Compute rankings
bat_ranked, top_10_batters, bowl_ranked, top_10_bowlers = get_computed_rankings(filtered_df, min_opps, thresh)
eligible_bowlers = bowl_ranked[bowl_ranked["is_eligible"]].sort_values("reliability_score", ascending=False).reset_index(drop=True)
eligible_bowlers["rank"] = range(1, len(eligible_bowlers) + 1)

# Player Spotlight Selector Row
col_sp1, col_sp2 = st.columns([2.5, 1.5])
with col_sp1:
    player_names = eligible_bowlers["player_name"].tolist() if not eligible_bowlers.empty else []
    p_opts = ["None (All Cohort)"] + sorted(player_names)
    idx = 0
    if focus_p in p_opts:
        idx = p_opts.index(focus_p)
    chosen_p = st.selectbox("Bowler Spotlight Selector", p_opts, index=idx, key="sel_bowl_spotlight", help="Select a player to highlight across all charts")
    if chosen_p == "None (All Cohort)" and focus_p is not None:
        st.session_state["bowl_focus_player"] = None
        st.rerun()
    elif chosen_p != "None (All Cohort)" and chosen_p != focus_p:
        st.session_state["bowl_focus_player"] = chosen_p
        st.rerun()

st.markdown("<br/>", unsafe_allow_html=True)


# ==================== 3. FOUR DYNAMIC BOWLING KPI CARDS ====================
k1, k2, k3, k4 = st.columns(4)

total_eval_bowlers = len(eligible_bowlers)
hp_balls_total = int(filtered_df["is_high_pressure_bowl"].sum())
cohort_avg_econ = eligible_bowlers["hp_economy"].mean() if not eligible_bowlers.empty else 0.0
top_bowl = eligible_bowlers.iloc[0] if not eligible_bowlers.empty else None

with k1:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Bowlers Evaluated</div>
        <div class="rr-kpi-value">{total_eval_bowlers}</div>
        <div class="rr-kpi-sub-blue">Qualified (≥{min_opps} HP Balls)</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">High-Pressure Balls Bowled</div>
        <div class="rr-kpi-value">{hp_balls_total:,}</div>
        <div class="rr-kpi-sub">Across {filtered_df['match_id'].nunique()} Fixtures</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Cohort Mean HP Economy</div>
        <div class="rr-kpi-value">{cohort_avg_econ:.2f} <span style="font-size:14px; color:#A8B3CC;">RPO</span></div>
        <div class="rr-kpi-sub">Pressure ≥{thresh:.0f} Baseline</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    top_name = top_bowl["player_name"] if top_bowl is not None else "N/A"
    top_score = top_bowl["reliability_score"] if top_bowl is not None else 0.0
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">#1 Ranked Bowler</div>
        <div class="rr-kpi-value" style="font-size: 20px; color: #287BFF;">{top_name}</div>
        <div class="rr-kpi-sub-blue">Score: {top_score:.1f} | HP Econ: {top_bowl['hp_economy'] if top_bowl is not None else 0:.2f}</div>
    </div>
    """, unsafe_allow_html=True)


# ==================== ACTIVE PLAYER SPOTLIGHT CARD ====================
if focus_p:
    matching = eligible_bowlers[eligible_bowlers["player_name"] == focus_p]
    if not matching.empty:
        st.markdown(build_player_spotlight_card_html(matching.iloc[0], is_batter=False), unsafe_allow_html=True)
        col_c1, col_c2 = st.columns([0.85, 0.15])
        with col_c2:
            st.button("❌ Clear Focus", on_click=handle_clear_bowl_focus, use_container_width=True)


# ==================== 4. THREE COMPREHENSIVE TABS ====================
tab1, tab2, tab3 = st.tabs([
    "🏆 Interactive Bowling Leaderboard",
    "🎯 Containment & Heatmap Matrix",
    "👤 Bowler Scouting Dossier"
])

with tab1:
    st.markdown(f"#### Bowling Reliability Ranking (Min {min_opps} HP Legal Balls Bowled)")
    st.caption("Click any bar on the chart to spotlight that bowler and filter all subsequent analyses.")

    # Metric Sorter
    col_sort_l, col_sort_r = st.columns([1.4, 2.6])
    with col_sort_l:
        sort_metric = st.selectbox(
            "Sort Cohort Table By:",
            options=["Reliability Score", "HP Economy (Lowest to Highest)", "HP Wickets (Highest to Lowest)", "Dot Ball %", "Clutch Delta (Δ Econ)", "HP Balls Bowled"],
            key="sel_bowl_sort_metric"
        )

    sort_col_map = {
        "Reliability Score": ("reliability_score", False),
        "HP Economy (Lowest to Highest)": ("hp_economy", True),
        "HP Wickets (Highest to Lowest)": ("hp_wickets", False),
        "Dot Ball %": ("hp_dot_pct", False),
        "Clutch Delta (Δ Econ)": ("econ_delta", True),
        "HP Balls Bowled": ("hp_legal_balls", False)
    }
    col_to_sort, asc = sort_col_map[sort_metric]
    sorted_bowlers = eligible_bowlers.sort_values(col_to_sort, ascending=asc).reset_index(drop=True)

    c_chart, c_tbl = st.columns([1.1, 0.9])

    with c_chart:
        fig_bar = build_pbi_leaderboard_chart(eligible_bowlers, is_batter=False, selected_player=focus_p, top_n=10)
        chart_event = st.plotly_chart(fig_bar, on_select="rerun", selection_mode="points", key="bowl_lead_chart", use_container_width=True)
        if chart_event and chart_event.get("selection") and chart_event["selection"].get("points"):
            pt = chart_event["selection"]["points"][0]
            c_name = pt.get("customdata", [None])[0] if "customdata" in pt else pt.get("y")
            if c_name and c_name != focus_p:
                st.session_state["bowl_focus_player"] = c_name
                st.rerun()

    with c_tbl:
        st.markdown(f"##### Full Qualified Cohort (Sorted by {sort_metric})")
        disp_cols = [
            "rank", "player_name", "reliability_score", "hp_legal_balls", "hp_overs",
            "hp_wickets", "hp_economy", "hp_strike_rate", "hp_dot_pct", "econ_delta", "ci_lower", "ci_upper"
        ]
        tbl_disp = sorted_bowlers[disp_cols].copy()
        tbl_disp["95% CI"] = tbl_disp.apply(lambda r: f"[{r['ci_lower']:.1f}-{r['ci_upper']:.1f}]", axis=1)
        tbl_disp.drop(columns=["ci_lower", "ci_upper"], inplace=True)
        tbl_disp.columns = ["Rank", "Player", "Score", "HP Balls", "Overs", "Wkts", "HP Econ", "Strike Rate", "Dot %", "Δ Econ", "95% CI"]
        st.dataframe(tbl_disp, use_container_width=True, hide_index=True)

        csv_data = sorted_bowlers.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export Bowling Leaderboard (CSV)",
            data=csv_data,
            file_name=f"Bowling_Leaderboard_{st.session_state['bowl_comp']}.csv",
            mime="text/csv"
        )

with tab2:
    st.markdown("#### 🎯 Containment, Pressure Heatmap & Phase Spread")

    subtab_mat, subtab_comp = st.tabs(["📊 Containment Matrix & Heatmap", "⏱️ Bowler Phase Comparison & Economy Spread"])

    with subtab_mat:
        col_mat_l, col_mat_r = st.columns(2)
        with col_mat_l:
            fig_scatter = plot_bowling_scatter(bowl_ranked, min_balls=min_opps)
            st.plotly_chart(fig_scatter, use_container_width=True)

            st.markdown("""
            <div style="background: #111A32; border: 1px solid #1D2B52; border-radius: 10px; padding: 14px 18px; font-size: 12px; color: #A8B3CC;">
                <b style="color: #F7F8FC;">Matrix Quadrant Guide:</b><br/>
                • <b style="color: #E6007E;">Top-Right (Golden Zone):</b> Low Econ (<8.5) + Rapid Wickets (SR < 12). Elite clutch assets like Sunil Narine and Rashid Khan.<br/>
                • <b style="color: #287BFF;">Top-Left (Stranglers):</b> Low Econ (<8.0) + Moderate Wickets. Chokes run rate and forces mistakes.<br/>
                • <b style="color: #F39C12;">Bottom-Right (Death Enforcers):</b> Higher Econ (>9.5) + High Wicket Volumes. Death-over wicket hounds like Arshdeep Singh.
            </div>
            """, unsafe_allow_html=True)

        with col_mat_r:
            fig_heat = build_pbi_heatmap_chart(
                filtered_df,
                eligible_bowlers,
                is_batter=False,
                selected_player=focus_p,
                top_n=8
            )
            st.plotly_chart(fig_heat, use_container_width=True)

    with subtab_comp:
        col_c_left, col_c_right = st.columns(2)
        with col_c_left:
            top_p_list = eligible_bowlers.head(4)["player_name"].tolist()
            if focus_p and focus_p not in top_p_list:
                top_p_list = [focus_p] + top_p_list[:3]
            fig_phase_grouped = plot_phase_comparison_grouped(filtered_df, top_p_list, is_batter=False)
            st.plotly_chart(fig_phase_grouped, use_container_width=True)

        with col_c_right:
            fig_box = plot_metric_distribution_box(
                eligible_bowlers,
                metric_col="hp_economy",
                title="Cohort High-Pressure Economy Consistency Spread",
                is_batter=False
            )
            st.plotly_chart(fig_box, use_container_width=True)

with tab3:
    st.markdown("#### 👤 Individual Bowler Evidence Dossier")

    if player_names:
        default_idx = player_names.index(focus_p) if focus_p in player_names else 0
        sel_dossier_p = st.selectbox("Select Bowler for Profile Breakdown:", options=player_names, index=default_idx)

        if sel_dossier_p:
            p_row = eligible_bowlers[eligible_bowlers["player_name"] == sel_dossier_p].iloc[0]
            p_id = int(p_row["player_id"])
            card = build_bowler_evidence_card(p_row)

            c_left, c_right = st.columns([1.1, 0.9])
            with c_left:
                st.markdown(f"""
                <div class="rr-card" style="border-top: 3px solid #287BFF; padding: 22px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div>
                            <div style="font-size: 22px; font-weight: 800; color: #F7F8FC;">{card['player_name']}</div>
                            <div style="font-size: 12px; color: #A8B3CC;">Rank #{card['rank']} | ID: {card['player_id']} | {card['role']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 28px; font-weight: 900; color: #287BFF;">{card['reliability_score']:.1f}</div>
                            <div style="font-size: 10px; font-weight: 700; letter-spacing: 0.8px; color: #A8B3CC;">RELIABILITY SCORE</div>
                        </div>
                    </div>

                    <div style="margin-bottom: 14px;">
                        <span class="rr-badge rr-badge-blue">Strongest: {card['strongest_metric']}</span>
                        <span class="rr-badge rr-badge-pink">Confidence: {card['confidence_rating']} ({card['confidence_interval']})</span>
                        <span class="rr-badge rr-badge-gold">Consistency: {card['consistency']}</span>
                    </div>

                    <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid #1D2B52;">
                        <div style="font-size: 11px; font-weight: 700; color: #287BFF; text-transform: uppercase; letter-spacing: 0.5px;">Scouting Rationale</div>
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
                    plot_pressure_vs_normal_comparison(p_row, is_batter=False),
                    use_container_width=True
                )

            st.markdown("#### Performance Breakdown by Competition & Phase")
            splits = compute_bowling_splits(filtered_df, p_id)
            sp1, sp2, sp3 = st.columns(3)
            with sp1:
                st.caption("By Competition")
                if "competition" in splits and not splits["competition"].empty:
                    st.dataframe(splits["competition"][["competition_type", "legal_balls", "runs_conceded", "wickets", "economy", "hp_legal_balls", "hp_economy"]], hide_index=True)
            with sp2:
                st.caption("By Match Phase")
                if "phase" in splits and not splits["phase"].empty:
                    st.dataframe(splits["phase"][["phase", "legal_balls", "runs_conceded", "wickets", "economy", "hp_legal_balls", "hp_economy"]], hide_index=True)
            with sp3:
                st.caption("By Season")
                if "season" in splits and not splits["season"].empty:
                    st.dataframe(splits["season"][["season", "legal_balls", "runs_conceded", "wickets", "economy", "hp_legal_balls", "hp_economy"]], hide_index=True)
