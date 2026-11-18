"""
Pressure Intelligence Engine Module for SupeRR SCOUT Platform.
Computes mathematically rigorous, transparent 0-100 Pressure Indices separately
for Batters and Bowlers across Chases and First-Innings match situations.
"""

from typing import Dict
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Default Pressure Weights
DEFAULT_CHASE_BAT_WEIGHTS = {
    "run_rate_demand": 0.40,
    "wickets_remaining": 0.25,
    "innings_stage": 0.20,
    "match_closeness": 0.15
}

DEFAULT_FIRST_INN_BAT_WEIGHTS = {
    "wickets_lost": 0.45,
    "innings_stage": 0.35,
    "scoring_demand": 0.20
}

DEFAULT_CHASE_BOWL_WEIGHTS = {
    "target_closeness": 0.35,
    "innings_stage": 0.25,
    "opposition_wickets": 0.20,
    "margin_pressure": 0.20
}

DEFAULT_FIRST_INN_BOWL_WEIGHTS = {
    "phase_difficulty": 0.45,
    "batting_strength": 0.30,
    "tempo_threat": 0.25
}

DEFAULT_PRESSURE_THRESHOLD = 65.0
KNOCKOUT_MULTIPLIER = 1.08


def compute_batting_pressure(
    df: pd.DataFrame,
    chase_weights: Dict[str, float] = DEFAULT_CHASE_BAT_WEIGHTS,
    first_inn_weights: Dict[str, float] = DEFAULT_FIRST_INN_BAT_WEIGHTS,
    knockout_boost: float = KNOCKOUT_MULTIPLIER
) -> pd.Series:
    """
    Compute Batting Pressure Index (0-100) for every delivery.

    In a Chase (2nd Innings):
    - Run Rate Demand: Scaled from required run rate (RRR) relative to par.
    - Wickets Remaining: Inversely related to wickets in hand (fewer wickets = higher pressure).
    - Innings Stage: Progressive urgency as deliveries run down.
    - Match Closeness: Peak pressure occurs when the target is within touch and balance is on a knife-edge.

    In 1st Innings:
    - Wickets Lost: Wickets down relative to expected phase baseline (collapse crisis).
    - Innings Stage: Acceleration pressure in death overs (overs 16-20).
    - Scoring Demand: Pressure caused by trailing par run rate.
    """
    # ---------------- 1. Chase Batting Pressure ----------------
    # A. Run Rate Demand (0-100)
    rrr = df["required_run_rate"].fillna(0)
    rrr_demand = np.clip((rrr - 4.0) / (14.0 - 4.0) * 80.0 + 10.0, 0.0, 100.0)
    rrr_demand = np.where(rrr >= 14.0, np.clip(90.0 + (rrr - 14.0) * 2.0, 90.0, 100.0), rrr_demand)
    rrr_demand = np.where(rrr <= 3.0, 5.0, rrr_demand)

    # B. Wickets Remaining Factor (0-100)
    w_lost = df["cum_innings_wickets"]
    w_pressure = np.clip((w_lost / 9.0) ** 1.15 * 100.0, 5.0, 100.0)

    # C. Innings Stage Urgency (0-100)
    stage_urgency = np.clip(df["innings_progress"] * 100.0, 10.0, 100.0)

    # D. Match Closeness Factor (0-100)
    closeness = df["match_closeness"].fillna(50.0)

    chase_pressure = (
        chase_weights["run_rate_demand"] * rrr_demand +
        chase_weights["wickets_remaining"] * w_pressure +
        chase_weights["innings_stage"] * stage_urgency +
        chase_weights["match_closeness"] * closeness
    )

    # ---------------- 2. First Innings Batting Pressure ----------------
    # A. Wickets Lost Crisis (0-100)
    w_crisis = df["wicket_crisis_index"].fillna(30.0)

    # B. Stage Urgency in 1st Innings
    overs = df["overid"]
    stage_1st = np.where(
        overs <= 6,
        25.0 + (overs / 6.0) * 15.0,
        np.where(
            overs <= 15,
            40.0 + ((overs - 6) / 9.0) * 25.0,
            65.0 + ((overs - 15) / 5.0) * 35.0
        )
    )

    # C. Scoring Demand: Par gap
    crr = df["current_run_rate"].fillna(0)
    par_rr = df["par_run_rate"].fillna(8.5)
    rr_gap = par_rr - crr
    scoring_demand = np.where(
        overs >= 4,
        np.clip(50.0 + rr_gap * 12.0, 10.0, 100.0),
        35.0
    )

    first_inn_pressure = (
        first_inn_weights["wickets_lost"] * w_crisis +
        first_inn_weights["innings_stage"] * stage_1st +
        first_inn_weights["scoring_demand"] * scoring_demand
    )

    # ---------------- 3. Combine Chase and 1st Innings ----------------
    batting_pressure = np.where(
        df["innings"] == 2,
        chase_pressure,
        np.where(df["innings"] == 1, first_inn_pressure, 100.0)
    )

    # Knockout tournament multiplier
    is_ko = df["knock_out"] == 1
    batting_pressure = np.where(is_ko, batting_pressure * knockout_boost, batting_pressure)

    return pd.Series(np.clip(batting_pressure, 0.0, 100.0), index=df.index, name="pressure_batting")


def compute_bowling_pressure(
    df: pd.DataFrame,
    chase_weights: Dict[str, float] = DEFAULT_CHASE_BOWL_WEIGHTS,
    first_inn_weights: Dict[str, float] = DEFAULT_FIRST_INN_BOWL_WEIGHTS,
    knockout_boost: float = KNOCKOUT_MULTIPLIER
) -> pd.Series:
    """
    Compute Bowling Pressure Index (0-100) for every delivery.

    Represents the difficulty and stress of the match situation the bowler is bowling into.

    In a Chase (2nd Innings):
    - Target Closeness: Maximum when chase is in balance (RRR 6.0 - 13.0).
    - Innings Stage: Death overs defending small margins creates acute pressure.
    - Opposition Wickets Remaining: Opposition with many wickets in hand can hit freely.
    - Margin Pressure: High when runs needed is small in late overs.

    In 1st Innings:
    - Phase Difficulty: Powerplay (overs 1-6) and Death (overs 16-20).
    - Batting Strength Remaining: Bowling against top/middle order with wickets in hand.
    - Tempo Threat: Opposition scoring at rapid tempo (> par run rate).
    """
    # ---------------- 1. Chase Bowling Pressure ----------------
    rrr = df["required_run_rate"].fillna(0)
    balls_rem = df["balls_remaining"].fillna(120)
    w_hand = df["wickets_in_hand"].fillna(10)
    runs_needed = df["runs_needed"].fillna(100)

    # RRR Stress: High when chase is tight, low when game is mathematically won
    rrr_stress = np.where(
        rrr > 18.0,
        np.clip(30.0 - (rrr - 18.0) * 2.0, 5.0, 30.0),
        np.where(
            rrr >= 12.0,
            np.clip(70.0 - (rrr - 12.0) * 6.5, 30.0, 70.0),
            np.where(
                rrr >= 6.0,
                np.clip(70.0 + (12.0 - rrr) * 3.0, 70.0, 95.0),
                np.clip(90.0 - (6.0 - rrr) * 10.0, 40.0, 90.0)
            )
        )
    )

    # Stage Urgency
    stage_stress = np.clip((120.0 - balls_rem) / 120.0 * 100.0, 10.0, 100.0)

    # Opposition Wickets in Hand
    w_threat = np.clip((w_hand / 10.0) * 80.0 + 10.0, 10.0, 100.0)

    # Margin Stress in late overs
    margin_stress = np.where(
        balls_rem <= 36,
        np.clip(100.0 - (runs_needed / np.maximum(1, balls_rem) - 1.0) * 10.0, 20.0, 100.0),
        40.0
    )

    chase_bowl = (
        chase_weights["target_closeness"] * rrr_stress +
        chase_weights["innings_stage"] * stage_stress +
        chase_weights["opposition_wickets"] * w_threat +
        chase_weights["margin_pressure"] * margin_stress
    )

    # ---------------- 2. First Innings Bowling Pressure ----------------
    overs = df["overid"]
    phase_stress = np.where(
        overs <= 6,
        45.0 + (overs / 6.0) * 15.0,
        np.where(
            overs <= 15,
            25.0 + ((overs - 6) / 9.0) * 20.0,
            60.0 + ((overs - 15) / 5.0) * 35.0
        )
    )

    w_bat_res = np.clip((w_hand / 10.0) * 60.0 + 20.0, 20.0, 80.0)

    crr = df["current_run_rate"].fillna(0)
    par_rr = df["par_run_rate"].fillna(8.5)
    tempo_gap = crr - par_rr
    tempo_stress = np.clip(45.0 + tempo_gap * 8.0, 15.0, 90.0)

    first_inn_bowl = (
        first_inn_weights["phase_difficulty"] * phase_stress +
        first_inn_weights["batting_strength"] * w_bat_res +
        first_inn_weights["tempo_threat"] * tempo_stress
    )

    # ---------------- 3. Combine Chase and 1st Innings ----------------
    bowling_pressure = np.where(
        df["innings"] == 2,
        chase_bowl,
        np.where(df["innings"] == 1, first_inn_bowl, 100.0)
    )

    # Knockout tournament multiplier
    is_ko = df["knock_out"] == 1
    bowling_pressure = np.where(is_ko, bowling_pressure * knockout_boost, bowling_pressure)

    return pd.Series(np.clip(bowling_pressure, 0.0, 100.0), index=df.index, name="pressure_bowling")


def apply_pressure_indices(
    df: pd.DataFrame,
    threshold: float = DEFAULT_PRESSURE_THRESHOLD
) -> pd.DataFrame:
    """Calculate and append batting and bowling pressure indices and high-pressure boolean tags."""
    res = df.copy()
    res["pressure_batting"] = compute_batting_pressure(res).round(2)
    res["pressure_bowling"] = compute_bowling_pressure(res).round(2)

    res["is_high_pressure_bat"] = res["pressure_batting"] >= threshold
    res["is_high_pressure_bowl"] = res["pressure_bowling"] >= threshold

    logger.info(
        "Applied pressure indices: Mean Bat Pressure=%.2f, Mean Bowl Pressure=%.2f, HP Bat Deliveries=%d (%.1f%%), HP Bowl Deliveries=%d (%.1f%%)",
        res["pressure_batting"].mean(),
        res["pressure_bowling"].mean(),
        res["is_high_pressure_bat"].sum(),
        res["is_high_pressure_bat"].mean() * 100.0,
        res["is_high_pressure_bowl"].sum(),
        res["is_high_pressure_bowl"].mean() * 100.0
    )
    return res
