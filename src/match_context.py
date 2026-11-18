"""
Match Context Module for SupeRR SCOUT Platform.
Computes contextual signals, venue/competition benchmarks, and situational closeness indices.
"""

from typing import Dict
import pandas as pd
import numpy as np

# Empirical Par Scoring Rates across competitions
PAR_RUN_RATES = {
    "IPL": 9.25,        # ~185 par total
    "T20I": 8.30,       # ~166 par total
    "Other T20": 8.50   # ~170 par total
}

# Venue-specific empirical benchmarks (Sawai Mansingh Stadium, Jaipur)
JAIPUR_SMS_PAR_RUN_RATE = 8.40   # Sawai Mansingh Stadium historical IPL par ~168 total
LEAGUE_AVERAGE_PAR_RUN_RATE = 9.25


def get_venue_par_run_rate(venue_name: str = None, competition_type: str = "IPL") -> float:
    """
    Return empirical par run rate.
    Sawai Mansingh Stadium (Jaipur) has longer square boundaries (70-75m) and plays at par 8.40 RPO,
    whereas standard IPL tracks average 9.25 RPO.
    """
    if venue_name and any(v in str(venue_name).lower() for v in ["sawai", "mansingh", "jaipur", "sms"]):
        return JAIPUR_SMS_PAR_RUN_RATE
    return PAR_RUN_RATES.get(competition_type, 8.50)


def add_match_context_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich reconstructed delivery DataFrame with situational context and match leverage signals."""
    res = df.copy()

    # 1. Par run rates based on competition
    res["par_run_rate"] = res["competition_type"].map(PAR_RUN_RATES).fillna(8.50)

    # 2. Stage flags
    res["is_powerplay"] = res["overid"] <= 6
    res["is_middle"] = (res["overid"] >= 7) & (res["overid"] <= 15)
    res["is_death"] = res["overid"] >= 16
    res["is_super_over"] = res["innings"] >= 3
    res["is_chase"] = res["innings"] == 2
    res["is_first_innings"] = res["innings"] == 1

    # 3. Innings progression fraction (0.0 at start, 1.0 at 20 overs)
    res["innings_progress"] = np.clip(res["cum_legal_balls"] / np.maximum(1, res["scheduled_legal_balls"]), 0.0, 1.0)

    # 4. Chase Closeness / Leverage Index (0 to 100)
    # A chase is closest in late overs when runs needed is within reachable margin
    rrr = res["required_run_rate"]
    balls_rem = res["balls_remaining"]
    w_hand = res["wickets_in_hand"]

    # Optimal closeness: RRR between 7.5 and 13.5, balls remaining < 60, wickets in hand >= 2
    # Distance from balanced RRR (9.0)
    rrr_balance = np.exp(-0.5 * ((rrr - 9.0) / 4.0) ** 2)
    # Urgency increases as balls deplete
    ball_urgency = 1.0 - (balls_rem / 120.0)
    # Wicket viability (0 if 0 wickets, peaks around 3-6 wickets)
    wicket_factor = np.clip(w_hand / 5.0, 0.1, 1.0)

    closeness_raw = rrr_balance * ball_urgency * wicket_factor * 100.0
    res["match_closeness"] = np.where(res["is_chase"], np.clip(closeness_raw * 1.5, 0.0, 100.0), 50.0)

    # 5. First-innings Wicket Crisis Factor
    # Measures how far ahead of the wicket curve the bowling team is
    # Expected wickets lost at progression p: roughly p * 6.0 wickets
    expected_wickets = res["innings_progress"] * 6.0
    actual_wickets = res["cum_innings_wickets"]
    wicket_deficit = actual_wickets - expected_wickets

    # Positive deficit = crisis (lost wickets too early)
    res["wicket_crisis_index"] = np.clip((wicket_deficit + 2.0) / 6.0 * 100.0, 0.0, 100.0)

    # 6. Scoring Rate Demand Gap
    # Difference between required rate and current rate (chase) or par rate and current rate (1st inn)
    res["rrr_minus_crr"] = np.where(
        res["is_chase"],
        res["required_run_rate"] - res["current_run_rate"],
        res["par_run_rate"] - res["current_run_rate"]
    )

    # 7. Close match indicator: True if in 2nd innings death overs with RRR <= 15 and wickets in hand >= 2
    res["is_close_match"] = (
        res["is_chase"] &
        (res["overid"] >= 15) &
        (res["required_run_rate"] <= 16.0) &
        (res["wickets_in_hand"] >= 2)
    )

    return res
