"""
Page 8: IPL 2027 Auction Intelligence & Strategic Recruitment Dossier
Rajasthan Royals War Room Analytics | Empirical Data vs Scouting Interpretations
Features:
- Power BI Slicers for Shortlisted Candidates
- IPL-Only vs Combined Rankings Matrix
- Competition Disaggregation (IPL vs T20I Performance)
- Empirical Role Classification & Phase Distribution
- Sample-Size and Uncertainty Indicators
- Rajasthan Royals Tactical Suitability & Sawai Mansingh Stadium Fit
- Downloadable Comprehensive Auction Scouting Dossier & PDF
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

from src.ui_helpers import (
    inject_custom_css, load_core_data, render_sidebar_filters, filter_deliveries
)
from src.auction_intelligence import (
    compute_auction_rankings, compute_player_competition_split,
    classify_player_role_and_phases, generate_all_auction_assets,
    build_auction_dossier
)
from src.visualizations import (
    plot_ipl_vs_combined_scores, plot_phase_allocation_stacked,
    plot_single_player_split, apply_rr_theme,
    RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY, RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN
)
from src.report_generator import build_auction_pdf_report

st.set_page_config(
    page_title="IPL 2027 Auction Intelligence | SupeRR SCOUT",
    page_icon="🏰",
    layout="wide"
)
inject_custom_css()

# Load Core Data
deliveries_df, matches_df = load_core_data()
filters = render_sidebar_filters(deliveries_df, matches_df)
filtered_df = filter_deliveries(deliveries_df, filters)

# Pre-generate / Cache Auction Assets
@st.cache_data(show_spinner=False)
def load_auction_assets_cached():
    assets_dir = Path("assets")
    return generate_all_auction_assets(deliveries_df, assets_dir)

auction_assets = load_auction_assets_cached()
dossier_df = auction_assets["dossier"]
ipl_bat = auction_assets["ipl_bat"]
ipl_bowl = auction_assets["ipl_bowl"]
comb_bat = auction_assets["comb_bat"]
comb_bowl = auction_assets["comb_bowl"]

# Session State for Auction War Room
if "auc_category" not in st.session_state:
    st.session_state["auc_category"] = "All Candidates"
if "auc_tier" not in st.session_state:
    st.session_state["auc_tier"] = "All Tiers"
if "auc_focus_player" not in st.session_state:
    st.session_state["auc_focus_player"] = None

def handle_clear_auc_focus():
    st.session_state["auc_focus_player"] = None

# ==================== 1. HEADER CARD WITH ACTIVE SLICER CHIPS ====================
focus_p = st.session_state.get("auc_focus_player")
focus_badge = (
    f"<span class='rr-badge' style='background:rgba(243,156,18,0.22); color:#F39C12; border:1px solid #F39C12;'>★ FOCUS: {focus_p}</span>"
    if focus_p else ""
)

st.markdown(f"""
<div class="rr-header-card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <div class="rr-title">8. IPL 2027 Auction Intelligence & Recruitment Layer</div>
            <div class="rr-subtitle">Rajasthan Royals War Room Analytics | Empirical Pressure Reliability vs Scouting Interpretations</div>
        </div>
        <div style="text-align: right; margin-top: 4px;">
            <span class="rr-badge rr-badge-pink" style="font-size: 11px; padding: 4px 12px;">RR AUCTION WAR ROOM</span>
        </div>
    </div>
    <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
        <span style="font-size: 11px; font-weight: 700; color: #A8B3CC; letter-spacing: 0.5px;">ACTIVE SLICERS:</span>
        <span class="rr-badge rr-badge-navy">Category: {st.session_state['auc_category']}</span>
        <span class="rr-badge rr-badge-gold">Recruitment Tier: {st.session_state['auc_tier']}</span>
        <span class="rr-badge rr-badge-blue">Venue Target: SMS Jaipur</span>
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
            🎛️ AUCTION CANDIDATE SHORTLIST SLICER
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2, col_s3, col_s4 = st.columns([1.3, 1.4, 1.8, 0.8])
    with col_s1:
        cat_options = ["All Candidates", "🏏 Batters Only", "🎯 Bowlers Only"]
        curr_cat_idx = 0
        if "Batters" in st.session_state["auc_category"]:
            curr_cat_idx = 1
        elif "Bowlers" in st.session_state["auc_category"]:
            curr_cat_idx = 2
            
        c_choice = st.selectbox("Candidate Category", cat_options, index=curr_cat_idx, key="sel_auc_cat")
        if c_choice != st.session_state["auc_category"]:
            st.session_state["auc_category"] = c_choice
            st.session_state["auc_focus_player"] = None
            st.rerun()

    with col_s2:
        tier_options = ["All Tiers", "Tier 1: Priority", "Tier 2: Value", "Tier 3: Depth"]
        t_choice = st.selectbox("Recruitment Tier", tier_options, index=tier_options.index(st.session_state["auc_tier"]), key="sel_auc_tier")
        if t_choice != st.session_state["auc_tier"]:
            st.session_state["auc_tier"] = t_choice
            st.session_state["auc_focus_player"] = None
            st.rerun()

    # Filter shortlist based on slicers
    filtered_dossier = dossier_df.copy()
    if "Batters" in st.session_state["auc_category"]:
        filtered_dossier = filtered_dossier[filtered_dossier["category"] == "Batter"]
    elif "Bowlers" in st.session_state["auc_category"]:
        filtered_dossier = filtered_dossier[filtered_dossier["category"] == "Bowler"]

    if st.session_state["auc_tier"] != "All Tiers":
        tier_prefix = st.session_state["auc_tier"].split(":")[0]
        filtered_dossier = filtered_dossier[filtered_dossier["target_tier"].str.contains(tier_prefix, na=False)]

    with col_s3:
        all_shortlist_names = filtered_dossier["player_name"].tolist()
        p_opts = ["None (All Shortlist)"] + sorted(all_shortlist_names)
        idx_p = 0
        if focus_p in p_opts:
            idx_p = p_opts.index(focus_p)
            
        chosen_auc_p = st.selectbox("Candidate Spotlight Selector", p_opts, index=idx_p, key="sel_auc_spotlight")
        if chosen_auc_p == "None (All Shortlist)" and focus_p is not None:
            st.session_state["auc_focus_player"] = None
            st.rerun()
        elif chosen_auc_p != "None (All Shortlist)" and chosen_auc_p != focus_p:
            st.session_state["auc_focus_player"] = chosen_auc_p
            st.rerun()

    with col_s4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Reset", key="btn_reset_auc", use_container_width=True):
            st.session_state["auc_category"] = "All Candidates"
            st.session_state["auc_tier"] = "All Tiers"
            st.session_state["auc_focus_player"] = None
            st.rerun()

st.markdown("<br/>", unsafe_allow_html=True)


# ==================== 3. FOUR DYNAMIC AUCTION KPI CARDS ====================
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Shortlisted Candidates</div>
        <div class="rr-kpi-value">{len(filtered_dossier)} / {len(dossier_df)}</div>
        <div class="rr-kpi-sub">Across IPL & T20I (2022–2026)</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    top_ipl_b = ipl_bat.iloc[0]
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Top IPL-Only Batter</div>
        <div class="rr-kpi-value" style="font-size: 19px; color: #E6007E;">{top_ipl_b['player_name']}</div>
        <div class="rr-kpi-sub-pink">Score: {top_ipl_b['reliability_score']:.1f} (SR {top_ipl_b['hp_strike_rate']:.1f} | Avg {top_ipl_b['hp_average']:.1f})</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    top_ipl_bw = ipl_bowl.iloc[0]
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">Top IPL-Only Bowler</div>
        <div class="rr-kpi-value" style="font-size: 19px; color: #287BFF;">{top_ipl_bw['player_name']}</div>
        <div class="rr-kpi-sub-blue">Score: {top_ipl_bw['reliability_score']:.1f} (Econ {top_ipl_bw['hp_economy']:.2f} | {top_ipl_bw['hp_wickets']:.0f} Wkts)</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="rr-kpi-card">
        <div class="rr-kpi-title">High-Pressure Deliveries</div>
        <div class="rr-kpi-value">{(deliveries_df['is_high_pressure_bat']).sum():,}</div>
        <div class="rr-kpi-sub-pink">{(deliveries_df[deliveries_df['is_ipl']]['is_high_pressure_bat']).sum():,} in IPL Alone</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)


# ==================== ACTIVE CANDIDATE SPOTLIGHT CARD ====================
if focus_p:
    matching_auc = dossier_df[dossier_df["player_name"] == focus_p]
    if not matching_auc.empty:
        p_row = matching_auc.iloc[0]
        pid = int(p_row["player_id"])
        is_b = (p_row["category"] == "Batter")
        dossier_item = build_auction_dossier(deliveries_df, pid, is_batter=is_b, comb_score=p_row["comb_score"], ipl_score=p_row["ipl_score"])
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(230,0,126,0.16) 0%, rgba(23,70,162,0.25) 100%); 
                    border: 1px solid rgba(230,0,126,0.45); border-left: 5px solid {RR_GOLD}; 
                    border-radius: 12px; padding: 18px 24px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(8,13,32,0.8);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span class="rr-badge rr-badge-gold" style="font-size: 11px;">★ ACTIVE WAR ROOM SPOTLIGHT</span>
                    <span class="rr-badge {'rr-badge-pink' if is_b else 'rr-badge-blue'}" style="font-size: 11px;">{p_row['category'].upper()}</span>
                    <span class="rr-badge rr-badge-navy" style="font-size: 11px;">{p_row['target_tier']}</span>
                    <div style="font-size: 24px; font-weight: 800; color: #F7F8FC; margin-top: 6px;">
                        {focus_p} (ID: {pid})
                    </div>
                    <div style="font-size: 13px; color: #A8B3CC; margin-top: 4px;">
                        Role: <b>{p_row['primary_role']}</b> | Data Credibility: <b>{p_row['credibility_weight']:.1f}%</b> ({p_row['uncertainty_tier']})
                    </div>
                </div>
                <div style="text-align: right; margin-top: 4px;">
                    <div style="font-size: 28px; font-weight: 900; color: {RR_PINK if is_b else RR_ELECTRIC};">
                        {p_row['comb_score']:.1f} <span style="font-size: 13px; color: #A8B3CC;">Combined</span>
                    </div>
                    <div style="font-size: 14px; font-weight: 700; color: {RR_GOLD};">
                        {f"IPL-Only: {p_row['ipl_score']:.1f}" if pd.notna(p_row['ipl_score']) else "IPL: No Sample"}
                    </div>
                </div>
            </div>
            <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 13px; color: #F7F8FC; line-height: 1.5;">
                <b style="color: {RR_GOLD};">🏰 Sawai Mansingh Stadium & RR Tactical Fit:</b> {dossier_item['rr_tactical_fit']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns([0.85, 0.15])
        with col_c2:
            st.button("❌ Clear Focus", on_click=handle_clear_auc_focus, use_container_width=True)


# ==================== 4. MAIN AUCTION WAR ROOM TABS ====================
tab_matrix, tab_splits, tab_roles, tab_uncert, tab_dossiers, tab_export = st.tabs([
    "🏆 IPL-Only vs Combined Matrix",
    "⚖️ Competition Disaggregation (IPL vs T20I)",
    "🎯 Roles & Phase Fingerprint",
    "🛡️ Uncertainty & Bayesian Credibility",
    "📁 Comprehensive Scouting Dossiers",
    "📥 Export Center (CSV & PDF)"
])

# ==================== TAB 1: IPL-ONLY VS COMBINED MATRIX ====================
with tab_matrix:
    st.markdown("### 🏆 Combined vs IPL-Only Benchmark Comparison")
    st.caption("Side-by-side verification: combined leaderboard incorporates all supplied matches (IPL + T20I + Asia Cup Rising Stars), while IPL-only strictly isolates IPL fixtures.")
    
    cat_toggle = st.radio("Focus Category:", ["Batters", "Bowlers"], horizontal=True, key="matrix_cat_toggle")
    
    if cat_toggle == "Batters":
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### 🌐 Combined Top 10 Batters (IPL + T20I)")
            st.caption("Evaluated on Deliveries with Match Pressure ≥65.0 (Composite Reliability Score 0–100). Official hackathon benchmark (min 60 HP balls).")
            st.dataframe(
                comb_bat[[
                    "rank", "player_name", "player_id", "reliability_score", "hp_balls",
                    "hp_runs", "hp_strike_rate", "hp_average", "sr_delta"
                ]].rename(columns={
                    "rank": "Rank", "player_name": "Player", "player_id": "ID",
                    "reliability_score": "Score", "hp_balls": "HP Balls",
                    "hp_runs": "Runs", "hp_strike_rate": "HP SR",
                    "hp_average": "HP Avg", "sr_delta": "Δ SR"
                }),
                use_container_width=True,
                hide_index=True
            )
            
        with c_right:
            st.markdown("#### 🇮🇳 IPL-Only Top 10 Batters")
            st.caption("Evaluated on Deliveries with Match Pressure ≥65.0 (Composite Reliability Score 0–100). Filtered strictly to IPL matches (min 60 HP balls).")
            st.dataframe(
                ipl_bat[[
                    "rank", "player_name", "player_id", "reliability_score", "hp_balls",
                    "hp_runs", "hp_strike_rate", "hp_average", "sr_delta"
                ]].rename(columns={
                    "rank": "Rank", "player_name": "Player", "player_id": "ID",
                    "reliability_score": "Score", "hp_balls": "IPL Balls",
                    "hp_runs": "Runs", "hp_strike_rate": "HP SR",
                    "hp_average": "HP Avg", "sr_delta": "Δ SR"
                }),
                use_container_width=True,
                hide_index=True
            )
            
        st.markdown("#### 📊 Overall vs IPL-Specific Reliability Delta (Batters)")
        st.plotly_chart(plot_ipl_vs_combined_scores(dossier_df, category="Batter"), use_container_width=True)
        
        st.markdown("""
        <div style="background: #111A32; border: 1px solid #1D2B52; border-left: 4px solid #E6007E; border-radius: 10px; padding: 14px 18px; margin-top: 10px; box-shadow: 0 4px 14px rgba(8,13,32,0.6);">
            <b style="color: #E6007E;">Key Analytical Takeaways (Batting):</b><br/>
            • <b>Rinku Singh (#1 in both):</b> Score of 85.3 (Combined) vs 85.9 (IPL). Invariant excellence under pressure.<br/>
            • <b>Tim David Surges in IPL (+4.6 pts):</b> Score rises from 75.8 (Combined) to 80.4 (IPL). His 194.5 IPL HP strike rate across 254 balls confirms him as an elite IPL power finisher.<br/>
            • <b>Dinesh Karthik Enters IPL Top 10 (#6):</b> 144 IPL pressure balls at 206.2 SR proves his dedicated domestic finisher pedigree.<br/>
            • <b>Towhid Hridoy & Matthew Wade Filter Out:</b> Their high combined rankings were driven entirely by international T20I matches (0 IPL balls).
        </div>
        """, unsafe_allow_html=True)
        
    else:
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### 🌐 Combined Top 10 Bowlers (IPL + T20I)")
            st.caption("Evaluated on Deliveries with Match Pressure ≥65.0 (Composite Reliability Score 0–100). Official hackathon benchmark (min 60 HP balls).")
            st.dataframe(
                comb_bowl[[
                    "rank", "player_name", "player_id", "reliability_score", "hp_legal_balls",
                    "hp_overs", "hp_wickets", "hp_economy", "hp_dot_pct"
                ]].rename(columns={
                    "rank": "Rank", "player_name": "Player", "player_id": "ID",
                    "reliability_score": "Score", "hp_legal_balls": "HP Balls",
                    "hp_overs": "Overs", "hp_wickets": "Wkts",
                    "hp_economy": "Econ", "hp_dot_pct": "Dot %"
                }),
                use_container_width=True,
                hide_index=True
            )
            
        with c_right:
            st.markdown("#### 🇮🇳 IPL-Only Top 10 Bowlers")
            st.caption("Evaluated on Deliveries with Match Pressure ≥65.0 (Composite Reliability Score 0–100). Filtered strictly to IPL matches (min 60 HP balls).")
            st.dataframe(
                ipl_bowl[[
                    "rank", "player_name", "player_id", "reliability_score", "hp_legal_balls",
                    "hp_overs", "hp_wickets", "hp_economy", "hp_dot_pct"
                ]].rename(columns={
                    "rank": "Rank", "player_name": "Player", "player_id": "ID",
                    "reliability_score": "Score", "hp_legal_balls": "IPL Balls",
                    "hp_overs": "Overs", "hp_wickets": "Wkts",
                    "hp_economy": "Econ", "hp_dot_pct": "Dot %"
                }),
                use_container_width=True,
                hide_index=True
            )
            
        st.markdown("#### 📊 Overall vs IPL-Specific Reliability Delta (Bowlers)")
        st.plotly_chart(plot_ipl_vs_combined_scores(dossier_df, category="Bowler"), use_container_width=True)
        
        st.markdown("""
        <div style="background: #111A32; border: 1px solid #1D2B52; border-left: 4px solid #287BFF; border-radius: 10px; padding: 14px 18px; margin-top: 10px; box-shadow: 0 4px 14px rgba(8,13,32,0.6);">
            <b style="color: #287BFF;">Key Analytical Takeaways (Bowling):</b><br/>
            • <b>Sunil Narine Holds #1 in Both:</b> Unrivaled pressure economy of 6.23 in IPL across 209 deliveries (34.5 overs).<br/>
            • <b>Yuzvendra Chahal Vaults to #2 in IPL:</b> In IPL conditions, Chahal's 25 pressure wickets and 8.76 economy rank him #2 in the entire league, validating him as RR's highest priority buy-back.<br/>
            • <b>Arshdeep Singh (#4) & Harshal Patel (#5):</b> Domestic seam workhorses who bowl over 70% of their pressure overs at the death, taking 29 and 32 pressure wickets respectively.<br/>
            • <b>International Disaggregation:</b> Haris Rauf, Shaheen Afridi, Sufiyan Muqeem, and Mujeeb Ur Rahman do not play IPL or had 0 IPL balls; their combined stats reflect bilateral T20Is only.
        </div>
        """, unsafe_allow_html=True)


# ==================== TAB 2: COMPETITION SPLITS ====================
with tab_splits:
    st.markdown("### ⚖️ Competition Disaggregation (IPL vs T20I Breakdown)")
    st.caption("Inspect how a candidate's high-pressure execution translates between the franchise tournament and international cricket.")
    
    player_options = filtered_dossier["player_name"].tolist() if not filtered_dossier.empty else dossier_df["player_name"].tolist()
    dflt_idx = player_options.index(focus_p) if focus_p in player_options else 0
    selected_player = st.selectbox("Select Candidate for Deep-Dive Split:", player_options, index=dflt_idx)
    
    p_data = dossier_df[dossier_df["player_name"] == selected_player].iloc[0]
    pid = int(p_data["player_id"])
    is_bat = p_data["category"] == "Batter"
    
    split_info = compute_player_competition_split(deliveries_df, pid, is_batter=is_bat)
    splits = split_info["splits"]
    
    c_split_left, c_split_right = st.columns([1.1, 0.9])
    
    with c_split_left:
        st.markdown(f"#### 📋 Performance Breakdown: {selected_player} (ID: {pid})")
        if is_bat:
            split_table = pd.DataFrame([
                {
                    "Competition": "IPL Only",
                    "Matches": splits["IPL"]["matches"],
                    "HP Balls": splits["IPL"]["hp_balls"],
                    "HP Runs": splits["IPL"]["hp_runs"],
                    "HP SR": f"{splits['IPL']['hp_sr']:.1f}",
                    "HP Avg": f"{splits['IPL']['hp_avg']:.1f}",
                    "Bnd %": f"{splits['IPL']['boundary_pct']:.1f}%",
                    "Dot %": f"{splits['IPL']['dot_pct']:.1f}%",
                    "Normal SR": f"{splits['IPL']['norm_sr']:.1f}",
                    "Clutch Δ SR": f"{splits['IPL']['sr_delta']:+.1f}"
                },
                {
                    "Competition": "T20I Only",
                    "Matches": splits["T20I"]["matches"],
                    "HP Balls": splits["T20I"]["hp_balls"],
                    "HP Runs": splits["T20I"]["hp_runs"],
                    "HP SR": f"{splits['T20I']['hp_sr']:.1f}",
                    "HP Avg": f"{splits['T20I']['hp_avg']:.1f}",
                    "Bnd %": f"{splits['T20I']['boundary_pct']:.1f}%",
                    "Dot %": f"{splits['T20I']['dot_pct']:.1f}%",
                    "Normal SR": f"{splits['T20I']['norm_sr']:.1f}",
                    "Clutch Δ SR": f"{splits['T20I']['sr_delta']:+.1f}"
                },
                {
                    "Competition": "Combined Benchmark",
                    "Matches": splits["Combined"]["matches"],
                    "HP Balls": splits["Combined"]["hp_balls"],
                    "HP Runs": splits["Combined"]["hp_runs"],
                    "HP SR": f"{splits['Combined']['hp_sr']:.1f}",
                    "HP Avg": f"{splits['Combined']['hp_avg']:.1f}",
                    "Bnd %": f"{splits['Combined']['boundary_pct']:.1f}%",
                    "Dot %": f"{splits['Combined']['dot_pct']:.1f}%",
                    "Normal SR": f"{splits['Combined']['norm_sr']:.1f}",
                    "Clutch Δ SR": f"{splits['Combined']['sr_delta']:+.1f}"
                }
            ])
        else:
            split_table = pd.DataFrame([
                {
                    "Competition": "IPL Only",
                    "Matches": splits["IPL"]["matches"],
                    "HP Balls": splits["IPL"]["hp_legal_balls"],
                    "Overs": f"{splits['IPL']['hp_overs']:.1f}",
                    "Wkts": splits["IPL"]["hp_wickets"],
                    "HP Econ": f"{splits['IPL']['hp_economy']:.2f}",
                    "Dot %": f"{splits['IPL']['dot_pct']:.1f}%",
                    "Normal Econ": f"{splits['IPL']['norm_economy']:.2f}",
                    "Clutch Δ Econ": f"{splits['IPL']['econ_delta']:+.2f}"
                },
                {
                    "Competition": "T20I Only",
                    "Matches": splits["T20I"]["matches"],
                    "HP Balls": splits["T20I"]["hp_legal_balls"],
                    "Overs": f"{splits['T20I']['hp_overs']:.1f}",
                    "Wkts": splits["T20I"]["hp_wickets"],
                    "HP Econ": f"{splits['T20I']['hp_economy']:.2f}",
                    "Dot %": f"{splits['T20I']['dot_pct']:.1f}%",
                    "Normal Econ": f"{splits['T20I']['norm_economy']:.2f}",
                    "Clutch Δ Econ": f"{splits['T20I']['econ_delta']:+.2f}"
                },
                {
                    "Competition": "Combined Benchmark",
                    "Matches": splits["Combined"]["matches"],
                    "HP Balls": splits["Combined"]["hp_legal_balls"],
                    "Overs": f"{splits['Combined']['hp_overs']:.1f}",
                    "Wkts": splits["Combined"]["hp_wickets"],
                    "HP Econ": f"{splits['Combined']['hp_economy']:.2f}",
                    "Dot %": f"{splits['Combined']['dot_pct']:.1f}%",
                    "Normal Econ": f"{splits['Combined']['norm_economy']:.2f}",
                    "Clutch Δ Econ": f"{splits['Combined']['econ_delta']:+.2f}"
                }
            ])
            
        st.dataframe(split_table, use_container_width=True, hide_index=True)
        analytical_note = split_info.get("analytical_note") or f"Evaluation based on high-pressure deliveries (Pressure ≥ 65.0) across IPL and T20I competitions."
        st.caption(f"**Analytical Note:** {analytical_note}")
        
    with c_split_right:
        st.plotly_chart(
            plot_single_player_split(splits, selected_player, is_batter=is_bat),
            use_container_width=True
        )


# ==================== TAB 3: ROLES & PHASE ALLOCATION ====================
with tab_roles:
    st.markdown("### 🎯 Empirical Role Classification & Phase Fingerprint")
    st.caption("Tactical role classification derived from measured ball distribution across Powerplay (1-6), Middle (7-16), and Death (17-20).")
    
    st.plotly_chart(plot_phase_allocation_stacked(dossier_df), use_container_width=True)
    
    st.dataframe(
        filtered_dossier[[
            "player_name", "category", "primary_role", "batting_hand",
            "powerplay_pct", "middle_pct", "death_pct", "target_tier"
        ]].rename(columns={
            "player_name": "Player", "category": "Category", "primary_role": "Tactical Role",
            "batting_hand": "Hand / Style", "powerplay_pct": "PP %", "middle_pct": "Mid %",
            "death_pct": "Death %", "target_tier": "Recruitment Tier"
        }),
        use_container_width=True,
        hide_index=True
    )


# ==================== TAB 4: UNCERTAINTY & CREDIBILITY ====================
with tab_uncert:
    st.markdown("### 🛡️ Sample-Size Uncertainty & Bayesian Credibility Framework")
    st.caption("Ensuring statistical fairness: small-sample anomalies are shrunk toward league baseline priors using Empirical Bayes.")
    
    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-radius: 10px; padding: 16px 20px; margin-bottom: 16px;">
        <h4 style="color: #E6007E; margin-top: 0;">Statistical Regularization Architecture</h4>
        • <b>Bayesian Credibility Weight:</b> <code>w_i = n_i / (n_i + 50)</code>. A player with 250 balls receives 83.3% credibility from their observed data, whereas a player with 60 balls receives only 54.5%.<br/>
        • <b>Opportunity Factor:</b> Scaled by <code>min(1.0, 0.70 + 0.30 · (n_i / 180))</code>, ensuring multi-year proven contributors are rewarded over single-season bursts.<br/>
        • <b>Margin of Error (95% CI):</b> Derived asymptotically via <code>± 1.96 · (16.0 / √(n_i / 25))</code>.
    </div>
    """, unsafe_allow_html=True)
    
    st.dataframe(
        filtered_dossier[[
            "player_name", "category", "comb_hp_balls", "uncertainty_tier",
            "credibility_weight", "comb_score", "ipl_score"
        ]].rename(columns={
            "player_name": "Player", "category": "Category", "comb_hp_balls": "Total HP Balls",
            "uncertainty_tier": "Certainty Tier", "credibility_weight": "Data Credibility %",
            "comb_score": "Combined Score", "ipl_score": "IPL Score"
        }),
        use_container_width=True,
        hide_index=True
    )


# ==================== TAB 5: SCOUTING DOSSIERS ====================
with tab_dossiers:
    st.markdown("### 📁 Comprehensive Auction Scouting Dossiers (28 Shortlisted Candidates)")
    st.caption("In-depth tactical profiles combining measured empirical data, statistical watchpoints, and Rajasthan Royals Jaipur fortress suitability.")
    
    for _, row in filtered_dossier.iterrows():
        pname = row["player_name"]
        pid = int(row["player_id"])
        is_b = row["category"] == "Batter"
        tier = row["target_tier"]
        role = row["primary_role"]
        
        c_score = row["comb_score"]
        i_score = row["ipl_score"]
        score_text = f"Combined: {c_score:.1f}" + (f" | IPL-Only: {i_score:.1f}" if pd.notna(i_score) else " | IPL: N/A")
        
        is_focused = bool(focus_p and pname == focus_p)
        with st.expander(f"⭐ {pname} (ID: {pid}) — {role} | [{tier}] — {score_text} {'★ ACTIVE FOCUS' if is_focused else ''}", expanded=is_focused):
            col_d1, col_d2 = st.columns([1.1, 0.9])
            
            with col_d1:
                st.markdown(f"**Primary Role:** `{role}` ({row['batting_hand']})")
                st.markdown(f"**Recruitment Tier:** `{tier}`")
                st.markdown(f"**Uncertainty Level:** `{row['uncertainty_tier']}` ({row['credibility_weight']:.1f}% data weight)")
                
                dossier = build_auction_dossier(deliveries_df, pid, is_batter=is_b, comb_score=c_score, ipl_score=i_score)
                
                st.markdown("##### 🔍 Empirically Verified Strengths")
                for s in dossier["strengths"]:
                    st.markdown(f"• {s}")
                    
                st.markdown("##### ⚠️ Analytical Watchpoints & Limitations")
                for lim in dossier["limitations"]:
                    st.markdown(f"• {lim}")
                    
            with col_d2:
                st.markdown("##### 🏰 Sawai Mansingh Stadium (Jaipur) & RR Fit")
                st.markdown(f"""
                <div style="background: rgba(23, 70, 162, 0.20); border: 1px solid rgba(40, 123, 255, 0.35); border-radius: 8px; padding: 12px 14px; font-size: 13px; line-height: 1.5; color: #F7F8FC;">
                    {dossier['rr_tactical_fit']}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br/>", unsafe_allow_html=True)
                st.markdown("##### 📊 Measured High-Pressure Evidence")
                sp = dossier["splits"]
                if is_b:
                    st.markdown(f"• **IPL HP Balls:** {sp['IPL']['hp_balls']} (SR {sp['IPL']['hp_sr']:.1f}, Avg {sp['IPL']['hp_avg']:.1f})")
                    st.markdown(f"• **T20I HP Balls:** {sp['T20I']['hp_balls']} (SR {sp['T20I']['hp_sr']:.1f}, Avg {sp['T20I']['hp_avg']:.1f})")
                    st.markdown(f"• **Clutch Gear Shift (Δ SR):** {sp['Combined']['sr_delta']:+.1f} above baseline")
                else:
                    st.markdown(f"• **IPL HP Balls:** {sp['IPL']['hp_legal_balls']} ({sp['IPL']['hp_overs']:.1f} ov, Econ {sp['IPL']['hp_economy']:.2f}, {sp['IPL']['hp_wickets']} Wkts)")
                    st.markdown(f"• **T20I HP Balls:** {sp['T20I']['hp_legal_balls']} ({sp['T20I']['hp_overs']:.1f} ov, Econ {sp['T20I']['hp_economy']:.2f}, {sp['T20I']['hp_wickets']} Wkts)")
                    st.markdown(f"• **Clutch Economy Delta:** {sp['Combined']['econ_delta']:+.2f} RPO improvement")
                st.markdown(f"• **Phase Allocation:** PP: {dossier['phase_distribution']['Powerplay']:.0f}% | Mid: {dossier['phase_distribution']['Middle']:.0f}% | Death: {dossier['phase_distribution']['Death']:.0f}%")


# ==================== TAB 6: EXPORT CENTER ====================
with tab_export:
    st.markdown("### 📥 Official Rajasthan Royals Auction Intelligence Exports")
    st.caption("Download verified, uncorrupted research assets formatted for franchise war-room distribution.")
    
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    
    with col_e1:
        ipl_bat_csv = ipl_bat.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📄 Export IPL-Only Batters (CSV)",
            data=ipl_bat_csv,
            file_name="RR_IPL_Only_Top_10_Batters.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with col_e2:
        ipl_bowl_csv = ipl_bowl.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📄 Export IPL-Only Bowlers (CSV)",
            data=ipl_bowl_csv,
            file_name="RR_IPL_Only_Top_10_Bowlers.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with col_e3:
        dossier_csv = dossier_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📋 Export Full Auction Dossier (CSV)",
            data=dossier_csv,
            file_name="RR_Auction_Shortlist_Comprehensive_Dossier.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with col_e4:
        summary_stats = {
            "total_deliveries": len(deliveries_df),
            "total_matches": deliveries_df["match_id"].nunique()
        }
        auction_pdf_bytes = build_auction_pdf_report(
            dossier_df, ipl_bat, ipl_bowl, comb_bat, comb_bowl, summary_stats
        )
        st.download_button(
            "📑 Download Official Auction PDF",
            data=auction_pdf_bytes,
            file_name="RR_IPL_2027_Auction_Intelligence_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

st.markdown("---")
st.caption("SupeRR SCOUT Pressure Intelligence Engine | Rajasthan Royals IPL 2027 Auction Analytics Build | Verified Local Execution")
