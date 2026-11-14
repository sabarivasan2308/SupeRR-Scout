"""
Data Validation Module for SupeRR SCOUT Platform.
Verifies data integrity, column schemas, relational constraints, and invariant checks.
"""

from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


EXPECTED_SCHEMAS = {
    "ball_by_ball": [
        "match_id", "innings", "overid", "over_ball_num", "innings_ball_num",
        "batting_team_id", "bowling_team_id", "striker_id", "striker_name",
        "non_striker_id", "non_striker_name", "bowler_id", "bowler_name",
        "runs", "is_four", "is_six", "is_wicket"
    ],
    "matches": [
        "match_id", "comp_id", "match_number", "match_date", "stage",
        "home_team_id", "home_team", "away_team_id", "away_team", "result"
    ],
    "competitions": [
        "comp_id", "comp_name", "match_format", "season"
    ],
    "teams": [
        "comp_id", "team_id", "team_name"
    ],
    "playing_eleven": [
        "match_id", "team_id", "player_id"
    ],
    "player_mapping": [
        "comp_id", "team_id", "player_id", "player_name"
    ]
}


def validate_schema(df: pd.DataFrame, dataset_name: str) -> List[str]:
    """Check that all essential columns are present in the DataFrame."""
    issues = []
    expected_cols = EXPECTED_SCHEMAS.get(dataset_name, [])
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        issues.append(f"[{dataset_name}] Missing critical columns: {missing_cols}")
    return issues


def validate_raw_datasets(datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Perform comprehensive validation across all loaded raw datasets.
    
    Returns:
        dict containing validation status ('passed', 'warnings', 'errors'),
        metrics, and detailed issues if any.
    """
    report = {
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "summary": {}
    }
    
    # 1. Check datasets presence
    for name in EXPECTED_SCHEMAS:
        if name not in datasets:
            report["errors"].append(f"Dataset '{name}' is missing from loaded datasets.")
            report["status"] = "FAILED"
            return report
            
        df = datasets[name]
        schema_issues = validate_schema(df, name)
        if schema_issues:
            report["errors"].extend(schema_issues)
            report["status"] = "FAILED"
            
        report["summary"][name] = {
            "row_count": len(df),
            "column_count": len(df.columns)
        }
    
    # 2. Key relational integrity checks
    bbb = datasets["ball_by_ball"]
    matches = datasets["matches"]
    comps = datasets["competitions"]
    
    # Foreign key checks
    orphan_matches = set(bbb["match_id"]) - set(matches["match_id"])
    if orphan_matches:
        report["errors"].append(f"Found {len(orphan_matches)} match_ids in ball_by_ball not present in matches.csv")
        report["status"] = "FAILED"
        
    orphan_comps = set(matches["comp_id"]) - set(comps["comp_id"])
    if orphan_comps:
        report["errors"].append(f"Found {len(orphan_comps)} comp_ids in matches not present in competitions.csv")
        report["status"] = "FAILED"
        
    # 3. Ball-by-ball semantic integrity
    null_strikers = bbb["striker_id"].isna().sum()
    null_bowlers = bbb["bowler_id"].isna().sum()
    if null_strikers > 0:
        report["errors"].append(f"Found {null_strikers} rows with missing striker_id in ball_by_ball")
        report["status"] = "FAILED"
    if null_bowlers > 0:
        report["errors"].append(f"Found {null_bowlers} rows with missing bowler_id in ball_by_ball")
        report["status"] = "FAILED"
        
    # Check negative runs
    negative_runs = (bbb["runs"] < 0).sum()
    if negative_runs > 0:
        report["errors"].append(f"Found {negative_runs} rows with negative runs in ball_by_ball")
        report["status"] = "FAILED"
        
    # Check innings range
    invalid_innings = (~bbb["innings"].isin([1, 2, 3, 4])).sum()
    if invalid_innings > 0:
        report["warnings"].append(f"Found {invalid_innings} deliveries with unexpected innings numbers.")
        
    # Invariant: is_six implies runs >= 6
    inconsistent_six = ((bbb["is_six"] == True) & (bbb["runs"] < 6)).sum()
    if inconsistent_six > 0:
        report["warnings"].append(f"Found {inconsistent_six} deliveries where is_six is True but runs < 6.")
        
    # Check legal balls
    legal_balls = (~bbb["extras_type"].isin(["wide", "Overstep", "other"])).sum()
    report["summary"]["ball_by_ball"]["legal_deliveries"] = int(legal_balls)
    report["summary"]["ball_by_ball"]["illegal_deliveries"] = int(len(bbb) - legal_balls)
    report["summary"]["ball_by_ball"]["unique_strikers"] = int(bbb["striker_id"].nunique())
    report["summary"]["ball_by_ball"]["unique_bowlers"] = int(bbb["bowler_id"].nunique())
    report["summary"]["matches"]["total_matches"] = int(len(matches))
    
    if report["errors"]:
        report["status"] = "FAILED"
    elif report["warnings"]:
        report["status"] = "PASSED_WITH_WARNINGS"
        
    return report
