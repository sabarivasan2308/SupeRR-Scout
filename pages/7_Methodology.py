"""
Page 7: Methodology & Mathematical Transparency
Complete scientific documentation, implemented formulas, Bayesian shrinkage simulations,
and statistical limitations for Rajasthan Royals analytics war room.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.ui_helpers import inject_custom_css
from src.visualizations import (
    apply_rr_theme, RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY, RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN
)
from src.data_dictionary import get_data_dictionary, get_methodology_glossary, get_pipeline_stages

st.set_page_config(page_title="Methodology & Transparency | SupeRR SCOUT", page_icon="📐", layout="wide")
inject_custom_css()

# ==================== 1. HEADER CARD ====================
st.markdown("""
<div class="rr-header-card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <div class="rr-title">7. Methodology & Scientific Transparency</div>
            <div class="rr-subtitle">Mathematical formulations, Bayesian shrinkage derivation, credibility curves & statistical defenses</div>
        </div>
        <div style="text-align: right; margin-top: 4px;">
            <span class="rr-badge rr-badge-pink" style="font-size: 11px; padding: 4px 12px;">RR SCIENTIFIC CORE</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== 2. FOUR CORE METHODOLOGY KPIS ====================
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Prior Half-Credibility Constant</div>
        <div class="rr-kpi-value" style="color: {RR_PINK};">K = 50.0</div>
        <div class="rr-kpi-sub">Deliveries for 50% Sample Credibility</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Population Prior Benchmarks</div>
        <div class="rr-kpi-value" style="font-size: 20px;">138.5 SR | 10.14 Econ</div>
        <div class="rr-kpi-sub">Empirical League Mean under HP</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Knockout Stage Multiplier</div>
        <div class="rr-kpi-value" style="color: {RR_GOLD};">1.08× Boost</div>
        <div class="rr-kpi-sub">Applied in Playoff & Final Matches</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Confidence Level</div>
        <div class="rr-kpi-value" style="color: {RR_ELECTRIC};">95.0% CI</div>
        <div class="rr-kpi-sub">Asymptotic Error Propagation</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)


# ==================== 3. FIVE COMPREHENSIVE TRANSPARENCY TABS ====================
m1, m2, m3, m4, m5 = st.tabs([
    "📐 Mathematical Formulations",
    "🔄 End-to-End Pipeline Workflow",
    "📊 Bayesian Shrinkage & Live Sandbox",
    "📖 Data Dictionary & Feature Glossary",
    "🛡️ Statistical Defenses & Limitations"
])

with m1:
    st.markdown("### 1. Delivery-Level Pressure Index Formulations")
    st.markdown("""
    Pressure is computed separately for batting and bowling as a continuous value between 0.0 and 100.0 for every legal delivery.
    
    #### A. Batting Chase Pressure (Innings 2)
    In run chases, pressure is driven by the arithmetic challenge of reaching the target:
    """)
    st.latex(r"P_{\text{chase\_bat}} = 0.40 \cdot R_{\text{demand}} + 0.25 \cdot W_{\text{lost}} + 0.20 \cdot S_{\text{stage}} + 0.15 \cdot L_{\text{closeness}}")
    st.markdown(r"""
    Where:
    - **$R_{\text{demand}}$**: Scaled required run rate (RRR) relative to par. RRR $\le 4.0 \rightarrow 10$, RRR $= 8.5 \rightarrow 45$, RRR $= 14.0 \rightarrow 90$, RRR $\ge 18.0 \rightarrow 100$.
    - **$W_{\text{lost}}$**: Wickets lost urgency: $\min\left(100, \left(\frac{\text{wickets\_lost}}{9.0}\right)^{1.15} \times 100\right)$.
    - **$S_{\text{stage}}$**: Innings progression fraction over scheduled 120 balls: $\frac{b}{120} \times 100$.
    - **$L_{\text{closeness}}$**: Match leverage index based on proximity to target and resources remaining.
    - **Knockout Boost**: Multiplied by $1.08\times$ in playoff/knockout matches (capped at 100).
    
    #### B. Batting First-Innings Pressure (Innings 1)
    In the first innings where no fixed target exists, pressure stems from collapse crises and death-over scoring demands:
    """)
    st.latex(r"P_{\text{1st\_bat}} = 0.45 \cdot W_{\text{crisis}} + 0.35 \cdot S_{\text{phase}} + 0.20 \cdot R_{\text{deficit}}")
    st.markdown(r"""
    Where:
    - **$W_{\text{crisis}}$**: Wickets lost ahead of the empirical over-by-over progression curve.
    - **$S_{\text{phase}}$**: Innings stage urgency (Powerplay: 25-40, Middle: 40-65, Death: 70-100).
    - **$R_{\text{deficit}}$**: Deficit of current run rate against competition par (IPL 9.25 RPO, T20I 8.30 RPO).
    
    #### C. Bowling Pressure Index
    For bowlers, pressure represents the difficulty and margin of error in defending against the opposition:
    """)
    st.latex(r"P_{\text{chase\_bowl}} = 0.35 \cdot R_{\text{threat}} + 0.25 \cdot S_{\text{stage}} + 0.20 \cdot W_{\text{in\_hand}} + 0.20 \cdot M_{\text{margin}}")
    st.markdown(r"""
    Where:
    - **$R_{\text{threat}}$**: Peaks when the chase is in active balance (RRR 6.0 to 12.0 in late overs).
    - **$W_{\text{in\_hand}}$**: Opposition batting resources (more opposition wickets in hand = higher threat).
    - **$M_{\text{margin}}$**: Margin stress in final 30 balls when runs needed is under 40.
    """)

    st.markdown("---")
    st.markdown("### 2. Multi-Factor Reliability Score Architecture (0–100)")
    
    col_w_b, col_w_bw = st.columns(2)
    with col_w_b:
        st.markdown("#### Batting Score Weights")
        bat_weights = pd.DataFrame({
            "Sub-Component": ["Scoring Pace", "Dismissal Survival", "Boundary-Dot Ratio", "Clutch Gear Shift", "Multi-Match Consistency"],
            "Weight": [30, 25, 20, 15, 10]
        })
        fig_w_bat = px.bar(
            bat_weights, x="Weight", y="Sub-Component", orientation="h",
            color="Sub-Component", color_discrete_sequence=[RR_PINK, RR_ELECTRIC, RR_BLUE, RR_GOLD, RR_GREEN],
            text=[f"{w}%" for w in bat_weights["Weight"]],
            title="Batting Multi-Factor Composition"
        )
        fig_w_bat.update_layout(height=280, showlegend=False, xaxis=dict(range=[0, 35]))
        st.plotly_chart(apply_rr_theme(fig_w_bat), use_container_width=True)

    with col_w_bw:
        st.markdown("#### Bowling Score Weights")
        bowl_weights = pd.DataFrame({
            "Sub-Component": ["Economy Containment", "Breakthrough Wickets", "Dot Ball Generation", "Clutch Delta (vs Norm)", "Multi-Match Consistency"],
            "Weight": [30, 25, 20, 15, 10]
        })
        fig_w_bowl = px.bar(
            bowl_weights, x="Weight", y="Sub-Component", orientation="h",
            color="Sub-Component", color_discrete_sequence=[RR_ELECTRIC, RR_PINK, RR_BLUE, RR_GOLD, RR_GREEN],
            text=[f"{w}%" for w in bowl_weights["Weight"]],
            title="Bowling Multi-Factor Composition"
        )
        fig_w_bowl.update_layout(height=280, showlegend=False, xaxis=dict(range=[0, 35]))
        st.plotly_chart(apply_rr_theme(fig_w_bowl), use_container_width=True)

with m2:
    st.markdown("### 🔄 End-to-End Analytics Workflow Pipeline")
    st.caption("Visual architecture representing the six computational transformation stages from raw deliveries to franchise recruitment dossiers.")
    
    stages = get_pipeline_stages()
    for s in stages:
        st.markdown(f"""
        <div style="background: #111A32; border: 1px solid #1D2B52; border-left: 4px solid #E6007E; border-radius: 10px; padding: 14px 20px; margin-bottom: 12px;">
            <div style="font-size: 15px; font-weight: 800; color: #F7F8FC;">
                {s['Icon']} {s['Stage']}
            </div>
            <div style="font-size: 13px; color: #A8B3CC; margin-top: 4px;">
                {s['Details']}
            </div>
        </div>
        """, unsafe_allow_html=True)

with m3:
    st.markdown("### 📊 Interactive Bayesian Shrinkage & Uncertainty Simulator")
    st.caption("Explore how Empirical Bayes protects leaderboards against small-sample noise and calculates 95% Confidence Intervals.")
    
    # Interactive Sandbox Slider
    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px;">
        <b style="color: #E6007E;">🎛️ Live Empirical Bayes Sandbox</b><br/>
        <span style="font-size: 12px; color: #A8B3CC;">Test any sample size to observe real-time shrinkage weights and margin-of-error narrowing:</span>
    </div>
    """, unsafe_allow_html=True)
    
    sandbox_n = st.slider("Select Sample Size (High-Pressure Deliveries):", min_value=10, max_value=300, value=75, step=5, key="sandbox_n_slider")
    sandbox_w = (sandbox_n / (sandbox_n + 50.0)) * 100.0
    sandbox_ci = 1.96 * (16.0 / np.sqrt(sandbox_n / 25.0))
    
    sb1, sb2, sb3 = st.columns(3)
    with sb1:
        st.metric("Sample Size", f"{sandbox_n} balls", help="Observed deliveries under match pressure ≥ 65.0")
    with sb2:
        st.metric("Data Credibility Weight (w_i)", f"{sandbox_w:.1f}%", help="Weight given to observed player stats vs prior baseline (K=50)")
    with sb3:
        st.metric("95% CI Margin of Error", f"± {sandbox_ci:.1f} pts", help="Asymptotic propagation uncertainty interval")
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    col_sim_l, col_sim_r = st.columns(2)
    
    # 1. Shrinkage Credibility Curve
    n_range = np.linspace(10, 300, 100)
    w_range = n_range / (n_range + 50.0)
    
    df_sim_cred = pd.DataFrame({"HP Deliveries": n_range, "Sample Credibility Weight (%)": w_range * 100.0})
    fig_cred = px.line(
        df_sim_cred, x="HP Deliveries", y="Sample Credibility Weight (%)",
        title="Empirical Bayes Credibility Weight curve: w_i = n_i / (n_i + 50)"
    )
    fig_cred.add_vline(x=60, line_dash="dash", line_color=RR_GOLD, annotation_text="Min Cutoff (60b = 54.5%)")
    fig_cred.add_vline(x=200, line_dash="dash", line_color=RR_PINK, annotation_text="High Credibility (200b = 80.0%)")
    fig_cred.update_traces(line=dict(color=RR_PINK, width=3))
    
    with col_sim_l:
        st.plotly_chart(apply_rr_theme(fig_cred), use_container_width=True)
        
    # 2. Confidence Interval Margin of Error curve
    ci_margin = 1.96 * (16.0 / np.sqrt(n_range / 25.0))
    df_sim_ci = pd.DataFrame({"HP Deliveries": n_range, "Margin of Error (± pts)": ci_margin})
    
    fig_ci = px.line(
        df_sim_ci, x="HP Deliveries", y="Margin of Error (± pts)",
        title="95% Confidence Interval Width (Uncertainty Narrowing)"
    )
    fig_ci.update_traces(line=dict(color=RR_ELECTRIC, width=3))
    fig_ci.add_hline(y=10.0, line_dash="dot", line_color=RR_MUTED, annotation_text="High Uncertainty (>10 pts)")
    fig_ci.add_hline(y=4.5, line_dash="dot", line_color=RR_GREEN, annotation_text="Tight Precision (<4.5 pts)")
    
    with col_sim_r:
        st.plotly_chart(apply_rr_theme(fig_ci), use_container_width=True)

with m4:
    st.markdown("### 📖 Formal Data Dictionary & Methodology Glossary")
    st.caption("Complete technical specifications of operational features and scientific terminology.")
    
    sub_dict_tab, sub_gloss_tab = st.tabs(["📋 Data Dictionary", "📚 Analytical Glossary"])
    with sub_dict_tab:
        dict_df = get_data_dictionary()
        search_feat = st.text_input("Filter Features:", placeholder="Type feature name...", key="dict_search_feat")
        if search_feat.strip():
            dict_df = dict_df[dict_df["Feature"].str.contains(search_feat.strip(), case=False, na=False)]
        st.dataframe(dict_df, use_container_width=True, hide_index=True)
        
    with sub_gloss_tab:
        glossary = get_methodology_glossary()
        for g in glossary:
            with st.expander(f"📌 {g['Term']}"):
                st.markdown(f"<div style='font-size: 13px; color: #F7F8FC; line-height: 1.5;'>{g['Definition']}</div>", unsafe_allow_html=True)

with m5:
    st.markdown("### 🛡️ Statistical Defenses & Limitations")
    st.markdown("""
    #### 1. Why Aggregate Averages Fail Under Pressure
    Traditional cricket analytics rely on raw averages and strike rates across all deliveries. This treats a boundary hit in the 3rd over of a relaxed league match identically to a six needed off the final ball of a tournament semi-final. 
    Our pressure model partitions performance based on verified match context, revealing that players who appear dominant in low-pressure conditions frequently dip when pressure exceeds index 65.
    
    #### 2. Separation of Individual Performance from Team Match Outcomes
    A batter can play a heroic 48 off 22 balls under extreme pressure only for their team to lose by 1 run due to bowling concessions. 
    Our system evaluates delivery-level execution independently of team win/loss outcomes, preventing unfair penalties on individual excellence.
    
    #### 3. Strict Bowling Attribution Rules
    - **No Byes or Leg-byes:** Conceded byes and leg-byes are excluded from the bowler's runs conceded, complying strictly with MCC Law 21 and official ICC playing conditions.
    - **Illegal Balls Handled Accurately:** Wides and no-balls are counted towards runs conceded and bowler stress, but are NOT counted as legal balls in over completion calculations.
    - **Dismissal Verification:** Only Caught, Bowled, LBW, Stumped, and Hit Wicket dismissals are credited as bowler wickets; run-outs and retired-outs are excluded.
    
    #### 4. Known Analytical Limitations
    - **Drop-in Pitches & Dew Factor:** Ground-level moisture and pitch deterioration are not explicitly coded in the raw CSV feeds; par run rates are normalized at the competition level.
    - **Batting Order Shifts:** Players used as makeshift pinch-hitters or floater resources can experience sudden shifts in situational exposure.
    - **Opposition Bowling Quality:** While competition type (IPL vs T20I) is accounted for, bowler-quality weighting per individual delivery is not applied to preserve computational reproducibility.
    
    #### 5. Dataset Scope & Tournament Segregation
    - **Combined Rankings:** Use all **200,999 deliveries** from the supplied archive (883 matches), including IPL (371 matches, 87,687 deliveries), T20I (482 matches, 106,327 deliveries), and the 30 Emerging Teams Asia Cup / Asia Cup Rising Stars matches (6,985 deliveries).
    - **IPL-Only Rankings:** Use strictly **87,687 IPL deliveries** across **371 matches** (IPL 2022–2026), isolating domestic franchise conditions.
    """)
