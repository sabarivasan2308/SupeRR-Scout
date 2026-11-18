"""
Page 8: IPL 2027 Rajasthan Royals Auction Intelligence War Room
Empirical Pressure Reliability vs Verified Player Availability & Squad Strategy.

Features:
- Franchise-wise Availability Explorer & Official Retention Matrix (All 10 Franchises)
- Strictly Filtered Auction-Eligible Player Rankings (Retained/Contracted Excluded)
- Rajasthan Royals Tactical Squad Gap Analysis & Priority Shortlist
- Budget-Aware Squad Planner & Auction Simulator (RR 20-Player Roster, 5 Slots Open, 2 Overseas Open)
- Historical Multi-Competition Disaggregation (IPL vs International & Emerging T20)
- Jaipur Sawai Mansingh Stadium Tactical Suitability Dossiers & PDF Export
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np

from src.ui_helpers import (
    inject_custom_css, load_core_data, render_sidebar_filters, filter_deliveries
)
from src.auction_intelligence import (
    compute_player_competition_split, classify_player_role_and_phases,
    generate_all_auction_assets, build_auction_dossier
)
from src.player_availability import (
    load_player_status_registry, get_player_availability, is_player_auction_eligible,
    filter_available_rankings, get_rr_squad_state, get_rr_squad_gaps,
    get_rr_priority_shortlist, get_unverified_shortlist_targets, get_franchise_availability_summary,
    STATUS_AUCTION_ELIGIBLE, STATUS_RETAINED, STATUS_CONTRACTED,
    STATUS_RR_CURRENT, STATUS_INELIGIBLE, STATUS_WITHDRAWN_RETIRED, STATUS_UNVERIFIED,
    RR_SQUAD_LIMIT, RR_MIN_SQUAD, RR_OVERSEAS_LIMIT
)
from src.visualizations import (
    plot_ipl_vs_combined_scores, plot_phase_allocation_stacked,
    plot_single_player_split, plot_squad_budget_chart, apply_rr_theme,
    RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY, RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN
)
from src.squad_planner import (
    compute_squad_financials, analyze_squad_balance, compare_saved_scenarios,
    DEFAULT_PURSE_INR_CR, MAX_OVERSEAS_PLAYERS
)
from src.report_generator import build_auction_pdf_report

st.set_page_config(
    page_title="IPL 2027 Auction War Room | SupeRR SCOUT",
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

# Precompute available rankings
avail_batters = filter_available_rankings(comb_bat, is_batter=True)
avail_bowlers = filter_available_rankings(comb_bowl, is_batter=False)
rr_squad_state = get_rr_squad_state()
rr_gaps = get_rr_squad_gaps()
rr_shortlist = get_rr_priority_shortlist(deliveries_df)

# Session State for Auction War Room
if "auc_category" not in st.session_state:
    st.session_state["auc_category"] = "All Candidates"
if "auc_tier" not in st.session_state:
    st.session_state["auc_tier"] = "All Tiers"
if "auc_focus_player" not in st.session_state:
    st.session_state["auc_focus_player"] = None
if "squad_bids" not in st.session_state:
    st.session_state["squad_bids"] = {
        "Towhid Hridoy": 2.50,
        "Taskin Ahmed": 4.00,
        "Mustafizur Rahman": 4.50,
        "Nahid Rana": 2.00,
        "Mohammad Rishad Hossain": 2.00
    }
if "squad_scenarios" not in st.session_state:
    st.session_state["squad_scenarios"] = {}
if "selected_draft_players" not in st.session_state:
    # Default to verified auction-eligible targets that fill RR gaps
    st.session_state["selected_draft_players"] = [
        "Towhid Hridoy", "Taskin Ahmed", "Mustafizur Rahman"
    ]

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
            <div class="rr-title">8. IPL 2027 Rajasthan Royals Auction War Room</div>
            <div class="rr-subtitle">Verified Player Availability Filtering, Tactical Squad Gaps & Strategic Recruitment Intelligence</div>
        </div>
        <div style="text-align: right; margin-top: 4px;">
            <span class="rr-badge rr-badge-pink" style="font-size: 11px; padding: 4px 12px;">RR IPL 2027 WAR ROOM</span>
        </div>
    </div>
    <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
        <span style="font-size: 11px; font-weight: 700; color: #A8B3CC; letter-spacing: 0.5px;">WAR ROOM STATUS:</span>
        <span class="rr-badge rr-badge-navy">Target Franchise: Rajasthan Royals</span>
        <span class="rr-badge rr-badge-gold">Confirmed Roster: 19/25 (6 Open Slots)</span>
        <span class="rr-badge rr-badge-pink">Overseas: 5/8 (3 Open Slots)</span>
        <span class="rr-badge rr-badge-gold">Available Purse: ₹27.05 Cr</span>
        <span class="rr-badge rr-badge-blue">Venue Engine: SMS Jaipur (Par 8.4 RPO)</span>
        {focus_badge}
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== 2. FOUR STRATEGIC AUCTION KPI CARDS ====================
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="rr-kpi-card" style="border-top: 3px solid #E6007E;">
        <div class="rr-kpi-title">RR Squad Capacity</div>
        <div class="rr-kpi-value">{rr_squad_state['squad_size']} / {rr_squad_state['max_squad_limit']}</div>
        <div class="rr-kpi-sub-pink"><b>{rr_squad_state['remaining_squad_capacity']} Open Slots</b> to Fill in Auction</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="rr-kpi-card" style="border-top: 3px solid #287BFF;">
        <div class="rr-kpi-title">RR Overseas Slots</div>
        <div class="rr-kpi-value">{rr_squad_state['overseas_count']} / {rr_squad_state['max_overseas_limit']}</div>
        <div class="rr-kpi-sub-blue"><b>{rr_squad_state['remaining_overseas_capacity']} Overseas Slots</b> Remaining</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="rr-kpi-card" style="border-top: 3px solid #F39C12;">
        <div class="rr-kpi-title">Verified Available Targets</div>
        <div class="rr-kpi-value">{len(avail_batters) + len(avail_bowlers)}</div>
        <div class="rr-kpi-sub" style="color: #F39C12;">100% Eligible (Retained Stars Excluded)</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="rr-kpi-card" style="border-top: 3px solid #2ECC71;">
        <div class="rr-kpi-title">RR Priority Shortlist</div>
        <div class="rr-kpi-value">{len(rr_shortlist)} Targets</div>
        <div class="rr-kpi-sub" style="color: #2ECC71;">Curated for 4 Critical Squad Gaps</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)


# ==================== 3. MAIN WAR ROOM TABS ====================
tab_gaps, tab_avail, tab_rankings, tab_planner, tab_history, tab_export = st.tabs([
    "⚔️ RR Squad Gaps & Priority Shortlist",
    "🏛️ Franchise Availability Explorer",
    "🎯 Verified Available Rankings",
    "💰 Squad Planner & Budget Simulator",
    "🏆 Historical Benchmarks (Combined vs IPL)",
    "📥 War Room Export Center"
])


# ==================== TAB 1: RR SQUAD GAPS & PRIORITY SHORTLIST ====================
with tab_gaps:
    st.markdown("### ⚔️ Rajasthan Royals Tactical Squad Gaps & Priority Targets")
    st.caption("Derived by analyzing Rajasthan Royals' confirmed 19-player roster and ₹27.05 Cr remaining purse (Official 17-Nov-2026 Announcement) against high-leverage execution requirements at Sawai Mansingh Stadium.")

    st.markdown("""
    <div style="background: #111A32; border: 1px solid #1D2B52; border-left: 4px solid #E6007E; border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;">
        <b style="color: #E6007E;">Rajasthan Royals IPL 2027 Confirmed Baseline (17-Nov-2026 Announcement):</b><br/>
        • <b>Confirmed Roster (19 Players | ₹27.05 Cr Remaining Purse):</b> Riyan Parag (C), Yashasvi Jaiswal, Ravindra Jadeja, Dhruv Jurel, Jofra Archer, Mohammed Shami (Traded in for ₹8.0 Cr), Sandeep Sharma, Ravi Bishnoi, Nandre Burger, Donovan Ferreira, Dasun Shanaka, M Siddharth (Traded in for ₹0.75 Cr), Lhuan-dre Pretorius, Sushant Mishra, Shubham Dubey, Vaibhav Sooryavanshi.<br/>
        • <b>Key Released Assets:</b> Shimron Hetmyer, Tushar Deshpande, Kwena Maphaka, Adam Milne, Kuldeep Sen, Yudhvir Singh.<br/>
        • <b>Immediate Priorities (6 Slots, 3 Overseas):</b> Urgent replacement for released finisher Shimron Hetmyer; express death pacer reinforcement to cover Shami & Archer workloads; powerplay left-arm swing option.
    </div>
    """, unsafe_allow_html=True)

    # 4 Gap Cards
    gap_cols = st.columns(len(rr_gaps))
    for i, g in enumerate(rr_gaps):
        with gap_cols[i]:
            badge_color = "#E6007E" if g["priority"] == "HIGH" else "#287BFF" if g["priority"] == "MEDIUM" else "#A8B3CC"
            st.markdown(f"""
            <div style="background: #111A32; border: 1px solid #1D2B52; border-top: 3px solid {badge_color}; border-radius: 10px; padding: 14px 16px; height: 100%; box-shadow: 0 4px 14px rgba(8,13,32,0.6);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="rr-badge" style="background: rgba(230,0,126,0.15); color: {badge_color}; font-size: 10px; padding: 2px 8px;">{g['priority']} PRIORITY</span>
                    <span style="font-size: 11px; font-weight: 700; color: #A8B3CC;">Gap #{i+1}</span>
                </div>
                <div style="font-size: 14px; font-weight: 800; color: #F7F8FC; margin-top: 8px;">{g['gap_name']}</div>
                <div style="font-size: 11px; color: #A8B3CC; margin-top: 6px; line-height: 1.4;">{g['description']}</div>
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #1D2B52; font-size: 11px; color: {RR_GOLD};">
                    <b>Targets:</b> {", ".join(g['recommended_targets'])}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("#### 🎯 Curated Rajasthan Royals Priority Shortlist (100% Verified Auction-Eligible)")
    st.caption("Every candidate in this shortlist is verified available for auction bidding, possesses proven pressure metrics, and fills an exact RR squad gap.")

    shortlist_df = pd.DataFrame(rr_shortlist)
    display_shortlist = shortlist_df[[
        "player_name", "category", "tactical_role", "hp_balls",
        "hp_metric", "base_price_cr", "estimated_bid_min_cr", "estimated_bid_max_cr"
    ]].rename(columns={
        "player_name": "Target Candidate",
        "category": "Discipline",
        "tactical_role": "Primary Tactical Role",
        "hp_balls": "HP Balls Faced/Bowled",
        "hp_metric": "HP Metric (SR / Econ)",
        "base_price_cr": "Base Price (₹ Cr)",
        "estimated_bid_min_cr": "Est. Min Bid (₹ Cr)",
        "estimated_bid_max_cr": "Est. Max Bid (₹ Cr)"
    })

    st.dataframe(display_shortlist, use_container_width=True, hide_index=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("#### 📁 Deep-Dive Tactical Dossiers & Sawai Mansingh Stadium Fit")
    for item in rr_shortlist:
        pname = item["player_name"]
        pid = item["player_id"]
        role = item["tactical_role"]
        base_p = item["base_price_cr"]
        bid_range = f"₹{item['estimated_bid_min_cr']:.2f} – ₹{item['estimated_bid_max_cr']:.2f} Cr"

        with st.expander(f"⭐ {pname} (ID: {pid}) — {role} | Base: ₹{base_p:.2f} Cr | Est. Value: {bid_range}"):
            col_t1, col_t2 = st.columns([1.1, 0.9])
            with col_t1:
                st.markdown(f"**Discipline:** `{item['category']}` | **Tactical Role:** `{role}`")
                st.markdown(f"**High-Pressure Exposure:** `{item['hp_balls']}` balls under match leverage ≥65.0")
                st.markdown(f"**Key HP Execution:** `{item['hp_metric_label']}: {item['hp_metric']:.2f}`")
                st.markdown(f"**Official Base Price:** `₹{base_p:.2f} Cr` | **Target Valuation:** `{bid_range}`")
                st.markdown("**Key Empirical Strengths:**")
                for s in item["strengths"]:
                    st.markdown(f"• {s}")
            with col_t2:
                st.markdown(f"""
                <div style="background: #0E162B; border: 1px solid #1D2B52; border-radius: 8px; padding: 14px; font-size: 12px; line-height: 1.5;">
                    <b style="color: {RR_GOLD};">🏰 Sawai Mansingh Stadium (Jaipur) Fit:</b><br/>
                    {item['rr_tactical_fit']}
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown("**Scouting Watchpoints / Limitations:**")
                for lim in item["limitations"]:
                    st.markdown(f"• {lim}")

    # Excluded & Unverified Candidates Audit
    st.markdown("<br/>", unsafe_allow_html=True)
    with st.expander("⚠️ Excluded & Unverified Candidates Audit (Strict Availability Governance)"):
        st.markdown("""
        **Regulatory Notice:** Per strict franchise risk governance, a released player is **NOT** automatically auction-eligible.
        Players whose official auction registration or retention status cannot be confirmed via an authoritative primary source
        are marked `UNVERIFIED` or `RETAINED` and **strictly excluded** from verified auction recommendations.
        """)
        unverified_list = get_unverified_shortlist_targets()
        unv_df = pd.DataFrame(unverified_list).rename(columns={
            "name": "Player Name",
            "status": "Audit Status",
            "franchise": "Franchise / Prior Team",
            "reason": "Authoritative Audit Reason"
        })
        st.dataframe(unv_df, use_container_width=True, hide_index=True)


# ==================== TAB 2: FRANCHISE AVAILABILITY EXPLORER ====================
with tab_avail:
    st.markdown("### 🏛️ All 10 IPL Franchises: Official Retention & Availability Matrix")
    st.caption("Verified against official Board of Control for Cricket in India (BCCI) retention publications and mega-auction records. (Verification Date: November 18, 2026).")

    # 10 Franchise summary table
    franchise_summary = get_franchise_availability_summary()
    st.dataframe(franchise_summary, use_container_width=True, hide_index=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("#### 🔍 Master Player Status & Contract Registry")
    st.caption("Search across all tracked domestic and overseas players to verify whether a target is Retained, Contracted, Auction-Eligible, Ineligible, or Withdrawn.")

    status_reg = load_player_status_registry()
    all_reg_records = []
    seen_ids = set()
    for k, v in status_reg.items():
        pid = v.get("player_id")
        if pid not in seen_ids:
            seen_ids.add(pid)
            all_reg_records.append(v)

    reg_df = pd.DataFrame(all_reg_records)

    col_f1, col_f2, col_f3 = st.columns([1.5, 1.2, 1.3])
    with col_f1:
        search_q = st.text_input("Search Player by Name:", placeholder="e.g. Rinku, Towhid, Narine, Taskin...", key="reg_search_q")
    with col_f2:
        status_filter_opts = ["All Statuses", STATUS_AUCTION_ELIGIBLE, STATUS_RETAINED, STATUS_CONTRACTED, STATUS_RR_CURRENT, STATUS_INELIGIBLE, STATUS_WITHDRAWN_RETIRED]
        selected_status_filter = st.selectbox("Filter by Availability Status:", status_filter_opts, key="reg_status_filter")
    with col_f3:
        role_filter_opts = ["All Roles", "Batter", "Bowler", "All-rounder", "Wicketkeeper"]
        selected_role_filter = st.selectbox("Filter by Role:", role_filter_opts, key="reg_role_filter")

    filtered_reg = reg_df.copy()
    if search_q.strip():
        filtered_reg = filtered_reg[filtered_reg["player_name"].str.contains(search_q.strip(), case=False, na=False)]
    if selected_status_filter != "All Statuses":
        filtered_reg = filtered_reg[filtered_reg["ipl_status"] == selected_status_filter]
    if selected_role_filter != "All Roles":
        filtered_reg = filtered_reg[filtered_reg["role"] == selected_role_filter]

    display_reg = filtered_reg[[
        "player_name", "player_id", "ipl_status", "franchise", "role",
        "country", "retention_price_cr", "contract_price_cr", "base_price_cr", "verified_date"
    ]].rename(columns={
        "player_name": "Player Name",
        "player_id": "Canonical ID",
        "ipl_status": "IPL 2027 Status",
        "franchise": "Contracted Franchise",
        "role": "Role",
        "country": "Country",
        "retention_price_cr": "Retention (₹ Cr)",
        "contract_price_cr": "Contract (₹ Cr)",
        "base_price_cr": "Base Price (₹ Cr)",
        "verified_date": "Verified Date"
    })

    st.dataframe(display_reg, use_container_width=True, hide_index=True)
    st.caption("📌 **Strict Data Integrity Policy:** Statuses marked as `UNVERIFIED` are never assumed to be available. Only players with verified release records or uncontracted pool registrations are marked `AUCTION_ELIGIBLE`.")


# ==================== TAB 3: VERIFIED AVAILABLE PLAYER RANKINGS ====================
with tab_rankings:
    st.markdown("### 🎯 Verified Available Player Rankings (Auction-Eligible Only)")
    st.caption("Filtered exclusively for players available for auction bidding. Retained franchise stars are strictly excluded.")

    st.markdown("""
    <div style="background: rgba(230,0,126,0.10); border: 1px solid rgba(230,0,126,0.30); border-radius: 8px; padding: 10px 16px; margin-bottom: 16px; font-size: 12px; color: #F7F8FC;">
        🛡️ <b>Availability Guardrail Active:</b> Retained superstars like Rinku Singh (KKR), Sunil Narine (KKR), Rashid Khan (GT), Jasprit Bumrah (MI), and Nicholas Pooran (LSG) are legally contracted and excluded from this auction board.
    </div>
    """, unsafe_allow_html=True)

    avail_role_choice = st.radio(
        "Select Discipline:",
        ["🏏 Available Batters & Finishers", "🎯 Available Bowlers & Death Specialists"],
        horizontal=True,
        key="avail_role_toggle"
    )

    if "Batters" in avail_role_choice:
        disp_avail = avail_batters[[
            "available_rank", "player_name", "player_id", "reliability_score",
            "hp_balls", "hp_runs", "hp_strike_rate", "hp_average",
            "base_price_cr", "estimated_bid_min_cr", "estimated_bid_max_cr"
        ]].rename(columns={
            "available_rank": "Rank", "player_name": "Player", "player_id": "ID",
            "reliability_score": "Reliability Score", "hp_balls": "HP Balls",
            "hp_runs": "HP Runs", "hp_strike_rate": "HP SR", "hp_average": "HP Avg",
            "base_price_cr": "Base (₹ Cr)", "estimated_bid_min_cr": "Est. Min Bid", "estimated_bid_max_cr": "Est. Max Bid"
        })
        st.dataframe(disp_avail, use_container_width=True, hide_index=True)
    else:
        disp_avail = avail_bowlers[[
            "available_rank", "player_name", "player_id", "reliability_score",
            "hp_legal_balls", "hp_runs_conceded", "hp_wickets", "hp_economy",
            "base_price_cr", "estimated_bid_min_cr", "estimated_bid_max_cr"
        ]].rename(columns={
            "available_rank": "Rank", "player_name": "Player", "player_id": "ID",
            "reliability_score": "Reliability Score", "hp_legal_balls": "HP Balls",
            "hp_runs_conceded": "Conceded", "hp_wickets": "Wkts", "hp_economy": "HP Econ",
            "base_price_cr": "Base (₹ Cr)", "estimated_bid_min_cr": "Est. Min Bid", "estimated_bid_max_cr": "Est. Max Bid"
        })
        st.dataframe(disp_avail, use_container_width=True, hide_index=True)


# ==================== TAB 4: SQUAD PLANNER & BUDGET SIMULATOR ====================
with tab_planner:
    st.markdown("### 💰 Rajasthan Royals IPL 2027 Squad Planner & Budget Simulator")
    st.caption("Plan acquisitions for RR's 5 open squad slots and 2 open overseas slots while managing purse utilization.")

    # RR Current Squad Expander
    with st.expander("📋 View Rajasthan Royals Current 20-Player Contracted Roster (Click to Expand)"):
        rr_roster_df = pd.DataFrame(rr_squad_state["roster"])
        st.dataframe(
            rr_roster_df.rename(columns={
                "name": "Player Name", "role": "Role", "is_overseas": "Overseas",
                "price_cr": "Price (₹ Cr)", "acquisition": "Acquisition Type"
            }),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    col_p_purse, col_p_draft = st.columns([1.2, 2.8])

    with col_p_purse:
        total_purse_val = st.number_input(
            "Total Franchise Purse (₹ Cr):",
            min_value=100.0,
            max_value=150.0,
            value=float(DEFAULT_PURSE_INR_CR),
            step=1.0,
            key="input_total_purse_upg"
        )
        st.caption(f"RR Spent on Roster: **₹{rr_squad_state['spent_purse_cr']} Cr** | Available for 5 Slots: **₹{total_purse_val - rr_squad_state['spent_purse_cr']:.2f} Cr**")

    # Available draft options: strictly auction-eligible candidates
    avail_draft_pool = sorted(list(set(avail_batters["player_name"].tolist() + avail_bowlers["player_name"].tolist())))
    valid_draft_defaults = [p for p in st.session_state["selected_draft_players"] if p in avail_draft_pool] or avail_draft_pool[:4]

    with col_p_draft:
        drafted_players = st.multiselect(
            "Draft Available Players for RR's Open Slots (Max 5 recommended, Max 2 Overseas):",
            options=avail_draft_pool,
            default=valid_draft_defaults,
            key="ms_draft_players_upg"
        )
        st.session_state["selected_draft_players"] = drafted_players

    # Build active squad roster
    squad_roster = []
    if drafted_players:
        for p in drafted_players:
            p_reg = get_player_availability(player_name=p)
            base_b = p_reg.get("base_price_cr", 1.0)
            suggested_bid = p_reg.get("estimated_bid_min_cr", base_b or 1.0)
            default_bid = st.session_state["squad_bids"].get(p, suggested_bid)

            squad_roster.append({
                "player_name": p,
                "player_id": p_reg.get("player_id"),
                "category": p_reg.get("role", "All-rounder"),
                "role": p_reg.get("role", "All-rounder"),
                "reliability_score": 65.0,
                "is_overseas": p_reg.get("is_overseas", False),
                "base_price_cr": base_b,
                "bid_cr": float(default_bid)
            })

    # Combined simulated squad (RR current + newly drafted)
    all_sim_players = rr_squad_state["roster"] + squad_roster
    sim_spent = sum(p["price_cr"] if "price_cr" in p else p["bid_cr"] for p in all_sim_players)
    sim_remaining = total_purse_val - sim_spent
    sim_overseas = sum(1 for p in all_sim_players if p["is_overseas"])
    sim_squad_size = len(all_sim_players)

    # 4 Dynamic Financial KPI Cards
    st.markdown("<br/>", unsafe_allow_html=True)
    pk1, pk2, pk3, pk4 = st.columns(4)
    with pk1:
        st.markdown(f"""
        <div class="rr-kpi-card" style="border-top: 3px solid #E6007E;">
            <div class="rr-kpi-title">Total Simulated Spent</div>
            <div class="rr-kpi-value" style="color: #E6007E;">₹{sim_spent:.2f} <span style="font-size:14px; color:#A8B3CC;">Cr</span></div>
            <div class="rr-kpi-sub-pink">Utilization: {(sim_spent/total_purse_val)*100.0:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with pk2:
        rem_color = RR_GREEN if sim_remaining >= 0 else "#FF0055"
        st.markdown(f"""
        <div class="rr-kpi-card" style="border-top: 3px solid {rem_color};">
            <div class="rr-kpi-title">Remaining Purse</div>
            <div class="rr-kpi-value" style="color: {rem_color};">₹{sim_remaining:.2f} <span style="font-size:14px; color:#A8B3CC;">Cr</span></div>
            <div class="rr-kpi-sub" style="color: {rem_color};">{'Purse Available' if sim_remaining >= 0 else 'DEFICIT ALERT'}</div>
        </div>
        """, unsafe_allow_html=True)

    with pk3:
        sq_color = RR_GREEN if (RR_MIN_SQUAD <= sim_squad_size <= RR_SQUAD_LIMIT) else "#F39C12"
        st.markdown(f"""
        <div class="rr-kpi-card" style="border-top: 3px solid {sq_color};">
            <div class="rr-kpi-title">Squad Size</div>
            <div class="rr-kpi-value" style="color: {sq_color};">{sim_squad_size} / {RR_SQUAD_LIMIT}</div>
            <div class="rr-kpi-sub" style="color: {sq_color};">RR Min: {RR_MIN_SQUAD} | Max: {RR_SQUAD_LIMIT}</div>
        </div>
        """, unsafe_allow_html=True)

    with pk4:
        ov_color = RR_GREEN if sim_overseas <= RR_OVERSEAS_LIMIT else "#FF0055"
        st.markdown(f"""
        <div class="rr-kpi-card" style="border-top: 3px solid {ov_color};">
            <div class="rr-kpi-title">Overseas Quota</div>
            <div class="rr-kpi-value" style="color: {ov_color};">{sim_overseas} / {RR_OVERSEAS_LIMIT}</div>
            <div class="rr-kpi-sub" style="color: {ov_color};">{'Within IPL Limit' if sim_overseas <= RR_OVERSEAS_LIMIT else 'OVERSEAS LIMIT EXCEEDED'}</div>
        </div>
        """, unsafe_allow_html=True)

    # Individual Bid Sliders for Drafted Players
    if squad_roster:
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("#### 🎯 Simulated Acquisition Bids for Drafted Targets")
        st.caption("Adjust simulated auction purchase prices. Suggested market ranges reflect underlying clutch reliability scores.")

        bid_cols = st.columns(min(len(squad_roster), 4))
        for idx, p in enumerate(squad_roster):
            col_idx = idx % 4
            pname = p["player_name"]
            curr_bid = p["bid_cr"]
            base_p = p.get("base_price_cr") or 0.50

            with bid_cols[col_idx]:
                new_bid = st.slider(
                    f"{pname} (Base: ₹{base_p:.2f} Cr)",
                    min_value=float(base_p),
                    max_value=15.0,
                    value=float(curr_bid),
                    step=0.25,
                    key=f"slider_bid_{pname}"
                )
                st.session_state["squad_bids"][pname] = new_bid


# ==================== TAB 5: HISTORICAL BENCHMARKS ====================
with tab_history:
    st.markdown("### 🏆 Historical Performance Benchmarks (2022–2026 Archive)")
    st.caption("Preserved reference benchmarks from the 200,999 delivery archive. Clearly disaggregates IPL franchise conditions from International & Emerging T20 fixtures.")

    cat_toggle = st.radio("Focus Category:", ["Batters", "Bowlers"], horizontal=True, key="hist_matrix_toggle")
    if cat_toggle == "Batters":
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### 🌐 Combined Top 10 Batters (IPL + T20I)")
            st.caption("Evaluated on Deliveries with Match Pressure ≥65.0. Official benchmark (min 60 HP balls).")
            st.dataframe(comb_bat[["rank", "player_name", "player_id", "reliability_score", "hp_balls", "hp_runs", "hp_strike_rate", "hp_average", "sr_delta"]], use_container_width=True, hide_index=True)
        with c_right:
            st.markdown("#### 🇮🇳 IPL-Only Top 10 Batters")
            st.caption("Evaluated on Deliveries with Match Pressure ≥65.0. Filtered strictly to IPL matches (min 60 HP balls).")
            st.dataframe(ipl_bat[["rank", "player_name", "player_id", "reliability_score", "hp_balls", "hp_runs", "hp_strike_rate", "hp_average", "sr_delta"]], use_container_width=True, hide_index=True)
    else:
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### 🌐 Combined Top 10 Bowlers (IPL + T20I)")
            st.caption("Evaluated on Deliveries with Match Pressure ≥65.0. Official benchmark (min 60 HP balls).")
            st.dataframe(comb_bowl[["rank", "player_name", "player_id", "reliability_score", "hp_legal_balls", "hp_overs", "hp_wickets", "hp_economy", "hp_dot_pct"]], use_container_width=True, hide_index=True)
        with c_right:
            st.markdown("#### 🇮🇳 IPL-Only Top 10 Bowlers")
            st.caption("Evaluated on Deliveries with Match Pressure ≥65.0. Filtered strictly to IPL matches (min 60 HP balls).")
            st.dataframe(ipl_bowl[["rank", "player_name", "player_id", "reliability_score", "hp_legal_balls", "hp_overs", "hp_wickets", "hp_economy", "hp_dot_pct"]], use_container_width=True, hide_index=True)


# ==================== TAB 6: WAR ROOM EXPORT CENTER ====================
with tab_export:
    st.markdown("### 📥 Rajasthan Royals War Room Export Center")
    st.caption("Generate official scouting dossiers and data tables for franchise recruitment.")

    ex_c1, ex_c2, ex_c3 = st.columns(3)
    with ex_c1:
        st.markdown("#### 📄 RR Priority Shortlist (CSV)")
        st.caption("Target list with base prices and SMS Jaipur tactical fit.")
        shortlist_csv = pd.DataFrame(rr_shortlist).to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Priority Shortlist (CSV)",
            data=shortlist_csv,
            file_name="RR_IPL_2027_Priority_Shortlist.csv",
            mime="text/csv",
            use_container_width=True
        )

    with ex_c2:
        st.markdown("#### 📄 Verified Available Players (CSV)")
        st.caption("Full list of auction-eligible players with market valuations.")
        dfs_to_concat = [df for df in [avail_batters, avail_bowlers] if not df.empty]
        avail_all = pd.concat(dfs_to_concat, ignore_index=True) if dfs_to_concat else pd.DataFrame()
        avail_csv = avail_all.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Available Candidates (CSV)",
            data=avail_csv,
            file_name="IPL_2027_Verified_Available_Players.csv",
            mime="text/csv",
            use_container_width=True
        )

    with ex_c3:
        st.markdown("#### 📑 Official War Room Dossier (PDF)")
        st.caption("Complete executive dossier compiled with ReportLab.")
        total_strikers = deliveries_df["striker_id"].nunique() if "striker_id" in deliveries_df.columns else 0
        total_bowlers = deliveries_df["bowler_id"].nunique() if "bowler_id" in deliveries_df.columns else 0
        seasons = sorted(deliveries_df["season"].astype(str).unique().tolist()) if "season" in deliveries_df.columns else []
        summary_stats = {
            "total_deliveries": len(deliveries_df),
            "total_matches": deliveries_df["match_id"].nunique() if "match_id" in deliveries_df.columns else 0,
            "total_players": total_strikers + total_bowlers,
            "seasons": seasons
        }
        pdf_bytes = build_auction_pdf_report(
            dossier_df, ipl_bat, ipl_bowl, comb_bat, comb_bowl, summary_stats
        )
        st.download_button(
            "📥 Download War Room Dossier (PDF)",
            data=pdf_bytes,
            file_name="RR_IPL_2027_War_Room_Dossier.pdf",
            mime="application/pdf",
            use_container_width=True
        )
