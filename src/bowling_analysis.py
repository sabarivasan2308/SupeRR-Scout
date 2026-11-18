"""
Bowling Intelligence Module for SupeRR SCOUT Platform.
Computes comprehensive bowler-level performance under high pressure and normal conditions,
strict bowler-attributable runs/wickets accounting, consistency, and situational splits.
"""

from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def compute_bowling_metrics(
    df: pd.DataFrame,
    min_balls_hp: int = 60,
    pressure_col: str = "is_high_pressure_bowl"
) -> pd.DataFrame:
    """
    Compute player-level bowling statistics partitioned into High Pressure and Normal conditions.

    Adheres strictly to cricket scoring rules:
    - Runs conceded: Only batter runs + wides/no-balls (byes and leg-byes excluded).
    - Wickets: Only bowler-credited dismissals (Caught, Bowled, LBW, Stumped, Hit Wicket).
    - Legal balls: Deliveries that count towards the 6-ball over (excluding wides and no-balls).
    """
    # Only consider legal balls for bowler rate calculations
    # Note: We must also account for runs conceded on illegal deliveries
    bowl_df = df.copy()

    # Partition by high-pressure bowling flag
    hp_df = bowl_df[bowl_df[pressure_col]]
    norm_df = bowl_df[~bowl_df[pressure_col]]

    def _agg_bowling(sub_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        if sub_df.empty:
            return pd.DataFrame(columns=[
                "bowler_id", f"{prefix}_legal_balls", f"{prefix}_runs_conceded",
                f"{prefix}_wickets", f"{prefix}_dots", f"{prefix}_boundaries",
                f"{prefix}_matches", f"{prefix}_overs"
            ])

        # Group by bowler_id and bowler_name
        agg = sub_df.groupby(["bowler_id", "bowler_name"]).agg(
            legal_balls=("is_legal_ball_bowler", "sum"),
            runs_conceded=("runs_bowler", "sum"),
            wickets=("is_bowler_wicket", "sum"),
            dots=("is_bowler_dot", "sum"),
            boundaries=("is_boundary", "sum"),
            matches=("match_id", "nunique"),
            total_deliveries=("runs_bowler", "count")
        ).reset_index()

        # Calculate overs as standard cricket decimal (e.g. 19 legal balls = 3.1 overs)
        agg["overs"] = (agg["legal_balls"] // 6) + (agg["legal_balls"] % 6) / 10.0

        agg.rename(columns={
            "legal_balls": f"{prefix}_legal_balls",
            "runs_conceded": f"{prefix}_runs_conceded",
            "wickets": f"{prefix}_wickets",
            "dots": f"{prefix}_dots",
            "boundaries": f"{prefix}_boundaries",
            "matches": f"{prefix}_matches",
            "total_deliveries": f"{prefix}_total_deliveries",
            "overs": f"{prefix}_overs"
        }, inplace=True)
        return agg

    hp_agg = _agg_bowling(hp_df, "hp")
    norm_agg = _agg_bowling(norm_df, "norm")
    total_agg = _agg_bowling(bowl_df, "total")

    # Merge aggregations
    merged = total_agg.merge(hp_agg, on=["bowler_id", "bowler_name"], how="left")
    merged = merged.merge(norm_agg, on=["bowler_id", "bowler_name"], how="left")

    for col in merged.columns:
        if col not in ["bowler_id", "bowler_name"]:
            merged[col] = merged[col].fillna(0)

    # Calculate derived rates for HP
    merged["hp_economy"] = np.where(
        merged["hp_legal_balls"] > 0,
        (merged["hp_runs_conceded"] / merged["hp_legal_balls"]) * 6.0,
        0.0
    ).round(2)

    merged["hp_strike_rate"] = np.where(
        merged["hp_wickets"] > 0,
        (merged["hp_legal_balls"] / merged["hp_wickets"]),
        merged["hp_legal_balls"]
    ).round(2)

    merged["hp_average"] = np.where(
        merged["hp_wickets"] > 0,
        (merged["hp_runs_conceded"] / merged["hp_wickets"]),
        merged["hp_runs_conceded"]
    ).round(2)

    merged["hp_dot_pct"] = np.where(
        merged["hp_legal_balls"] > 0,
        (merged["hp_dots"] / merged["hp_legal_balls"]) * 100.0,
        0.0
    ).round(2)

    merged["hp_boundary_pct"] = np.where(
        merged["hp_legal_balls"] > 0,
        (merged["hp_boundaries"] / merged["hp_legal_balls"]) * 100.0,
        0.0
    ).round(2)

    # Calculate derived rates for Normal
    merged["norm_economy"] = np.where(
        merged["norm_legal_balls"] > 0,
        (merged["norm_runs_conceded"] / merged["norm_legal_balls"]) * 6.0,
        0.0
    ).round(2)

    merged["norm_strike_rate"] = np.where(
        merged["norm_wickets"] > 0,
        (merged["norm_legal_balls"] / merged["norm_wickets"]),
        merged["norm_legal_balls"]
    ).round(2)

    merged["norm_dot_pct"] = np.where(
        merged["norm_legal_balls"] > 0,
        (merged["norm_dots"] / merged["norm_legal_balls"]) * 100.0,
        0.0
    ).round(2)

    merged["norm_boundary_pct"] = np.where(
        merged["norm_legal_balls"] > 0,
        (merged["norm_boundaries"] / merged["norm_legal_balls"]) * 100.0,
        0.0
    ).round(2)

    # Total rates
    merged["total_economy"] = np.where(
        merged["total_legal_balls"] > 0,
        (merged["total_runs_conceded"] / merged["total_legal_balls"]) * 6.0,
        0.0
    ).round(2)

    # Differentials (Normal minus HP: positive econ_delta means tighter economy under pressure!)
    merged["econ_delta"] = (merged["norm_economy"] - merged["hp_economy"]).round(2)
    merged["dot_delta"] = (merged["hp_dot_pct"] - merged["norm_dot_pct"]).round(2)
    merged["boundary_delta"] = (merged["norm_boundary_pct"] - merged["hp_boundary_pct"]).round(2)  # positive means fewer boundaries conceded

    # 2. Match-by-match consistency under pressure
    match_hp = hp_df[hp_df["is_legal_ball_bowler"]].groupby(["bowler_id", "match_id"]).agg(
        m_runs=("runs_bowler", "sum"),
        m_balls=("runs_bowler", "count"),
        m_wickets=("is_bowler_wicket", "sum")
    ).reset_index()
    match_hp["m_econ"] = (match_hp["m_runs"] / match_hp["m_balls"]) * 6.0

    # Effective bowling performance: Economy <= 8.5 OR >= 1 HP wicket
    match_hp["is_effective"] = (match_hp["m_econ"] <= 8.5) | (match_hp["m_wickets"] >= 1)
    consistency_agg = match_hp.groupby("bowler_id").agg(
        effective_match_rate=("is_effective", "mean"),
        std_econ=("m_econ", "std")
    ).reset_index()
    consistency_agg["std_econ"] = consistency_agg["std_econ"].fillna(3.0)
    consistency_agg["consistency_score"] = np.clip(
        (consistency_agg["effective_match_rate"] * 70.0 + (1.0 - np.clip(consistency_agg["std_econ"] / 6.0, 0.0, 1.0)) * 30.0),
        10.0, 95.0
    ).round(1)

    merged = merged.merge(consistency_agg[["bowler_id", "consistency_score", "effective_match_rate"]], on="bowler_id", how="left")
    merged["consistency_score"] = merged["consistency_score"].fillna(30.0)

    # Flag eligibility based on min legal balls
    merged["is_eligible"] = merged["hp_legal_balls"] >= min_balls_hp

    # Clean player name
    merged.rename(columns={"bowler_name": "player_name", "bowler_id": "player_id"}, inplace=True)

    return merged.sort_values(by="hp_wickets", ascending=False).reset_index(drop=True)


def compute_bowling_splits(df: pd.DataFrame, player_id: int) -> Dict[str, pd.DataFrame]:
    """Compute detailed bowling breakdown for a specific player across competitions, seasons, and phases."""
    p_df = df[df["bowler_id"] == player_id].copy()
    if p_df.empty:
        return {}

    def _split_summary(sub: pd.DataFrame, group_col: str) -> pd.DataFrame:
        res = sub.groupby(group_col).agg(
            legal_balls=("is_legal_ball_bowler", "sum"),
            runs_conceded=("runs_bowler", "sum"),
            wickets=("is_bowler_wicket", "sum"),
            dots=("is_bowler_dot", "sum"),
            boundaries=("is_boundary", "sum"),
            hp_legal_balls=("is_high_pressure_bowl", lambda s: (s & sub.loc[s.index, "is_legal_ball_bowler"]).sum()),
            hp_runs=("runs_bowler", lambda r: r[sub.loc[r.index, "is_high_pressure_bowl"]].sum()),
            hp_wickets=("is_bowler_wicket", lambda w: w[sub.loc[w.index, "is_high_pressure_bowl"]].sum())
        ).reset_index()
        res["economy"] = np.where(res["legal_balls"] > 0, (res["runs_conceded"] / res["legal_balls"]) * 6.0, 0.0).round(2)
        res["hp_economy"] = np.where(res["hp_legal_balls"] > 0, (res["hp_runs"] / res["hp_legal_balls"]) * 6.0, 0.0).round(2)
        res["overs"] = (res["legal_balls"] // 6) + (res["legal_balls"] % 6) / 10.0
        return res

    return {
        "competition": _split_summary(p_df, "competition_type"),
        "season": _split_summary(p_df, "season"),
        "phase": _split_summary(p_df, "phase")
    }
