"""
Streamlit UI and Styling Helper Module for SupeRR SCOUT Platform.
Provides centralized CSS injection, Rajasthan Royals branding components,
cached dataset management, and interactive filter controls.
"""

from typing import Tuple, Dict, Any, Optional
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

from src.data_loader import load_processed_dataset, load_all_raw_data
from src.preprocessing import preprocess_matches, reconstruct_deliveries
from src.match_context import add_match_context_signals
from src.pressure_engine import apply_pressure_indices
from src.batting_analysis import compute_batting_metrics
from src.bowling_analysis import compute_bowling_metrics
from src.reliability_model import apply_batting_reliability_model, apply_bowling_reliability_model
from src.rankings import get_top_10_batters, get_top_10_bowlers


def inject_custom_css():
    """
    Inject Rajasthan Royals mandatory visual brand identity into the Streamlit session.
    Brand Palette:
    - RR Royal Pink: #E6007E
    - Deep Royal Blue: #1746A2
    - Electric Blue: #287BFF
    - Deep Navy: #080D20
    - Card Background: #111A32
    - White: #F7F8FC
    - Muted Text: #A8B3CC
    """
    st.markdown("""
    <style>
        /* Import clean modern font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        :root {
            --rr-pink: #E6007E;
            --rr-blue: #1746A2;
            --rr-electric: #287BFF;
            --deep-navy: #080D20;
            --card-bg: #111A32;
            --white: #F7F8FC;
            --muted-text: #A8B3CC;
            --card-border: #1D2B52;
        }

        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #080D20 !important;
            color: #F7F8FC !important;
        }

        /* Main page container */
        .block-container {
            padding-top: 1.8rem !important;
            padding-bottom: 3rem !important;
            max-width: 1400px;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #0C1226 !important;
            border-right: 1px solid #1D2B52 !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem !important;
        }

        /* Sidebar navigation link overrides */
        div[data-testid="stSidebarNav"] {
            padding-top: 0.5rem;
        }

        div[data-testid="stSidebarNav"] ul {
            padding-left: 0;
        }

        div[data-testid="stSidebarNav"] li {
            margin-bottom: 4px;
        }

        div[data-testid="stSidebarNav"] a {
            border-radius: 8px !important;
            color: #A8B3CC !important;
            font-weight: 500 !important;
            transition: all 0.2s ease-in-out !important;
            padding: 8px 14px !important;
        }

        div[data-testid="stSidebarNav"] a:hover {
            background-color: #111A32 !important;
            color: #287BFF !important;
            transform: translateX(3px);
        }

        div[data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(90deg, rgba(230, 0, 126, 0.20) 0%, rgba(23, 70, 162, 0.25) 100%) !important;
            border-left: 3px solid #E6007E !important;
            color: #F7F8FC !important;
            font-weight: 700 !important;
            box-shadow: 0 2px 10px rgba(230, 0, 126, 0.15) !important;
        }

        /* Custom Rajasthan Royals Header Card */
        .rr-header-card {
            background: linear-gradient(135deg, rgba(230, 0, 126, 0.16) 0%, rgba(23, 70, 162, 0.28) 100%);
            border: 1px solid rgba(230, 0, 126, 0.35);
            border-top: 3px solid #E6007E;
            border-radius: 14px;
            padding: 24px 30px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(8, 13, 32, 0.8), 0 0 15px rgba(230, 0, 126, 0.10);
            position: relative;
            overflow: hidden;
        }

        .rr-header-card::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 250px;
            height: 100%;
            background: radial-gradient(circle at top right, rgba(40, 123, 255, 0.15) 0%, transparent 70%);
            pointer-events: none;
        }

        .rr-title {
            font-size: 26px;
            font-weight: 800;
            background: linear-gradient(90deg, #E6007E 0%, #FFFFFF 52%, #287BFF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
            letter-spacing: -0.5px;
            line-height: 1.2;
        }

        .rr-subtitle {
            font-size: 13px;
            color: #A8B3CC;
            font-weight: 500;
            letter-spacing: 0.3px;
        }

        /* Metric KPI Card */
        .rr-kpi-card {
            background: #111A32;
            border: 1px solid #1D2B52;
            border-radius: 12px;
            padding: 18px 22px;
            margin-bottom: 12px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 18px rgba(8, 13, 32, 0.7);
            position: relative;
            overflow: hidden;
        }

        .rr-kpi-card:hover {
            border-color: #E6007E;
            box-shadow: 0 8px 25px rgba(230, 0, 126, 0.22);
            transform: translateY(-3px);
        }

        .rr-kpi-title {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #A8B3CC;
            margin-bottom: 6px;
        }

        .rr-kpi-value {
            font-size: 26px;
            font-weight: 800;
            color: #F7F8FC;
            line-height: 1.15;
        }

        .rr-kpi-sub {
            font-size: 12px;
            color: #2ECC71;
            margin-top: 5px;
            font-weight: 500;
        }

        .rr-kpi-sub-pink {
            font-size: 12px;
            color: #E6007E;
            margin-top: 5px;
            font-weight: 600;
        }

        .rr-kpi-sub-blue {
            font-size: 12px;
            color: #287BFF;
            margin-top: 5px;
            font-weight: 600;
        }

        /* Badge tags */
        .rr-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.4px;
            margin-right: 6px;
        }

        .rr-badge-pink {
            background: rgba(230, 0, 126, 0.16);
            color: #E6007E;
            border: 1px solid rgba(230, 0, 126, 0.45);
            box-shadow: 0 0 10px rgba(230, 0, 126, 0.20);
        }

        .rr-badge-blue {
            background: rgba(40, 123, 255, 0.16);
            color: #287BFF;
            border: 1px solid rgba(40, 123, 255, 0.45);
            box-shadow: 0 0 10px rgba(40, 123, 255, 0.20);
        }

        .rr-badge-gold {
            background: rgba(243, 156, 18, 0.16);
            color: #F39C12;
            border: 1px solid rgba(243, 156, 18, 0.45);
        }

        .rr-badge-navy {
            background: rgba(23, 70, 162, 0.25);
            color: #82B1FF;
            border: 1px solid rgba(40, 123, 255, 0.35);
        }

        /* Generic Card Container */
        .rr-card {
            background: #111A32;
            border: 1px solid #1D2B52;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 16px;
            box-shadow: 0 4px 18px rgba(8, 13, 32, 0.7);
        }

        .rr-card-highlight {
            background: linear-gradient(135deg, rgba(230, 0, 126, 0.10) 0%, rgba(23, 70, 162, 0.18) 100%);
            border: 1px solid rgba(230, 0, 126, 0.30);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 16px;
        }

        /* Streamlit Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            border-bottom: 2px solid #1D2B52;
            padding-bottom: 2px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0 !important;
            color: #A8B3CC !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            padding: 10px 18px !important;
            background: transparent !important;
            border: none !important;
            transition: all 0.2s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #287BFF !important;
            background-color: rgba(40, 123, 255, 0.08) !important;
        }

        .stTabs [aria-selected="true"] {
            color: #E6007E !important;
            border-bottom: 3px solid #E6007E !important;
            background-color: rgba(230, 0, 126, 0.08) !important;
            font-weight: 700 !important;
        }

        /* Streamlit Dataframe Overrides */
        [data-testid="stDataFrame"] {
            border: 1px solid #1D2B52 !important;
            border-radius: 10px !important;
            background-color: #111A32 !important;
            overflow: hidden;
        }

        /* Streamlit Expanders */
        .streamlit-expanderHeader {
            background-color: #111A32 !important;
            border: 1px solid #1D2B52 !important;
            border-radius: 10px !important;
            color: #F7F8FC !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
        }

        .streamlit-expanderHeader:hover {
            border-color: #287BFF !important;
            color: #287BFF !important;
        }

        [data-testid="stExpander"] {
            border: none !important;
            margin-bottom: 10px;
        }

        [data-testid="stExpanderDetails"] {
            background-color: #0E162B !important;
            border: 1px solid #1D2B52 !important;
            border-top: none !important;
            border-radius: 0 0 10px 10px !important;
            padding: 16px 20px !important;
        }

        /* Action & Download Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #E6007E 0%, #1746A2 100%) !important;
            color: #F7F8FC !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            padding: 8px 20px !important;
            box-shadow: 0 4px 16px rgba(230, 0, 126, 0.35) !important;
            transition: all 0.25s ease !important;
        }

        .stButton>button:hover {
            box-shadow: 0 6px 22px rgba(230, 0, 126, 0.55) !important;
            transform: translateY(-2px) !important;
            color: #FFFFFF !important;
        }

        .stDownloadButton>button {
            background-color: #111A32 !important;
            border: 1px solid #287BFF !important;
            color: #F7F8FC !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            padding: 8px 18px !important;
            transition: all 0.25s ease !important;
        }

        .stDownloadButton>button:hover {
            border-color: #E6007E !important;
            color: #E6007E !important;
            box-shadow: 0 0 18px rgba(230, 0, 126, 0.30) !important;
            transform: translateY(-2px) !important;
        }

        /* Radio Buttons & Sliders */
        div[role="radiogroup"] label {
            color: #A8B3CC !important;
            font-weight: 500 !important;
        }

        div[role="radiogroup"] label[data-checked="true"] {
            color: #F7F8FC !important;
            font-weight: 700 !important;
        }

        /* Horizontal rule */
        hr {
            border-color: #1D2B52 !important;
            margin: 20px 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_core_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load or build the preprocessed deliveries and matches datasets."""
    deliveries = load_processed_dataset("deliveries_processed.pkl")
    matches = load_processed_dataset("matches_processed.pkl")

    if deliveries is None or matches is None:
        raw = load_all_raw_data()
        matches = preprocess_matches(raw["matches"], raw["competitions"])
        deliveries = reconstruct_deliveries(raw["ball_by_ball"], matches)
        deliveries = add_match_context_signals(deliveries)
        deliveries = apply_pressure_indices(deliveries, threshold=65.0)

    return deliveries, matches


def render_sidebar_filters(
    deliveries_df: pd.DataFrame,
    matches_df: pd.DataFrame
) -> Dict[str, Any]:
    """Render global sidebar filters and return user filter criteria."""
    st.sidebar.markdown("""
    <div style='background: linear-gradient(135deg, rgba(230,0,126,0.18) 0%, rgba(23,70,162,0.28) 100%); border: 1px solid rgba(230,0,126,0.35); border-top: 3px solid #E6007E; border-radius: 12px; padding: 14px 16px; margin-bottom: 18px; text-align: center;'>
        <div style='font-size: 20px; font-weight: 900; background: linear-gradient(90deg, #E6007E 0%, #FFFFFF 50%, #287BFF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px;'>
            SupeRR SCOUT
        </div>
        <div style='font-size: 10px; font-weight: 700; letter-spacing: 1.2px; color: #A8B3CC; margin-top: 2px; text-transform: uppercase;'>
            Pressure Intelligence Platform
        </div>
        <div style='margin-top: 8px;'>
            <span class='rr-badge rr-badge-pink' style='font-size: 10px; padding: 2px 8px;'>RR IPL 2027 WAR ROOM</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### 🎛️ Global Filters")

    # Season Filter
    available_seasons = sorted(matches_df["season"].dropna().unique().tolist())
    selected_seasons = st.sidebar.multiselect(
        "Seasons",
        options=available_seasons,
        default=available_seasons,
        help="Select one or more cricket seasons to include in the analysis."
    )
    if not selected_seasons:
        selected_seasons = available_seasons

    # Competition Filter
    comp_options = ["All Competitions", "IPL Only", "T20I Only"]
    selected_comp_type = st.sidebar.radio(
        "Competition Scope",
        options=comp_options,
        index=0,
        help="Filter exclusively for IPL franchise games or international T20I fixtures."
    )

    # Team Filter
    all_teams = sorted(list(set(matches_df["home_team"].dropna()).union(set(matches_df["away_team"].dropna()))))
    selected_team = st.sidebar.selectbox(
        "Focus Team",
        options=["All Teams"] + all_teams,
        index=0,
        help="Optionally filter deliveries where the selected team is batting or bowling."
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Analytical Assumptions")

    # Pressure Threshold Slider
    pressure_threshold = st.sidebar.slider(
        "High-Pressure Threshold",
        min_value=50.0,
        max_value=85.0,
        value=65.0,
        step=5.0,
        help="Delivery pressure index boundary (default: 65.0). Deliveries with pressure ≥ threshold are classified as high pressure."
    )

    # Minimum Opportunities Slider
    min_opportunities = st.sidebar.slider(
        "Min Pressure Opportunities",
        min_value=20,
        max_value=150,
        value=60,
        step=10,
        help="Minimum balls faced (batters) or legal balls bowled (bowlers) under pressure to be eligible for ranking."
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style='background: #111A32; border: 1px solid #1D2B52; border-radius: 8px; padding: 12px; font-size: 11px; color: #A8B3CC; line-height: 1.4;'>
        <b style='color: #E6007E;'>SupeRR Selector Season 2</b><br/>
        Rajasthan Royals Hackathon<br/>
        <span style='color: #287BFF;'>Confidential War Room Platform</span>
    </div>
    """, unsafe_allow_html=True)

    return {
        "seasons": selected_seasons,
        "comp_type": selected_comp_type,
        "team": selected_team,
        "pressure_threshold": pressure_threshold,
        "min_opportunities": min_opportunities
    }


def filter_deliveries(
    deliveries_df: pd.DataFrame,
    filters: Dict[str, Any]
) -> pd.DataFrame:
    """Apply sidebar filter selections to the reconstructed deliveries DataFrame."""
    df = deliveries_df.copy()

    # Filter seasons
    if filters["seasons"]:
        df = df[df["season"].isin(filters["seasons"])]

    # Filter competition
    if filters["comp_type"] == "IPL Only":
        df = df[df["is_ipl"]]
    elif filters["comp_type"] == "T20I Only":
        df = df[df["match_format"] == "T20I"]

    # Filter team
    if filters["team"] != "All Teams":
        df = df[(df["home_team"] == filters["team"]) | (df["away_team"] == filters["team"])]

    # Re-apply threshold if modified from default 65.0
    thresh = filters["pressure_threshold"]
    df["is_high_pressure_bat"] = df["pressure_batting"] >= thresh
    df["is_high_pressure_bowl"] = df["pressure_bowling"] >= thresh

    return df


@st.cache_data(show_spinner=False)
def get_computed_rankings(
    filtered_df: pd.DataFrame,
    min_opps: int,
    thresh: float
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute batting and bowling metrics, apply reliability model, and extract top 10."""
    # Batting
    bat_metrics = compute_batting_metrics(filtered_df, min_balls_hp=min_opps)
    bat_ranked = apply_batting_reliability_model(bat_metrics)
    top_10_batters = get_top_10_batters(bat_ranked, min_balls=min_opps)

    # Bowling
    bowl_metrics = compute_bowling_metrics(filtered_df, min_balls_hp=min_opps)
    bowl_ranked = apply_bowling_reliability_model(bowl_metrics)
    top_10_bowlers = get_top_10_bowlers(bowl_ranked, min_balls=min_opps)

    return bat_ranked, top_10_batters, bowl_ranked, top_10_bowlers
