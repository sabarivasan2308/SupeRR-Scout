"""
Data Loader Module for SupeRR SCOUT Platform.
Loads raw CSV datasets and processed analytical artifacts with error handling and path resolution.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Base directory for the project
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def get_data_paths() -> Dict[str, Path]:
    """Return dictionary of standard raw data paths."""
    return {
        "ball_by_ball": DATA_RAW_DIR / "ball_by_ball.csv",
        "matches": DATA_RAW_DIR / "matches.csv",
        "competitions": DATA_RAW_DIR / "competitions.csv",
        "teams": DATA_RAW_DIR / "teams.csv",
        "playing_eleven": DATA_RAW_DIR / "playing_eleven.csv",
        "player_mapping": DATA_RAW_DIR / "competition_team_player_mapping.csv",
    }


def load_raw_dataset(name: str, nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Load a single raw dataset by key name.

    Args:
        name: One of 'ball_by_ball', 'matches', 'competitions', 'teams', 'playing_eleven', 'player_mapping'
        nrows: Optional number of rows to load (useful for fast testing)
    """
    paths = get_data_paths()
    if name not in paths:
        raise ValueError(f"Unknown dataset name '{name}'. Expected one of: {list(paths.keys())}")

    file_path = paths[name]
    if not file_path.exists():
        raise FileNotFoundError(f"Required raw dataset not found at expected path: {file_path}")

    logger.info(f"Loading {name} from {file_path}")
    df = pd.read_csv(file_path, nrows=nrows, low_memory=False)
    return df


def load_all_raw_data(nrows: Optional[int] = None) -> Dict[str, pd.DataFrame]:
    """Load all raw CSV datasets into a dictionary of DataFrames."""
    paths = get_data_paths()
    datasets = {}
    for key in paths:
        datasets[key] = load_raw_dataset(key, nrows=nrows)
    return datasets


def save_processed_dataset(df: pd.DataFrame, filename: str) -> Path:
    """Save processed dataframe to data/processed directory using pickle and csv formats."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    base_name = filename.rsplit(".", 1)[0]
    pkl_path = DATA_PROCESSED_DIR / f"{base_name}.pkl"
    csv_path = DATA_PROCESSED_DIR / f"{base_name}.csv"

    # Save both pickle for ultra-fast cache and CSV for transparency/inspection
    df.to_pickle(pkl_path)
    df.to_csv(csv_path, index=False)

    logger.info(f"Saved processed dataset to {pkl_path} and {csv_path}")
    return pkl_path


def load_processed_dataset(filename: str) -> Optional[pd.DataFrame]:
    """Load a processed dataset from data/processed/ if it exists."""
    base_name = filename.rsplit(".", 1)[0]
    pkl_path = DATA_PROCESSED_DIR / f"{base_name}.pkl"
    csv_path = DATA_PROCESSED_DIR / f"{base_name}.csv"

    if pkl_path.exists():
        return pd.read_pickle(pkl_path)
    elif csv_path.exists():
        return pd.read_csv(csv_path, low_memory=False)
    return None
