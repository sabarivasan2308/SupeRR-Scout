"""
Page 6: Match Situation Analysis — Leverage & Phase Dynamics Engine
Power BI-Style situational breakdowns by innings phase, wickets remaining,
required run-rate bands, and single-match ball-by-ball leverage trajectories.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.ui_helpers import (
    inject_custom_css, load_core_data, render_sidebar_filters, filter_deliveries
)
from src.visualizations import (
    plot_phase_breakdown, apply_rr_theme,
    RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY, RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN
)

st.set_page_config(page_title="Match Situation Analysis | SupeRR SCOUT", page_icon="📈", layout="wide")
inject_custom_css()

# Load Core Data
deliveries_df, matches_df = load_core_data()
filters = render_sidebar_filters(deliveries_df, matches_df)
filtered_df = filter_deliveries(deliveries_df, filters)

# ==================== 1. HEADER CARD WITH ACTIVE SLICER CHIPS ====================
hp_count = int(filtered_df["is_high_pressure_bat"].sum())
hp_pct = (hp_count / max(1, len(filtered_df))) * 100.0

st.markdown(f"""
<div class="rr-header-card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <div class="rr-title">6. Match Situation & Leverage Analytics</div>
            <div class="rr-subtitle">Deconstructing performance across innings phases, required run-rate stress & close finishes</div>
        </div>
        <div style="text-align: right; margin-top: 4px;">
            <span class="rr-badge rr-badge-pink" style="font-size: 11px; padding: 4px 12px;">RR LEVERAGE ENGINE</span>
        </div>
    </div>
    <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
        <span style="font-size: 11px; font-weight: 700; color: #A8B3CC; letter-spacing: 0.5px;">ACTIVE CONTEXT:</span>
        <span class="rr-badge rr-badge-pink">Scope: {filters['comp_type']}</span>
        <span class="rr-badge rr-badge-blue">Deliveries: {len(filtered_df):,}</span>
        <span class="rr-badge rr-badge-gold">HP Balls: {hp_count:,} ({hp_pct:.1f}%)</span>
        <span class="rr-badge rr-badge-navy">Threshold: ≥{filters['pressure_threshold']:.0f}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== 2. FOUR DYNAMIC SITUATIONAL KPI CARDS ====================
k1, k2, k3, k4 = st.columns(4)

chases = filtered_df[filtered_df["is_chase"]].copy()
avg_chase_rrr = chases[chases["is_high_pressure_bat"]]["required_run_rate"].mean() if not chases.empty else 0.0
death_hp_pct = (filtered_df[filtered_df["is_death"]]["is_high_pressure_bat"].sum() / max(1, hp_count)) * 100.0
hp_run_rate = (filtered_df[filtered_df["is_high_pressure_bat"]]["runs_total_ball"].sum() / max(1, hp_count)) * 6.0

with k1:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">High-Pressure Balls</div>
        <div class="rr-kpi-value">{hp_count:,}</div>
        <div class="rr-kpi-sub-pink">{hp_pct:.1f}% of Reconstructed Deliveries</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Death-Over Concentration</div>
        <div class="rr-kpi-value">{death_hp_pct:.1f}%</div>
        <div class="rr-kpi-sub-blue">HP Balls Occur in Overs 17–20</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">HP Run Rate Demand</div>
        <div class="rr-kpi-value">{hp_run_rate:.2f} <span style="font-size:14px; color:#A8B3CC;">RPO</span></div>
        <div class="rr-kpi-sub">Realized Scoring Pace under HP</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Mean Chase RRR Under HP</div>
        <div class="rr-kpi-value" style="color: {RR_GOLD};">{avg_chase_rrr:.2f} <span style="font-size:14px; color:#A8B3CC;">RPO</span></div>
        <div class="rr-kpi-sub">Required Rate in Crunch Chases</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)


# ==================== 3. SECTION 1: INNINGS PHASE BREAKDOWN ====================
st.markdown("### ⏱️ Innings Phase Leverage & Pressure Distribution")
c_p1, c_p2 = st.columns([1.1, 0.9])

with c_p1:
    st.plotly_chart(plot_phase_breakdown(filtered_df), use_container_width=True)

with c_p2:
    st.markdown("#### Phase Statistics Summary")
    phase_summary = filtered_df.groupby("phase").agg(
        total_balls=("runs_batter", "count"),
        hp_balls=("is_high_pressure_bat", "sum"),
        avg_bat_pressure=("pressure_batting", "mean"),
        avg_bowl_pressure=("pressure_bowling", "mean"),
        runs_per_over=("runs_total_ball", lambda r: (r.sum() / len(r)) * 6.0)
    ).reset_index()
    phase_summary["hp_pct"] = (phase_summary["hp_balls"] / phase_summary["total_balls"]) * 100.0
    phase_summary.columns = ["Phase", "Total Balls", "HP Balls", "Mean Bat P", "Mean Bowl P", "Run Rate (RPO)", "HP %"]
    st.dataframe(phase_summary, use_container_width=True, hide_index=True)

st.markdown("---")


# ==================== 4. SECTION 2: REQUIRED RUN RATE BANDS ====================
st.markdown("### 🎯 Chase Pressure by Required Run Rate (RRR) Bands")
st.caption("Partitioning 2nd innings run chases into escalating pressure brackets.")

bins = [0, 6.0, 9.0, 12.0, 15.0, 99.0]
labels = ["Cruise (<6.0)", "Moderate (6.0–9.0)", "Demanding (9.0–12.0)", "Intense (12.0–15.0)", "Extreme (>15.0)"]
chases["rrr_band"] = pd.cut(chases["required_run_rate"], bins=bins, labels=labels, right=False)

rrr_agg = chases.groupby("rrr_band", observed=False).agg(
    balls=("runs_batter", "count"),
    runs=("runs_batter", "sum"),
    wickets=("is_wicket", "sum"),
    boundaries=("is_boundary", "sum"),
    dots=("is_batter_dot", "sum"),
    avg_pressure=("pressure_batting", "mean")
).reset_index()

rrr_agg["strike_rate"] = (rrr_agg["runs"] / np.maximum(1, rrr_agg["balls"])) * 100.0
rrr_agg["boundary_pct"] = (rrr_agg["boundaries"] / np.maximum(1, rrr_agg["balls"])) * 100.0
rrr_agg["dot_pct"] = (rrr_agg["dots"] / np.maximum(1, rrr_agg["balls"])) * 100.0

col_r1, col_r2 = st.columns(2)
with col_r1:
    fig_rrr = px.bar(
        rrr_agg,
        x="rrr_band",
        y="strike_rate",
        color="avg_pressure",
        color_continuous_scale=[[0, RR_BLUE], [0.5, RR_ELECTRIC], [1, RR_PINK]],
        title="Batting Strike Rate across Required Run Rate Bands"
    )
    fig_rrr.update_layout(xaxis_title="Required Run Rate Band", yaxis_title="Realized Strike Rate")
    st.plotly_chart(apply_rr_theme(fig_rrr), use_container_width=True)

with col_r2:
    fig_dots = px.line(
        rrr_agg,
        x="rrr_band",
        y=["boundary_pct", "dot_pct"],
        markers=True,
        title="Boundary % vs Dot % across Required Run Rate Bands",
        color_discrete_map={"boundary_pct": RR_PINK, "dot_pct": RR_ELECTRIC}
    )
    fig_dots.update_layout(xaxis_title="Required Run Rate Band", yaxis_title="Percentage (%)")
    st.plotly_chart(apply_rr_theme(fig_dots), use_container_width=True)

st.markdown("---")


# ==================== 5. SECTION 3: BALL-BY-BALL MATCH TRAJECTORY ====================
st.markdown("### 🔍 Ball-by-Ball Match Pressure Trajectory Engine")
match_list = filtered_df[["match_id", "match_date", "home_team", "away_team", "result"]].drop_duplicates("match_id").head(100)
match_options = {
    f"Match #{r['match_id']} | {r['home_team']} vs {r['away_team']} ({str(r['match_date'])[:10]})": r["match_id"]
    for _, r in match_list.iterrows()
}

selected_label = st.selectbox("Select Match to Inspect:", options=list(match_options.keys()), index=0)
selected_match_id = match_options[selected_label]

match_balls = filtered_df[filtered_df["match_id"] == selected_match_id].sort_values(
    by=["innings", "overid", "over_ball_num"]
).reset_index(drop=True)

fig_match = go.Figure()

for inn in match_balls["innings"].unique():
    inn_data = match_balls[match_balls["innings"] == inn]
    color = RR_PINK if inn == 2 else RR_BLUE
    team_name = inn_data['home_team'].iloc[0] if inn == 1 else inn_data['away_team'].iloc[0]
    
    fig_match.add_trace(go.Scatter(
        x=list(range(1, len(inn_data) + 1)),
        y=inn_data["pressure_batting"],
        mode="lines+markers",
        name=f"Innings {inn} ({team_name})",
        line=dict(color=color, width=2.5),
        marker=dict(size=4)
    ))

fig_match.add_hline(
    y=filters["pressure_threshold"],
    line_dash="dash",
    line_color=RR_GOLD,
    annotation_text=f"HP Threshold ({filters['pressure_threshold']:.0f})"
)

fig_match.update_layout(
    title=dict(text=f"Ball-by-Ball Match Leverage Profile — Match #{selected_match_id}", font=dict(size=15)),
    xaxis_title="Delivery Sequence Number",
    yaxis_title="Pressure Index (0–100)",
    height=440
)
st.plotly_chart(apply_rr_theme(fig_match), use_container_width=True)
