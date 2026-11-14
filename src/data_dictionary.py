"""
Data Dictionary and Methodology Transparency Engine for SupeRR SCOUT Platform.
Provides formal data dictionaries, methodology glossaries, and workflow pipeline specifications.
"""

from typing import List, Dict, Any
import pandas as pd


def get_data_dictionary() -> pd.DataFrame:
    """
    Return the formal data dictionary of primary features utilized across the platform.
    """
    data = [
        {"Feature": "match_id", "Source": "matches / ball_by_ball", "Type": "Integer", "Description": "Unique match identifier assigned across tournament fixtures."},
        {"Feature": "season", "Source": "matches", "Type": "Integer", "Description": "Tournament calendar year (2022–2026)."},
        {"Feature": "competition_type", "Source": "derived", "Type": "Categorical", "Description": "Tournament classification: 'IPL', 'T20I', or 'Other T20'."},
        {"Feature": "innings", "Source": "ball_by_ball", "Type": "Integer", "Description": "Innings number (1 for setting total, 2 for chasing target)."},
        {"Feature": "overid", "Source": "ball_by_ball", "Type": "Integer", "Description": "Completed overs in innings (0 to 19)."},
        {"Feature": "phase", "Source": "derived", "Type": "Categorical", "Description": "Match stage: Powerplay (overs 1–6), Middle (7–16), Death (17–20)."},
        {"Feature": "striker_name", "Source": "ball_by_ball", "Type": "String", "Description": "Name of batter facing the delivery."},
        {"Feature": "bowler_name", "Source": "ball_by_ball", "Type": "String", "Description": "Name of legal bowler executing the delivery."},
        {"Feature": "runs_batter", "Source": "ball_by_ball", "Type": "Integer", "Description": "Runs scored directly off the bat on this delivery."},
        {"Feature": "runs_bowler", "Source": "derived", "Type": "Integer", "Description": "Runs credited/debited to bowler (including wides & no-balls, excluding byes/leg-byes)."},
        {"Feature": "is_legal_ball_bowler", "Source": "derived", "Type": "Boolean", "Description": "Flag indicating legal delivery counted towards bowler's over tally."},
        {"Feature": "is_ball_faced_batter", "Source": "derived", "Type": "Boolean", "Description": "Flag indicating ball faced counted against batter (excludes wides)."},
        {"Feature": "is_boundary", "Source": "derived", "Type": "Boolean", "Description": "Binary flag indicating if 4 or 6 runs were scored."},
        {"Feature": "is_wicket", "Source": "ball_by_ball", "Type": "Boolean", "Description": "Binary indicator that a dismissal occurred on the delivery."},
        {"Feature": "required_run_rate", "Source": "match_context", "Type": "Float", "Description": "Required run rate per 6 balls for chasing side to win."},
        {"Feature": "pressure_batting", "Source": "pressure_engine", "Type": "Float", "Description": "Continuous pressure index for batting side (0.0 to 100.0)."},
        {"Feature": "pressure_bowling", "Source": "pressure_engine", "Type": "Float", "Description": "Continuous pressure index for bowling side (0.0 to 100.0)."},
        {"Feature": "is_high_pressure_bat", "Source": "pressure_engine", "Type": "Boolean", "Description": "Delivery has pressure_batting ≥ 65.0 threshold."},
        {"Feature": "is_high_pressure_bowl", "Source": "pressure_engine", "Type": "Boolean", "Description": "Delivery has pressure_bowling ≥ 65.0 threshold."},
        {"Feature": "reliability_score", "Source": "reliability_model", "Type": "Float", "Description": "Composite Bayesian-shrunk clutch reliability score (0.0 to 100.0)."}
    ]
    return pd.DataFrame(data)


def get_methodology_glossary() -> List[Dict[str, str]]:
    """
    Return formal definitions for core analytics, Bayesian models, and pressure terms.
    """
    return [
        {
            "Term": "High-Pressure Delivery (HP)",
            "Definition": "Any legal delivery where the computed continuous match pressure index is ≥ 65.0 out of 100.0, indicating acute situational leverage."
        },
        {
            "Term": "Bayesian Shrinkage",
            "Definition": "Empirical Bayes technique that pulls small-sample player observations towards the tournament population prior, preventing small-sample outliers from dominating leaderboards."
        },
        {
            "Term": "Half-Credibility Constant (K = 50)",
            "Definition": "The exact number of high-pressure deliveries required for a player's observed performance to receive equal (50%) weight with the tournament prior mean in the shrinkage formula w_i = n_i / (n_i + 50)."
        },
        {
            "Term": "Clutch Differential (Δ SR / Δ Econ)",
            "Definition": "The direct algebraic delta between a player's high-pressure performance (P ≥ 65.0) and their baseline performance under normal conditions (P < 65.0). Positive Δ SR and negative Δ Econ denote elite clutch execution."
        },
        {
            "Term": "95% Confidence Interval (CI)",
            "Definition": "Asymptotic uncertainty range calculated via propagation error ± 1.96 · (16.0 / √(n_i / 25)), illustrating the statistical certainty of the composite reliability score."
        },
        {
            "Term": "Opportunity Scaling Factor",
            "Definition": "Regularization coefficient scaled by min(1.0, 0.70 + 0.30 · (n_i / 180)), rewarding multi-year volume over brief hot streaks."
        },
        {
            "Term": "Sawai Mansingh Fortress Profile",
            "Definition": "Tactical suitability assessment for RR's home venue in Jaipur, characterized by large boundary dimensions, high running demands, and high value on death bowling control."
        }
    ]


def get_pipeline_stages() -> List[Dict[str, Any]]:
    """
    Return structured data representing the end-to-end analytics workflow.
    """
    return [
        {"Stage": "1. Data Ingestion", "Icon": "📥", "Details": "Ingest 200,999 raw deliveries and 889 matches across IPL, T20I, and Rising Stars."},
        {"Stage": "2. Context Signal Engine", "Icon": "⏱️", "Details": "Reconstruct ball-by-ball running scores, wickets in hand, RRR, match phase, and chase dynamics."},
        {"Stage": "3. Pressure Engine", "Icon": "🔥", "Details": "Compute continuous 0–100 delivery leverage combining demand, wicket crisis, stage, and closeness."},
        {"Stage": "4. Reliability Model", "Icon": "🧠", "Details": "Apply Empirical Bayes shrinkage (K=50) and 95% asymptotic confidence intervals."},
        {"Stage": "5. Ranking Command", "Icon": "🏆", "Details": "Extract official Top 10 leaderboards for Combined and IPL-only scopes with strict eligibility rules."},
        {"Stage": "6. Auction War Room", "Icon": "🏰", "Details": "Role fingerprinting, budget simulation, squad planning, and RR tactical dossier generation."}
    ]
