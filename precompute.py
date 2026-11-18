"""
Precompute script to build base artifacts in data/processed/.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import time
import logging
from src.data_loader import load_all_raw_data, save_processed_dataset
from src.preprocessing import preprocess_matches, reconstruct_deliveries
from src.match_context import add_match_context_signals
from src.pressure_engine import apply_pressure_indices
from src.batting_analysis import compute_batting_metrics
from src.bowling_analysis import compute_bowling_metrics
from src.reliability_model import apply_batting_reliability_model, apply_bowling_reliability_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def build_artifacts():
    t0 = time.time()
    logging.info("Starting baseline data precomputation...")

    raw = load_all_raw_data()
    matches_clean = preprocess_matches(raw["matches"], raw["competitions"])
    deliveries = reconstruct_deliveries(raw["ball_by_ball"], matches_clean)
    deliveries = add_match_context_signals(deliveries)
    deliveries = apply_pressure_indices(deliveries, threshold=65.0)

    # Save processed deliveries
    save_processed_dataset(deliveries, "deliveries_processed.parquet")
    save_processed_dataset(matches_clean, "matches_processed.parquet")

    # Precompute default batting and bowling stats
    bat_metrics = compute_batting_metrics(deliveries, min_balls_hp=60)
    bat_ranked = apply_batting_reliability_model(bat_metrics)
    save_processed_dataset(bat_ranked, "batters_ranked.parquet")

    bowl_metrics = compute_bowling_metrics(deliveries, min_balls_hp=60)
    bowl_ranked = apply_bowling_reliability_model(bowl_metrics)
    save_processed_dataset(bowl_ranked, "bowlers_ranked.parquet")

    logging.info(f"All processed artifacts built and saved in {time.time()-t0:.2f}s!")

if __name__ == "__main__":
    build_artifacts()
