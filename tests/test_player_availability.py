"""
Unit Tests for IPL 2027 Player Availability and RR Auction Shortlisting.
Verifies:
1. Status registry completeness and schema validity based on official 17-Nov-2026 announcements.
2. Accurate exclusion of retained players (including Powell, Holder, Samson).
3. Accurate exclusion of contracted and traded players (including Hardik at PBKS, Arshdeep at MI, Pant at DC, Curran at LSG).
4. Accurate exclusion of withdrawn players (Travis Head opted out, MS Dhoni retired/mentoring) and ineligible players.
5. Strict exclusion of released players whose auction registration cannot be verified (Hetmyer, Deshpande, Boult, Starc, Pathirana, Raza, Mujeeb).
6. Accurate identification of 100% verified auction-eligible targets with authoritative registration citations.
7. Default rejection of unverified/unregistered players.
8. filter_available_rankings strictly filters out all non-eligible players.
9. RR squad state: 19 players, 6 available slots, 3 overseas slots, ₹92.95 Cr spent, ₹27.05 Cr remaining purse.
10. All RR priority shortlist candidates are 100% verified auction-eligible.
11. Franchise availability summary covers all 10 IPL franchises with exact 17-Nov-2026 figures.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.player_availability import (
    load_player_status_registry,
    get_player_availability,
    is_player_auction_eligible,
    filter_available_rankings,
    get_rr_squad_state,
    get_rr_squad_gaps,
    get_rr_priority_shortlist,
    get_unverified_shortlist_targets,
    get_franchise_availability_summary,
    STATUS_AUCTION_ELIGIBLE,
    STATUS_RETAINED,
    STATUS_CONTRACTED,
    STATUS_RR_CURRENT,
    STATUS_INELIGIBLE,
    STATUS_WITHDRAWN_RETIRED,
    STATUS_UNVERIFIED,
)


def test_status_registry_loaded():
    """Verify player status registry loads properly and has minimum required entries."""
    registry = load_player_status_registry()
    assert isinstance(registry, dict)
    assert len(registry) >= 50, f"Expected at least 50 players in registry, got {len(registry)}"

    for pid, data in registry.items():
        assert "name" in data, f"Player {pid} missing name"
        assert "status" in data, f"Player {pid} missing status"
        assert "source_url" in data, f"Player {pid} missing source_url"
        assert "last_verified_date" in data, f"Player {pid} missing last_verified_date"
        assert data["last_verified_date"] == "2026-11-18", f"Verification date must be 2026-11-18"


def test_retained_players_excluded():
    """Verify marquee retained players across franchises are strictly ineligible for auction."""
    retained_checks = [
        (4708, "Rinku Singh", STATUS_RETAINED, "Kolkata Knight Riders (KKR)"),
        (781, "Sunil Narine", STATUS_RETAINED, "Kolkata Knight Riders (KKR)"),
        (4986, "Rovman Powell", STATUS_RETAINED, "Kolkata Knight Riders (KKR)"),
        (2633, "Jason Holder", STATUS_RETAINED, "Gujarat Titans (GT)"),
        (2258, "Sanju Samson", STATUS_RETAINED, "Chennai Super Kings (CSK)"),
        (4722, "Rashid Khan", STATUS_RETAINED, "Gujarat Titans (GT)"),
        (2933, "Jasprit Bumrah", STATUS_RETAINED, "Mumbai Indians (MI)"),
        (4721, "Heinrich Klaasen", STATUS_RETAINED, "Sunrisers Hyderabad (SRH)"),
        (25, "Virat Kohli", STATUS_RETAINED, "Royal Challengers Bengaluru (RCB)"),
    ]

    for pid, name, expected_status, franchise in retained_checks:
        info = get_player_availability(pid)
        assert info["status"] == expected_status, f"{name} should be {expected_status}, got {info['status']}"
        assert info["franchise"] == franchise, f"{name} franchise mismatch: expected {franchise}, got {info['franchise']}"
        assert is_player_auction_eligible(pid) is False, f"Retained player {name} must NOT be auction-eligible"


def test_contracted_and_traded_players_excluded():
    """Verify players signed on contracts or traded are marked CONTRACTED and ineligible."""
    contracted_checks = [
        (3296, "Hardik Pandya", STATUS_CONTRACTED, "Punjab Kings (PBKS)"),
        (6464, "Arshdeep Singh", STATUS_CONTRACTED, "Mumbai Indians (MI)"),
        (4276, "Rishabh Pant", STATUS_CONTRACTED, "Delhi Capitals (DC)"),
        (2934, "Kuldeep Yadav", STATUS_CONTRACTED, "Lucknow Super Giants (LSG)"),
        (6424, "Sam Curran", STATUS_CONTRACTED, "Lucknow Super Giants (LSG)"),
        (1077, "David Miller", STATUS_CONTRACTED, "Lucknow Super Giants (LSG)"),
        (6396, "Tim David", STATUS_CONTRACTED, "Royal Challengers Bengaluru (RCB)"),
        (1612, "Yuzvendra Chahal", STATUS_CONTRACTED, "Punjab Kings (PBKS)"),
    ]

    for pid, name, expected_status, franchise in contracted_checks:
        info = get_player_availability(pid)
        assert info["status"] == expected_status, f"{name} should be {expected_status}, got {info['status']}"
        assert info["franchise"] == franchise, f"{name} franchise mismatch"
        assert is_player_auction_eligible(pid) is False, f"Contracted player {name} must NOT be auction-eligible"


def test_ineligible_and_withdrawn_excluded():
    """Verify Pakistani players, opted-out stars, and retired veterans are strictly ineligible."""
    special_cases = [
        (3918, "Travis Head", STATUS_WITHDRAWN_RETIRED),
        (1, "MS Dhoni", STATUS_WITHDRAWN_RETIRED),
        (6355, "Shaheen Shah Afridi", STATUS_INELIGIBLE),
        (7364, "Haris Rauf", STATUS_INELIGIBLE),
        (143, "Dinesh Karthik", STATUS_WITHDRAWN_RETIRED),
        (796, "Matthew Wade", STATUS_WITHDRAWN_RETIRED),
    ]

    for pid, name, expected_status in special_cases:
        info = get_player_availability(pid)
        assert info["status"] == expected_status, f"{name} should be {expected_status}, got {info['status']}"
        assert is_player_auction_eligible(pid) is False, f"{name} must NOT be auction-eligible"


def test_released_unverified_players_excluded():
    """Verify released players whose 2027 auction registration is unverified are marked UNVERIFIED and ineligible."""
    released_unverified = [
        (3297, "Shimron Hetmyer"),
        (6806, "Tushar Deshpande"),
        (1324, "Trent Boult"),
        (1989, "Mitchell Starc"),
        (7509, "Matheesha Pathirana"),
        (2984, "Sikandar Raza"),
        (6450, "Mujeeb Ur Rahman"),
        (39657, "Eshan Malinga"),
    ]

    for pid, name in released_unverified:
        info = get_player_availability(pid)
        assert info["status"] == STATUS_UNVERIFIED, f"{name} should be UNVERIFIED, got {info['status']}"
        assert is_player_auction_eligible(pid) is False, f"Unverified player {name} must NOT be auction-eligible"


def test_auction_eligible_included():
    """Verify players with authoritative board confirmation of 2027 registration are auction-eligible."""
    eligible_checks = [
        (6651, "Towhid Hridoy"),
        (2681, "Taskin Ahmed"),
        (4373, "Mustafizur Rahman"),
        (37939, "Nahid Rana"),
        (7344, "Shoriful Islam"),
        (8380, "Mohammad Rishad Hossain"),
        (6643, "Hasan Mahmud"),
    ]

    for pid, name in eligible_checks:
        info = get_player_availability(pid)
        assert info["status"] == STATUS_AUCTION_ELIGIBLE, f"{name} should be AUCTION_ELIGIBLE, got {info['status']}"
        assert is_player_auction_eligible(pid) is True, f"{name} must be auction-eligible"
        assert "base_price_inr_cr" in info
        assert "est_bid_range_inr_cr" in info


def test_unverified_player_default():
    """Verify unlisted players default to UNVERIFIED and are not eligible for auction."""
    unknown_pid = 99999999
    info = get_player_availability(unknown_pid)
    assert info["status"] == STATUS_UNVERIFIED
    assert is_player_auction_eligible(unknown_pid) is False


def test_filter_available_rankings():
    """Verify filter_available_rankings completely strips out unavailable and unverified players."""
    sample_df = pd.DataFrame([
        {"player_id": 4708, "player_name": "Rinku Singh", "reliability_score": 92.5},     # Retained KKR
        {"player_id": 6651, "player_name": "Towhid Hridoy", "reliability_score": 85.0},   # Eligible
        {"player_id": 4986, "player_name": "Rovman Powell", "reliability_score": 84.0},   # Retained KKR
        {"player_id": 2681, "player_name": "Taskin Ahmed", "reliability_score": 81.2},    # Eligible
        {"player_id": 3297, "player_name": "Shimron Hetmyer", "reliability_score": 82.0}, # Unverified Released
        {"player_id": 6355, "player_name": "Shaheen Afridi", "reliability_score": 89.0},  # Ineligible
        {"player_id": 99999, "player_name": "Unknown Person", "reliability_score": 75.0}, # Unverified
    ])

    filtered = filter_available_rankings(sample_df)

    # Must contain only eligible players
    assert len(filtered) == 2, f"Expected exactly 2 eligible players, got {len(filtered)}"
    assert set(filtered["player_id"].tolist()) == {6651, 2681}
    assert all(filtered["is_available"] == True)
    assert all(filtered["auction_status"] == STATUS_AUCTION_ELIGIBLE)

    # Verify descending sort order on reliability_score
    assert filtered.iloc[0]["player_name"] == "Towhid Hridoy"
    assert filtered.iloc[1]["player_name"] == "Taskin Ahmed"
    assert filtered.iloc[0]["available_rank"] == 1
    assert filtered.iloc[1]["available_rank"] == 2


def test_rr_squad_state_and_limits():
    """Verify RR squad roster count (19), available slots (6), overseas slots (3), and purse (₹27.05 Cr)."""
    squad_state = get_rr_squad_state()

    assert squad_state["total_players"] == 19
    assert squad_state["squad_size"] == 19
    assert squad_state["open_slots"] == 6              # 25 - 19
    assert squad_state["remaining_squad_capacity"] == 6
    assert squad_state["overseas_count"] == 5
    assert squad_state["open_overseas_slots"] == 3     # 8 - 5
    assert squad_state["remaining_overseas_capacity"] == 3
    assert squad_state["domestic_count"] == 14
    assert squad_state["total_spent_cr"] == 92.95
    assert squad_state["spent_purse_cr"] == 92.95
    assert squad_state["remaining_purse_cr"] == 27.05
    assert len(squad_state["roster"]) == 19

    # Ensure key RR confirmed pillars are present
    roster_names = [p["name"] for p in squad_state["roster"]]
    assert "Riyan Parag" in roster_names
    assert "Yashasvi Jaiswal" in roster_names
    assert "Ravindra Jadeja" in roster_names
    assert "Dhruv Jurel" in roster_names
    assert "Jofra Archer" in roster_names
    assert "Sandeep Sharma" in roster_names
    assert "Mohammed Shami" in roster_names
    assert "Ravi Bishnoi" in roster_names
    assert "Manimaran Siddharth" in roster_names

    # Ensure released players are NOT in current squad
    assert "Sanju Samson" not in roster_names          # Traded to CSK
    assert "Shimron Hetmyer" not in roster_names        # Released
    assert "Tushar Deshpande" not in roster_names       # Released
    assert "Kwena Maphaka" not in roster_names          # Released


def test_rr_priority_shortlist_validity():
    """Verify all RR priority shortlist candidates are 100% verified auction-eligible."""
    shortlist = get_rr_priority_shortlist()
    assert len(shortlist) >= 5, f"Expected at least 5 shortlisted players, got {len(shortlist)}"

    for target in shortlist:
        pid = target["player_id"]
        assert is_player_auction_eligible(pid) is True, (
            f"Target {target['name']} ({pid}) is not auction eligible!"
        )
        assert target["target_role"] != ""
        assert target["tactical_fit"] != ""
        assert target["jaipur_sms_fit"] != ""
        assert target["est_bid_range"] != ""


def test_unverified_shortlist_targets():
    """Verify excluded/unverified audit registry correctly documents why non-eligible stars are barred."""
    unverified = get_unverified_shortlist_targets()
    assert len(unverified) >= 10

    unv_names = [u["name"] for u in unverified]
    assert "Rovman Powell" in unv_names       # Retained by KKR
    assert "Jason Holder" in unv_names        # Retained by GT
    assert "Travis Head" in unv_names         # Opted out
    assert "MS Dhoni" in unv_names            # Retired
    assert "Shimron Hetmyer" in unv_names     # Released by RR, registration unverified
    assert "Tushar Deshpande" in unv_names    # Released by RR, registration unverified


def test_franchise_availability_summary():
    """Verify franchise retention and contract summary covers all 10 teams with official 17-Nov-2026 data."""
    franchises = get_franchise_availability_summary()
    assert isinstance(franchises, pd.DataFrame)
    assert len(franchises) == 10

    assert "Franchise" in franchises.columns
    assert "Remaining Purse (Cr)" in franchises.columns
    assert "Remaining Slots" in franchises.columns

    team_names = franchises["Franchise"].tolist()
    expected_codes = ["RR", "KKR", "CSK", "MI", "DC", "GT", "LSG", "SRH", "RCB", "PBKS"]
    for code in expected_codes:
        assert any(code in t for t in team_names), f"Missing franchise {code} in summary"

    # Check RR row specifically
    rr_row = franchises[franchises["Franchise"].str.contains("RR|Rajasthan Royals", case=False)]
    assert not rr_row.empty
    assert rr_row.iloc[0]["Remaining Purse (Cr)"] == "₹27.05"
    assert rr_row.iloc[0]["Remaining Slots"] == 6
    assert rr_row.iloc[0]["Overseas Open"] == 3
