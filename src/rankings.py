"""
Rankings Engine Module for SupeRR SCOUT Platform.
Generates verified, deduplicated Top 10 Leaderboards for Batters and Bowlers under pressure,
supports dynamic filtering, generates evidence insights, and produces Unstop submission files.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def generate_batter_insight(row: pd.Series) -> str:
    """Generate concise, factual scouting insight for a top batter based on calculated statistics."""
    name = row["player_name"]
    score = row["reliability_score"]
    balls = int(row["hp_balls"])
    sr = row["hp_strike_rate"]
    avg = row["hp_average"]
    sr_delta = row["sr_delta"]
    bnd_pct = row["hp_boundary_pct"]

    if sr_delta > 35:
        clutch_text = f"elevating strike rate by +{sr_delta:.1f} compared to normal situations"
    elif sr_delta > 15:
        clutch_text = f"maintaining aggressive scoring (+{sr_delta:.1f} SR above baseline)"
    else:
        clutch_text = f"operating at an imposing {sr:.1f} strike rate"

    if avg >= 40.0:
        surv_text = f"elite dismissal resistance (HP Avg {avg:.1f})"
    elif avg >= 30.0:
        surv_text = f"solid match-finishing capability (HP Avg {avg:.1f})"
    else:
        surv_text = f"high boundary impact ({bnd_pct:.1f}% boundary ball rate)"

    return f"{name} demonstrates exceptional clutch reliability ({score:.1f}/100 across {balls} pressure balls), {clutch_text} paired with {surv_text}."


def generate_bowler_insight(row: pd.Series) -> str:
    """Generate concise, factual scouting insight for a top bowler based on calculated statistics."""
    name = row["player_name"]
    score = row["reliability_score"]
    balls = int(row["hp_legal_balls"])
    overs = row["hp_overs"]
    econ = row["hp_economy"]
    wkts = int(row["hp_wickets"])
    dot_pct = row["hp_dot_pct"]
    econ_delta = row["econ_delta"]

    if econ_delta > 0:
        contain_text = f"tightening economy to {econ:.2f} RPO (+{econ_delta:.2f} improvement over normal overs)"
    else:
        contain_text = f"sustaining world-class composure at {econ:.2f} RPO"

    if wkts >= 20:
        wicket_text = f"taking {wkts} breakthrough pressure wickets"
    elif wkts >= 10:
        wicket_text = f"snagging {wkts} key pressure breakthroughs with {dot_pct:.1f}% dot balls"
    else:
        wicket_text = f"enforcing suffocating run containment ({dot_pct:.1f}% dot ball frequency)"

    return f"{name} secures a high-trust reliability rating ({score:.1f}/100 across {balls} balls / {overs:.1f} ov), {contain_text} while {wicket_text}."


def get_top_10_batters(
    bat_df: pd.DataFrame,
    min_balls: int = 60
) -> pd.DataFrame:
    """
    Extract Top 10 Batters under pressure.
    Enforces uniqueness, opportunity threshold, and generates insight text.
    """
    eligible = bat_df[bat_df["hp_balls"] >= min_balls].copy()

    # Sort by reliability score descending
    sorted_df = eligible.sort_values(
        by=["reliability_score", "hp_runs", "hp_strike_rate"],
        ascending=[False, False, False]
    ).drop_duplicates(subset=["player_id"]).head(10).reset_index(drop=True)

    sorted_df["rank"] = range(1, len(sorted_df) + 1)

    # Format display columns
    sorted_df["pressure_performance"] = sorted_df.apply(
        lambda r: f"{r['hp_runs']:.0f} runs | SR {r['hp_strike_rate']:.1f} | Avg {r['hp_average']:.1f}",
        axis=1
    )
    sorted_df["normal_performance"] = sorted_df.apply(
        lambda r: f"{r['norm_runs']:.0f} runs | SR {r['norm_strike_rate']:.1f} | Avg {r['norm_average']:.1f}",
        axis=1
    )
    sorted_df["confidence_interval"] = sorted_df.apply(
        lambda r: f"[{r['ci_lower']:.1f} - {r['ci_upper']:.1f}]",
        axis=1
    )
    sorted_df["consistency_indicator"] = sorted_df.apply(
        lambda r: f"{r['consistency_score']:.0f}/100 ({r['effective_match_rate']*100:.0f}% high-impact matches)",
        axis=1
    )
    sorted_df["best_supporting_insight"] = sorted_df.apply(generate_batter_insight, axis=1)

    output_cols = [
        "rank", "player_name", "player_id", "reliability_score", "hp_balls",
        "pressure_performance", "normal_performance", "consistency_indicator",
        "confidence_interval", "confidence_rating", "ci_lower", "ci_upper", "best_supporting_insight",
        "hp_runs", "hp_strike_rate", "hp_average", "hp_boundary_pct", "sr_delta",
        "hp_matches"
    ]
    return sorted_df[[c for c in output_cols if c in sorted_df.columns]]


def get_top_10_bowlers(
    bowl_df: pd.DataFrame,
    min_balls: int = 60
) -> pd.DataFrame:
    """
    Extract Top 10 Bowlers under pressure.
    Enforces uniqueness, opportunity threshold, and generates insight text.
    """
    eligible = bowl_df[bowl_df["hp_legal_balls"] >= min_balls].copy()

    sorted_df = eligible.sort_values(
        by=["reliability_score", "hp_wickets", "hp_economy"],
        ascending=[False, False, True]
    ).drop_duplicates(subset=["player_id"]).head(10).reset_index(drop=True)

    sorted_df["rank"] = range(1, len(sorted_df) + 1)

    sorted_df["pressure_performance"] = sorted_df.apply(
        lambda r: f"Econ {r['hp_economy']:.2f} | {r['hp_wickets']:.0f} wkts | SR {r['hp_strike_rate']:.1f}",
        axis=1
    )
    sorted_df["normal_performance"] = sorted_df.apply(
        lambda r: f"Econ {r['norm_economy']:.2f} | {r['norm_wickets']:.0f} wkts | SR {r['norm_strike_rate']:.1f}",
        axis=1
    )
    sorted_df["confidence_interval"] = sorted_df.apply(
        lambda r: f"[{r['ci_lower']:.1f} - {r['ci_upper']:.1f}]",
        axis=1
    )
    sorted_df["consistency_indicator"] = sorted_df.apply(
        lambda r: f"{r['consistency_score']:.0f}/100 ({r['effective_match_rate']*100:.0f}% high-impact matches)",
        axis=1
    )
    sorted_df["best_supporting_insight"] = sorted_df.apply(generate_bowler_insight, axis=1)

    output_cols = [
        "rank", "player_name", "player_id", "reliability_score", "hp_legal_balls", "hp_overs",
        "pressure_performance", "normal_performance", "consistency_indicator",
        "confidence_interval", "confidence_rating", "ci_lower", "ci_upper", "best_supporting_insight",
        "hp_wickets", "hp_economy", "hp_strike_rate", "hp_dot_pct", "econ_delta",
        "hp_matches"
    ]
    return sorted_df[[c for c in output_cols if c in sorted_df.columns]]


def generate_unstop_submission_table(
    top_batters: pd.DataFrame,
    top_bowlers: pd.DataFrame
) -> pd.DataFrame:
    """Format exact combined submission table matching Unstop dropdown requirements."""
    bat_rows = top_batters[["rank", "player_name", "player_id", "reliability_score"]].copy()
    bat_rows["category"] = "Batter"

    bowl_rows = top_bowlers[["rank", "player_name", "player_id", "reliability_score"]].copy()
    bowl_rows["category"] = "Bowler"

    combined = pd.concat([bat_rows, bowl_rows], ignore_index=True)
    return combined[["category", "rank", "player_name", "player_id", "reliability_score"]]
