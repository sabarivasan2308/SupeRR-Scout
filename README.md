# SupeRR Scout — IPL Pressure Intelligence Platform

A production-grade sports analytics and auction intelligence platform designed for T20 cricket player evaluation under high-leverage and high-pressure match situations.

---

## 📌 1. Project Overview

In franchise T20 cricket, aggregate statistics often obscure critical performance nuances. A boundary hit in a low-stakes opening powerplay carries vastly different leverage than a boundary required off the final over of a tournament chase.

**SupeRR Scout** addresses this fundamental gap by quantifying **situational pressure on every delivery ($0.0 - 100.0$)** and applying **Empirical Bayes shrinkage** to evaluate player reliability fairly across varying opportunity sample sizes. The platform translates complex ball-by-ball physics and game-state data into actionable scouting dossiers, dynamic leaderboards, and auction strategy tools.

---

## 🎯 2. Problem Statement (High-Level)

Traditional scouting metrics (aggregate runs, standard strike rates, raw batting averages, overall bowling economy rates) suffer from three critical distortions:

1. **Context Blindness:** A delivery faced at Required Run Rate ($\text{RRR}$) of 14.0 with 7 wickets down is treated identically to one faced during a relaxed chase at 6.0 RPO.
2. **Sample-Size Instability:** Unadjusted high-pressure averages can heavily favor small sample anomalies (e.g., a batter who faced 15 balls and hit three boundaries) over proven multi-season franchise performers.
3. **Role Asymmetry:** Batters face urgency driven by $\text{RRR}$ and remaining wickets, while bowlers face containment stress influenced by boundary defense, field restrictions, and phase-specific leverage.

**SupeRR Scout** solves these challenges by dynamically reconstructing match states, computing independent pressure indices for batting and bowling, and deriving stabilized Bayesian reliability scores.

---

## 🚀 3. Key Features

- **Continuous Pressure Intelligence Engine ($0 - 100$):** Reconstructs dynamic match leverage on every delivery based on required run rates, wickets in hand, phase progression, and match closeness.
- **Empirical Bayes Regularization:** Bayesian shrinkage ($K = 50.0$) stabilizes small-sample volatility toward league-wide priors, paired with 95% confidence intervals to communicate statistical certainty transparently.
- **Power BI-Style Interactive Analytics:** Built with a high-contrast Rajasthan Royals-inspired dark theme, dynamic persistent slicers, cross-filtering, active parameter badges, and one-click reset controls.
- **Competition & Phase Disaggregation:** Separate filters for franchise-specific (IPL) versus international (T20I) performance, with Powerplay (overs 1–6), Middle (overs 7–16), and Death (overs 17–20) drill-downs.
- **Auction Intelligence War Room:** Comprehensive scouting profiles including tactical role classifications, sample certainty tiers, and venue-specific suitability assessments.
- **Standardized Export Capabilities:** Automated report compilation and clean data exports for scouting workflows.

---

## 🛠️ 4. Technology Stack

- **Language:** Python 3.11+
- **Interactive UI & Dashboards:** [Streamlit](https://streamlit.io/) (v1.35+)
- **Data Engineering:** [Pandas](https://pandas.pydata.org/) (v2.1+), [NumPy](https://numpy.org/) (v1.26+)
- **Interactive Visualizations:** [Plotly](https://plotly.com/) (v5.20+)
- **Scientific & Statistical Computing:** [SciPy](https://scipy.org/), [Scikit-Learn](https://scikit-learn.org/)
- **Document Generation:** [ReportLab](https://www.reportlab.com/) (v4.1+), [pypdf](https://pypdf.readthedocs.io/)
- **Test Automation:** [Pytest](https://docs.pytest.org/) (v8.0+)

---

## 📂 5. Project Structure

```text
SupeRR-Scout/
├── app.py                             # Main Streamlit web application entry point
├── precompute.py                      # Rapid baseline precomputation pipeline
├── requirements.txt                   # Production package dependencies
├── README.md                          # Platform documentation & setup guide
├── methodology.md                     # Mathematical formulations & scientific derivations
├── .gitignore                         # Strict exclusion rules for datasets and artifacts
│
├── src/                               # Modular analytics core
│   ├── __init__.py
│   ├── auction_intelligence.py        # Auction tiering, role fingerprints & venue fit
│   ├── batting_analysis.py            # High-pressure batting metrics & boundary conversion
│   ├── bowling_analysis.py            # Legal ball tracking, economy under leverage & dot %
│   ├── data_loader.py                 # File loading & processed cache management
│   ├── data_validation.py             # Schema & relational constraint tests
│   ├── match_context.py               # Chase state reconstruction & par benchmarks
│   ├── pbi_overview_helpers.py        # Power BI components (leaderboards, scatter, heatmaps)
│   ├── player_profiles.py             # Evidence card generators & scouting rationales
│   ├── preprocessing.py               # Legal ball, overs & match reconstruction
│   ├── pressure_engine.py             # 0-100 continuous Pressure Intelligence Engine
│   ├── rankings.py                    # Leaderboards & standardized export formatters
│   ├── reliability_model.py           # Empirical Bayes shrinkage & 95% confidence intervals
│   ├── report_generator.py            # Automated ReportLab PDF report builder
│   ├── ui_helpers.py                  # Streamlit CSS and global filter bindings
│   └── visualizations.py              # Themed Plotly chart engines & palettes
│
├── pages/                             # Eight Multi-Page Streamlit Dashboards
│   ├── 1_Executive_Overview.py        # Macro tournament KPIs, scatter matrix & spotlights
│   ├── 2_Batting_Intelligence.py      # Batting leaderboard & phase efficiency matrix
│   ├── 3_Bowling_Intelligence.py      # Bowling containment, death economy & dot-ball %
│   ├── 4_Top_10_Rankings.py           # Official leaderboards & evidence cards
│   ├── 5_Player_Comparison.py         # Multi-player 5-axis radar & head-to-head metrics
│   ├── 6_Match_Situation_Analysis.py  # Ball-by-ball leverage engine & RRR stress curves
│   ├── 7_Methodology.py               # Mathematical formulas, derivations & transparency
│   └── 8_Auction_Intelligence.py      # IPL 2027 Auction War Room & candidate dossiers
│
└── tests/                             # Comprehensive automated test suite (31 tests)
    ├── test_auction_intelligence.py   # Auction rankings, competition splits & dossiers
    ├── test_batting_analysis.py       # Batting metrics, boundary % & reliability scores
    ├── test_bowling_analysis.py       # Bowling legal balls, economy & breakdown schemas
    ├── test_data_validation.py        # Schema checks & integrity tests
    ├── test_pbi_overview.py           # Power BI charts, scatter & pre-ranked handling
    ├── test_pressure_engine.py        # Boundary [0, 100] & monotonicity tests
    └── test_rankings.py               # Ranking uniqueness & standardized export tests
```

---

## ⚡ 6. Installation Instructions

### Prerequisites
- Python 3.11 or higher installed on your system.
- Git installed.

### Setup Steps
```bash
# Clone the repository
git clone https://github.com/sabarivasan2308/SupeRR-Scout.git
cd SupeRR-Scout

# Create and activate a virtual environment (recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 🖥️ 7. Launching the Application

Start the Streamlit application using the official entry point:

```bash
python -m streamlit run app.py
```

Once started, open your web browser and navigate to:

```
http://localhost:8501
```

---

## 📑 8. Application Pages

1. **Executive Overview (`pages/1_Executive_Overview.py`):** Macro tournament KPIs, dynamic filters, horizontal reliability leaderboards, scatter plots (Reliability vs. Opportunities), and active player spotlights.
2. **Batting Intelligence (`pages/2_Batting_Intelligence.py`):** In-depth batting analytics under leverage, phase breakdowns (Powerplay, Middle, Death), Bayesian credibility intervals, and clutch delta indicators ($\Delta \text{SR}$).
3. **Bowling Intelligence (`pages/3_Bowling_Intelligence.py`):** Defensive containment metrics under pressure, clutch economy rates, dot-ball percentages, and breakdown tables across competitions, phases, and seasons.
4. **Top 10 Rankings (`pages/4_Top_10_Rankings.py`):** Official leaderboards for Batters and Bowlers with scope toggles (Combined vs. IPL-only), individual scouting dossiers, and one-click data downloads.
5. **Player Comparison (`pages/5_Player_Comparison.py`):** Multi-player 5-axis radar overlays comparing volume, boundary conversion, dot-ball resistance, clutch delta, and composite reliability score.
6. **Match Situation Analysis (`pages/6_Match_Situation_Analysis.py`):** Ball-by-ball leverage curves, cumulative match pressure trajectories, and phase leverage comparisons.
7. **Methodology & Transparency (`pages/7_Methodology.py`):** Complete mathematical formulas, Bayesian shrinkage simulations, prior parameter settings, and scientific limitation disclosures.
8. **Auction Intelligence (`pages/8_Auction_Intelligence.py`):** Franchise auction war room featuring shortlisted candidate dossiers, competition split comparisons, phase fingerprints, uncertainty indicators, and venue tactical fit profiles.

---

## 📐 9. Analytical Methodology (Summary)

The platform evaluates pressure and reliability using a rigorous multi-stage mathematical model:

### A. Delivery-Level Pressure Index ($P \in [0.0, 100.0]$)
- **Chase Pressure (Second Innings):**
  $$\text{Pressure}_{\text{chase}} = 0.40 \cdot R_{\text{demand}} + 0.25 \cdot W_{\text{lost}} + 0.20 \cdot S_{\text{stage}} + 0.15 \cdot L_{\text{closeness}}$$
  Evaluates required run rate demand, wickets lost progression, overs completed, and close-finish leverage.
- **First-Innings Pressure:**
  $$\text{Pressure}_{\text{1st}} = 0.45 \cdot W_{\text{crisis}} + 0.35 \cdot S_{\text{phase}} + 0.20 \cdot R_{\text{deficit}}$$
  Measures early wicket collapses, phase acceleration urgency (Death overs 16–20), and trailing run rates relative to tournament par.

### B. High-Pressure Filtering
Deliveries where $P \ge 65.0$ are classified as **High-Pressure (HP)**, isolating the top 20–25% most critical moments of every match.

### C. Empirical Bayes Regularization & 95% Confidence Intervals
To avoid small-sample bias, raw performance estimates $\hat{\theta}_i$ are regularized toward the league population prior $\mu_{\text{pop}}$:
$$\hat{\theta}_{\text{shrunk}} = w_i \cdot \hat{\theta}_i + (1 - w_i) \cdot \mu_{\text{pop}}, \quad \text{where} \quad w_i = \frac{n_i}{n_i + K}$$
where $n_i$ is the number of high-pressure deliveries faced or bowled, and $K = 50.0$ is the half-credibility constant.

Associated 95% credibility intervals are constructed via asymptotic error propagation:
$$\text{CI}_{95\%} = \hat{\theta}_{\text{shrunk}} \pm 1.96 \cdot \frac{\sigma_{\text{pop}}}{\sqrt{n_i / n_0}}$$

For full derivations and proofs, refer to [`methodology.md`](methodology.md) and **Page 7** of the application.

---

## 🧪 10. Automated Testing

The project includes an automated test suite covering all modules:

```bash
python -m pytest tests/ -v
```

### Verified Test Suite (31 Tests Passing)
- `tests/test_auction_intelligence.py` (8 tests): Auction rankings, competition splits, role classification, uncertainty profiles, and dossier generation.
- `tests/test_batting_analysis.py` (2 tests): High-pressure strike rates, averages, and boundary conversion.
- `tests/test_bowling_analysis.py` (3 tests): Legal deliveries, economy rates, wickets, and breakdown table schemas.
- `tests/test_data_validation.py` (4 tests): Schema constraints, data types, and relational integrity.
- `tests/test_pbi_overview.py` (8 tests): Interactive visualizations, scatter charts, heatmaps, and pre-ranked leaderboard handling.
- `tests/test_pressure_engine.py` (3 tests): Boundedness ($[0, 100]$), monotonicity, and pressure tagging.
- `tests/test_rankings.py` (3 tests): Uniqueness, minimum opportunity thresholds, and standardized output formatting.

---

## 🔒 11. Data Availability & Usage Disclaimer

- **Proprietary Datasets Excluded:** In compliance with challenge guidelines and data governance policies, proprietary match and delivery datasets (`data/raw/`, `data/processed/`, and challenge-derived exports) are **strictly excluded** from this public repository via `.gitignore`.
- **Data Schema Compatibility:** To run the application with compatible datasets, place standard ball-by-ball and match files into `data/raw/` following the schema outlined in `src/data_validation.py`, then run:
  ```bash
  python precompute.py
  ```
- **License & Rights:** This software and analytical framework are developed for sports analytics research and evaluation. All team names, tournament trademarks, and player identities remain the property of their respective owners.
