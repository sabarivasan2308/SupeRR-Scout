"""
Unit tests for bowling analytics and reliability metrics.
"""

import pytest
import pandas as pd
import numpy as np
from src.bowling_analysis import compute_bowling_metrics, compute_bowling_splits
from src.reliability_model import apply_bowling_reliability_model


@pytest.fixture
def mock_bowling_data():
    """Create sample deliveries for two bowlers."""
    return pd.DataFrame({
        "match_id": [1]*12 + [2]*12,
        "innings": [1]*24,
        "is_legal_ball_bowler": [True]*24,
        "is_high_pressure_bowl": [True]*10 + [False]*2 + [True]*10 + [False]*2,
        "bowler_id": [201]*12 + [202]*12,
        "bowler_name": ["Bowler X"]*12 + ["Bowler Y"]*12,
        "runs_bowler": [0, 0, 1, 0, 4, 1, 0, 0, 1, 0, 1, 2] + [4, 6, 2, 4, 1, 6, 4, 2, 1, 4, 1, 4],
        "is_bowler_wicket": [True, False, False, False, False, True, False, False, False, False, False, False] + [False]*12,
        "is_bowler_dot": [True, True, False, True, False, False, True, True, False, True, False, False] + [False]*12,
        "is_boundary": [False, False, False, False, True, False, False, False, False, False, False, False] + [True, True, False, True, False, True, True, False, False, True, False, True]
    })


def test_bowling_metrics_calculation(mock_bowling_data):
    """Verify bowling metrics aggregate correctly."""
    metrics = compute_bowling_metrics(mock_bowling_data, min_balls_hp=6)
    assert len(metrics) == 2

    bowler_x = metrics[metrics["player_name"] == "Bowler X"].iloc[0]
    assert bowler_x["hp_legal_balls"] == 10
    assert bowler_x["hp_runs_conceded"] == 7
    assert bowler_x["hp_wickets"] == 2
    assert bowler_x["hp_economy"] == pytest.approx(4.2)
    assert bowler_x["hp_dot_pct"] == (6 / 10) * 100.0


def test_bowling_reliability_score(mock_bowling_data):
    """Verify reliability score calculation and ranking."""
    metrics = compute_bowling_metrics(mock_bowling_data, min_balls_hp=6)
    ranked = apply_bowling_reliability_model(metrics)

    assert "reliability_score" in ranked.columns
    assert "ci_lower" in ranked.columns
    assert "ci_upper" in ranked.columns
    # Bowler X has lower economy and more wickets, so should score higher than Bowler Y
    assert ranked.iloc[0]["player_name"] == "Bowler X"
    assert ranked.iloc[0]["reliability_score"] > ranked.iloc[1]["reliability_score"]


def test_bowling_splits_schema_and_runs_conceded():
    """Regression test for Bug 1: Verify compute_bowling_splits returns runs_conceded and table slice succeeds."""
    df = pd.DataFrame({
        "match_id": [1, 1, 2, 2],
        "bowler_id": [781, 781, 781, 781],
        "bowler_name": ["Sunil Narine"] * 4,
        "is_legal_ball_bowler": [True, True, True, True],
        "is_high_pressure_bowl": [True, True, False, True],
        "runs_bowler": [0, 4, 1, 1],
        "is_bowler_wicket": [False, True, False, False],
        "is_bowler_dot": [True, False, False, False],
        "is_boundary": [False, True, False, False],
        "competition_type": ["IPL", "IPL", "IPL", "IPL"],
        "season": ["IPL 2024", "IPL 2024", "IPL 2024", "IPL 2024"],
        "phase": ["Middle", "Middle", "Death", "Death"]
    })
    splits = compute_bowling_splits(df, 781)
    assert "competition" in splits
    comp_df = splits["competition"]
    assert "runs_conceded" in comp_df.columns
    # Ensure exact column slice used by Bowling Intelligence page works without KeyError
    slice_cols = ["competition_type", "legal_balls", "runs_conceded", "wickets", "economy", "hp_legal_balls", "hp_economy"]
    selected = comp_df[slice_cols]
    assert len(selected) > 0
