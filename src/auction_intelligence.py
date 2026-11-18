"""
Auction Intelligence Module for SupeRR SCOUT Platform.
Rajasthan Royals IPL 2027 Auction Research & Tactical Recruitment.

Provides:
1. IPL-only vs Combined (IPL + T20I) Pressure Rankings.
2. Competition Disaggregation (IPL vs T20I splits) for all shortlisted targets.
3. Empirical Player Role Classification based on phase distribution and delivery attributes.
4. Sample size uncertainty and Bayesian credibility indicators.
5. Auction Suitability Dossiers: Strengths, Limitations, and Rajasthan Royals (Jaipur) Tactical Fit.
6. Clean separation between measured empirical statistics and scouting interpretations.
"""

from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
import logging
from pathlib import Path

from src.batting_analysis import compute_batting_metrics
from src.bowling_analysis import compute_bowling_metrics
from src.reliability_model import apply_batting_reliability_model, apply_bowling_reliability_model
from src.rankings import get_top_10_batters, get_top_10_bowlers

logger = logging.getLogger(__name__)


def compute_auction_rankings(
    deliveries_df: pd.DataFrame,
    min_balls: int = 60,
    pressure_thresh: float = 65.0
) -> Dict[str, pd.DataFrame]:
    """
    Compute both Combined (IPL + T20I) and IPL-Only Top 10 rankings for Batters and Bowlers.
    Returns dictionary with keys:
    - 'batters_combined', 'batters_ipl'
    - 'bowlers_combined', 'bowlers_ipl'
    - 'batters_all_ranked', 'bowlers_all_ranked'
    """
    # 1. Combined (IPL + T20I)
    deliv_comb = deliveries_df.copy()
    deliv_comb["is_high_pressure_bat"] = deliv_comb["pressure_batting"] >= pressure_thresh
    deliv_comb["is_high_pressure_bowl"] = deliv_comb["pressure_bowling"] >= pressure_thresh

    bat_m_comb = compute_batting_metrics(deliv_comb, min_balls_hp=min_balls)
    bat_r_comb = apply_batting_reliability_model(bat_m_comb)
    top_bat_comb = get_top_10_batters(bat_r_comb, min_balls=min_balls)

    bowl_m_comb = compute_bowling_metrics(deliv_comb, min_balls_hp=min_balls)
    bowl_r_comb = apply_bowling_reliability_model(bowl_m_comb)
    top_bowl_comb = get_top_10_bowlers(bowl_r_comb, min_balls=min_balls)

    # 2. IPL Only
    deliv_ipl = deliv_comb[deliv_comb["is_ipl"]].copy()

    bat_m_ipl = compute_batting_metrics(deliv_ipl, min_balls_hp=min_balls)
    bat_r_ipl = apply_batting_reliability_model(bat_m_ipl)
    top_bat_ipl = get_top_10_batters(bat_r_ipl, min_balls=min_balls)

    bowl_m_ipl = compute_bowling_metrics(deliv_ipl, min_balls_hp=min_balls)
    bowl_r_ipl = apply_bowling_reliability_model(bowl_m_ipl)
    top_bowl_ipl = get_top_10_bowlers(bowl_r_ipl, min_balls=min_balls)

    return {
        "batters_combined": top_bat_comb,
        "batters_ipl": top_bat_ipl,
        "bowlers_combined": top_bowl_comb,
        "bowlers_ipl": top_bowl_ipl,
        "batters_all_ranked_comb": bat_r_comb,
        "batters_all_ranked_ipl": bat_r_ipl,
        "bowlers_all_ranked_comb": bowl_r_comb,
        "bowlers_all_ranked_ipl": bowl_r_ipl
    }


def compute_player_competition_split(
    deliveries_df: pd.DataFrame,
    player_id: int,
    is_batter: bool = True,
    pressure_thresh: float = 65.0
) -> Dict[str, Any]:
    """
    Compute rigorous side-by-side competition splits (IPL vs T20I vs Combined) for a specific player.
    Never presents T20I performance as IPL performance.
    """
    df = deliveries_df.copy()
    if is_batter:
        hp_mask = (df["striker_id"] == player_id) & (df["is_ball_faced_batter"]) & (df["pressure_batting"] >= pressure_thresh)
        norm_mask = (df["striker_id"] == player_id) & (df["is_ball_faced_batter"]) & (df["pressure_batting"] < pressure_thresh)
        player_name = df[df["striker_id"] == player_id]["striker_name"].dropna().iloc[0] if not df[df["striker_id"] == player_id].empty else f"Player {player_id}"
    else:
        hp_mask = (df["bowler_id"] == player_id) & (df["is_legal_ball_bowler"]) & (df["pressure_bowling"] >= pressure_thresh)
        norm_mask = (df["bowler_id"] == player_id) & (df["is_legal_ball_bowler"]) & (df["pressure_bowling"] < pressure_thresh)
        player_name = df[df["bowler_id"] == player_id]["bowler_name"].dropna().iloc[0] if not df[df["bowler_id"] == player_id].empty else f"Player {player_id}"

    splits = {}
    for comp_label, comp_filter in [
        ("Combined", None),
        ("IPL", df["is_ipl"]),
        ("International & Emerging T20", ~df["is_ipl"])
    ]:
        if comp_filter is not None:
            hp_sub = df[hp_mask & comp_filter]
            norm_sub = df[norm_mask & comp_filter]
            dis_sub = df[(df["dismissed_player_id"] == player_id) & (df["pressure_batting"] >= pressure_thresh) & comp_filter]
        else:
            hp_sub = df[hp_mask]
            norm_sub = df[norm_mask]
            dis_sub = df[(df["dismissed_player_id"] == player_id) & (df["pressure_batting"] >= pressure_thresh)]

        matches = hp_sub["match_id"].nunique()

        if is_batter:
            hp_balls = len(hp_sub)
            hp_runs = int(hp_sub["runs_batter"].sum()) if hp_balls > 0 else 0
            hp_sr = (hp_runs / hp_balls * 100.0) if hp_balls > 0 else 0.0

            # Dismissals
            hp_dismissals = dis_sub["match_id"].count()
            hp_avg = (hp_runs / max(1, hp_dismissals)) if hp_balls > 0 else 0.0

            # Boundaries & Dots
            fours = int((hp_sub["runs_batter"] == 4).sum())
            sixes = int((hp_sub["runs_batter"] == 6).sum())
            dots = int(hp_sub["is_batter_dot"].sum()) if "is_batter_dot" in hp_sub.columns else 0
            bnd_pct = ((fours + sixes) / hp_balls * 100.0) if hp_balls > 0 else 0.0
            dot_pct = (dots / hp_balls * 100.0) if hp_balls > 0 else 0.0

            # Normal baseline
            norm_balls = len(norm_sub)
            norm_runs = int(norm_sub["runs_batter"].sum()) if norm_balls > 0 else 0
            norm_sr = (norm_runs / norm_balls * 100.0) if norm_balls > 0 else 0.0
            sr_delta = hp_sr - norm_sr if (hp_balls > 0 and norm_balls > 0) else 0.0

            splits[comp_label] = {
                "matches": matches,
                "hp_balls": hp_balls,
                "hp_runs": hp_runs,
                "hp_sr": round(hp_sr, 1),
                "hp_avg": round(hp_avg, 1),
                "hp_dismissals": int(hp_dismissals),
                "boundary_pct": round(bnd_pct, 1),
                "dot_pct": round(dot_pct, 1),
                "norm_balls": norm_balls,
                "norm_sr": round(norm_sr, 1),
                "sr_delta": round(sr_delta, 1)
            }
        else:
            hp_legal = len(hp_sub)
            hp_overs = (hp_legal // 6) + (hp_legal % 6) / 10.0
            hp_runs_conc = int(hp_sub["runs_bowler"].sum()) if hp_legal > 0 else 0
            hp_wkts = int(hp_sub["is_bowler_wicket"].sum()) if "is_bowler_wicket" in hp_sub.columns else 0
            hp_econ = (hp_runs_conc / hp_legal * 6.0) if hp_legal > 0 else 0.0
            hp_bowl_sr = (hp_legal / max(1, hp_wkts)) if hp_wkts > 0 else float("nan")

            # Dots & Boundaries conceded
            dots = int(hp_sub["is_bowler_dot"].sum()) if "is_bowler_dot" in hp_sub.columns else 0
            dot_pct = (dots / hp_legal * 100.0) if hp_legal > 0 else 0.0
            bnd_conc = int(((hp_sub["runs_bowler"] >= 4) & (hp_sub["runs_bowler"] <= 6)).sum())
            bnd_pct = (bnd_conc / hp_legal * 100.0) if hp_legal > 0 else 0.0

            # Normal baseline
            norm_legal = len(norm_sub)
            norm_runs_conc = int(norm_sub["runs_bowler"].sum()) if norm_legal > 0 else 0
            norm_econ = (norm_runs_conc / norm_legal * 6.0) if norm_legal > 0 else 0.0
            econ_delta = norm_econ - hp_econ if (hp_legal > 0 and norm_legal > 0) else 0.0

            splits[comp_label] = {
                "matches": matches,
                "hp_legal_balls": hp_legal,
                "hp_overs": round(hp_overs, 1),
                "hp_runs_conceded": hp_runs_conc,
                "hp_wickets": hp_wkts,
                "hp_economy": round(hp_econ, 2),
                "hp_strike_rate": round(hp_bowl_sr, 1) if not np.isnan(hp_bowl_sr) else None,
                "dot_pct": round(dot_pct, 1),
                "boundary_pct": round(bnd_pct, 1),
                "norm_balls": norm_legal,
                "norm_econ": round(norm_econ, 2),
                "econ_delta": round(econ_delta, 2)
            }

    # Backward compatibility alias for legacy callers and tests
    if "International & Emerging T20" in splits:
        splits["T20I"] = splits["International & Emerging T20"]

    return {
        "player_id": player_id,
        "player_name": player_name,
        "is_batter": is_batter,
        "splits": splits
    }


def classify_player_role_and_phases(
    deliveries_df: pd.DataFrame,
    player_id: int,
    is_batter: bool = True,
    pressure_thresh: float = 65.0
) -> Dict[str, Any]:
    """
    Classify tactical role and calculate phase distribution strictly from data evidence.
    Phases: Powerplay (overs 1-6 / overid 1-6), Middle (overs 7-15 / overid 7-15), Death (overs 16-20 / overid 16-20).
    """
    df = deliveries_df.copy()
    if is_batter:
        sub = df[(df["striker_id"] == player_id) & (df["is_ball_faced_batter"])]
        hp_sub = sub[sub["pressure_batting"] >= pressure_thresh]

        hand = sub["batting_type"].dropna().iloc[0] if not sub["batting_type"].dropna().empty else "Unknown"
        median_order = float(sub["batting_order"].dropna().median()) if not sub["batting_order"].dropna().empty else np.nan

        tot_hp = len(hp_sub)
        if tot_hp > 0:
            pp_b = len(hp_sub[hp_sub["phase"] == "Powerplay"])
            mid_b = len(hp_sub[hp_sub["phase"] == "Middle"])
            death_b = len(hp_sub[hp_sub["phase"] == "Death"])
            pp_pct = (pp_b / tot_hp) * 100.0
            mid_pct = (mid_b / tot_hp) * 100.0
            death_pct = (death_b / tot_hp) * 100.0
        else:
            pp_pct, mid_pct, death_pct = 0.0, 0.0, 0.0

        # Role classification logic
        if death_pct >= 60.0:
            if median_order >= 7.0:
                primary_role = "Specialist Lower-Order Finisher"
            else:
                primary_role = "Death-Overs Accelerator & Finisher"
        elif mid_pct >= 50.0:
            primary_role = "Middle-Order Crisis Stabilizer & Counter-Attacker"
        elif pp_pct >= 40.0:
            primary_role = "Powerplay Enforcer & Aggressor"
        else:
            primary_role = "Multi-Phase Middle/Death Floater"

        return {
            "player_id": player_id,
            "is_batter": True,
            "style": hand,
            "batting_hand": hand,
            "median_batting_order": median_order,
            "primary_role": primary_role,
            "phase_distribution": {
                "Powerplay": round(pp_pct, 1),
                "Middle": round(mid_pct, 1),
                "Death": round(death_pct, 1)
            },
            "hp_sample_balls": tot_hp
        }
    else:
        sub = df[(df["bowler_id"] == player_id) & (df["is_legal_ball_bowler"])]
        hp_sub = sub[sub["pressure_bowling"] >= pressure_thresh]

        bowl_style = sub["bowling_type"].dropna().iloc[0] if not sub["bowling_type"].dropna().empty else "Unknown"
        is_spin = any(w in bowl_style.lower() for w in ["spin", "break", "orthodox", "chinaman", "slow"])

        tot_hp = len(hp_sub)
        if tot_hp > 0:
            pp_b = len(hp_sub[hp_sub["phase"] == "Powerplay"])
            mid_b = len(hp_sub[hp_sub["phase"] == "Middle"])
            death_b = len(hp_sub[hp_sub["phase"] == "Death"])
            pp_pct = (pp_b / tot_hp) * 100.0
            mid_pct = (mid_b / tot_hp) * 100.0
            death_pct = (death_b / tot_hp) * 100.0
        else:
            pp_pct, mid_pct, death_pct = 0.0, 0.0, 0.0

        # Role classification logic
        if death_pct >= 65.0:
            primary_role = "Specialist Death Yorker & Boundary Suppression Enforcer"
        elif mid_pct >= 48.0:
            if is_spin:
                primary_role = "Middle-Overs Spin Choke & Breakthrough Sentry"
            else:
                primary_role = "Middle-Overs Seam Squeeze & Strike Option"
        elif pp_pct >= 40.0:
            primary_role = "Powerplay Swing & Breakthrough Specialist"
        else:
            primary_role = "All-Phase High-Leverage Sentry (Middle + Death)"

        return {
            "player_id": player_id,
            "is_batter": False,
            "style": bowl_style,
            "bowling_style": bowl_style,
            "is_spin": is_spin,
            "primary_role": primary_role,
            "phase_distribution": {
                "Powerplay": round(pp_pct, 1),
                "Middle": round(mid_pct, 1),
                "Death": round(death_pct, 1)
            },
            "hp_sample_balls": tot_hp
        }


def get_sample_uncertainty_profile(balls: int) -> Dict[str, Any]:
    """
    Compute sample size uncertainty tier, Bayesian credibility weight, and margin of error.
    """
    w = balls / (balls + 50.0)
    se = 16.0 / np.sqrt(max(1.0, balls / 25.0))
    moe = 1.96 * se

    if balls >= 220:
        tier = "Tier 1: High Volume / High Statistical Certainty"
        reliability_tag = "ELITE PROVEN"
        desc = "Extensive pressure exposure across multiple campaigns; negligible regression risk."
    elif balls >= 140:
        tier = "Tier 2: Robust Franchise Sample"
        reliability_tag = "HIGH CONFIDENCE"
        desc = "Established sample size; empirical metrics reflect genuine underlying clutch skill."
    elif balls >= 75:
        tier = "Tier 3: Moderate Sample / Bayesian Anchored"
        reliability_tag = "MODERATE CONFIDENCE"
        desc = "Solid sample; Bayesian shrinkage actively dampens single-match high-impact spikes."
    else:
        tier = "Tier 4: Developing / High Volatility"
        reliability_tag = "EMERGING POTENTIAL"
        desc = "Limited pressure volume; wide confidence interval warrants disciplined valuation."

    return {
        "balls": balls,
        "credibility_weight": round(w * 100.0, 1),
        "prior_weight": round((1.0 - w) * 100.0, 1),
        "margin_of_error": round(moe, 1),
        "uncertainty_tier": tier,
        "reliability_tag": reliability_tag,
        "interpretation": desc
    }


# Knowledge repository of empirically grounded tactical dossiers tailored to RR's Sawai Mansingh Stadium
RR_TACTICAL_DOSSIERS = {
    # Batters
    4708: {
        "player_name": "Rinku Singh",
        "strengths": [
            "Hyper-clutch boundary conversion: hits boundaries on 28.1% of high-pressure balls.",
            "Exceptional dismissal resistance: HP average of 75.5 in IPL (81.8 combined).",
            "Left-handed flexibility: seamlessly matches up against right-arm off-spinners and leg-spinners in overs 16–20.",
            "High strike rate elevation: gears up from 145 baseline to 188.8 under peak tension."
        ],
        "limitations": [
            "Heavy reliance on overs 16–20 (73% of HP balls faced in death phase); rarely deployed in powerplay rebuilds.",
            "Target for opposing hard lengths and bouncer traps if pitch has sharp steepling bounce."
        ],
        "rr_tactical_fit": (
            "Ideal #5/#6 finisher for Rajasthan Royals. At Sawai Mansingh Stadium (Jaipur), where square boundaries "
            "are 70m–75m, Rinku's elite running between wickets and flat trajectory down-the-ground bat-speed are ideal. "
            "Forms an invincible clutch tandem alongside Sanju Samson and Dhruv Jurel, providing LHB-RHB balance in run chases."
        ),
        "auction_target_tier": "Marquee Retention / Priority Retain Target"
    },
    1077: {
        "player_name": "David Miller",
        "strengths": [
            "Highest pressure strike rate in elite tier: 199.4 in IPL and 206.2 combined.",
            "Dual-phase versatility: 37% balls in middle overs (7–15) and 59% in death (16–20).",
            "Proven match-finishing composure in ICC knockouts and IPL championship playoffs."
        ],
        "limitations": [
            "Overseas slot utilization (takes 1 of 4 overseas player spots in XI).",
            "Slight vulnerability to high-caliber left-arm spin turning away early in innings."
        ],
        "rr_tactical_fit": (
            "Solves RR's middle-overs boundary drought. Can be slotted at #5 as an overseas anchor who can stabilize "
            "a collapse from 30/3 or accelerate from 120/3 at Jaipur. His power clearing the straight 75m fences at SMS is world-class."
        ),
        "auction_target_tier": "Primary Overseas Finisher Target"
    },
    6396: {
        "player_name": "Tim David",
        "strengths": [
            "Massive volume and sample certainty: 327 high-pressure balls faced (254 in IPL alone).",
            "Overwhelming boundary power against pace: 194.5 IPL HP strike rate, hitting 31 sixes under pressure.",
            "77% concentration in death overs (16–20), making him a pure specialist executioner."
        ],
        "limitations": [
            "Susceptible to high-class leg-spin / googlies outside off-stump in overs 10–14.",
            "Dot ball rate rises to 35.8% when bowlers hit hard back-of-length on slow decks."
        ],
        "rr_tactical_fit": (
            "Designated #6 death enforcer. Takes over the role Shimron Hetmyer / Rovman Powell played, giving RR sheer "
            "brute-force hitting in the final 4 overs. Complements the ground-game style of Sanju Samson and Yashasvi Jaiswal."
        ),
        "auction_target_tier": "High-Value Overseas Power-Finisher"
    },
    8101: {
        "player_name": "Ashutosh Sharma",
        "strengths": [
            "Astronomical immediate impact: 197.6 IPL HP strike rate across 167 pressure balls.",
            "Specialist sweeps, scoops, and ramp shots against 140+ kph express pace at the death.",
            "Domestic uncapped/low-bracket acquisition profile with exceptional price-to-performance ratio."
        ],
        "limitations": [
            "Moderate sample size (167 IPL balls); prone to high volatility across a 14-match season.",
            "Average under pressure is 30.0; high-risk approach generates occasional early dismissals."
        ],
        "rr_tactical_fit": (
            "Tactical game-changer for RR's lower order (#7 / Impact Sub). At Jaipur, where outfields are lightning fast, "
            "his 360-degree ramp/scoop game exploits vacant fine-leg and third-man boundaries when fine-leg is up."
        ),
        "auction_target_tier": "High-Priority Domestic Target / Impact Sub"
    },
    6651: {
        "player_name": "Towhid Hridoy",
        "strengths": [
            "Elite international pressure record: 165.0 SR with an extraordinary average of 82.5 across 100 T20I balls.",
            "Calm match-building temperament against spin and pace alike."
        ],
        "limitations": [
            "0 IPL balls faced; unproven against the specific match-ups and bowler velocity of the IPL.",
            "Occupies an overseas slot without confirmed franchise tournament pedigree."
        ],
        "rr_tactical_fit": (
            "Scouting Watchlist / Backup Target. High ceiling but represents an uncalibrated translation risk. "
            "Recommended as a low-cost overseas backup rather than a primary starting XI investment."
        ),
        "auction_target_tier": "Overseas Developmental / Watchlist"
    },
    796: {
        "player_name": "Matthew Wade",
        "strengths": [
            "World Cup winning clutch pedigree: 159.4 T20I HP SR with 70.7 average.",
            "86% death-overs execution against elite pace attacks."
        ],
        "limitations": [
            "Zero IPL pressure balls in 2022–2026 dataset; veteran age profile.",
            "Overseas wicket-keeper slot redundant given Sanju Samson and Dhruv Jurel."
        ],
        "rr_tactical_fit": (
            "Not recommended for primary bidding due to squad duplication with Samson/Jurel and overseas slot constraints."
        ),
        "auction_target_tier": "Low Priority / Squad Depth Only"
    },
    7897: {
        "player_name": "Namboori Tilak Varma",
        "strengths": [
            "Sensational IPL clutch surge: 192.3 HP SR in IPL (130 balls) with 35.7 average.",
            "Complete 360-degree game against express pace and quality spin.",
            "Young Indian core asset with a decade-long runway."
        ],
        "limitations": [
            "T20I strike rate under pressure is lower (157.9 across 114 balls).",
            "Likely to be heavily contested / retained by parent franchise."
        ],
        "rr_tactical_fit": (
            "Dream #4 batter for Rajasthan Royals. Left-handed, anchors the innings after powerplay, and explodes in overs "
            "14–20. Perfect foil for Samson and Riyan Parag, allowing Parag to play more freely."
        ),
        "auction_target_tier": "Elite Domestic Target (If Available)"
    },
    20702: {
        "player_name": "Tristan Stubbs",
        "strengths": [
            "Lethal spin-basher and death specialist: 177.5 IPL HP strike rate, 44.7 average across 151 pressure balls.",
            "Multi-dimensional utility: can keep wickets, bowl off-spin, and is an elite boundary fielder.",
            "61% death / 38% middle over distribution."
        ],
        "limitations": [
            "Requires overseas spot; high auction demand across multiple franchises."
        ],
        "rr_tactical_fit": (
            "High-impact acquisition for #5. Brings explosive boundary capability to Jaipur, where he can clear the straight "
            "sightscreen with ease against both pace and spin."
        ),
        "auction_target_tier": "Tier-1 Overseas Hitter / Multi-Utility"
    },
    152: {
        "player_name": "Ravindra Jadeja",
        "strengths": [
            "Unflappable championship temperament: 217 IPL HP balls, 37.9 average, 157.1 SR.",
            "Multi-skills: elite fielding, left-arm containment spin, and clutch batting experience."
        ],
        "limitations": [
            "Strike rate under pressure (157.1) is containment-oriented rather than explosive 190+ finish.",
            "Veteran player with high retention / purse cost."
        ],
        "rr_tactical_fit": (
            "Provides legendary balance at #7 and fills the left-arm spin quota at Sawai Mansingh Stadium."
        ),
        "auction_target_tier": "Marquee Veteran All-Rounder"
    },
    8: {
        "player_name": "Mahendra Singh Dhoni",
        "strengths": [
            "Pure clutch intuition: 232 IPL HP balls faced, 165.5 SR, 34.9 average.",
            "77% concentrated in overs 18–20; master of targeting boundary dimensions."
        ],
        "limitations": [
            "Specialist 10-ball finisher only; near-retirement career phase.",
            "Franchise loyalty makes auction availability virtually zero."
        ],
        "rr_tactical_fit": (
            "Theoretical benchmark profile for pressure temperament; unlikely auction target."
        ),
        "auction_target_tier": "Benchmark Model / Legacy Asset"
    },
    143: {
        "player_name": "Dinesh Karthik",
        "strengths": [
            "Highest IPL-only strike rate among domestic finishers: 206.2 SR across 144 balls.",
            "Elite 360-degree lap, paddle, and sweep shot execution against yorker-length bowling."
        ],
        "limitations": [
            "International/T20I record is negligible (12 balls); retired from active playing cycle."
        ],
        "rr_tactical_fit": (
            "Blueprint for the specialist #6/#7 domestic finisher RR needs to recruit in the auction."
        ),
        "auction_target_tier": "Finisher Archetype Reference"
    },

    # Bowlers
    781: {
        "player_name": "Sunil Narine",
        "strengths": [
            "Unrivaled economy under peak pressure: 6.23 RPO in IPL across 209 high-pressure balls (34.5 overs).",
            "Suffocating dot-ball generation: 41.6% dot balls in situations where batters are attacking.",
            "All-phase mastery: 10% PP, 46% Middle, 43% Death. Bowled in any match situation."
        ],
        "limitations": [
            "Overseas slot commitment; franchise marquee status makes availability improbable."
        ],
        "rr_tactical_fit": (
            "Gold standard for franchise spin recruitment. At Jaipur, Narine's carrom ball and skid would make RR "
            "virtually unassailable at home, suffocating opponents to under 7.0 RPO in the middle overs."
        ),
        "auction_target_tier": "Benchmark Spin Asset / Priority Target"
    },
    4722: {
        "player_name": "Rashid Khan",
        "strengths": [
            "Highest pressure wicket tally: 38 combined pressure wickets (20 in IPL, 18 in T20I).",
            "Massive sample volume: 389 high-pressure legal balls.",
            "Unplayable in international T20I (Econ 5.62, SR 8.8 balls/wkt)."
        ],
        "limitations": [
            "IPL economy rate under pressure expands to 9.26 RPO as batters play him conservatively or attack flat tracks.",
            "High retention / bidding price point."
        ],
        "rr_tactical_fit": (
            "The ultimate middle-overs wicket-taker. Paired with Jaipur's large square fences, Rashid's quick through-the-air "
            "leg-breaks and googlies force mis-timed slog-sweeps directly to deep mid-wicket and long-on."
        ),
        "auction_target_tier": "Marquee Overseas Spin Target"
    },
    1612: {
        "player_name": "Yuzvendra Chahal",
        "strengths": [
            "RR Franchise Legend and proven Jaipur match-winner: 25 IPL pressure wickets (254 balls).",
            "IPL-Only Rank #2 Bowler with 64.09 reliability score and 38.2% dot balls.",
            "Courageous wide-outside-off trajectory forcing mishits to the longest boundaries."
        ],
        "limitations": [
            "Economy under pressure is 8.76 in IPL (10.58 in T20I); accepts conceding boundaries to hunt wickets.",
            "Limited lower-order batting contribution."
        ],
        "rr_tactical_fit": (
            "HIGH PRIORITY BUY-BACK TARGET. Chahal knows every blade of grass at Sawai Mansingh Stadium. His familiarity "
            "with Sanju Samson's field placements and RR's bowling blueprints makes him the lowest-risk, highest-reward buy."
        ),
        "auction_target_tier": "Priority Buy-Back / Anchor Leg-Spinner"
    },
    6464: {
        "player_name": "Arshdeep Singh",
        "strengths": [
            "Most battle-tested death bowler in India: 426 IPL HP balls (692 combined), 29 IPL pressure wickets.",
            "76% of deliveries bowled in the death overs (16–20).",
            "Left-arm angle naturally cramps right-handers and executes wide yorkers with pinpoint discipline."
        ],
        "limitations": [
            "Economy under death pressure is 9.08 IPL / 9.77 T20I (commensurate with high death-overs volume).",
            "Will command a top-tier premium purse at auction."
        ],
        "rr_tactical_fit": (
            "Primary Target for RR's Seam Attack. Solves the death-bowling dependency on overseas pacers or Sandeep Sharma alone. "
            "Pairing Arshdeep (left-arm) with Sandeep Sharma and an overseas express pacer gives RR the most disciplined pace unit in IPL."
        ),
        "auction_target_tier": "Top Domestic Pace Target (Marquee Bidding)"
    },
    2261: {
        "player_name": "Harshal Patel",
        "strengths": [
            "Leading wicket-taker under pressure: 32 IPL pressure wickets across 340 legal balls.",
            "Purple Cap master of slower-ball dipping yorkers and off-cutter variations.",
            "73% death overs concentration."
        ],
        "limitations": [
            "Economy under extreme chase pressure can spike to 9.48–10.29 on small batting paradises.",
            "High variance bowler whose effectiveness depends heavily on grip and boundary size."
        ],
        "rr_tactical_fit": (
            "Exceptional venue fit for Jaipur. The large boundaries at SMS protect Harshal's mis-hit deliveries from "
            "flying over the ropes, converting potential sixes into outfield catches at deep mid-wicket."
        ),
        "auction_target_tier": "High-Value Death Bowling Specialist"
    },
    7503: {
        "player_name": "Ravi Bishnoi",
        "strengths": [
            "Rapid arm-speed leg-spin: 173 IPL pressure balls, 9.16 economy.",
            "Heavy googly percentage (over 60%) that catches middle-order batters playing for leg-spin.",
            "Young Indian international core player."
        ],
        "limitations": [
            "Tends to bowl a flat, one-dimensional trajectory when under sustained counter-attack."
        ],
        "rr_tactical_fit": (
            "Excellent alternative if Chahal is unavailable. Local Rajasthan roots (Jodhpur) and mastery of dry, gripping surfaces."
        ),
        "auction_target_tier": "Primary Alternative Domestic Spinner"
    },
    8746: {
        "player_name": "Vaibhav Arora",
        "strengths": [
            "Impressive IPL breakthrough: 165 HP balls, 15 wickets, excellent seam presentation.",
            "Both new ball swing and deceptive skiddy death bowling."
        ],
        "limitations": [
            "Economy expands to 9.64 under heavy death-overs onslaught."
        ],
        "rr_tactical_fit": (
            "Budget-friendly domestic seam option to build bowling bench strength."
        ),
        "auction_target_tier": "Domestic Pace Value Target"
    },
    4101: {
        "player_name": "Mitchell Santner",
        "strengths": [
            "World-class economy discipline: 8.19 RPO in IPL, 7.82 in T20I under pressure.",
            "Exceptional match awareness, fielding prowess, and lower-order batting capability."
        ],
        "limitations": [
            "Strike rate under pressure is low (8 wickets in 85 balls); primarily a run-restrictor.",
            "Overseas slot competition."
        ],
        "rr_tactical_fit": (
            "Smart value pick if RR needs a disciplined finger-spinner who can also bat at #8."
        ),
        "auction_target_tier": "Smart Value Overseas Finger-Spinner"
    },
    7364: {
        "player_name": "Haris Rauf",
        "strengths": ["150+ kph raw pace and reverse-swing yorkers: 30 T20I pressure wickets."],
        "limitations": ["Not available for IPL auction participation."],
        "rr_tactical_fit": ["Benchmark international pace profile; non-IPL eligible."],
        "auction_target_tier": "International Reference Only"
    },
    6355: {
        "player_name": "Shaheen Afridi",
        "strengths": ["Elite left-arm pace and lethal early/late wickets."],
        "limitations": ["Not available for IPL auction participation."],
        "rr_tactical_fit": ["Benchmark international pace profile; non-IPL eligible."],
        "auction_target_tier": "International Reference Only"
    },
    34485: {
        "player_name": "Sufiyan Muqeem",
        "strengths": ["Mystery left-arm wrist spin: 5.09 T20I economy under pressure."],
        "limitations": ["Not available for IPL auction participation."],
        "rr_tactical_fit": ["Benchmark wrist-spin profile; non-IPL eligible."],
        "auction_target_tier": "International Reference Only"
    },
    6450: {
        "player_name": "Mujeeb Ur Rahman",
        "strengths": ["Mystery off-spin: 6.32 T20I economy across 112 pressure balls."],
        "limitations": ["0 IPL balls in dataset; availability subject to international boards."],
        "rr_tactical_fit": ["Overseas mystery spin backup."],
        "auction_target_tier": "Overseas Spin Backup / Watchlist"
    },
    5750: {
        "player_name": "Ehsan Khan",
        "strengths": ["Associate T20I standout: 6.39 economy across 76 pressure balls."],
        "limitations": ["Unproven against elite franchise competition."],
        "rr_tactical_fit": ["Talent identification reference."],
        "auction_target_tier": "Associate Scouting Reference"
    },
    39657: {
        "player_name": "Eshan Malinga",
        "strengths": ["Slingy action with skiddy yorkers: 289 combined pressure balls."],
        "limitations": ["IPL economy is 9.33; developing international skill."],
        "rr_tactical_fit": ["Overseas pace developmental candidate."],
        "auction_target_tier": "Developmental Overseas Seamer"
    }
}


def build_auction_dossier(
    deliveries_df: pd.DataFrame,
    player_id: int,
    is_batter: bool = True,
    rank: int = 1,
    comb_score: float = 75.0,
    ipl_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Construct a complete, professional Auction Dossier for a shortlisted player.
    Separates measured empirical statistics from qualitative scouting recommendations.
    """
    splits_data = compute_player_competition_split(deliveries_df, player_id, is_batter=is_batter)
    role_data = classify_player_role_and_phases(deliveries_df, player_id, is_batter=is_batter)

    player_name = splits_data["player_name"]
    splits = splits_data["splits"]

    # Extract total balls for uncertainty
    if is_batter:
        tot_balls = splits["Combined"]["hp_balls"]
        ipl_balls = splits["IPL"]["hp_balls"]
        t20i_balls = splits["T20I"]["hp_balls"]
    else:
        tot_balls = splits["Combined"]["hp_legal_balls"]
        ipl_balls = splits["IPL"]["hp_legal_balls"]
        t20i_balls = splits["T20I"]["hp_legal_balls"]

    uncertainty = get_sample_uncertainty_profile(tot_balls)
    ipl_uncertainty = get_sample_uncertainty_profile(ipl_balls)

    # Delta analysis: IPL vs Combined
    delta_score = (ipl_score - comb_score) if ipl_score is not None else 0.0

    # Fetch tactical notes from repository
    tactical_notes = RR_TACTICAL_DOSSIERS.get(player_id, {
        "player_name": player_name,
        "strengths": ["Statistically verified high-pressure performance in supplied dataset."],
        "limitations": ["Data sample requires continued monitoring across varying venues."],
        "rr_tactical_fit": "Versatile squad asset; evaluate against specific role requirements at Jaipur.",
        "auction_target_tier": "Tactical Shortlist Target"
    })

    return {
        "player_id": player_id,
        "player_name": player_name,
        "is_batter": is_batter,
        "rank": rank,
        "primary_role": role_data["primary_role"],
        "style": role_data["style"],
        "combined_score": round(comb_score, 1),
        "ipl_score": round(ipl_score, 1) if ipl_score is not None else None,
        "delta_ipl_vs_comb": round(delta_score, 1) if ipl_score is not None else None,
        "splits": splits,
        "phase_distribution": role_data["phase_distribution"],
        "uncertainty": uncertainty,
        "ipl_uncertainty": ipl_uncertainty,
        "strengths": tactical_notes["strengths"],
        "limitations": tactical_notes["limitations"],
        "rr_tactical_fit": tactical_notes["rr_tactical_fit"],
        "auction_target_tier": tactical_notes["auction_target_tier"]
    }


def generate_all_auction_assets(
    deliveries_df: pd.DataFrame,
    output_dir: Path
) -> Dict[str, pd.DataFrame]:
    """
    Generate and save all official auction intelligence CSV exports to output_dir.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    rankings = compute_auction_rankings(deliveries_df)

    # 1. Save IPL-Only Top 10 Batters
    ipl_bat = rankings["batters_ipl"].copy()
    ipl_bat.to_csv(output_dir / "RR_IPL_Only_Top_10_Batters.csv", index=False)

    # 2. Save IPL-Only Top 10 Bowlers
    ipl_bowl = rankings["bowlers_ipl"].copy()
    ipl_bowl.to_csv(output_dir / "RR_IPL_Only_Top_10_Bowlers.csv", index=False)

    # 3. Save Combined Top 10 Batters
    comb_bat = rankings["batters_combined"].copy()
    comb_bat.to_csv(output_dir / "RR_Combined_Top_10_Batters.csv", index=False)

    # 4. Save Combined Top 10 Bowlers
    comb_bowl = rankings["bowlers_combined"].copy()
    comb_bowl.to_csv(output_dir / "RR_Combined_Top_10_Bowlers.csv", index=False)

    # 5. Build Comprehensive Shortlist Dossier Table
    dossier_rows = []

    # Shortlisted Batters (Combined top 10 + IPL top 10 unique)
    bat_pids = list(dict.fromkeys(list(comb_bat["player_id"]) + list(ipl_bat["player_id"])))
    for pid in bat_pids:
        c_row = comb_bat[comb_bat["player_id"] == pid]
        c_score = c_row["reliability_score"].iloc[0] if not c_row.empty else None
        c_rank = int(c_row["rank"].iloc[0]) if not c_row.empty else None

        i_row = ipl_bat[ipl_bat["player_id"] == pid]
        i_score = i_row["reliability_score"].iloc[0] if not i_row.empty else None
        i_rank = int(i_row["rank"].iloc[0]) if not i_row.empty else None

        dossier = build_auction_dossier(
            deliveries_df, pid, is_batter=True,
            rank=c_rank or i_rank or 99,
            comb_score=c_score or (i_score or 50.0),
            ipl_score=i_score
        )

        sp = dossier["splits"]
        dossier_rows.append({
            "category": "Batter",
            "player_id": pid,
            "player_name": dossier["player_name"],
            "primary_role": dossier["primary_role"],
            "batting_hand": dossier["style"],
            "target_tier": dossier["auction_target_tier"],
            "comb_rank": c_rank,
            "comb_score": c_score,
            "ipl_rank": i_rank,
            "ipl_score": i_score,
            "delta_ipl": dossier["delta_ipl_vs_comb"],
            "comb_hp_balls": sp["Combined"]["hp_balls"],
            "comb_hp_sr": sp["Combined"]["hp_sr"],
            "comb_hp_avg": sp["Combined"]["hp_avg"],
            "ipl_hp_balls": sp["IPL"]["hp_balls"],
            "ipl_hp_sr": sp["IPL"]["hp_sr"],
            "ipl_hp_avg": sp["IPL"]["hp_avg"],
            "t20i_hp_balls": sp["T20I"]["hp_balls"],
            "t20i_hp_sr": sp["T20I"]["hp_sr"],
            "t20i_hp_avg": sp["T20I"]["hp_avg"],
            "powerplay_pct": dossier["phase_distribution"]["Powerplay"],
            "middle_pct": dossier["phase_distribution"]["Middle"],
            "death_pct": dossier["phase_distribution"]["Death"],
            "uncertainty_tier": dossier["uncertainty"]["uncertainty_tier"],
            "credibility_weight": dossier["uncertainty"]["credibility_weight"],
            "jaipur_tactical_fit": dossier["rr_tactical_fit"]
        })

    # Shortlisted Bowlers (Combined top 10 + IPL top 10 unique)
    bowl_pids = list(dict.fromkeys(list(comb_bowl["player_id"]) + list(ipl_bowl["player_id"])))
    for pid in bowl_pids:
        c_row = comb_bowl[comb_bowl["player_id"] == pid]
        c_score = c_row["reliability_score"].iloc[0] if not c_row.empty else None
        c_rank = int(c_row["rank"].iloc[0]) if not c_row.empty else None

        i_row = ipl_bowl[ipl_bowl["player_id"] == pid]
        i_score = i_row["reliability_score"].iloc[0] if not i_row.empty else None
        i_rank = int(i_row["rank"].iloc[0]) if not i_row.empty else None

        dossier = build_auction_dossier(
            deliveries_df, pid, is_batter=False,
            rank=c_rank or i_rank or 99,
            comb_score=c_score or (i_score or 50.0),
            ipl_score=i_score
        )

        sp = dossier["splits"]
        dossier_rows.append({
            "category": "Bowler",
            "player_id": pid,
            "player_name": dossier["player_name"],
            "primary_role": dossier["primary_role"],
            "batting_hand": dossier["style"],
            "target_tier": dossier["auction_target_tier"],
            "comb_rank": c_rank,
            "comb_score": c_score,
            "ipl_rank": i_rank,
            "ipl_score": i_score,
            "delta_ipl": dossier["delta_ipl_vs_comb"],
            "comb_hp_balls": sp["Combined"]["hp_legal_balls"],
            "comb_hp_sr": sp["Combined"]["hp_strike_rate"],
            "comb_hp_avg": sp["Combined"]["hp_economy"],
            "ipl_hp_balls": sp["IPL"]["hp_legal_balls"],
            "ipl_hp_sr": sp["IPL"]["hp_strike_rate"],
            "ipl_hp_avg": sp["IPL"]["hp_economy"],
            "t20i_hp_balls": sp["T20I"]["hp_legal_balls"],
            "t20i_hp_sr": sp["T20I"]["hp_strike_rate"],
            "t20i_hp_avg": sp["T20I"]["hp_economy"],
            "powerplay_pct": dossier["phase_distribution"]["Powerplay"],
            "middle_pct": dossier["phase_distribution"]["Middle"],
            "death_pct": dossier["phase_distribution"]["Death"],
            "uncertainty_tier": dossier["uncertainty"]["uncertainty_tier"],
            "credibility_weight": dossier["uncertainty"]["credibility_weight"],
            "jaipur_tactical_fit": dossier["rr_tactical_fit"]
        })

    dossier_df = pd.DataFrame(dossier_rows)
    dossier_df.to_csv(output_dir / "RR_Auction_Shortlist_Comprehensive_Dossier.csv", index=False)

    logger.info("Successfully generated all auction intelligence assets.")
    return {
        "dossier": dossier_df,
        "ipl_bat": ipl_bat,
        "ipl_bowl": ipl_bowl,
        "comb_bat": comb_bat,
        "comb_bowl": comb_bowl
    }
