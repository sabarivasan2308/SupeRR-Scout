"""
Automated AppTest suite across all 8 pages and app.py
Ensures zero uncaught runtime exceptions across the platform.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("page_path", [
    "app.py",
    "pages/1_Executive_Overview.py",
    "pages/2_Batting_Intelligence.py",
    "pages/3_Bowling_Intelligence.py",
    "pages/4_Top_10_Rankings.py",
    "pages/5_Player_Comparison.py",
    "pages/6_Match_Situation_Analysis.py",
    "pages/7_Methodology.py",
    "pages/8_Auction_Intelligence.py"
])
def test_streamlit_page_renders_without_exception(page_path):
    abs_path = ROOT_DIR / page_path
    at = AppTest.from_file(str(abs_path), default_timeout=35)
    at.run()
    assert not at.exception, f"Page {page_path} raised exception: {at.exception}"
