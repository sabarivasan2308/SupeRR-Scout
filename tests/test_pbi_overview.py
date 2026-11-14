"""
Unit tests for Power BI-style Executive Overview visualizations and helpers.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go

from src.ui_helpers import load_core_data, get_computed_rankings
from src.pbi_overview_helpers import (
    build_pbi_leaderboard_chart,
    build_pbi_scatter_chart,
    build_pbi_heatmap_chart,
    build_pbi_comp_comparison_chart,
    build_pbi_distribution_chart,
    build_pbi_season_trends_chart,
    build_player_spotlight_card_html
)


@pytest.fixture(scope="module")
def core_data():
    deliv, matches = load_core_data()
    bat_ranked, top_b, bowl_ranked, top_bw = get_computed_rankings(deliv, 60, 65.0)
    return {
        "deliv": deliv,
        "matches": matches,
        "bat_ranked": bat_ranked,
        "top_b": top_b,
        "bowl_ranked": bowl_ranked,
        "top_bw": top_bw
    }


def test_pbi_leaderboard_chart(core_data):
    # Test Batters Leaderboard
    fig_bat = build_pbi_leaderboard_chart(core_data["bat_ranked"], is_batter=True, top_n=10)
    assert isinstance(fig_bat, go.Figure)
    assert len(fig_bat.data) == 1
    assert len(fig_bat.data[0].y) == 10

    # Test Bowlers Leaderboard with selected player
    fig_bowl = build_pbi_leaderboard_chart(
        core_data["bowl_ranked"], is_batter=False, selected_player="Sunil Narine", top_n=10
    )
    assert isinstance(fig_bowl, go.Figure)
    assert "Sunil Narine" in fig_bowl.data[0].y


def test_pbi_scatter_chart(core_data):
    # Batters Scatter
    fig_scat_b = build_pbi_scatter_chart(core_data["bat_ranked"], is_batter=True, selected_player="Rinku Singh")
    assert isinstance(fig_scat_b, go.Figure)
    # Trace 0 is scatter, Trace 1 is selected player star
    assert len(fig_scat_b.data) >= 2
    assert fig_scat_b.data[1].name == "Selected Player"

    # Bowlers Scatter
    fig_scat_bw = build_pbi_scatter_chart(core_data["bowl_ranked"], is_batter=False)
    assert isinstance(fig_scat_bw, go.Figure)
    assert len(fig_scat_bw.data) >= 1


def test_pbi_heatmap_chart(core_data):
    fig_heat = build_pbi_heatmap_chart(
        core_data["deliv"], core_data["bat_ranked"], is_batter=True, selected_player="Rinku Singh", top_n=8
    )
    assert isinstance(fig_heat, go.Figure)
    assert len(fig_heat.data) == 1
    assert isinstance(fig_heat.data[0], go.Heatmap)
    assert len(fig_heat.data[0].x) == 5  # 5 pressure bands


def test_pbi_comp_comparison_chart(core_data):
    fig_comp = build_pbi_comp_comparison_chart(core_data["deliv"], is_batter=True)
    assert isinstance(fig_comp, go.Figure)
    # Check that competition categories exist
    assert len(fig_comp.data) >= 2


def test_pbi_distribution_chart(core_data):
    fig_dist = build_pbi_distribution_chart(core_data["deliv"], is_batter=True)
    assert isinstance(fig_dist, go.Figure)
    assert isinstance(fig_dist.data[0], go.Pie)


def test_pbi_season_trends_chart(core_data):
    fig_trend = build_pbi_season_trends_chart(
        core_data["deliv"], is_batter=True, selected_player="Rinku Singh"
    )
    assert isinstance(fig_trend, go.Figure)
    assert len(fig_trend.data) == 2  # Cohort line + Rinku Singh line


def test_player_spotlight_card_html(core_data):
    top_batter = core_data["top_b"].iloc[0]
    html = build_player_spotlight_card_html(top_batter, is_batter=True)
    assert "ACTIVE PLAYER SPOTLIGHT" in html
    assert top_batter["player_name"] in html
    assert str(round(top_batter["reliability_score"], 1)) in html


def test_pbi_leaderboard_chart_preranked_without_is_eligible():
    """Regression test for Bug 2: build_pbi_leaderboard_chart handles dataframes without is_eligible column."""
    preranked_df = pd.DataFrame({
        "rank": [1, 2, 3],
        "player_name": ["Player A", "Player B", "Player C"],
        "reliability_score": [85.5, 82.3, 79.1],
        "hp_balls": [200, 180, 150],
        "hp_strike_rate": [190.0, 175.5, 168.0],
        "ci_lower": [75.0, 72.0, 68.0],
        "ci_upper": [95.0, 92.0, 89.0]
    })
    # Must execute cleanly without KeyError: 'is_eligible'
    fig = build_pbi_leaderboard_chart(preranked_df, is_batter=True, top_n=3)
    assert isinstance(fig, go.Figure)
    assert len(fig.data[0].y) == 3
    # Check that highest score is at the top
    assert fig.data[0].y[-1] == "Player A"

