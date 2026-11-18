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
tab_lead, tab_compare, tab_dossiers, tab_unstop = st.tabs([
    f"🏆 Top 10 { 'Batters' if is_batter else 'Bowlers'} Leaderboard",
    "⚔️ Top 10 Head-to-Head Duel",
    "📁 Individual Evidence Dossiers",
    "📋 Unstop Official Submission Table"
])

with tab_lead:
    st.markdown(f"#### Top 10 { 'Batters' if is_batter else 'Bowlers'} ({st.session_state['top10_scope']})")
    st.caption("Click any bar on the chart to spotlight that player across the war room.")

    # Search and Sort Controls
    col_ctrl_search, col_ctrl_sort = st.columns([1.5, 2.5])
    with col_ctrl_search:
        search_query = st.text_input("🔍 Filter by Player Name:", placeholder="Type to filter...", key="top10_search_box")
    with col_ctrl_sort:
        sort_choice = st.selectbox(
            "Sort Table By:",
            options=["Reliability Score (Official Rank)", "High-Pressure Deliveries", "HP Strike Rate / Economy", "Clutch Delta"],
            key="top10_sort_choice"
        )

    filtered_display_df = active_df.copy()
    if search_query.strip():
        filtered_display_df = filtered_display_df[
            filtered_display_df["player_name"].str.contains(search_query.strip(), case=False, na=False)
        ]

    if "Deliveries" in sort_choice:
        sort_c = "hp_balls" if is_batter else "hp_legal_balls"
        filtered_display_df = filtered_display_df.sort_values(sort_c, ascending=False)
    elif "Strike Rate" in sort_choice:
        if is_batter:
            filtered_display_df = filtered_display_df.sort_values("hp_strike_rate", ascending=False)
        else:
            filtered_display_df = filtered_display_df.sort_values("hp_economy", ascending=True)
    elif "Clutch Delta" in sort_choice:
        if is_batter:
            filtered_display_df = filtered_display_df.sort_values("sr_delta", ascending=False)
        else:
            filtered_display_df = filtered_display_df.sort_values("econ_delta", ascending=True)
    else:
        filtered_display_df = filtered_display_df.sort_values("rank", ascending=True)

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
            bat_disp = filtered_display_df[[
                "rank", "player_name", "player_id", "reliability_score", "hp_balls",
                "hp_strike_rate", "hp_average", "sr_delta", "confidence_interval"
            ]].copy()
            bat_disp.columns = ["Rank", "Player", "ID", "Score", "HP Balls", "HP SR", "HP Avg", "Δ SR", "95% CI"]
            st.dataframe(bat_disp, use_container_width=True, hide_index=True)
        else:
            bowl_disp = filtered_display_df[[
                "rank", "player_name", "player_id", "reliability_score", "hp_legal_balls", "hp_overs",
                "hp_wickets", "hp_economy", "econ_delta", "confidence_interval"
            ]].copy()
            bowl_disp.columns = ["Rank", "Player", "ID", "Score", "HP Balls", "Overs", "Wkts", "HP Econ", "Δ Econ", "95% CI"]
            st.dataframe(bowl_disp, use_container_width=True, hide_index=True)

        csv_bytes = filtered_display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"📥 Download Displayed { 'Batters' if is_batter else 'Bowlers'} CSV",
            data=csv_bytes,
            file_name=f"Top_10_{'Batters' if is_batter else 'Bowlers'}_{st.session_state['top10_scope'].replace(' ', '_')}.csv",
            mime="text/csv"
        )

    # Ranking Explanation Callout
    if not active_df.empty:
        top_hero = active_df.iloc[0]
        n_opp = top_hero["hp_balls"] if is_batter else top_hero["hp_legal_balls"]
        w_cred = (n_opp / (n_opp + 50.0)) * 100.0

        if is_batter:
            realization_str = f"a Strike Rate of <b>{top_hero['hp_strike_rate']:.1f}</b> and Average of <b>{top_hero['hp_average']:.1f}</b>"
            clutch_delta_val = top_hero.get("sr_delta", 0.0)
            clutch_delta_str = f"{clutch_delta_val:+.1f} SR"
        else:
            realization_str = f"an Economy of <b>{top_hero['hp_economy']:.2f} RPO</b> with <b>{int(top_hero['hp_wickets'])}</b> wickets"
            clutch_delta_val = top_hero.get("econ_delta", 0.0)
            clutch_delta_str = f"{clutch_delta_val:+.2f} Econ"

        ci_str = str(top_hero.get("confidence_interval", "N/A"))

        with st.expander(f"ℹ️ Why is {top_hero['player_name']} Ranked #1? (Mathematical Derivation Breakdown)"):
            st.markdown(f"""
            <div style="font-size: 13px; line-height: 1.6; color: #A8B3CC;">
                <b style="color: #F7F8FC;">1. Sample Volume & Bayesian Credibility:</b><br/>
                With <b>{int(n_opp)}</b> high-pressure balls, {top_hero['player_name']} receives a data credibility weight of <b>{w_cred:.1f}%</b> under the Empirical Bayes model (<code>w = n / (n + 50)</code>).<br/><br/>
                <b style="color: #F7F8FC;">2. High-Pressure Realization:</b><br/>
                Under extreme match leverage (P ≥ 65.0), {top_hero['player_name']} records {realization_str}.<br/><br/>
                <b style="color: #F7F8FC;">3. Clutch Elevation Factor:</b><br/>
                {top_hero['player_name']} elevates performance under pressure with a clutch delta of
                <b style="color: #2ECC71;">{clutch_delta_str}</b> relative to standard conditions.<br/><br/>
                <b style="color: #F7F8FC;">4. Uncertainty Regularization:</b><br/>
                The 95% Confidence Interval is compact at <code>{ci_str}</code>, verifying statistical stability.
            </div>
            """, unsafe_allow_html=True)

with tab_compare:
    st.markdown("#### ⚔️ Top 10 Head-to-Head Comparison")
    st.caption("Select any two players from the Top 10 to inspect side-by-side metric differentials.")

    p_names_list = active_df["player_name"].tolist()
    if len(p_names_list) >= 2:
        col_c_p1, col_c_p2 = st.columns(2)
        with col_c_p1:
            p1 = st.selectbox("Select Player 1:", options=p_names_list, index=0, key="duel_p1")
        with col_c_p2:
            p2 = st.selectbox("Select Player 2:", options=p_names_list, index=1, key="duel_p2")

        row_p1 = active_df[active_df["player_name"] == p1].iloc[0]
        row_p2 = active_df[active_df["player_name"] == p2].iloc[0]

        if is_batter:
            p1_stat_line = f"HP SR: <b>{row_p1['hp_strike_rate']:.1f}</b> | HP Avg: <b>{row_p1['hp_average']:.1f}</b>"
            p1_balls = int(row_p1["hp_balls"])
            p1_delta = row_p1.get("sr_delta", 0.0)
            p1_elev = " (Elevated)" if p1_delta > 0 else ""
            p1_clutch = f"<b>{p1_delta:+.1f} SR</b>{p1_elev}"

            p2_stat_line = f"HP SR: <b>{row_p2['hp_strike_rate']:.1f}</b> | HP Avg: <b>{row_p2['hp_average']:.1f}</b>"
            p2_balls = int(row_p2["hp_balls"])
            p2_delta = row_p2.get("sr_delta", 0.0)
            p2_elev = " (Elevated)" if p2_delta > 0 else ""
            p2_clutch = f"<b>{p2_delta:+.1f} SR</b>{p2_elev}"
        else:
            p1_stat_line = f"HP Econ: <b>{row_p1['hp_economy']:.2f}</b> | Wkts: <b>{int(row_p1['hp_wickets'])}</b>"
            p1_balls = int(row_p1["hp_legal_balls"])
            p1_delta = row_p1.get("econ_delta", 0.0)
            p1_clutch = f"<b>{p1_delta:+.2f} Econ</b>"

            p2_stat_line = f"HP Econ: <b>{row_p2['hp_economy']:.2f}</b> | Wkts: <b>{int(row_p2['hp_wickets'])}</b>"
            p2_balls = int(row_p2["hp_legal_balls"])
            p2_delta = row_p2.get("econ_delta", 0.0)
            p2_clutch = f"<b>{p2_delta:+.2f} Econ</b>"

        col_card1, col_card2 = st.columns(2)
        with col_card1:
            st.markdown(f"""
            <div class="rr-card" style="border-top: 3px solid {RR_PINK if is_batter else RR_ELECTRIC}; padding: 18px;">
                <div style="font-size: 11px; color: #A8B3CC;">RANK #{row_p1['rank']}</div>
                <div style="font-size: 20px; font-weight: 800; color: #F7F8FC;">{p1}</div>
                <div style="font-size: 26px; font-weight: 900; color: {RR_PINK if is_batter else RR_ELECTRIC}; margin-top: 4px;">
                    {row_p1['reliability_score']:.1f}<span style="font-size: 13px; color: #A8B3CC;">/100</span>
                </div>
                <div style="font-size: 12px; color: #A8B3CC; margin-top: 8px;">
                    {p1_stat_line}<br/>
                    HP Deliveries: <b>{p1_balls}</b><br/>
                    Clutch Delta: {p1_clutch}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_card2:
            st.markdown(f"""
            <div class="rr-card" style="border-top: 3px solid {RR_GOLD}; padding: 18px;">
                <div style="font-size: 11px; color: #A8B3CC;">RANK #{row_p2['rank']}</div>
                <div style="font-size: 20px; font-weight: 800; color: #F7F8FC;">{p2}</div>
                <div style="font-size: 26px; font-weight: 900; color: {RR_GOLD}; margin-top: 4px;">
                    {row_p2['reliability_score']:.1f}<span style="font-size: 13px; color: #A8B3CC;">/100</span>
                </div>
                <div style="font-size: 12px; color: #A8B3CC; margin-top: 8px;">
                    {p2_stat_line}<br/>
                    HP Deliveries: <b>{p2_balls}</b><br/>
                    Clutch Delta: {p2_clutch}
                </div>
            </div>
            """, unsafe_allow_html=True)

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

    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        unstop_csv = unstop_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Unstop Submission (CSV)",
            data=unstop_csv,
            file_name="SupeRR_Scout_Top10_Submission.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_u2:
        pdf_path = Path("assets/SupeRR_Scout_Official_Unstop_Report.pdf")
        if not pdf_path.exists():
            pdf_path = Path("assets/SupeRR_Scout_Auction_Report.pdf")
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                "📄 Unstop Report (PDF)",
                data=pdf_bytes,
                file_name="SupeRR_Scout_Official_Unstop_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    with col_u3:
        analytics_pdf_path = Path("assets/SupeRR_Scout_Data_Analytics_Report.pdf")
        if analytics_pdf_path.exists():
            with open(analytics_pdf_path, "rb") as f:
                analytics_pdf_bytes = f.read()
            st.download_button(
                "📊 Analytics Whitepaper (PDF)",
                data=analytics_pdf_bytes,
                file_name="SupeRR_Scout_Data_Analytics_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
