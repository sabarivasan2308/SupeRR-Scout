"""
Unit tests for batting analytics and reliability metrics.
"""

import pytest
import pandas as pd
import numpy as np
from src.batting_analysis import compute_batting_metrics
from src.reliability_model import apply_batting_reliability_model


@pytest.fixture
def mock_batting_data():
    """Create sample deliveries for two batters."""
    return pd.DataFrame({
        "match_id": [1]*10 + [2]*10,
        "innings": [1]*20,
        "is_ball_faced_batter": [True]*20,
        "is_high_pressure_bat": [True]*8 + [False]*2 + [True]*8 + [False]*2,
        "striker_id": [101]*10 + [102]*10,
        "striker_name": ["Batter A"]*10 + ["Batter B"]*10,
        "runs_batter": [4, 6, 1, 0, 0, 4, 6, 1, 1, 0] + [0, 1, 0, 0, 1, 0, 1, 0, 0, 0],
        "is_four": [True, False, False, False, False, True, False, False, False, False] + [False]*10,
        "is_six": [False, True, False, False, False, False, True, False, False, False] + [False]*10,
        "is_batter_dot": [False, False, False, True, True, False, False, False, False, True] + [True, False, True, True, False, True, False, True, True, True],
        "is_wicket": [False]*20,
        "dismissed_player_id": [np.nan]*20
    })


def test_batting_metrics_calculation(mock_batting_data):
    """Verify batting metrics aggregate correctly."""
    metrics = compute_batting_metrics(mock_batting_data, min_balls_hp=5)
    assert len(metrics) == 2

    batter_a = metrics[metrics["player_name"] == "Batter A"].iloc[0]
    assert batter_a["hp_balls"] == 8
    assert batter_a["hp_runs"] == 22
    assert batter_a["hp_strike_rate"] == (22 / 8) * 100.0
    assert batter_a["is_eligible"] == True


def test_batting_reliability_score(mock_batting_data):
    """Verify reliability score calculation and ranking."""
    metrics = compute_batting_metrics(mock_batting_data, min_balls_hp=5)
    ranked = apply_batting_reliability_model(metrics)

    assert "reliability_score" in ranked.columns
    assert "ci_lower" in ranked.columns
    assert "ci_upper" in ranked.columns
    assert ranked.iloc[0]["reliability_score"] >= ranked.iloc[1]["reliability_score"]
