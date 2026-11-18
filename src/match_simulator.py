"""
Match Simulator & Leverage Scenario Engine for SupeRR SCOUT Platform.
Provides validated cricket scenario calculations, deterministic pressure classification,
and historical cohort matching based on empirical delivery records.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def compute_cricket_scenario(
    overs_completed: float,
    current_score: int,
    wickets_lost: int,
    target_score: int,
    overs_limit: float = 20.0,
    is_batting_perspective: bool = True
) -> Dict[str, Any]:
    """
    Calculate strictly-valid cricket situation metrics and pressure index.

    Validations:
    - wickets_lost clamped to [0, 10]
    - overs_completed clamped to [0.0, overs_limit]
    - target_score and current_score clamped to non-negative integers
    """
    # Safe clamping
    w_lost = int(np.clip(wickets_lost, 0, 10))
    overs_limit_val = float(max(1.0, overs_limit))

    # Extract completed overs and fractional balls
    o_comp = float(np.clip(overs_completed, 0.0, overs_limit_val))
    full_overs = int(o_comp)
    balls_in_over = int(round((o_comp - full_overs) * 10))
    if balls_in_over >= 6:
        balls_in_over = 5  # Clamp invalid over decimals (e.g. .6 -> .5)

    balls_completed = full_overs * 6 + balls_in_over
    total_balls = int(round(overs_limit_val * 6))
    balls_remaining = max(0, total_balls - balls_completed)
    overs_remaining = balls_remaining / 6.0

    c_score = max(0, int(current_score))
    t_score = max(0, int(target_score))

    runs_needed = max(0, t_score - c_score)
    wickets_in_hand = max(0, 10 - w_lost)

    # Current Run Rate (CRR)
    crr = (c_score / (balls_completed / 6.0)) if balls_completed > 0 else 0.0

    # Required Run Rate (RRR)
    if balls_remaining <= 0:
        rrr = 0.0 if runs_needed == 0 else 99.0
    else:
        rrr = runs_needed / overs_remaining

    # Phase Classification
    if balls_completed < 36:
        phase = "Powerplay"
    elif balls_completed < 96:
        phase = "Middle"
    else:
        phase = "Death"

    # Pressure Index Calculation (using the exact formula from methodology and pressure engine)
    # 1. R_demand
    if rrr <= 4.0:
        r_demand = 10.0
    elif rrr <= 8.5:
        r_demand = 10.0 + (rrr - 4.0) * (35.0 / 4.5)
    elif rrr <= 14.0:
        r_demand = 45.0 + (rrr - 8.5) * (45.0 / 5.5)
    elif rrr <= 18.0:
        r_demand = 90.0 + (rrr - 14.0) * (10.0 / 4.0)
    else:
        r_demand = 100.0

    # 2. W_lost urgency
    w_urgency = min(100.0, ((w_lost / 9.0) ** 1.15) * 100.0) if w_lost > 0 else 0.0

    # 3. S_stage
    s_stage = min(100.0, (balls_completed / max(1, total_balls)) * 100.0)

    # 4. L_closeness
    if balls_remaining > 0:
        closeness_ratio = (runs_needed / max(1, balls_remaining)) * 6.0
        l_closeness = np.clip(closeness_ratio * 7.5, 0.0, 100.0)
    else:
        l_closeness = 100.0 if runs_needed > 0 else 0.0

    # Composite Batting Pressure
    raw_pressure_bat = 0.40 * r_demand + 0.25 * w_urgency + 0.20 * s_stage + 0.15 * l_closeness
    pressure_bat = float(np.clip(raw_pressure_bat, 0.0, 100.0))

    # Bowling Pressure (strictly harmonized with src/pressure_engine.py chase formulation)
    if rrr > 18.0:
        rrr_stress = float(np.clip(30.0 - (rrr - 18.0) * 2.0, 5.0, 30.0))
    elif rrr >= 12.0:
        rrr_stress = float(np.clip(70.0 - (rrr - 12.0) * 6.5, 30.0, 70.0))
    elif rrr >= 6.0:
        rrr_stress = float(np.clip(70.0 + (12.0 - rrr) * 3.0, 70.0, 95.0))
    else:
        rrr_stress = float(np.clip(90.0 - (6.0 - rrr) * 10.0, 40.0, 90.0))

    stage_stress = float(np.clip((total_balls - balls_remaining) / max(1, total_balls) * 100.0, 10.0, 100.0))
    w_threat = float(np.clip((wickets_in_hand / 10.0) * 80.0 + 10.0, 10.0, 100.0))
    margin_stress = float(np.clip(100.0 - (runs_needed / max(1, balls_remaining) - 1.0) * 10.0, 20.0, 100.0)) if balls_remaining <= 36 else 40.0

    raw_pressure_bowl = 0.35 * rrr_stress + 0.25 * stage_stress + 0.20 * w_threat + 0.20 * margin_stress
    pressure_bowl = float(np.clip(raw_pressure_bowl, 0.0, 100.0))

    active_pressure = pressure_bat if is_batting_perspective else pressure_bowl

    # Band Classification
    if active_pressure < 50.0:
        pressure_category = "Low (<50)"
        category_color = "#287BFF"  # Blue
    elif active_pressure < 65.0:
        pressure_category = "Moderate (50–64)"
        category_color = "#82B1FF"  # Light blue
    elif active_pressure < 75.0:
        pressure_category = "High (65–74)"
        category_color = "#F39C12"  # Amber
    elif active_pressure < 85.0:
        pressure_category = "Very High (75–84)"
        category_color = "#E6007E"  # RR Pink
    else:
        pressure_category = "Extreme (85+)"
        category_color = "#FF0055"  # Electric Pink

    is_high_pressure = active_pressure >= 65.0

    # Tactical situation narrative
    if w_lost >= 10:
        tactical_summary = "All out. Innings terminated."
    elif runs_needed == 0:
        tactical_summary = "Target achieved. Match concluded."
    elif balls_remaining == 0:
        tactical_summary = f"Overs exhausted. Deficit: {runs_needed} runs."
    elif rrr > 16.0:
        tactical_summary = f"Extreme escalation: {runs_needed} runs needed off {balls_remaining} balls ({rrr:.1f} RRR). High boundary demand."
    elif rrr > 11.0:
        tactical_summary = f"Demanding chase: {runs_needed} needed from {balls_remaining} balls with {wickets_in_hand} wickets in hand."
    elif w_lost >= 6:
        tactical_summary = f"Wicket crisis: Only {wickets_in_hand} wickets in hand. Dismissal resistance is critical."
    elif balls_completed <= 36:
        tactical_summary = f"Powerplay phase: Setting initial match tempo. CRR {crr:.1f} vs RRR {rrr:.1f}."
    else:
        tactical_summary = f"Balanced middle contest: {runs_needed} runs required from {balls_remaining} balls."

    return {
        "overs_completed": o_comp,
        "balls_completed": balls_completed,
        "balls_remaining": balls_remaining,
        "overs_remaining": overs_remaining,
        "current_score": c_score,
        "target_score": t_score,
        "runs_needed": runs_needed,
        "wickets_lost": w_lost,
        "wickets_in_hand": wickets_in_hand,
        "crr": float(crr),
        "rrr": float(rrr),
        "phase": phase,
        "pressure_batting": pressure_bat,
        "pressure_bowling": pressure_bowl,
        "active_pressure": active_pressure,
        "pressure_category": pressure_category,
        "category_color": category_color,
        "is_high_pressure": is_high_pressure,
        "tactical_summary": tactical_summary
    }


def find_historical_scenario_cohort(
    deliveries_df: pd.DataFrame,
    target_pressure: float,
    phase: str,
    tolerance: float = 7.5,
    is_batter: bool = True
) -> Dict[str, Any]:
    """
    Query empirical delivery archive to find deliveries matching similar pressure and phase.
    Returns real sample counts, realized strike rates/economy, and top historical performers.
    """
    if deliveries_df.empty:
        return {
            "sample_size": 0,
            "realized_metric": 0.0,
            "boundary_pct": 0.0,
            "dot_pct": 0.0,
            "wicket_pct": 0.0,
            "top_performers": []
        }

    pressure_col = "pressure_batting" if is_batter else "pressure_bowling"
    if pressure_col not in deliveries_df.columns:
        return {
            "sample_size": 0,
            "realized_metric": 0.0,
            "boundary_pct": 0.0,
            "dot_pct": 0.0,
            "wicket_pct": 0.0,
            "top_performers": []
        }

    p_min = max(0.0, target_pressure - tolerance)
    p_max = min(100.0, target_pressure + tolerance)

    # Slice matching phase and pressure window
    matched = deliveries_df[
        (deliveries_df[pressure_col] >= p_min) &
        (deliveries_df[pressure_col] <= p_max)
    ]

    # Try phase match first; if small sample, fallback to pressure band overall
    if phase and "phase" in matched.columns:
        phase_matched = matched[matched["phase"] == phase]
        if len(phase_matched) >= 30:
            matched = phase_matched

    sample_size = len(matched)
    if sample_size == 0:
        return {
            "sample_size": 0,
            "realized_metric": 0.0,
            "boundary_pct": 0.0,
            "dot_pct": 0.0,
            "wicket_pct": 0.0,
            "top_performers": []
        }

    if is_batter:
        runs = matched["runs_batter"].sum()
        balls = matched["is_ball_faced_batter"].sum()
        realized_metric = (runs / max(1, balls)) * 100.0  # Strike Rate
        boundaries = matched["is_boundary"].sum()
        dots = matched["is_batter_dot"].sum()
        wickets = matched["is_wicket"].sum()

        boundary_pct = (boundaries / max(1, balls)) * 100.0
        dot_pct = (dots / max(1, balls)) * 100.0
        wicket_pct = (wickets / max(1, balls)) * 100.0

        # Top 3 batters with min 15 balls in this state
        player_agg = matched.groupby("striker_name").agg(
            runs=("runs_batter", "sum"),
            balls=("is_ball_faced_batter", "sum")
        ).reset_index()
        eligible_agg = player_agg[player_agg["balls"] >= 15].copy()
        if not eligible_agg.empty:
            eligible_agg["sr"] = (eligible_agg["runs"] / eligible_agg["balls"]) * 100.0
            top_performers = eligible_agg.sort_values("sr", ascending=False).head(3).to_dict("records")
        else:
            top_performers = []
    else:
        runs = matched["runs_bowler"].sum()
        balls = matched["is_legal_ball_bowler"].sum()
        realized_metric = (runs / (max(1, balls) / 6.0))  # Economy
        boundaries = matched["is_boundary"].sum()
        dots = matched["is_bowler_dot"].sum()
        wickets = matched["is_bowler_wicket"].sum()

        boundary_pct = (boundaries / max(1, balls)) * 100.0
        dot_pct = (dots / max(1, balls)) * 100.0
        wicket_pct = (wickets / max(1, balls)) * 100.0

        # Top 3 bowlers with min 12 legal balls in this state
        player_agg = matched.groupby("bowler_name").agg(
            runs=("runs_bowler", "sum"),
            balls=("is_legal_ball_bowler", "sum"),
            wickets=("is_bowler_wicket", "sum")
        ).reset_index()
        eligible_agg = player_agg[player_agg["balls"] >= 12].copy()
        if not eligible_agg.empty:
            eligible_agg["econ"] = eligible_agg["runs"] / (eligible_agg["balls"] / 6.0)
            top_performers = eligible_agg.sort_values(["econ", "wickets"], ascending=[True, False]).head(3).to_dict("records")
        else:
            top_performers = []

    return {
        "sample_size": int(sample_size),
        "realized_metric": float(realized_metric),
        "boundary_pct": float(boundary_pct),
        "dot_pct": float(dot_pct),
        "wicket_pct": float(wicket_pct),
        "top_performers": top_performers
    }
