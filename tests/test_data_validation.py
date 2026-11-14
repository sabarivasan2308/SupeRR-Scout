"""
Unit tests for data validation and schema integrity.
"""

import pytest
import pandas as pd
from src.data_loader import load_all_raw_data, load_raw_dataset, get_data_paths
from src.data_validation import validate_schema, validate_raw_datasets


def test_data_paths_exist():
    """Verify all raw CSV file paths exist on disk."""
    paths = get_data_paths()
    for name, path in paths.items():
        assert path.exists(), f"Raw file {name} at {path} does not exist."


def test_raw_data_loading():
    """Verify raw datasets load with expected non-zero counts."""
    raw = load_all_raw_data(nrows=50)
    assert len(raw["ball_by_ball"]) == 50
    assert len(raw["matches"]) == 50
    assert len(raw["competitions"]) > 0


def test_data_validation_suite():
    """Run full data validation suite and verify passing status."""
    raw = load_all_raw_data()
    report = validate_raw_datasets(raw)
    assert report["status"] in ["PASSED", "PASSED_WITH_WARNINGS"], f"Validation failed: {report['errors']}"
    assert len(report["errors"]) == 0


def test_missing_column_detection():
    """Test schema validation catches missing columns."""
    dummy_df = pd.DataFrame({"col_a": [1, 2]})
    issues = validate_schema(dummy_df, "ball_by_ball")
    assert len(issues) > 0
    assert "Missing critical columns" in issues[0]
