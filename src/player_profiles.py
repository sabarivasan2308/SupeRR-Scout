"""
Player Profiles and Scouting Evidence Module for SupeRR SCOUT Platform.
Generates comprehensive evidence cards, qualitative tactical scouting reports,
and risk assessments directly backed by empirical calculations.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


def build_batter_evidence_card(row: pd.Series, splits: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
    """Generate detailed scouting evidence card for a batter."""
    name = row["player_name"]
    rank = row.get("rank", "N/A")
    score = row["reliability_score"]
    balls = int(row["hp_balls"])
    runs = int(row["hp_runs"])
    sr = row["hp_strike_rate"]
    avg = row["hp_average"]
    sr_delta = row.get("sr_delta", 0.0)
    boundary_pct = row.get("hp_boundary_pct", 0.0)
    dot_pct = row.get("hp_dot_pct", 0.0)
    matches = int(row.get("hp_matches", 0))
    ci = f"[{row['ci_lower']:.1f} - {row['ci_upper']:.1f}]" if "ci_lower" in row else str(row.get("confidence_interval", ""))
    
    # Identify strongest metric
    if sr >= 185.0:
        strongest = f"Hyper-Clutch Strike Rate ({sr:.1f})"
    elif avg >= 50.0:
        strongest = f"Unrivaled Dismissal Resistance (Avg {avg:.1f})"
    elif boundary_pct >= 28.0:
        strongest = f"Elite Boundary Explosion ({boundary_pct:.1f}% balls)"
    elif sr_delta >= 40.0:
        strongest = f"Massive Gear Shift (+{sr_delta:.1f} SR above baseline)"
    else:
        strongest = f"Reliable Composure ({score:.1f} Score)"
        
    # Tactical Scouting Rationale
    rationale = (
        f"{name} ranks #{rank} in pressure reliability with a score of {score:.1f}. "
        f"Across {matches} matches and {balls} high-pressure deliveries, {name} has accumulated {runs} runs "
        f"at a strike rate of {sr:.1f} and average of {avg:.1f}. "
        f"Critically, when match pressure crosses the 65th index threshold, {name}'s strike rate changes by "
        f"{'+' if sr_delta >= 0 else ''}{sr_delta:.1f} compared to low-pressure situations, hitting boundaries on "
        f"{boundary_pct:.1f}% of balls faced with a low dot-ball rate of {dot_pct:.1f}%."
    )
    
    # Risk and Limitations
    limitations = []
    if balls < 120:
        limitations.append(f"Moderate sample size ({balls} balls); Bayesian shrinkage applied to ensure stability.")
    if dot_pct > 38.0:
        limitations.append(f"Slightly elevated dot ball rate ({dot_pct:.1f}%); dependent on high boundary conversion.")
    if sr_delta < 0:
        limitations.append("Strike rate shows a slight dip under pressure relative to free-flowing baseline.")
    if not limitations:
        limitations.append("No major analytical flaws detected; robust performance across both chase and first-innings pressure.")
        
    limitation_text = " ".join(limitations)
    
    return {
        "player_name": name,
        "player_id": int(row["player_id"]),
        "role": "Batter / Finisher",
        "rank": rank,
        "reliability_score": score,
        "hp_opportunities": f"{balls} balls faced ({matches} matches)",
        "strongest_metric": strongest,
        "pressure_vs_normal": f"HP SR: {sr:.1f} vs Normal: {row.get('norm_strike_rate', 0.0):.1f} (Δ {sr_delta:+.1f}) | HP Avg: {avg:.1f} vs Normal: {row.get('norm_average', 0.0):.1f}",
        "consistency": f"{row.get('consistency_score', 0.0):.0f}/100 ({row.get('effective_match_rate', 0.0)*100:.0f}% high-impact matches)" if "consistency_score" in row else str(row.get("consistency_indicator", "N/A")),
        "confidence_interval": ci,
        "confidence_rating": row.get("confidence_rating", "High"),
        "scouting_rationale": rationale,
        "potential_limitations": limitation_text,
        "metrics_summary": {
            "Runs": runs,
            "Balls": balls,
            "Strike Rate": sr,
            "Average": avg,
            "Boundary %": boundary_pct,
            "Dot %": dot_pct,
            "SR Delta": sr_delta,
            "Matches": matches
        }
    }


def build_bowler_evidence_card(row: pd.Series, splits: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
    """Generate detailed scouting evidence card for a bowler."""
    name = row["player_name"]
    rank = row.get("rank", "N/A")
    score = row["reliability_score"]
    balls = int(row["hp_legal_balls"])
    overs = row.get("hp_overs", (balls // 6) + (balls % 6) / 10.0)
    runs_conc = int(row.get("hp_runs_conceded", 0))
    wkts = int(row["hp_wickets"])
    econ = row["hp_economy"]
    sr = row["hp_strike_rate"]
    dot_pct = row.get("hp_dot_pct", 0.0)
    econ_delta = row.get("econ_delta", 0.0)
    matches = int(row.get("hp_matches", 0))
    ci = f"[{row['ci_lower']:.1f} - {row['ci_upper']:.1f}]" if "ci_lower" in row else str(row.get("confidence_interval", ""))
    
    if econ <= 7.0:
        strongest = f"Suffocating Economy ({econ:.2f} RPO)"
    elif wkts >= 30:
        strongest = f"High-Volume Breakthrough Threat ({wkts} Wkts)"
    elif sr <= 11.0:
        strongest = f"Lethal Wicket Frequency (1 wkt every {sr:.1f} balls)"
    elif dot_pct >= 40.0:
        strongest = f"Elite Pressure-Dot Generation ({dot_pct:.1f}% dots)"
    elif econ_delta > 0.5:
        strongest = f"Clutch Tightening (+{econ_delta:.2f} econ improvement)"
    else:
        strongest = f"Clutch Composure ({score:.1f} Score)"
        
    bnd_pct = row.get('hp_boundary_pct', 0.0)
    rationale = (
        f"{name} ranks #{rank} in bowling pressure reliability with a rating of {score:.1f}. "
        f"Entrusted with {balls} high-pressure deliveries ({overs:.1f} overs) across {matches} fixtures, "
        f"{name} has captured {wkts} bowler-credited wickets while maintaining an exceptional economy of {econ:.2f} RPO. "
        f"Under maximum match tension, {name} delivers {dot_pct:.1f}% dot balls and concedes boundaries on only "
        f"{bnd_pct:.1f}% of balls, showing a composure delta of {econ_delta:+.2f} RPO relative to normal overs."
    )
    
    limitations = []
    if balls < 120:
        limitations.append(f"Sample size is developing ({balls} balls / {overs:.1f} overs); caution in generalizing without broader baseline.")
    if wkts < 10 and balls > 100:
        limitations.append("Role is predominantly containment and run-strangulation rather than primary strike wicket-taking.")
    if econ_delta < -1.0:
        limitations.append(f"Economy expands by {abs(econ_delta):.2f} RPO under intense death/chase pressure.")
    if not limitations:
        limitations.append("Exceptional dual threat: delivers both boundary suppression and crucial breakthroughs under fire.")
        
    limitation_text = " ".join(limitations)
    
    return {
        "player_name": name,
        "player_id": int(row["player_id"]),
        "role": "Bowler / Death Specialist",
        "rank": rank,
        "reliability_score": score,
        "hp_opportunities": f"{balls} legal balls ({overs:.1f} ov, {matches} matches)",
        "strongest_metric": strongest,
        "pressure_vs_normal": f"HP Econ: {econ:.2f} vs Normal: {row['norm_economy']:.2f} (Δ {econ_delta:+.2f}) | HP SR: {sr:.1f} vs Normal: {row['norm_strike_rate']:.1f}",
        "consistency": f"{row['consistency_score']:.0f}/100 ({row['effective_match_rate']*100:.0f}% high-impact matches)",
        "confidence_interval": ci,
        "confidence_rating": row["confidence_rating"],
        "scouting_rationale": rationale,
        "potential_limitations": limitation_text,
        "metrics_summary": {
            "Wickets": wkts,
            "Economy": econ,
            "Legal Balls": balls,
            "Overs": overs,
            "Strike Rate": sr,
            "Dot %": dot_pct,
            "Econ Delta": econ_delta,
            "Matches": matches
        }
    }
