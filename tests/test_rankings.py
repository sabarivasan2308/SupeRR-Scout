"""
Unit tests for leaderboard rankings and Unstop export formatting.
"""

import pytest
import pandas as pd
from src.rankings import get_top_10_batters, get_top_10_bowlers, generate_unstop_submission_table


@pytest.fixture
def mock_batters_ranked():
    return pd.DataFrame({
        "player_id": list(range(1, 16)),
        "player_name": [f"Batter {i}" for i in range(1, 16)],
        "reliability_score": [80.0 - i*2 for i in range(15)],
        "hp_balls": [100 - i*2 for i in range(15)],
        "hp_runs": [150 - i*5 for i in range(15)],
        "hp_strike_rate": [170.0 - i*2 for i in range(15)],
        "hp_average": [40.0 - i for i in range(15)],
        "hp_boundary_pct": [25.0]*15,
        "norm_runs": [200]*15,
        "norm_strike_rate": [140.0]*15,
        "norm_average": [30.0]*15,
        "sr_delta": [30.0 - i*2 for i in range(15)],
        "hp_matches": [15]*15,
        "consistency_score": [75.0]*15,
        "effective_match_rate": [0.70]*15,
        "ci_lower": [60.0]*15,
        "ci_upper": [85.0]*15,
        "confidence_rating": ["High"]*15
    })


@pytest.fixture
def mock_bowlers_ranked():
    return pd.DataFrame({
        "player_id": list(range(101, 116)),
        "player_name": [f"Bowler {i}" for i in range(1, 16)],
        "reliability_score": [85.0 - i*2 for i in range(15)],
        "hp_legal_balls": [120 - i*3 for i in range(15)],
        "hp_overs": [20.0 - i*0.5 for i in range(15)],
        "hp_runs_conceded": [120]*15,
        "hp_wickets": [15 - i for i in range(15)],
        "hp_economy": [7.0 + i*0.2 for i in range(15)],
        "hp_strike_rate": [12.0 + i*0.5 for i in range(15)],
        "hp_dot_pct": [35.0]*15,
        "hp_boundary_pct": [15.0]*15,
        "norm_economy": [8.5]*15,
        "norm_wickets": [20]*15,
        "norm_strike_rate": [15.0]*15,
        "econ_delta": [1.5 - i*0.2 for i in range(15)],
        "hp_matches": [20]*15,
        "consistency_score": [70.0]*15,
        "effective_match_rate": [0.65]*15,
        "ci_lower": [65.0]*15,
        "ci_upper": [88.0]*15,
        "confidence_rating": ["High"]*15
    })


def test_top_10_batters_count_and_uniqueness(mock_batters_ranked):
    """Verify exactly 10 distinct batters are returned in ranked order."""
    top10 = get_top_10_batters(mock_batters_ranked, min_balls=50)
    assert len(top10) == 10
    assert top10["player_id"].nunique() == 10
    assert list(top10["rank"]) == list(range(1, 11))
    assert top10.iloc[0]["reliability_score"] >= top10.iloc[1]["reliability_score"]


def test_top_10_bowlers_count_and_uniqueness(mock_bowlers_ranked):
    """Verify exactly 10 distinct bowlers are returned in ranked order."""
    top10 = get_top_10_bowlers(mock_bowlers_ranked, min_balls=50)
    assert len(top10) == 10
    assert top10["player_id"].nunique() == 10
    assert list(top10["rank"]) == list(range(1, 11))
    assert top10.iloc[0]["reliability_score"] >= top10.iloc[1]["reliability_score"]


def test_unstop_submission_format(mock_batters_ranked, mock_bowlers_ranked):
    """Verify combined Unstop submission table format."""
    top_bat = get_top_10_batters(mock_batters_ranked, min_balls=50)
    top_bowl = get_top_10_bowlers(mock_bowlers_ranked, min_balls=50)
    submission = generate_unstop_submission_table(top_bat, top_bowl)
    
    assert len(submission) == 20
    assert set(submission["category"].unique()) == {"Batter", "Bowler"}
    assert list(submission.columns) == ["category", "rank", "player_name", "player_id", "reliability_score"]
