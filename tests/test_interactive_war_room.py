"""
Unit tests for Elite Interactive War Room features:
- Match Situation Scenario Simulator
- Auction Squad Planner & Budget Simulator
- Data Dictionary and Methodology Transparency
- Executive Intelligence Insights
"""

import pytest
import pandas as pd
import numpy as np

from src.match_simulator import compute_cricket_scenario, find_historical_scenario_cohort
from src.squad_planner import compute_squad_financials, analyze_squad_balance, compare_saved_scenarios
from src.data_dictionary import get_data_dictionary, get_methodology_glossary, get_pipeline_stages
from src.pbi_overview_helpers import generate_executive_insights


def test_compute_cricket_scenario_normal_chase():
    scen = compute_cricket_scenario(
        overs_completed=15.0,
        current_score=135,
        wickets_lost=4,
        target_score=185,
        overs_limit=20.0,
        is_batting_perspective=True
    )
    assert scen["runs_needed"] == 50
    assert scen["balls_remaining"] == 30
    assert scen["overs_remaining"] == 5.0
    assert pytest.approx(scen["rrr"], 0.1) == 10.0
    assert pytest.approx(scen["crr"], 0.1) == 9.0
    assert scen["wickets_in_hand"] == 6
    assert 0.0 <= scen["active_pressure"] <= 100.0
    assert scen["phase"] == "Middle"

    # Test Death overs at 17.0
    scen_death = compute_cricket_scenario(
        overs_completed=17.0,
        current_score=150,
        wickets_lost=5,
        target_score=185
    )
    assert scen_death["phase"] == "Death"


def test_compute_cricket_scenario_boundary_clamping():
    # Test boundary clamping for extreme inputs
    scen_clamped = compute_cricket_scenario(
        overs_completed=25.0,  # Exceeds 20.0
        current_score=-10,     # Negative score
        wickets_lost=15,       # Exceeds 10 wickets
        target_score=150,
        overs_limit=20.0
    )
    assert scen_clamped["overs_completed"] == 20.0
    assert scen_clamped["current_score"] == 0
    assert scen_clamped["wickets_lost"] == 10
    assert scen_clamped["wickets_in_hand"] == 0
    assert scen_clamped["balls_remaining"] == 0


def test_compute_cricket_scenario_target_reached():
    scen_won = compute_cricket_scenario(
        overs_completed=18.2,
        current_score=186,
        wickets_lost=3,
        target_score=185
    )
    assert scen_won["runs_needed"] == 0
    assert "concluded" in scen_won["tactical_summary"].lower() or "achieved" in scen_won["tactical_summary"].lower()


def test_find_historical_scenario_cohort_empty():
    empty_df = pd.DataFrame()
    res = find_historical_scenario_cohort(empty_df, target_pressure=70.0, phase="Death")
    assert res["sample_size"] == 0
    assert res["realized_metric"] == 0.0
    assert isinstance(res["top_performers"], list)


def test_compute_squad_financials():
    mock_squad = [
        {"player_name": "Rinku Singh", "role": "Batter", "bid_cr": 14.0},
        {"player_name": "David Miller", "role": "Batter", "bid_cr": 11.5},
        {"player_name": "Sunil Narine", "role": "All-rounder", "bid_cr": 16.0}
    ]
    fin = compute_squad_financials(mock_squad, total_purse_cr=120.0)
    assert pytest.approx(fin["total_spent"], 0.01) == 41.5
    assert pytest.approx(fin["remaining_purse"], 0.01) == 78.5
    assert pytest.approx(fin["utilization_pct"], 0.1) == (41.5 / 120.0) * 100.0
    assert fin["squad_count"] == 3


def test_analyze_squad_balance():
    mock_squad = [
        {"player_name": "Rinku Singh", "role": "Batter", "reliability_score": 75.0, "is_overseas": False},
        {"player_name": "David Miller", "role": "Batter", "reliability_score": 72.0, "is_overseas": True},
        {"player_name": "Heinrich Klaasen", "role": "Wicketkeeper Batter", "reliability_score": 74.0, "is_overseas": True},
        {"player_name": "Sunil Narine", "role": "All-rounder", "reliability_score": 78.0, "is_overseas": True},
        {"player_name": "Rashid Khan", "role": "Bowler", "reliability_score": 76.0, "is_overseas": True},
    ]
    bal = analyze_squad_balance(mock_squad)
    assert bal["squad_count"] == 5
    assert bal["role_counts"]["Batter"] == 2
    assert bal["role_counts"]["Wicketkeeper"] == 1
    assert bal["role_counts"]["All-rounder"] == 1
    assert bal["role_counts"]["Bowler"] == 1
    assert bal["overseas_count"] == 4
    assert bal["domestic_count"] == 1
    assert pytest.approx(bal["avg_reliability"], 0.1) == 75.0
    assert any("Squad has 5 players" in alert for alert in bal["alerts"])


def test_compare_saved_scenarios():
    scenarios = {
        "Plan A": {
            "players": [{"player_name": "P1", "bid_cr": 10.0, "role": "Batter", "reliability_score": 70.0}],
            "total_purse": 120.0
        },
        "Plan B": {
            "players": [{"player_name": "P2", "bid_cr": 25.0, "role": "Bowler", "reliability_score": 80.0}],
            "total_purse": 120.0
        }
    }
    cmp_df = compare_saved_scenarios(scenarios, total_purse_cr=120.0)
    assert len(cmp_df) == 2
    assert "Plan A" in cmp_df["Scenario"].values
    assert "Plan B" in cmp_df["Scenario"].values


def test_data_dictionary_and_glossary():
    dict_df = get_data_dictionary()
    assert not dict_df.empty
    assert "Feature" in dict_df.columns
    assert "Description" in dict_df.columns

    gloss = get_methodology_glossary()
    assert len(gloss) >= 5
    assert any("Bayesian Shrinkage" in g["Term"] for g in gloss)

    stages = get_pipeline_stages()
    assert len(stages) == 6


def test_generate_executive_insights():
    mock_ranked = pd.DataFrame([{
        "player_name": "Rinku Singh",
        "reliability_score": 75.5,
        "hp_strike_rate": 188.8,
        "hp_average": 75.5,
        "hp_balls": 240,
        "sr_delta": 23.4,
        "is_eligible": True
    }])
    mock_deliv = pd.DataFrame([
        {"is_high_pressure_bat": True, "phase": "Death"} for _ in range(50)
    ])
    insights = generate_executive_insights(mock_ranked, is_batter=True, filtered_df=mock_deliv)
    assert len(insights) >= 2
    assert any("Rinku Singh" in ins for ins in insights)
