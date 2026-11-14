"""
Reliability Model Module for SupeRR SCOUT Platform.
Applies Empirical Bayes shrinkage, multi-attribute composite scoring,
confidence interval estimation, and statistical fairness algorithms.
"""

from typing import Tuple, Dict
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Shrinkage Hyperparameters (Prior Half-Credibility Counts)
K_BAT_SR = 50.0
K_BAT_AVG = 50.0
K_BOWL_ECON = 50.0
K_BOWL_SR = 50.0

# Target Opportunity Counts for 100% Credibility Weight
TARGET_BAT_BALLS = 180.0
TARGET_BOWL_BALLS = 200.0


def apply_batting_reliability_model(
    df: pd.DataFrame,
    k_sr: float = K_BAT_SR,
    k_avg: float = K_BAT_AVG
) -> pd.DataFrame:
    """
    Apply Empirical Bayes shrinkage and multi-factor reliability scoring to batter metrics.
    
    Returns enriched DataFrame with:
    - Shrunk Strike Rate & Shrunk Average
    - Sub-scores: scoring_rate_idx, survival_idx, boundary_dot_idx, clutch_delta_idx, consistency_idx
    - composite_reliability_score (0-100)
    - ci_lower, ci_upper (95% Confidence Interval)
    - confidence_rating ("High", "Moderate", "Developing")
    """
    res = df.copy()
    
    # Filter to players with at least some HP balls to compute baseline
    active_hp = res[res["hp_balls"] >= 15]
    
    # Population Priors
    pop_sr = (active_hp["hp_runs"].sum() / np.maximum(1, active_hp["hp_balls"].sum())) * 100.0
    pop_avg = (active_hp["hp_runs"].sum() / np.maximum(1, active_hp["hp_dismissals"].sum()))
    
    logger.info("Batting Empirical Priors: Pop SR=%.2f, Pop Avg=%.2f", pop_sr, pop_avg)
    
    # Empirical Bayes Credibility Weights
    w_sr = res["hp_balls"] / (res["hp_balls"] + k_sr)
    w_avg = res["hp_balls"] / (res["hp_balls"] + k_avg)
    
    # Shrunk estimates
    res["shrunk_hp_sr"] = (w_sr * res["hp_strike_rate"] + (1.0 - w_sr) * pop_sr).round(2)
    res["shrunk_hp_avg"] = (w_avg * res["hp_average"] + (1.0 - w_avg) * pop_avg).round(2)
    
    # 1. Scoring Rate Index (0 to 100): 100 at SR 200+, 0 at SR 90-
    res["sub_scoring_rate"] = np.clip(
        (res["shrunk_hp_sr"] - 95.0) / (195.0 - 95.0) * 100.0,
        0.0, 100.0
    )
    
    # 2. Survival / Average Index (0 to 100): 100 at Avg 50+, 0 at Avg 10-
    res["sub_survival"] = np.clip(
        (res["shrunk_hp_avg"] - 12.0) / (45.0 - 12.0) * 100.0,
        0.0, 100.0
    )
    
    # 3. Boundary & Dot Suppression Index (0 to 100)
    # Rewards high boundary % and penalizes high dot %
    bnd_dot_score = (res["hp_boundary_pct"] * 2.2) + ((40.0 - res["hp_dot_pct"]) * 1.2)
    res["sub_boundary_dot"] = np.clip(bnd_dot_score, 0.0, 100.0)
    
    # 4. Clutch Elevation Delta Index (0 to 100)
    # Does player elevate under pressure relative to their normal baseline?
    clutch_score = 50.0 + (res["sr_delta"] * 0.7) + (res["avg_delta"] * 0.4)
    res["sub_clutch_delta"] = np.clip(clutch_score, 10.0, 95.0)
    
    # 5. Consistency Index
    res["sub_consistency"] = res["consistency_score"].fillna(30.0)
    
    # Composite Raw Reliability Score
    raw_score = (
        0.30 * res["sub_scoring_rate"] +
        0.25 * res["sub_survival"] +
        0.20 * res["sub_boundary_dot"] +
        0.15 * res["sub_clutch_delta"] +
        0.10 * res["sub_consistency"]
    )
    
    # Opportunity Scale Multiplier (Sample Size Credibility)
    opp_factor = np.clip(0.70 + 0.30 * (res["hp_balls"] / TARGET_BAT_BALLS), 0.70, 1.0)
    
    # Final Shrunk Reliability Score (0-100)
    res["reliability_score"] = (raw_score * opp_factor).round(2)
    
    # Uncertainty Estimation (Standard Error & 95% Confidence Interval)
    se = 16.0 / np.sqrt(np.maximum(1, res["hp_balls"]) / 25.0)
    res["ci_lower"] = np.clip((res["reliability_score"] - 1.96 * se).round(1), 0.0, 100.0)
    res["ci_upper"] = np.clip((res["reliability_score"] + 1.96 * se).round(1), 0.0, 100.0)
    res["ci_margin"] = ((res["ci_upper"] - res["ci_lower"]) / 2.0).round(1)
    
    # Confidence Level
    res["confidence_rating"] = np.where(
        res["hp_balls"] >= 160, "High",
        np.where(res["hp_balls"] >= 80, "Moderate", "Low")
    )
    
    return res


def apply_bowling_reliability_model(
    df: pd.DataFrame,
    k_econ: float = K_BOWL_ECON,
    k_sr: float = K_BOWL_SR
) -> pd.DataFrame:
    """
    Apply Empirical Bayes shrinkage and multi-factor reliability scoring to bowler metrics.
    
    Returns enriched DataFrame with:
    - Shrunk Economy & Shrunk Strike Rate
    - Sub-scores: containment_idx, wicket_threat_idx, dot_suppression_idx, clutch_delta_idx, consistency_idx
    - composite_reliability_score (0-100)
    - ci_lower, ci_upper (95% Confidence Interval)
    - confidence_rating ("High", "Moderate", "Developing")
    """
    res = df.copy()
    
    active_hp = res[res["hp_legal_balls"] >= 15]
    
    # Population Priors
    pop_econ = (active_hp["hp_runs_conceded"].sum() / np.maximum(1, active_hp["hp_legal_balls"].sum())) * 6.0
    pop_sr = (active_hp["hp_legal_balls"].sum() / np.maximum(1, active_hp["hp_wickets"].sum()))
    
    logger.info("Bowling Empirical Priors: Pop Econ=%.2f, Pop SR=%.2f", pop_econ, pop_sr)
    
    # Empirical Bayes Credibility Weights
    w_econ = res["hp_legal_balls"] / (res["hp_legal_balls"] + k_econ)
    w_sr = res["hp_legal_balls"] / (res["hp_legal_balls"] + k_sr)
    
    # Shrunk estimates
    res["shrunk_hp_econ"] = (w_econ * res["hp_economy"] + (1.0 - w_econ) * pop_econ).round(2)
    res["shrunk_hp_sr"] = (w_sr * res["hp_strike_rate"] + (1.0 - w_sr) * pop_sr).round(2)
    
    # 1. Containment / Economy Index (0 to 100)
    # Lower economy is better: 100 at 6.0 RPO, 0 at 12.5+ RPO
    res["sub_containment"] = np.clip(
        (12.5 - res["shrunk_hp_econ"]) / (12.5 - 6.5) * 100.0,
        0.0, 100.0
    )
    
    # 2. Wicket Threat Index (0 to 100)
    # Lower balls-per-wicket is better: 100 at SR 8.0, 0 at SR 28.0+
    res["sub_wicket_threat"] = np.clip(
        (26.0 - res["shrunk_hp_sr"]) / (26.0 - 8.0) * 100.0,
        0.0, 100.0
    )
    
    # 3. Dot Creation & Boundary Suppression Index (0 to 100)
    # Rewards high dot % and low boundary concession %
    dot_suppress_score = (res["hp_dot_pct"] * 1.5) + ((35.0 - res["hp_boundary_pct"]) * 1.5)
    res["sub_dot_suppress"] = np.clip(dot_suppress_score, 0.0, 100.0)
    
    # 4. Clutch Elevation Delta Index (0 to 100)
    # Economy improvement under pressure (normal econ - hp econ)
    clutch_score = 50.0 + (res["econ_delta"] * 10.0)
    res["sub_clutch_delta"] = np.clip(clutch_score, 10.0, 95.0)
    
    # 5. Consistency Index
    res["sub_consistency"] = res["consistency_score"].fillna(30.0)
    
    # Composite Raw Reliability Score
    raw_score = (
        0.30 * res["sub_containment"] +
        0.25 * res["sub_wicket_threat"] +
        0.20 * res["sub_dot_suppress"] +
        0.15 * res["sub_clutch_delta"] +
        0.10 * res["sub_consistency"]
    )
    
    # Opportunity Scale Multiplier
    opp_factor = np.clip(0.70 + 0.30 * (res["hp_legal_balls"] / TARGET_BOWL_BALLS), 0.70, 1.0)
    
    # Final Reliability Score
    res["reliability_score"] = (raw_score * opp_factor).round(2)
    
    # Uncertainty Estimation
    se = 16.0 / np.sqrt(np.maximum(1, res["hp_legal_balls"]) / 25.0)
    res["ci_lower"] = np.clip((res["reliability_score"] - 1.96 * se).round(1), 0.0, 100.0)
    res["ci_upper"] = np.clip((res["reliability_score"] + 1.96 * se).round(1), 0.0, 100.0)
    res["ci_margin"] = ((res["ci_upper"] - res["ci_lower"]) / 2.0).round(1)
    
    # Confidence Level
    res["confidence_rating"] = np.where(
        res["hp_legal_balls"] >= 180, "High",
        np.where(res["hp_legal_balls"] >= 90, "Moderate", "Low")
    )
    
    return res
