"""
Unit tests for pressure intelligence engine.
"""

import pytest
import pandas as pd
import numpy as np
from src.pressure_engine import compute_batting_pressure, compute_bowling_pressure, apply_pressure_indices


@pytest.fixture
def mock_chase_deliveries():
    """Create synthetic chase deliveries spanning low to high pressure situations."""
    return pd.DataFrame({
        "match_id": [1, 1, 1, 1],
        "innings": [2, 2, 2, 2],
        "overid": [3, 10, 18, 20],
        "cum_innings_wickets": [1, 2, 5, 8],
        "wickets_in_hand": [9, 8, 5, 2],
        "innings_progress": [0.15, 0.50, 0.90, 0.98],
        "required_run_rate": [5.0, 8.5, 13.5, 22.0],
        "balls_remaining": [102, 60, 12, 2],
        "runs_needed": [85, 85, 27, 8],
        "current_run_rate": [7.5, 7.8, 8.2, 8.0],
        "par_run_rate": [8.5, 8.5, 8.5, 8.5],
        "match_closeness": [20.0, 50.0, 85.0, 95.0],
        "wicket_crisis_index": [20.0, 30.0, 60.0, 80.0],
        "knock_out": [0, 0, 0, 1]
    })


def test_pressure_boundaries(mock_chase_deliveries):
    """Verify pressure indices stay strictly within [0.0, 100.0] boundaries."""
    bat_p = compute_batting_pressure(mock_chase_deliveries)
    bowl_p = compute_bowling_pressure(mock_chase_deliveries)

    assert bat_p.min() >= 0.0
    assert bat_p.max() <= 100.0
    assert bowl_p.min() >= 0.0
    assert bowl_p.max() <= 100.0


def test_pressure_monotonicity(mock_chase_deliveries):
    """Verify that late overs with high required rate produce higher pressure than early comfortable overs."""
    bat_p = compute_batting_pressure(mock_chase_deliveries)
    # Delivery 0 (early, RRR 5.0) vs Delivery 2 (over 18, RRR 13.5)
    assert bat_p.iloc[2] > bat_p.iloc[0]


def test_apply_pressure_indices_tags(mock_chase_deliveries):
    """Verify boolean flags for high-pressure threshold."""
    res = apply_pressure_indices(mock_chase_deliveries, threshold=65.0)
    assert "is_high_pressure_bat" in res.columns
    assert "is_high_pressure_bowl" in res.columns
    assert res["is_high_pressure_bat"].dtype == bool
