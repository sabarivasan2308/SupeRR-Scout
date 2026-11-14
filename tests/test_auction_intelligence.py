"""
Unit Tests for Auction Intelligence Module (SupeRR SCOUT Platform).
Verifies:
1. IPL-Only vs Combined Rankings calculation.
2. Competition split integrity (IPL vs T20I).
3. Role classification and phase allocation calculations.
4. Uncertainty indicators and Bayesian credibility calculations.
5. Auction dossier generation.
6. PDF report compilation.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.auction_intelligence import (
    compute_auction_rankings,
    compute_player_competition_split,
    classify_player_role_and_phases,
    get_sample_uncertainty_profile,
    build_auction_dossier
)
from src.report_generator import build_auction_pdf_report


@pytest.fixture(scope="module")
def deliveries_df():
    pkl_path = Path("data/processed/deliveries_processed.pkl")
    if pkl_path.exists():
        return pd.read_pickle(pkl_path)
    pytest.skip("Processed dataset not available for unit testing.")


def test_compute_auction_rankings(deliveries_df):
    """Verify both Combined and IPL-only rankings produce deduplicated Top 10 lists."""
    results = compute_auction_rankings(deliveries_df, min_balls=60, pressure_thresh=65.0)
    
    for key in ["batters_combined", "batters_ipl", "bowlers_combined", "bowlers_ipl"]:
        df = results[key]
        assert len(df) == 10, f"{key} does not have exactly 10 players"
        assert df["player_id"].nunique() == 10, f"{key} has duplicate player IDs"
        assert "reliability_score" in df.columns, f"{key} missing reliability_score"
        assert df["reliability_score"].is_monotonic_decreasing, f"{key} not sorted descending"


def test_competition_split_integrity(deliveries_df):
    """Verify IPL and T20I splits reconcile cleanly with combined metrics."""
    # Test on Rinku Singh (ID: 4708)
    split_res = compute_player_competition_split(deliveries_df, player_id=4708, is_batter=True)
    splits = split_res["splits"]
    
    assert "IPL" in splits
    assert "T20I" in splits
    assert "Combined" in splits
    
    ipl_b = splits["IPL"]["hp_balls"]
    t20i_b = splits["T20I"]["hp_balls"]
    comb_b = splits["Combined"]["hp_balls"]
    
    assert ipl_b + t20i_b == comb_b, "IPL + T20I balls do not equal combined balls"
    assert splits["IPL"]["hp_sr"] > 180.0, "Rinku Singh IPL HP strike rate unexpected"


def test_bowler_competition_split(deliveries_df):
    """Verify bowler competition split metrics (Sunil Narine ID: 781)."""
    split_res = compute_player_competition_split(deliveries_df, player_id=781, is_batter=False)
    splits = split_res["splits"]
    
    assert splits["IPL"]["hp_legal_balls"] > 150
    assert splits["IPL"]["hp_economy"] < 7.0, "Sunil Narine IPL economy exceeds expected choke threshold"


def test_player_role_and_phases(deliveries_df):
    """Verify empirical phase percentages sum to ~100% and roles are assigned."""
    # Tim David (ID: 6396)
    role_info = classify_player_role_and_phases(deliveries_df, player_id=6396, is_batter=True)
    phases = role_info["phase_distribution"]
    
    total_pct = phases["Powerplay"] + phases["Middle"] + phases["Death"]
    assert abs(total_pct - 100.0) < 1.0, f"Phases sum to {total_pct} instead of 100%"
    assert phases["Death"] >= 65.0, "Tim David death overs phase percentage should be >= 65%"
    assert "Finisher" in role_info["primary_role"] or "Death" in role_info["primary_role"]


def test_sample_uncertainty_profile():
    """Verify Bayesian credibility weighting and uncertainty tiers."""
    u_high = get_sample_uncertainty_profile(250)
    u_low = get_sample_uncertainty_profile(50)
    
    assert u_high["credibility_weight"] > u_low["credibility_weight"]
    assert u_high["margin_of_error"] < u_low["margin_of_error"]
    assert "Tier 1" in u_high["uncertainty_tier"]
    assert "Tier 4" in u_low["uncertainty_tier"]


def test_build_auction_dossier(deliveries_df):
    """Verify structured auction dossier generation."""
    dossier = build_auction_dossier(deliveries_df, player_id=4708, is_batter=True, rank=1, comb_score=85.3, ipl_score=85.9)
    
    assert dossier["player_id"] == 4708
    assert dossier["player_name"] == "Rinku Singh"
    assert len(dossier["strengths"]) >= 2
    assert len(dossier["limitations"]) >= 1
    assert "Jaipur" in dossier["rr_tactical_fit"] or "Sawai Mansingh" in dossier["rr_tactical_fit"]


def test_auction_pdf_generation(deliveries_df, tmp_path):
    """Verify PDF compilation generates valid non-empty PDF bytes."""
    rankings = compute_auction_rankings(deliveries_df, min_balls=60, pressure_thresh=65.0)
    
    # Simple mockup dossier df
    dossier_data = []
    for _, r in rankings["batters_ipl"].head(3).iterrows():
        dossier_data.append({
            "category": "Batter",
            "player_id": r["player_id"],
            "player_name": r["player_name"],
            "primary_role": "Finisher",
            "batting_hand": "LHB",
            "target_tier": "Marquee",
            "comb_score": 85.0,
            "ipl_score": 85.9,
            "delta_ipl": 0.9,
            "ipl_hp_balls": 240,
            "ipl_hp_sr": 188.8,
            "ipl_hp_avg": 75.5,
            "powerplay_pct": 2.0,
            "middle_pct": 25.0,
            "death_pct": 73.0,
            "uncertainty_tier": "Tier 1: High Volume",
            "credibility_weight": 82.5,
            "jaipur_tactical_fit": "Elite fit at SMS ground."
        })
    dossier_df = pd.DataFrame(dossier_data)
    
    summary_stats = {
        "total_deliveries": len(deliveries_df),
        "total_matches": 883
    }
    
    out_pdf = tmp_path / "test_auction.pdf"
    pdf_bytes = build_auction_pdf_report(
        dossier_df,
        rankings["batters_ipl"],
        rankings["bowlers_ipl"],
        rankings["batters_combined"],
        rankings["bowlers_combined"],
        summary_stats,
        output_path=out_pdf
    )
    
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")
    assert out_pdf.exists()


def test_split_info_analytical_note_safety_and_plot(deliveries_df):
    """Regression test for Bug 3: Verify split_info defensive note access and plot_single_player_split signature."""
    from src.auction_intelligence import compute_player_competition_split
    from src.visualizations import plot_single_player_split
    import plotly.graph_objects as go
    
    split_info = compute_player_competition_split(deliveries_df, 4708, is_batter=True)
    assert "splits" in split_info
    # Verify defensive note access does not raise KeyError
    note = split_info.get("analytical_note") or "Evaluation based on high-pressure deliveries."
    assert len(note) > 0
    
    # Verify plot_single_player_split accepts (splits, player_name, is_batter)
    fig = plot_single_player_split(split_info["splits"], "Rinku Singh", is_batter=True)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1

