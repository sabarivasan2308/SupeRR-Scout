"""
Data Preprocessing and Match Reconstruction Module for SupeRR SCOUT Platform.
Transforms raw ball-by-ball, match, and competition records into fully reconstructed match-state deliveries.
"""

from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from .data_loader import load_all_raw_data, save_processed_dataset, load_processed_dataset

logger = logging.getLogger(__name__)

# Dismissal types that count towards bowler's record
BOWLER_DISMISSAL_TYPES = {
    "Caught", "Bowled", "LBW", "Stump", "Hit Wicket"
}

# Illegal deliveries that must be re-bowled
ILLEGAL_DELIVERIES = {"wide", "Overstep", "other"}


def preprocess_matches(matches_df: pd.DataFrame, comps_df: pd.DataFrame) -> pd.DataFrame:
    """Clean, parse dates, and enrich match records with competition details."""
    df = matches_df.copy()
    
    # Parse match dates
    df["match_date"] = pd.to_datetime(df["match_date"], errors="coerce")
    df["year"] = df["match_date"].dt.year
    
    # Merge competition metadata
    comp_cols = ["comp_id", "comp_name", "match_format", "season"]
    comps_clean = comps_df[comp_cols].drop_duplicates(subset=["comp_id"])
    df = df.merge(comps_clean, on="comp_id", how="left")
    
    # Flag IPL vs T20I
    df["is_ipl"] = df["comp_name"].str.contains("IPL|Indian Premier League", case=False, na=False)
    df["competition_type"] = np.where(df["is_ipl"], "IPL", np.where(df["match_format"] == "T20I", "T20I", "Other T20"))
    
    # Knockout flag
    df["knock_out"] = df["knock_out"].fillna(0).astype(int)
    
    # Standardize team names
    df["home_team"] = df["home_team"].fillna("Unknown")
    df["away_team"] = df["away_team"].fillna("Unknown")
    
    return df


def reconstruct_deliveries(
    bbb_df: pd.DataFrame,
    matches_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Reconstruct match state delivery-by-delivery with exact cumulative metrics,
    legal ball accounting, chase target calculation, and phase tagging.
    """
    logger.info("Starting match reconstruction on ball-by-ball deliveries...")
    
    # Work on a copy and sort chronologically
    df = bbb_df.copy()
    
    # Sort to guarantee exact sequence: match, innings, overid, over_ball_num, innings_ball_num
    df = df.sort_values(
        by=["match_id", "innings", "overid", "over_ball_num", "innings_ball_num"]
    ).reset_index(drop=True)
    
    # 1. Classify delivery types
    df["is_wide"] = df["extras_type"] == "wide"
    df["is_noball"] = df["extras_type"].isin(["Overstep", "other"])
    df["is_illegal_ball"] = df["extras_type"].isin(ILLEGAL_DELIVERIES)
    
    # Legal ball for bowler (counts toward 6-ball over)
    df["is_legal_ball_bowler"] = ~df["is_illegal_ball"]
    
    # Ball faced for batter (all except wides)
    df["is_ball_faced_batter"] = ~df["is_wide"]
    
    # 2. Run attribution
    # Runs off the bat
    df["runs_batter"] = df["runs"].fillna(0).astype(int)
    
    # Bowler conceded runs: bat runs + wide extras + no-ball extras. Legbyes/byes/penalty excluded.
    bowler_extras = np.where(df["is_illegal_ball"], df["extras1_runs"].fillna(0), 0)
    df["runs_bowler"] = df["runs_batter"] + bowler_extras
    
    # Total runs scored on delivery (for team total)
    df["runs_total_ball"] = (
        df["runs_batter"] + 
        df["extras1_runs"].fillna(0).astype(int) + 
        df["extras_2_runs"].fillna(0).astype(int)
    )
    
    # 3. Wicket attribution
    df["is_wicket"] = df["is_wicket"].fillna(False).astype(bool)
    df["is_bowler_wicket"] = df["is_wicket"] & df["dismissal_type"].isin(BOWLER_DISMISSAL_TYPES)
    df["is_team_wicket"] = df["is_wicket"]  # includes run outs, etc.
    
    # 4. Dot balls
    # Batter dot: ball faced where batter scored 0 runs
    df["is_batter_dot"] = df["is_ball_faced_batter"] & (df["runs_batter"] == 0)
    # Bowler dot: legal delivery where 0 runs were conceded by bowler
    df["is_bowler_dot"] = df["is_legal_ball_bowler"] & (df["runs_bowler"] == 0)
    
    # 5. Boundaries
    df["is_four"] = df["is_four"].fillna(False).astype(bool)
    df["is_six"] = df["is_six"].fillna(False).astype(bool)
    df["is_boundary"] = df["is_four"] | df["is_six"]
    
    # 6. Cumulative totals within each innings (BEFORE current delivery)
    grp = df.groupby(["match_id", "innings"])
    
    # Cumulative legal balls bowled prior to this delivery
    df["cum_legal_balls"] = grp["is_legal_ball_bowler"].cumsum() - df["is_legal_ball_bowler"].astype(int)
    
    # Cumulative innings runs prior to this delivery
    df["cum_innings_runs"] = grp["runs_total_ball"].cumsum() - df["runs_total_ball"]
    
    # Cumulative wickets fallen prior to this delivery
    df["cum_innings_wickets"] = grp["is_team_wicket"].cumsum() - df["is_team_wicket"].astype(int)
    
    # Wickets in hand for the batting team
    df["wickets_in_hand"] = np.clip(10 - df["cum_innings_wickets"], 0, 10)
    
    # Current Run Rate (CRR) before delivery
    df["overs_completed"] = df["cum_legal_balls"] / 6.0
    df["current_run_rate"] = np.where(
        df["cum_legal_balls"] > 0,
        (df["cum_innings_runs"] / df["cum_legal_balls"]) * 6.0,
        0.0
    )
    
    # 7. Merge Match Metadata
    match_meta_cols = [
        "match_id", "comp_id", "comp_name", "match_format", "season", "match_date", "year",
        "is_ipl", "competition_type", "knock_out", "stage", "venue_id", "venue_country",
        "home_team", "away_team", "win_team_id", "result",
        "first_inn_revised_overs", "second_inn_revised_overs", "revised_target"
    ]
    meta_subset = matches_df[[c for c in match_meta_cols if c in matches_df.columns]].drop_duplicates("match_id")
    df = df.merge(meta_subset, on="match_id", how="left")
    
    # 8. Compute 1st Innings Totals for Chase Targets
    inn1_totals = df[df["innings"] == 1].groupby("match_id")["runs_total_ball"].sum().reset_index()
    inn1_totals.rename(columns={"runs_total_ball": "inn1_total_runs"}, inplace=True)
    df = df.merge(inn1_totals, on="match_id", how="left")
    df["inn1_total_runs"] = df["inn1_total_runs"].fillna(0)
    
    # 9. Compute Target, Balls Remaining, Runs Needed, and RRR for 2nd Innings
    # Determine scheduled overs for innings 2
    scheduled_overs = np.where(
        df["second_inn_revised_overs"].notna() & (df["second_inn_revised_overs"] > 0),
        df["second_inn_revised_overs"],
        np.where(
            df["first_inn_revised_overs"].notna() & (df["first_inn_revised_overs"] > 0),
            df["first_inn_revised_overs"],
            20.0
        )
    )
    df["scheduled_legal_balls"] = (scheduled_overs * 6).astype(int)
    
    # Target runs for Innings 2:
    # Use revised_target if present, else inn1_total_runs + 1
    chase_target = np.where(
        df["revised_target"].notna() & (df["revised_target"] > 0),
        df["revised_target"],
        df["inn1_total_runs"] + 1
    )
    df["target_runs"] = np.where(df["innings"] == 2, chase_target, np.nan)
    
    # Balls remaining in 2nd innings
    df["balls_remaining"] = np.where(
        df["innings"] == 2,
        np.clip(df["scheduled_legal_balls"] - df["cum_legal_balls"], 0, None),
        np.clip(df["scheduled_legal_balls"] - df["cum_legal_balls"], 0, None)
    )
    
    # Runs needed in 2nd innings
    df["runs_needed"] = np.where(
        df["innings"] == 2,
        np.clip(df["target_runs"] - df["cum_innings_runs"], 0, None),
        0
    )
    
    # Required Run Rate (RRR)
    df["required_run_rate"] = np.where(
        (df["innings"] == 2) & (df["balls_remaining"] > 0),
        (df["runs_needed"] / df["balls_remaining"]) * 6.0,
        np.where((df["innings"] == 2) & (df["runs_needed"] > 0), 99.0, 0.0)
    )
    
    # 10. Phase classification
    df["phase"] = np.where(
        df["innings"] >= 3,
        "Super Over",
        np.where(
            df["overid"] <= 6,
            "Powerplay",
            np.where(df["overid"] <= 15, "Middle", "Death")
        )
    )
    
    logger.info("Match reconstruction complete. Reconstructed %d deliveries.", len(df))
    return df
