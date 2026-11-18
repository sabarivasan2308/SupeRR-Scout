"""
Auction Squad Planner & Budget Simulation Engine for SupeRR SCOUT Platform.
Enables franchise recruitment war room planners to draft hypothetical squads,
track purse utilization, verify squad balance constraints, and compare multi-scenario plans.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


# Default IPL Squad Regulations
DEFAULT_PURSE_INR_CR = 120.0
MIN_SQUAD_SIZE = 18
MAX_SQUAD_SIZE = 25
MAX_OVERSEAS_PLAYERS = 8


def compute_squad_financials(
    squad_players: List[Dict[str, Any]],
    total_purse_cr: float = DEFAULT_PURSE_INR_CR
) -> Dict[str, Any]:
    """
    Compute total spent, remaining purse, and utilization percentages for a drafted squad.
    """
    total_purse = float(max(10.0, total_purse_cr))
    if not squad_players:
        return {
            "total_purse": total_purse,
            "total_spent": 0.0,
            "remaining_purse": total_purse,
            "utilization_pct": 0.0,
            "squad_count": 0,
            "avg_player_cost": 0.0
        }

    total_spent = sum(float(p.get("bid_cr", 0.0)) for p in squad_players)
    remaining_purse = total_purse - total_spent
    utilization_pct = (total_spent / total_purse) * 100.0
    avg_cost = total_spent / max(1, len(squad_players))

    return {
        "total_purse": total_purse,
        "total_spent": float(total_spent),
        "remaining_purse": float(remaining_purse),
        "utilization_pct": float(utilization_pct),
        "squad_count": len(squad_players),
        "avg_player_cost": float(avg_cost)
    }


def analyze_squad_balance(
    squad_players: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze role distribution, overseas limits, and tactical squad balance.
    """
    if not squad_players:
        return {
            "squad_count": 0,
            "role_counts": {"Batter": 0, "Bowler": 0, "All-rounder": 0, "Wicketkeeper": 0},
            "overseas_count": 0,
            "domestic_count": 0,
            "avg_reliability": 0.0,
            "alerts": ["⚠️ Squad is empty. Draft players from the shortlist to begin."]
        }

    role_counts = {"Batter": 0, "Bowler": 0, "All-rounder": 0, "Wicketkeeper": 0}
    overseas_count = 0
    scores = []

    for p in squad_players:
        role = str(p.get("role", "Batter")).lower()
        if "keeper" in role or "wk" in role:
            role_counts["Wicketkeeper"] += 1
        elif "all-rounder" in role or "allrounder" in role:
            role_counts["All-rounder"] += 1
        elif "bowler" in role:
            role_counts["Bowler"] += 1
        else:
            role_counts["Batter"] += 1

        if p.get("is_overseas", False):
            overseas_count += 1

        scores.append(float(p.get("reliability_score", 50.0)))

    squad_count = len(squad_players)
    domestic_count = squad_count - overseas_count
    avg_reliability = float(np.mean(scores)) if scores else 0.0

    alerts = []
    if squad_count < MIN_SQUAD_SIZE:
        alerts.append(f"ℹ️ Squad has {squad_count} players (IPL minimum is {MIN_SQUAD_SIZE}).")
    elif squad_count > MAX_SQUAD_SIZE:
        alerts.append(f"⚠️ Squad exceeds IPL maximum roster of {MAX_SQUAD_SIZE} players ({squad_count}).")

    if overseas_count > MAX_OVERSEAS_PLAYERS:
        alerts.append(f"🚨 Overseas players ({overseas_count}) exceed the IPL limit of {MAX_OVERSEAS_PLAYERS}!")

    if role_counts["Bowler"] + role_counts["All-rounder"] < 6:
        alerts.append("⚠️ Low bowling depth: Recommend at least 6 bowling options (specialists + all-rounders).")

    if role_counts["Wicketkeeper"] < 1:
        alerts.append("⚠️ No dedicated wicketkeeper identified in drafted roster.")

    if not alerts:
        alerts.append("✅ Squad meets primary role balance and IPL composition guidelines.")

    return {
        "squad_count": squad_count,
        "role_counts": role_counts,
        "overseas_count": overseas_count,
        "domestic_count": domestic_count,
        "avg_reliability": avg_reliability,
        "alerts": alerts
    }


def compare_saved_scenarios(
    scenarios: Dict[str, Dict[str, Any]],
    total_purse_cr: float = DEFAULT_PURSE_INR_CR
) -> pd.DataFrame:
    """
    Build a structured comparative DataFrame across all saved hypothetical squad scenarios.
    """
    if not scenarios:
        return pd.DataFrame()

    records = []
    for scn_name, scn_data in scenarios.items():
        players = scn_data.get("players", [])
        fin = compute_squad_financials(players, total_purse_cr)
        bal = analyze_squad_balance(players)

        records.append({
            "Scenario": scn_name,
            "Squad Size": fin["squad_count"],
            "Total Spent (₹ Cr)": f"₹{fin['total_spent']:.2f}",
            "Remaining Purse (₹ Cr)": f"₹{fin['remaining_purse']:.2f}",
            "Utilization": f"{fin['utilization_pct']:.1f}%",
            "Overseas": f"{bal['overseas_count']}/{MAX_OVERSEAS_PLAYERS}",
            "Avg Reliability": f"{bal['avg_reliability']:.1f}",
            "Batters": bal["role_counts"]["Batter"],
            "Bowlers": bal["role_counts"]["Bowler"],
            "All-rounders": bal["role_counts"]["All-rounder"],
            "Wicketkeepers": bal["role_counts"]["Wicketkeeper"]
        })

    return pd.DataFrame(records)
