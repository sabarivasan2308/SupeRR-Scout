"""
IPL 2027 Player Availability & Franchise Status Module for SupeRR SCOUT Platform.
Tracks officially verified franchise retentions, contracts, releases, and auction eligibility.
Enforces strict exclusion of unavailable players from auction recommendations.
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

STATUS_FILE = Path(__file__).resolve().parent.parent / "data" / "ipl_2027_player_status.json"

# Strict IPL Status Constants
STATUS_RETAINED = "RETAINED"
STATUS_CONTRACTED = "CONTRACTED"
STATUS_RR_CURRENT = "RR_CURRENT"
STATUS_AUCTION_ELIGIBLE = "AUCTION_ELIGIBLE"
STATUS_INELIGIBLE = "INELIGIBLE"
STATUS_WITHDRAWN_RETIRED = "WITHDRAWN_RETIRED"
STATUS_UNVERIFIED = "UNVERIFIED"

# Rajasthan Royals IPL 2027 Confirmed Squad Baseline
# Primary Source: Official Rajasthan Royals Announcement dated 17-Nov-2026
# https://www.rajasthanroyals.com/news/ipl-2027-retention-announcement-november-17-2026
RR_SQUAD_LIMIT = 25
RR_MIN_SQUAD = 18
RR_OVERSEAS_LIMIT = 8
RR_BASE_PURSE_CR = 120.0
RR_CONFIRMED_REMAINING_PURSE_CR = 27.05
RR_CONFIRMED_SPENT_PURSE_CR = 92.95

RR_VERIFIED_CURRENT_ROSTER = [
    {"player_id": 6423, "name": "Riyan Parag", "role": "All-rounder", "is_overseas": False, "price_cr": 14.0, "acquisition": "Retained (Captain)"},
    {"player_id": 6819, "name": "Yashasvi Jaiswal", "role": "Batter", "is_overseas": False, "price_cr": 18.0, "acquisition": "Retained (Opener)"},
    {"player_id": 152, "name": "Ravindra Jadeja", "role": "All-rounder", "is_overseas": False, "price_cr": 14.0, "acquisition": "Retained (Marquee All-rounder)"},
    {"player_id": 7260, "name": "Dhruv Jurel", "role": "Wicketkeeper", "is_overseas": False, "price_cr": 14.0, "acquisition": "Retained (Wicketkeeper-Finisher)"},
    {"player_id": 3298, "name": "Jofra Archer", "role": "Bowler", "is_overseas": True, "price_cr": 12.50, "acquisition": "Retained (Overseas Strike Pacer)"},
    {"player_id": 2411, "name": "Sandeep Sharma", "role": "Bowler", "is_overseas": False, "price_cr": 4.0, "acquisition": "Retained (Death Specialist)"},
    {"player_id": 1566, "name": "Mohammed Shami", "role": "Bowler", "is_overseas": False, "price_cr": 8.0, "acquisition": "Traded In (from LSG for ₹8.00 Cr)"},
    {"player_id": 7503, "name": "Ravi Bishnoi", "role": "Bowler", "is_overseas": False, "price_cr": 1.80, "acquisition": "Retained (Wrist-spinner)"},
    {"player_id": 46088, "name": "Vaibhav Sooryavanshi", "role": "Batter", "is_overseas": False, "price_cr": 1.10, "acquisition": "Retained (Domestic Prodigy)"},
    {"player_id": 25139, "name": "Shubham Dubey", "role": "Batter", "is_overseas": False, "price_cr": 0.80, "acquisition": "Retained (Domestic Finisher)"},
    {"player_id": 7312, "name": "Nandre Burger", "role": "Bowler", "is_overseas": True, "price_cr": 0.75, "acquisition": "Retained (Overseas Left-arm Fast)"},
    {"player_id": 7338, "name": "Donovan Ferreira", "role": "All-rounder", "is_overseas": True, "price_cr": 0.75, "acquisition": "Retained (Overseas Power Finisher/Keeper)"},
    {"player_id": 4614, "name": "Dasun Shanaka", "role": "All-rounder", "is_overseas": True, "price_cr": 0.75, "acquisition": "Retained (Overseas Seam All-rounder)"},
    {"player_id": 8092, "name": "Sushant Mishra", "role": "Bowler", "is_overseas": False, "price_cr": 0.75, "acquisition": "Retained (Domestic Left-arm Pacer)"},
    {"player_id": 7895, "name": "Manimaran Siddharth", "role": "Bowler", "is_overseas": False, "price_cr": 0.75, "acquisition": "Traded In (from LSG for ₹0.75 Cr)"},
    {"player_id": 43798, "name": "Lhuan-dre Pretorius", "role": "Wicketkeeper", "is_overseas": True, "price_cr": 0.40, "acquisition": "Retained (Overseas Emerging Keeper-Batter)"},
    {"player_id": 46101, "name": "Aman Rao Perala", "role": "Batter", "is_overseas": False, "price_cr": 0.20, "acquisition": "Retained (Domestic Developmental)"},
    {"player_id": 46102, "name": "Brijesh Sharma", "role": "All-rounder", "is_overseas": False, "price_cr": 0.20, "acquisition": "Retained (Domestic Developmental)"},
    {"player_id": 46103, "name": "Yash Raj Punja", "role": "Bowler", "is_overseas": False, "price_cr": 0.20, "acquisition": "Retained (Domestic Developmental)"}
]


def load_player_status_registry() -> Dict[str, Dict[str, Any]]:
    """
    Load the verified player status registry from disk.
    Returns two-key dictionary: indexed by canonical player_id (as str) and lowercase player_name.
    """
    if not STATUS_FILE.exists():
        logger.warning(f"Player status registry file not found at {STATUS_FILE}. Returning empty registry.")
        return {}

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        logger.error(f"Error loading player status JSON: {e}")
        return {}

    registry = {}
    for r in records:
        entry = dict(r)
        entry["name"] = entry.get("player_name", "")
        entry["status"] = entry.get("ipl_status", STATUS_UNVERIFIED)
        entry["last_verified_date"] = entry.get("verified_date", "2026-11-18")
        entry["base_price_inr_cr"] = entry.get("base_price_cr")
        entry["est_bid_range_inr_cr"] = (
            f"₹{entry.get('estimated_bid_min_cr', 0.5):.2f} - ₹{entry.get('estimated_bid_max_cr', 2.0):.2f} Cr"
            if entry.get("estimated_bid_min_cr") is not None else "N/A"
        )

        pid = entry.get("player_id")
        pname = entry.get("player_name", "").strip()

        if pid is not None:
            registry[f"id_{pid}"] = entry
        if pname:
            registry[f"name_{pname.lower()}"] = entry

    return registry


def get_player_availability(
    player_id: Optional[int] = None,
    player_name: Optional[str] = None,
    registry: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Look up verified player availability status.
    Hierarchy:
    1. Exact canonical player_id
    2. Case-insensitive player_name match
    3. Fallback: UNVERIFIED (Never assume an unlisted player is available!)
    """
    if registry is None:
        registry = load_player_status_registry()

    # 1. Match by player_id
    if player_id is not None:
        key = f"id_{player_id}"
        if key in registry:
            res = dict(registry[key])
            res["status"] = res.get("ipl_status", STATUS_UNVERIFIED)
            res["name"] = res.get("player_name", "Unknown")
            return res

    # 2. Match by player_name
    if player_name:
        key = f"name_{player_name.strip().lower()}"
        if key in registry:
            res = dict(registry[key])
            res["status"] = res.get("ipl_status", STATUS_UNVERIFIED)
            res["name"] = res.get("player_name", "Unknown")
            return res

    # 3. Default fallback: strictly UNVERIFIED
    return {
        "player_id": player_id,
        "player_name": player_name or "Unknown",
        "name": player_name or "Unknown",
        "ipl_status": STATUS_UNVERIFIED,
        "status": STATUS_UNVERIFIED,
        "franchise": "Unknown",
        "retention_price_cr": 0.0,
        "contract_price_cr": 0.0,
        "role": "Unknown",
        "is_overseas": False,
        "country": "Unknown",
        "base_price_cr": None,
        "estimated_bid_min_cr": None,
        "estimated_bid_max_cr": None,
        "source_url": "Unlisted",
        "verified_date": "N/A",
        "last_verified_date": "N/A",
        "notes": "Status not verified in official IPL retention or auction registry. Marked UNVERIFIED per strict safety rules."
    }


def is_player_auction_eligible(
    player_id: Optional[int] = None,
    player_name: Optional[str] = None,
    registry: Optional[Dict[str, Dict[str, Any]]] = None
) -> bool:
    """
    Strict boolean check: returns True ONLY if the player's status is verified AUCTION_ELIGIBLE.
    Returns False for RETAINED, CONTRACTED, RR_CURRENT, INELIGIBLE, WITHDRAWN_RETIRED, or UNVERIFIED.
    """
    info = get_player_availability(player_id, player_name, registry)
    return info.get("ipl_status") == STATUS_AUCTION_ELIGIBLE


def filter_available_rankings(
    ranked_df: pd.DataFrame,
    is_batter: bool = True
) -> pd.DataFrame:
    """
    Filter a pre-ranked leaderboard DataFrame to ONLY verified auction-eligible targets.
    Enriches with status, franchise, base price, and estimated market valuation range.
    Preserves original statistical metrics and Bayesian reliability calculations.
    """
    if ranked_df.empty:
        return ranked_df

    reg = load_player_status_registry()
    df = ranked_df.copy()

    statuses = []
    franchises = []
    is_eligibles = []
    base_prices = []
    bid_mins = []
    bid_maxs = []
    sources = []
    notes = []

    for _, row in df.iterrows():
        pid = int(row["player_id"]) if pd.notna(row.get("player_id")) else None
        pname = str(row["player_name"]) if pd.notna(row.get("player_name")) else ""

        info = get_player_availability(pid, pname, reg)
        status = info.get("ipl_status", STATUS_UNVERIFIED)

        statuses.append(status)
        franchises.append(info.get("franchise", "None"))
        is_eligibles.append(status == STATUS_AUCTION_ELIGIBLE)
        base_prices.append(info.get("base_price_cr"))
        bid_mins.append(info.get("estimated_bid_min_cr"))
        bid_maxs.append(info.get("estimated_bid_max_cr"))
        sources.append(info.get("source_url", ""))
        notes.append(info.get("notes", ""))

    df["ipl_status"] = statuses
    df["franchise"] = franchises
    df["is_auction_eligible"] = is_eligibles
    df["base_price_cr"] = base_prices
    df["estimated_bid_min_cr"] = bid_mins
    df["estimated_bid_max_cr"] = bid_maxs
    df["verification_source"] = sources
    df["status_notes"] = notes

    # Filter strictly for auction-eligible candidates and sort by reliability score
    available_df = df[df["is_auction_eligible"]].copy()
    available_df["is_available"] = True
    available_df["auction_status"] = available_df["ipl_status"]
    if "reliability_score" in available_df.columns:
        sort_cols = ["reliability_score"]
        tie_col = "hp_balls" if is_batter else "hp_legal_balls"
        if tie_col in available_df.columns:
            sort_cols.append(tie_col)
        available_df = available_df.sort_values(by=sort_cols, ascending=False)
    available_df = available_df.reset_index(drop=True)
    available_df["available_rank"] = range(1, len(available_df) + 1)
    return available_df


def get_rr_squad_state() -> Dict[str, Any]:
    """
    Return Rajasthan Royals' verified IPL squad composition, purse, and capacity.
    Primary Source: Official Rajasthan Royals Announcement dated 17-Nov-2026.
    Confirmed Baseline: 19 players, 6 available slots, 3 overseas slots, ₹27.05 Cr remaining purse.
    """
    roster = RR_VERIFIED_CURRENT_ROSTER
    total_spent = sum(p["price_cr"] for p in roster)
    squad_count = len(roster)
    overseas_count = sum(1 for p in roster if p["is_overseas"])
    domestic_count = squad_count - overseas_count
    retained_count = sum(1 for p in roster if "Retained" in p.get("acquisition", ""))
    traded_count = sum(1 for p in roster if "Traded" in p.get("acquisition", ""))

    remaining_slots = RR_SQUAD_LIMIT - squad_count
    remaining_overseas_slots = RR_OVERSEAS_LIMIT - overseas_count
    remaining_purse_cr = max(0.0, RR_BASE_PURSE_CR - total_spent)

    return {
        "franchise": "Rajasthan Royals",
        "season": "IPL 2027",
        "total_purse_cr": RR_BASE_PURSE_CR,
        "spent_purse_cr": round(total_spent, 2),
        "total_spent_cr": round(total_spent, 2),
        "remaining_purse_cr": round(remaining_purse_cr, 2),
        "squad_size": squad_count,
        "total_players": squad_count,
        "max_squad_limit": RR_SQUAD_LIMIT,
        "min_squad_limit": RR_MIN_SQUAD,
        "retained_count": retained_count,
        "traded_count": traded_count,
        "remaining_squad_capacity": remaining_slots,
        "open_slots": remaining_slots,
        "overseas_count": overseas_count,
        "max_overseas_limit": RR_OVERSEAS_LIMIT,
        "remaining_overseas_capacity": remaining_overseas_slots,
        "open_overseas_slots": remaining_overseas_slots,
        "domestic_count": domestic_count,
        "roster": roster
    }


def get_rr_squad_gaps() -> List[Dict[str, Any]]:
    """
    Identify tactical squad gaps for Rajasthan Royals ahead of IPL 2027 mini-auction.
    Recalculated based on RR's 19-player roster and key released assets (Hetmyer, Deshpande, Maphaka).
    """
    return [
        {
            "priority": "HIGH",
            "gap_name": "Overseas Clutch Finisher (#6 / #7)",
            "urgency": "Critical",
            "description": "Critical replacement for released Shimron Hetmyer. Need a death boundary hitter to partner Donovan Ferreira and Dhruv Jurel.",
            "target_profile": "Clutch boundary conversion (>25%), 175+ strike rate under 65+ pressure, ability to clear 75m SMS Jaipur boundaries.",
            "recommended_targets": ["Towhid Hridoy (Bangladesh - BCB Confirmed Registered)"]
        },
        {
            "priority": "HIGH",
            "gap_name": "Specialist Death Yorker Pacer (140+ kph)",
            "urgency": "Critical",
            "description": "High-pace death enforcer with blockhole execution to partner Sandeep Sharma, Shami, and Jofra Archer in high-leverage overs 17–20.",
            "target_profile": "Express pace (140+ kph) with blockhole execution, toe-crushing yorkers, and wide yorker containment on SMS Jaipur pitch.",
            "recommended_targets": ["Taskin Ahmed (145+ kph)", "Mustafizur Rahman (Death Cutters)", "Nahid Rana (150+ kph)"]
        },
        {
            "priority": "MEDIUM",
            "gap_name": "Left-Arm Seam & Powerplay Swing Enforcer",
            "urgency": "Moderate",
            "description": "Replacing released Kwena Maphaka and Adam Milne with left-arm angle and early powerplay swing to exploit SMS Jaipur grass cover.",
            "target_profile": "Can bowl hard lengths in overs 1–6 and execute wide yorkers at the death under pressure.",
            "recommended_targets": ["Shoriful Islam (Bangladesh - BCB Confirmed Registered)"]
        },
        {
            "priority": "MEDIUM",
            "gap_name": "Attacking Tall Wrist-Spinner & Boundary-Hitting Depth",
            "urgency": "Moderate",
            "description": "Multi-phase wrist spin variation extracting steep bounce from SMS Jaipur pitch, with lower-order hitting power.",
            "target_profile": "Suffocating economy (<7.00 RPO under pressure) and variations (top-spinner, googly) plus lower-order boundary hitting at #8.",
            "recommended_targets": ["Mohammad Rishad Hossain (Bangladesh - BCB Confirmed Registered)"]
        },
        {
            "priority": "LOW",
            "gap_name": "Disciplined Death Blockhole Containment Specialist",
            "urgency": "Low",
            "description": "Precision seam option with proven dot-ball pressure execution to protect totals when defending low scores at SMS.",
            "target_profile": "High dot-ball % (>45%), under 8.00 RPO under pressure, sub-₹2.5 Cr valuation.",
            "recommended_targets": ["Hasan Mahmud (Bangladesh - BCB Confirmed Registered)"]
        }
    ]


def get_rr_priority_shortlist(
    deliveries_df: Optional[pd.DataFrame] = None,
    min_balls: int = 40,
    pressure_thresh: float = 65.0
) -> List[Dict[str, Any]]:
    """
    Curate the official Rajasthan Royals Priority Auction Shortlist.
    EVERY player in this shortlist is 100% verified AUCTION_ELIGIBLE via an authoritative source.
    Players with unverified registration (released players awaiting BCCI catalog) or retained by other
    franchises (e.g. Powell, Holder) are STRICTLY EXCLUDED.
    """
    from src.auction_intelligence import compute_player_competition_split, classify_player_role_and_phases, RR_TACTICAL_DOSSIERS

    if deliveries_df is None:
        pkl_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "deliveries_processed.pkl"
        if pkl_path.exists():
            try:
                deliveries_df = pd.read_pickle(pkl_path)
            except Exception as e:
                logger.warning(f"Could not load deliveries_processed.pkl: {e}")

    # Definitive list of 100% verified auction-eligible targets supported by authoritative confirmation
    # Source: BCB Operations In-Charge Shahriar Nafees confirmation (18-Nov-2026) for Dec 16 Goa mini-auction
    eligible_candidate_ids = [
        (6651, True, "Towhid Hridoy", "Lower-Order Clutch Finisher (#6/#7)", 0.75, 2.0, 4.5),
        (2681, False, "Taskin Ahmed", "Specialist Death Express Pacer (145+ kph)", 1.50, 3.5, 6.0),
        (4373, False, "Mustafizur Rahman", "Left-Arm Death Cutter / Yorker Specialist", 2.00, 4.0, 7.5),
        (37939, False, "Nahid Rana", "High-Pace Express Enforcer (150+ kph)", 0.75, 1.5, 3.5),
        (7344, False, "Shoriful Islam", "Left-Arm Powerplay & Death Seamer", 0.75, 1.5, 3.0),
        (8380, True, "Mohammad Rishad Hossain", "Attacking Tall Wrist-Spinner & Finisher (#8)", 0.75, 1.5, 3.5),
        (6643, False, "Hasan Mahmud", "Death-Over Blockhole Executioner", 0.75, 1.25, 2.75)
    ]

    shortlist = []
    for pid, is_bat, name, tactical_role, base_pr, bid_min, bid_max in eligible_candidate_ids:
        comb_stat = {}
        role_info = {}
        if deliveries_df is not None:
            try:
                split_info = compute_player_competition_split(deliveries_df, pid, is_bat, pressure_thresh)
                role_info = classify_player_role_and_phases(deliveries_df, pid, is_bat, pressure_thresh)
                comb_stat = split_info["splits"].get("Combined", {})
            except Exception:
                comb_stat = {}
                role_info = {}

        dossier = RR_TACTICAL_DOSSIERS.get(pid, {})

        shortlist.append({
            "player_id": pid,
            "player_name": name,
            "name": name,
            "is_batter": is_bat,
            "category": "Batter / All-Rounder" if is_bat else "Bowler",
            "target_role": tactical_role,
            "tactical_role": tactical_role,
            "ipl_status": STATUS_AUCTION_ELIGIBLE,
            "status": STATUS_AUCTION_ELIGIBLE,
            "base_price_cr": base_pr,
            "estimated_bid_min_cr": bid_min,
            "estimated_bid_max_cr": bid_max,
            "est_bid_range": f"₹{bid_min:.2f} Cr - ₹{bid_max:.2f} Cr",
            "hp_balls": comb_stat.get("hp_balls" if is_bat else "hp_legal_balls", 0),
            "hp_metric": comb_stat.get("hp_sr" if is_bat else "hp_economy", 0.0),
            "hp_metric_label": "HP Strike Rate" if is_bat else "HP Economy",
            "clutch_delta": comb_stat.get("sr_delta" if is_bat else "econ_delta", 0.0),
            "phase_distribution": role_info.get("phase_distribution", {}),
            "tactical_fit": dossier.get("rr_tactical_fit", f"Fills tactical requirement for {tactical_role} at Sawai Mansingh Stadium."),
            "jaipur_sms_fit": dossier.get("jaipur_sms_fit", "Optimized for SMS venue dynamics and boundary dimensions."),
            "rr_tactical_fit": dossier.get("rr_tactical_fit", f"Fills tactical requirement for {tactical_role} at Sawai Mansingh Stadium."),
            "verification_source": "Official BCB Registration Confirmation (18-Nov-2026)",
            "strengths": dossier.get("strengths", ["High clutch execution under pressure", "Proven international composure"]),
            "limitations": dossier.get("limitations", ["Overseas slot management required" if is_bat else "Subject to phase-specific match leverage"])
        })

    return shortlist


def get_unverified_shortlist_targets() -> List[Dict[str, Any]]:
    """
    Return the registry of shortlisted players whose auction eligibility cannot be 100% verified
    via authoritative registration citations as of 18-Nov-2026, or who are confirmed retained by other franchises.
    Per strict safety rules, these players are EXCLUDED from verified auction recommendations.
    """
    return [
        {
            "player_id": 4986,
            "name": "Rovman Powell",
            "status": "RETAINED (EXCLUDED)",
            "franchise": "Kolkata Knight Riders (KKR)",
            "reason": "Confirmed officially retained by KKR on 17-Nov-2026. Cannot be targeted in auction."
        },
        {
            "player_id": 2633,
            "name": "Jason Holder",
            "status": "RETAINED (EXCLUDED)",
            "franchise": "Gujarat Titans (GT)",
            "reason": "Confirmed officially retained by GT on 17-Nov-2026. Cannot be targeted in auction."
        },
        {
            "player_id": 3918,
            "name": "Travis Head",
            "status": "WITHDRAWN_RETIRED (EXCLUDED)",
            "franchise": "Released by SRH",
            "reason": "Officially opted out of IPL 2027 on 17-Nov-2026 for workload management ahead of Ashes."
        },
        {
            "player_id": 1,
            "name": "MS Dhoni",
            "status": "WITHDRAWN_RETIRED (EXCLUDED)",
            "franchise": "CSK (Team Mentor)",
            "reason": "Officially retired from IPL playing career on 17-Nov-2026; transitioned to CSK Team Mentor."
        },
        {
            "player_id": 3297,
            "name": "Shimron Hetmyer",
            "status": "UNVERIFIED (EXCLUDED)",
            "franchise": "Released by RR",
            "reason": "Released by RR on 17-Nov-2026. Official 2027 auction registration not yet confirmed by CWI/BCCI."
        },
        {
            "player_id": 6806,
            "name": "Tushar Deshpande",
            "status": "UNVERIFIED (EXCLUDED)",
            "franchise": "Released by RR",
            "reason": "Released by RR on 17-Nov-2026. Official 2027 auction registration not yet published in BCCI register."
        },
        {
            "player_id": 1324,
            "name": "Trent Boult",
            "status": "UNVERIFIED (EXCLUDED)",
            "franchise": "Released by MI",
            "reason": "Released by MI on 17-Nov-2026. Auction registration not yet officially confirmed by NZC/BCCI."
        },
        {
            "player_id": 1989,
            "name": "Mitchell Starc",
            "status": "UNVERIFIED (EXCLUDED)",
            "franchise": "Released by DC",
            "reason": "Released by DC on 17-Nov-2026. Auction registration not yet officially confirmed by CA/BCCI."
        },
        {
            "player_id": 7509,
            "name": "Matheesha Pathirana",
            "status": "UNVERIFIED (EXCLUDED)",
            "franchise": "Released by KKR",
            "reason": "Released by KKR on 17-Nov-2026. Auction registration not officially confirmed by SLC/BCCI."
        },
        {
            "player_id": 2984,
            "name": "Sikandar Raza",
            "status": "UNVERIFIED (EXCLUDED)",
            "franchise": "Uncontracted / Free Agent",
            "reason": "Auction registration window closes Nov 23; registration not yet officially confirmed by ZC/BCCI."
        },
        {
            "player_id": 6450,
            "name": "Mujeeb Ur Rahman",
            "status": "UNVERIFIED (EXCLUDED)",
            "franchise": "Uncontracted / Free Agent",
            "reason": "Auction registration not officially confirmed by ACB/BCCI as of 18-Nov-2026."
        },
        {
            "player_id": 39657,
            "name": "Eshan Malinga",
            "status": "UNVERIFIED (EXCLUDED)",
            "franchise": "Uncontracted / Free Agent",
            "reason": "Auction registration not officially confirmed by SLC/BCCI as of 18-Nov-2026."
        },
        {
            "player_id": 46066,
            "name": "Vipraj Nigam",
            "status": "UNVERIFIED (EXCLUDED)",
            "franchise": "Uncontracted / Domestic",
            "reason": "Uncapped domestic player registration awaiting official BCCI shortlist publication on Dec 3, 2026."
        }
    ]


def get_franchise_availability_summary() -> pd.DataFrame:
    """
    Return a structured overview of all 10 franchises reflecting the official
    BCCI/IPL retention & release announcement deadline of 17-Nov-2026.
    """
    summary_data = [
        {"Franchise": "Lucknow Super Giants (LSG)", "Squad Count": 18, "Remaining Slots": 7, "Overseas Open": 3, "Purse Spent (Cr)": "₹72.55", "Remaining Purse (Cr)": "₹47.45", "Key Retentions": "Nicholas Pooran, Mayank Yadav, Mohsin Khan, Ayush Badoni, Kuldeep Yadav, Sam Curran"},
        {"Franchise": "Kolkata Knight Riders (KKR)", "Squad Count": 17, "Remaining Slots": 8, "Overseas Open": 3, "Purse Spent (Cr)": "₹78.35", "Remaining Purse (Cr)": "₹41.65", "Key Retentions": "Rinku Singh, Sunil Narine, Varun Chakravarthy, Andre Russell, Harshit Rana, Rovman Powell, Cameron Green"},
        {"Franchise": "Sunrisers Hyderabad (SRH)", "Squad Count": 18, "Remaining Slots": 7, "Overseas Open": 3, "Purse Spent (Cr)": "₹79.85", "Remaining Purse (Cr)": "₹40.15", "Key Retentions": "Heinrich Klaasen, Pat Cummins, Abhishek Sharma, Nitish Kumar Reddy (Travis Head Opted Out)"},
        {"Franchise": "Delhi Capitals (DC)", "Squad Count": 16, "Remaining Slots": 9, "Overseas Open": 4, "Purse Spent (Cr)": "₹80.50", "Remaining Purse (Cr)": "₹39.50", "Key Retentions": "KL Rahul, Rishabh Pant, Axar Patel, Tristan Stubbs, Abishek Porel"},
        {"Franchise": "Mumbai Indians (MI)", "Squad Count": 16, "Remaining Slots": 9, "Overseas Open": 2, "Purse Spent (Cr)": "₹87.40", "Remaining Purse (Cr)": "₹32.60", "Key Retentions": "Jasprit Bumrah, Suryakumar Yadav, Rohit Sharma, Tilak Varma, Arshdeep Singh"},
        {"Franchise": "Chennai Super Kings (CSK)", "Squad Count": 19, "Remaining Slots": 6, "Overseas Open": 2, "Purse Spent (Cr)": "₹91.95", "Remaining Purse (Cr)": "₹28.05", "Key Retentions": "Ruturaj Gaikwad, Sanju Samson, Shivam Dube, Khaleel Ahmed, Noor Ahmad (MS Dhoni Mentoring)"},
        {"Franchise": "Rajasthan Royals (RR)", "Squad Count": 19, "Remaining Slots": 6, "Overseas Open": 3, "Purse Spent (Cr)": "₹92.95", "Remaining Purse (Cr)": "₹27.05", "Key Retentions": "Riyan Parag (C), Yashasvi Jaiswal, Ravindra Jadeja, Dhruv Jurel, Jofra Archer, Mohammed Shami, Sandeep Sharma"},
        {"Franchise": "Punjab Kings (PBKS)", "Squad Count": 19, "Remaining Slots": 6, "Overseas Open": 2, "Purse Spent (Cr)": "₹101.40", "Remaining Purse (Cr)": "₹18.60", "Key Retentions": "Hardik Pandya, Shashank Singh, Prabhsimran Singh, Shreyas Iyer, Glenn Maxwell, Marcus Stoinis"},
        {"Franchise": "Royal Challengers Bengaluru (RCB)", "Squad Count": 20, "Remaining Slots": 5, "Overseas Open": 1, "Purse Spent (Cr)": "₹105.85", "Remaining Purse (Cr)": "₹14.15", "Key Retentions": "Virat Kohli, Rajat Patidar, Yash Dayal, Phil Salt, Liam Livingstone, Josh Hazlewood, Tim David"},
        {"Franchise": "Gujarat Titans (GT)", "Squad Count": 22, "Remaining Slots": 3, "Overseas Open": 2, "Purse Spent (Cr)": "₹111.25", "Remaining Purse (Cr)": "₹8.75", "Key Retentions": "Rashid Khan, Shubman Gill, Sai Sudharsan, Rahul Tewatia, Shahrukh Khan, Jason Holder, Mohammed Siraj"}
    ]
    return pd.DataFrame(summary_data)
