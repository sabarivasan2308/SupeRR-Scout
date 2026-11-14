"""
Batting Intelligence Module for SupeRR SCOUT Platform.
Computes comprehensive player-level batting analytics under high pressure
and normal conditions, consistency indices, and situational breakdowns.
"""

from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def compute_batting_metrics(
    df: pd.DataFrame,
    min_balls_hp: int = 60,
    pressure_col: str = "is_high_pressure_bat"
) -> pd.DataFrame:
    """
    Compute player-level batting statistics partitioned into High Pressure and Normal conditions.
    
    Metrics include:
    - Runs, balls faced, strike rate, average, dismissals, 4s, 6s, boundary %, dot %
    - Performance differentials (HP vs Normal)
    - Match-level consistency and opportunity counts
    """
    # Only consider balls faced by batters (exclude wides)
    bat_df = df[df["is_ball_faced_batter"]].copy()
    
    # 1. High Pressure Deliveries
    hp_df = bat_df[bat_df[pressure_col]]
    # Normal / Low Pressure Deliveries
    norm_df = bat_df[~bat_df[pressure_col]]
    
    # Aggregation helper function
    def _agg_batting(sub_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        if sub_df.empty:
            return pd.DataFrame(columns=[
                "striker_id", f"{prefix}_balls", f"{prefix}_runs", f"{prefix}_fours",
                f"{prefix}_sixes", f"{prefix}_dots", f"{prefix}_dismissals", f"{prefix}_matches",
                f"{prefix}_innings"
            ])
            
        # Group by striker_id and striker_name
        agg = sub_df.groupby(["striker_id", "striker_name"]).agg(
            balls=("runs_batter", "count"),
            runs=("runs_batter", "sum"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            dots=("is_batter_dot", "sum"),
            dismissals=("is_wicket", lambda s: (s & (sub_df.loc[s.index, "dismissed_player_id"] == sub_df.loc[s.index, "striker_id"])).sum()),
            matches=("match_id", "nunique"),
            innings=("innings", "count")
        ).reset_index()
        
        # Innings count where batter faced >= 1 ball
        inn_counts = sub_df.groupby("striker_id")[["match_id", "innings"]].apply(lambda g: len(g.drop_duplicates())).reset_index(name="unique_innings")
        agg = agg.merge(inn_counts, on="striker_id", how="left")
        
        agg.rename(columns={
            "balls": f"{prefix}_balls",
            "runs": f"{prefix}_runs",
            "fours": f"{prefix}_fours",
            "sixes": f"{prefix}_sixes",
            "dots": f"{prefix}_dots",
            "dismissals": f"{prefix}_dismissals",
            "matches": f"{prefix}_matches",
            "unique_innings": f"{prefix}_innings"
        }, inplace=True)
        agg.drop(columns=["innings"], errors="ignore", inplace=True)
        return agg

    hp_agg = _agg_batting(hp_df, "hp")
    norm_agg = _agg_batting(norm_df, "norm")
    total_agg = _agg_batting(bat_df, "total")
    
    # Merge aggregations
    merged = total_agg.merge(hp_agg, on=["striker_id", "striker_name"], how="left")
    merged = merged.merge(norm_agg, on=["striker_id", "striker_name"], how="left")
    
    # Fill NAs for players with 0 HP or 0 Normal balls
    for col in merged.columns:
        if col not in ["striker_id", "striker_name"]:
            merged[col] = merged[col].fillna(0)
            
    # Calculate derived rates for HP
    merged["hp_strike_rate"] = np.where(
        merged["hp_balls"] > 0,
        (merged["hp_runs"] / merged["hp_balls"]) * 100.0,
        0.0
    ).round(2)
    
    merged["hp_average"] = np.where(
        merged["hp_balls"] > 0,
        merged["hp_runs"] / np.maximum(1, merged["hp_dismissals"]),
        0.0
    ).round(2)
    
    merged["hp_boundary_pct"] = np.where(
        merged["hp_balls"] > 0,
        ((merged["hp_fours"] + merged["hp_sixes"]) / merged["hp_balls"]) * 100.0,
        0.0
    ).round(2)
    
    merged["hp_four_pct"] = np.where(
        merged["hp_balls"] > 0,
        (merged["hp_fours"] / merged["hp_balls"]) * 100.0,
        0.0
    ).round(2)
    
    merged["hp_six_pct"] = np.where(
        merged["hp_balls"] > 0,
        (merged["hp_sixes"] / merged["hp_balls"]) * 100.0,
        0.0
    ).round(2)
    
    merged["hp_dot_pct"] = np.where(
        merged["hp_balls"] > 0,
        (merged["hp_dots"] / merged["hp_balls"]) * 100.0,
        0.0
    ).round(2)
    
    # Calculate derived rates for Normal
    merged["norm_strike_rate"] = np.where(
        merged["norm_balls"] > 0,
        (merged["norm_runs"] / merged["norm_balls"]) * 100.0,
        0.0
    ).round(2)
    
    merged["norm_average"] = np.where(
        merged["norm_balls"] > 0,
        merged["norm_runs"] / np.maximum(1, merged["norm_dismissals"]),
        0.0
    ).round(2)
    
    merged["norm_boundary_pct"] = np.where(
        merged["norm_balls"] > 0,
        ((merged["norm_fours"] + merged["norm_sixes"]) / merged["norm_balls"]) * 100.0,
        0.0
    ).round(2)
    
    merged["norm_dot_pct"] = np.where(
        merged["norm_balls"] > 0,
        (merged["norm_dots"] / merged["norm_balls"]) * 100.0,
        0.0
    ).round(2)
    
    # Total rates
    merged["total_strike_rate"] = np.where(
        merged["total_balls"] > 0,
        (merged["total_runs"] / merged["total_balls"]) * 100.0,
        0.0
    ).round(2)
    
    # Differentials (High Pressure minus Normal)
    merged["sr_delta"] = (merged["hp_strike_rate"] - merged["norm_strike_rate"]).round(2)
    merged["avg_delta"] = (merged["hp_average"] - merged["norm_average"]).round(2)
    merged["boundary_delta"] = (merged["hp_boundary_pct"] - merged["norm_boundary_pct"]).round(2)
    merged["dot_delta"] = (merged["norm_dot_pct"] - merged["hp_dot_pct"]).round(2)  # positive means fewer dots under HP
    
    # 2. Match-by-match consistency under pressure
    # Measure stability across distinct matches where player faced pressure
    match_hp = hp_df.groupby(["striker_id", "match_id"]).agg(
        m_runs=("runs_batter", "sum"),
        m_balls=("runs_batter", "count")
    ).reset_index()
    match_hp["m_sr"] = (match_hp["m_runs"] / match_hp["m_balls"]) * 100.0
    
    # Compute consistency: % of matches where batter scored at SR >= 135 OR runs >= 15
    match_hp["is_effective"] = (match_hp["m_sr"] >= 135.0) | (match_hp["m_runs"] >= 15)
    consistency_agg = match_hp.groupby("striker_id").agg(
        effective_match_rate=("is_effective", "mean"),
        std_sr=("m_sr", "std")
    ).reset_index()
    consistency_agg["std_sr"] = consistency_agg["std_sr"].fillna(20.0)
    # Higher effective rate and lower relative variance = higher consistency score (0 to 100)
    consistency_agg["consistency_score"] = np.clip(
        (consistency_agg["effective_match_rate"] * 70.0 + (1.0 - np.clip(consistency_agg["std_sr"] / 100.0, 0.0, 1.0)) * 30.0),
        10.0, 95.0
    ).round(1)
    
    merged = merged.merge(consistency_agg[["striker_id", "consistency_score", "effective_match_rate"]], on="striker_id", how="left")
    merged["consistency_score"] = merged["consistency_score"].fillna(30.0)
    
    # Flag eligibility based on min balls threshold
    merged["is_eligible"] = merged["hp_balls"] >= min_balls_hp
    
    # Clean player name
    merged.rename(columns={"striker_name": "player_name", "striker_id": "player_id"}, inplace=True)
    
    return merged.sort_values(by="hp_runs", ascending=False).reset_index(drop=True)


def compute_batting_splits(df: pd.DataFrame, player_id: int) -> Dict[str, pd.DataFrame]:
    """Compute detailed batting breakdown for a specific player across competitions, seasons, and phases."""
    p_df = df[(df["striker_id"] == player_id) & df["is_ball_faced_batter"]].copy()
    if p_df.empty:
        return {}
        
    def _split_summary(sub: pd.DataFrame, group_col: str) -> pd.DataFrame:
        res = sub.groupby(group_col).agg(
            balls=("runs_batter", "count"),
            runs=("runs_batter", "sum"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            dots=("is_batter_dot", "sum"),
            dismissals=("is_wicket", lambda s: (s & (sub.loc[s.index, "dismissed_player_id"] == player_id)).sum()),
            hp_balls=("is_high_pressure_bat", lambda s: (s & sub.loc[s.index, "is_ball_faced_batter"]).sum()),
            hp_runs=("runs_batter", lambda r: r[sub.loc[r.index, "is_high_pressure_bat"]].sum())
        ).reset_index()
        res["strike_rate"] = np.where(res["balls"] > 0, (res["runs"] / res["balls"]) * 100.0, 0.0).round(1)
        res["hp_strike_rate"] = np.where(res["hp_balls"] > 0, (res["hp_runs"] / res["hp_balls"]) * 100.0, 0.0).round(1)
        return res

    return {
        "competition": _split_summary(p_df, "competition_type"),
        "season": _split_summary(p_df, "season"),
        "phase": _split_summary(p_df, "phase")
    }
