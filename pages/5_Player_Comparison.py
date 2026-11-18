"""
Page 5: Player Comparison — Multi-Player Battle Arena & Radar Benchmarking
Power BI-Style head-to-head comparison tool with normalized 5-axis radar profiles,
metric-by-metric comparison charts, sample-size uncertainty overlap, and tactical verdicts.
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
    plot_player_radar, plot_phase_comparison_grouped, apply_rr_theme,
    RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY, RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN, RR_CYAN
)
from src.player_profiles import build_batter_evidence_card, build_bowler_evidence_card

st.set_page_config(page_title="Player Comparison | SupeRR SCOUT", page_icon="⚖️", layout="wide")
inject_custom_css()

# Load and Filter Data
deliveries_df, matches_df = load_core_data()
filters = render_sidebar_filters(deliveries_df, matches_df)
filtered_df = filter_deliveries(deliveries_df, filters)

bat_ranked, top_10_batters, bowl_ranked, top_10_bowlers = get_computed_rankings(
    filtered_df, filters["min_opportunities"], filters["pressure_threshold"]
)

# Session State for Comparison
if "comp_role" not in st.session_state:
    st.session_state["comp_role"] = "🏏 Batters"

# ==================== 1. HEADER CARD WITH ACTIVE SLICER CHIPS ====================
st.markdown("""
<div class="rr-header-card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <div class="rr-title">5. Player Comparison — Head-to-Head Battle Arena</div>
            <div class="rr-subtitle">Multi-dimensional radar benchmarking, metric-by-metric differentials & tactical verdicts</div>
        </div>
        <div style="text-align: right; margin-top: 4px;">
            <span class="rr-badge rr-badge-pink" style="font-size: 11px; padding: 4px 12px;">RR BATTLE ARENA</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== 2. PERSISTENT SLICER & PRESET BAR ====================
with st.container():
    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-top: 3px solid #1746A2;
                border-radius: 12px 12px 0 0; padding: 12px 20px; margin-bottom: 0;">
        <div style="font-size: 13px; font-weight: 800; color: #F7F8FC; letter-spacing: 0.8px;">
            🎛️ COMPARISON CONFIGURATOR & CANDIDATE SELECTOR
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_c1, col_c2 = st.columns([1.2, 3.8])
    with col_c1:
        cat_choice = st.radio(
            "Player Role",
            options=["🏏 Batters", "🎯 Bowlers"],
            index=0 if "Batters" in st.session_state["comp_role"] else 1,
            horizontal=True,
            key="radio_comp_role"
        )
        if cat_choice != st.session_state["comp_role"]:
            st.session_state["comp_role"] = cat_choice
            st.rerun()

    is_batter = ("Batters" in st.session_state["comp_role"])
    active_ranked = bat_ranked if is_batter else bowl_ranked
    eligible_df = active_ranked[active_ranked["is_eligible"]].sort_values("reliability_score", ascending=False).reset_index(drop=True)
    all_players = eligible_df["player_name"].tolist()

    # Preset comparison defaults
    if is_batter:
        default_cohort = ["Rinku Singh", "David Miller", "Tim David"]
        filtered_defaults = [p for p in default_cohort if p in all_players] or all_players[:3]
    else:
        default_cohort = ["Sunil Narine", "Rashid Khan", "Haris Rauf"]
        filtered_defaults = [p for p in default_cohort if p in all_players] or all_players[:3]

    with col_c2:
        selected_players = st.multiselect(
            f"Select { 'Batters' if is_batter else 'Bowlers'} to Compare (2–5 recommended):",
            options=all_players,
            default=filtered_defaults,
            key=f"ms_compare_{'bat' if is_batter else 'bowl'}"
        )

st.markdown("<br/>", unsafe_allow_html=True)

if len(selected_players) < 2:
    st.info("⚠️ Please select at least 2 players from the dropdown above to generate the comparative battle arena.")
else:
    compare_df = eligible_df[eligible_df["player_name"].isin(selected_players)].copy()

    # ==================== 3. FOUR DYNAMIC TACTICAL VERDICT CARDS ====================
    st.markdown("### 🔍 Head-to-Head Tactical Verdict")
    best_overall = compare_df.sort_values("reliability_score", ascending=False).iloc[0]

    if is_batter:
        best_sr = compare_df.sort_values("hp_strike_rate", ascending=False).iloc[0]
        best_avg = compare_df.sort_values("hp_average", ascending=False).iloc[0]
        best_delta = compare_df.sort_values("sr_delta", ascending=False).iloc[0]

        v1, v2, v3, v4 = st.columns(4)
        with v1:
            st.markdown(f"""
            <div class='rr-kpi-card' style='border-top: 3px solid #E6007E;'>
                <div class='rr-kpi-title'><span class='rr-badge rr-badge-pink'>OVERALL #1</span></div>
                <div class='rr-kpi-value' style='font-size: 20px; color: #E6007E;'>{best_overall['player_name']}</div>
                <div class='rr-kpi-sub-pink'>Score: {best_overall['reliability_score']:.1f}/100</div>
                <div style='font-size: 11px; color: #A8B3CC; margin-top: 4px;'>Highest composite clutch reliability</div>
            </div>
            """, unsafe_allow_html=True)
        with v2:
            st.markdown(f"""
            <div class='rr-kpi-card' style='border-top: 3px solid #287BFF;'>
                <div class='rr-kpi-title'><span class='rr-badge rr-badge-blue'>PEAK SCORING PACE</span></div>
                <div class='rr-kpi-value' style='font-size: 20px; color: #287BFF;'>{best_sr['player_name']}</div>
                <div class='rr-kpi-sub-blue'>HP SR: {best_sr['hp_strike_rate']:.1f}</div>
                <div style='font-size: 11px; color: #A8B3CC; margin-top: 4px;'>Fastest run accumulation under pressure</div>
            </div>
            """, unsafe_allow_html=True)
        with v3:
            st.markdown(f"""
            <div class='rr-kpi-card' style='border-top: 3px solid #2ECC71;'>
                <div class='rr-kpi-title'><span class='rr-badge' style='background: rgba(46,204,113,0.16); color: #2ECC71; border: 1px solid rgba(46,204,113,0.45);'>RESILIENCE</span></div>
                <div class='rr-kpi-value' style='font-size: 20px; color: #2ECC71;'>{best_avg['player_name']}</div>
                <div class='rr-kpi-sub'>HP Avg: {best_avg['hp_average']:.1f}</div>
                <div style='font-size: 11px; color: #A8B3CC; margin-top: 4px;'>Highest dismissal resistance</div>
            </div>
            """, unsafe_allow_html=True)
        with v4:
            st.markdown(f"""
            <div class='rr-kpi-card' style='border-top: 3px solid #F39C12;'>
                <div class='rr-kpi-title'><span class='rr-badge rr-badge-gold'>GEAR SHIFT</span></div>
                <div class='rr-kpi-value' style='font-size: 20px; color: #F39C12;'>{best_delta['player_name']}</div>
                <div style='font-size: 12px; color: #F39C12; margin-top: 5px; font-weight: 600;'>Δ SR: {best_delta['sr_delta']:+.1f}</div>
                <div style='font-size: 11px; color: #A8B3CC; margin-top: 4px;'>Strongest positive clutch elevation</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        best_econ = compare_df.sort_values("hp_economy", ascending=True).iloc[0]
        best_wkts = compare_df.sort_values("hp_wickets", ascending=False).iloc[0]
        best_sr = compare_df.sort_values("hp_strike_rate", ascending=True).iloc[0]

        v1, v2, v3, v4 = st.columns(4)
        with v1:
            st.markdown(f"""
            <div class='rr-kpi-card' style='border-top: 3px solid #E6007E;'>
                <div class='rr-kpi-title'><span class='rr-badge rr-badge-pink'>OVERALL #1</span></div>
                <div class='rr-kpi-value' style='font-size: 20px; color: #E6007E;'>{best_overall['player_name']}</div>
                <div class='rr-kpi-sub-pink'>Score: {best_overall['reliability_score']:.1f}/100</div>
                <div style='font-size: 11px; color: #A8B3CC; margin-top: 4px;'>Top composite pressure execution</div>
            </div>
            """, unsafe_allow_html=True)
        with v2:
            st.markdown(f"""
            <div class='rr-kpi-card' style='border-top: 3px solid #287BFF;'>
                <div class='rr-kpi-title'><span class='rr-badge rr-badge-blue'>TIGHTEST ECONOMY</span></div>
                <div class='rr-kpi-value' style='font-size: 20px; color: #287BFF;'>{best_econ['player_name']}</div>
                <div class='rr-kpi-sub-blue'>HP Econ: {best_econ['hp_economy']:.2f} RPO</div>
                <div style='font-size: 11px; color: #A8B3CC; margin-top: 4px;'>Highest run strangulation under pressure</div>
            </div>
            """, unsafe_allow_html=True)
        with v3:
            st.markdown(f"""
            <div class='rr-kpi-card' style='border-top: 3px solid #2ECC71;'>
                <div class='rr-kpi-title'><span class='rr-badge' style='background: rgba(46,204,113,0.16); color: #2ECC71; border: 1px solid rgba(46,204,113,0.45);'>WICKET VOLUME</span></div>
                <div class='rr-kpi-value' style='font-size: 20px; color: #2ECC71;'>{best_wkts['player_name']}</div>
                <div class='rr-kpi-sub'>{best_wkts['hp_wickets']:.0f} Wickets</div>
                <div style='font-size: 11px; color: #A8B3CC; margin-top: 4px;'>Most high-pressure breakthroughs</div>
            </div>
            """, unsafe_allow_html=True)
        with v4:
            st.markdown(f"""
            <div class='rr-kpi-card' style='border-top: 3px solid #F39C12;'>
                <div class='rr-kpi-title'><span class='rr-badge rr-badge-gold'>STRIKE SPEED</span></div>
                <div class='rr-kpi-value' style='font-size: 20px; color: #F39C12;'>{best_sr['player_name']}</div>
                <div style='font-size: 12px; color: #F39C12; margin-top: 5px; font-weight: 600;'>SR: {best_sr['hp_strike_rate']:.1f} b/w</div>
                <div style='font-size: 11px; color: #A8B3CC; margin-top: 4px;'>Fastest pressure strike rate</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ==================== 4. RADAR & DIRECT METRIC VISUALIZATIONS ====================
    col_rad, col_bar = st.columns([1.1, 0.9])
    with col_rad:
        st.markdown("#### 🕸️ 5-Component Normalized Radar Arena")
        st.caption("Normalized on 0–100 percentile scales across the qualified tournament cohort.")
        st.plotly_chart(plot_player_radar(compare_df, is_batter=is_batter), use_container_width=True)
        st.markdown("""
        <div style="background: #111A32; border: 1px solid #1D2B52; border-radius: 8px; padding: 10px 14px; font-size: 11px; color: #A8B3CC;">
            <b style="color: #F7F8FC;">Radar Normalization Note:</b> Axes are min-max percentile scaled to [0, 100] across the cohort purely for visual shape comparison. Absolute un-normalized statistics are preserved in the table below.
        </div>
        """, unsafe_allow_html=True)

    with col_bar:
        st.markdown("#### 📊 Direct Metric Comparison")
        if is_batter:
            metric_options = ["hp_strike_rate", "hp_average", "hp_boundary_pct", "sr_delta", "consistency_score"]
            metric_labels = {"hp_strike_rate": "HP Strike Rate", "hp_average": "HP Average", "hp_boundary_pct": "Boundary %", "sr_delta": "Clutch Delta (Δ SR)", "consistency_score": "Consistency Score"}
            default_metrics = ["hp_strike_rate", "hp_average"]
        else:
            metric_options = ["hp_economy", "hp_strike_rate", "hp_wickets", "hp_dot_pct", "econ_delta", "consistency_score"]
            metric_labels = {"hp_economy": "HP Economy (RPO)", "hp_strike_rate": "Bowling SR", "hp_wickets": "HP Wickets", "hp_dot_pct": "Dot Ball %", "econ_delta": "Clutch Delta (Δ Econ)", "consistency_score": "Consistency Score"}
            default_metrics = ["hp_economy", "hp_strike_rate"]

        chosen_metrics = st.multiselect(
            "Select Metrics to Plot:",
            options=metric_options,
            default=default_metrics,
            format_func=lambda x: metric_labels.get(x, x),
            key="comp_metrics_choice"
        )
        if not chosen_metrics:
            chosen_metrics = default_metrics

        metric_comp = compare_df[["player_name"] + chosen_metrics].copy()
        fig_cmp = px.bar(
            metric_comp,
            x="player_name",
            y=chosen_metrics,
            barmode="group",
            color_discrete_sequence=[RR_PINK, RR_ELECTRIC, RR_GOLD, RR_GREEN, RR_CYAN],
            labels={"value": "Performance Value", "variable": "Metric", "player_name": "Player"}
        )
        fig_cmp.update_layout(height=420)
        st.plotly_chart(apply_rr_theme(fig_cmp), use_container_width=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ==================== PHASE-BY-PHASE BREAKDOWN ====================
    st.markdown("#### ⏱️ Phase-Wise Execution Comparison (Powerplay, Middle, Death)")
    fig_phases = plot_phase_comparison_grouped(filtered_df, selected_players, is_batter=is_batter)
    st.plotly_chart(fig_phases, use_container_width=True)

    # ==================== 5. KEY METRICS & UNCERTAINTY COMPARISON TABLE ====================
    st.markdown("#### 📋 Detailed Metrics & Confidence Interval Overlap")
    if is_batter:
        metric_cols = [
            "player_name", "reliability_score", "hp_balls", "hp_runs",
            "hp_strike_rate", "hp_average", "hp_boundary_pct", "sr_delta",
            "consistency_score", "ci_lower", "ci_upper"
        ]
        tbl_disp = compare_df[metric_cols].copy()
        tbl_disp["95% CI"] = tbl_disp.apply(lambda r: f"[{r['ci_lower']:.1f} – {r['ci_upper']:.1f}]", axis=1)
        tbl_disp.drop(columns=["ci_lower", "ci_upper"], inplace=True)
        tbl_disp.columns = ["Player", "Score", "HP Balls", "HP Runs", "HP SR", "HP Avg", "Bnd %", "Δ SR", "Consistency", "95% CI"]
    else:
        metric_cols = [
            "player_name", "reliability_score", "hp_legal_balls", "hp_overs",
            "hp_wickets", "hp_economy", "hp_strike_rate", "hp_dot_pct", "econ_delta",
            "consistency_score", "ci_lower", "ci_upper"
        ]
        tbl_disp = compare_df[metric_cols].copy()
        tbl_disp["95% CI"] = tbl_disp.apply(lambda r: f"[{r['ci_lower']:.1f} – {r['ci_upper']:.1f}]", axis=1)
        tbl_disp.drop(columns=["ci_lower", "ci_upper"], inplace=True)
        tbl_disp.columns = ["Player", "Score", "HP Balls", "Overs", "HP Wkts", "HP Econ", "Bowling SR", "Dot %", "Δ Econ", "Consistency", "95% CI"]

    st.dataframe(tbl_disp, use_container_width=True, hide_index=True)

    # CSV Download Button
    comp_csv = tbl_disp.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"📥 Export Head-to-Head Comparison (CSV)",
        data=comp_csv,
        file_name=f"{'Batter' if is_batter else 'Bowler'}_Comparison_Matrix.csv",
        mime="text/csv"
    )

    # ==================== 6. PLAYER PROFILE CARDS EXPANDER ====================
    with st.expander(f"👤 View Individual Profile Dossiers for Selected { 'Batters' if is_batter else 'Bowlers'}"):
        for p in selected_players:
            p_sub = compare_df[compare_df["player_name"] == p]
            if not p_sub.empty:
                row = p_sub.iloc[0]
                card = build_batter_evidence_card(row) if is_batter else build_bowler_evidence_card(row)
                st.markdown(f"**{p} (Rank #{card['rank']} — Score {card['reliability_score']:.1f})**")
                st.markdown(f"• **Role:** {card['role']} | **Confidence:** {card['confidence_rating']} ({card['confidence_interval']})")
                st.markdown(f"• **Scouting Rationale:** {card['scouting_rationale']}")
                st.markdown(f"• **Limitations:** {card['potential_limitations']}")
                st.markdown("---")
