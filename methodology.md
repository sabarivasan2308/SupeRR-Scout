# SupeRR SCOUT — Pressure Intelligence Engine
## Scientific Methodology & Analytical Framework
### Rajasthan Royals IPL 2027 Auction Research | Round 1 Official Methodology

---

## 1. Executive Summary & Objective

In franchise T20 cricket, auction strategy cannot rely on uncontextualized aggregate statistics. A boundary scored in a low-stakes 5th over carries vastly different leverage than a boundary needed off the final over of a tournament chase.

The **SupeRR SCOUT Pressure Intelligence Engine** was engineered for Round 1 of Rajasthan Royals' *SupeRR Selector Season 2* hackathon. The objective is to analyze the confidential 2022–2026 IPL and T20I datasets (comprising 883 matches and 200,999 ball-by-ball records) and identify:
1. **The Top 10 Most Reliable Batters under Pressure**
2. **The Top 10 Most Reliable Bowlers under Pressure**

This document details the mathematical definition of pressure, the match reconstruction engine, the Empirical Bayes shrinkage formulation, and the statistical proofs supporting the final leaderboards.

### 1.1 Dataset Scope & Tournament Segregation
- **Combined Rankings:** Use all **200,999 deliveries** from the supplied archive (883 matches), including IPL (371 matches, 87,687 deliveries), T20I (482 matches, 106,327 deliveries), and the 30 Emerging Teams Asia Cup / Asia Cup Rising Stars matches (6,985 deliveries).
- **IPL-Only Rankings:** Use strictly **87,687 IPL deliveries** across **371 matches** (IPL 2022–2026), isolating domestic franchise conditions.

---

## 2. Match Reconstruction & Invariant Integrity

Cricket analytics requires meticulous delivery-by-delivery state tracking. Raw feeds record events; analytical engines must reconstruct the exact game context preceding every delivery.

### 2.1 Delivery Accounting Invariants
- **Legal Delivery for Bowler (`is_legal_ball_bowler`):** Defined as any delivery where `extras_type` is NOT in `{'wide', 'Overstep', 'other'}`. Only legal deliveries advance the over ball count towards the 6-ball over.
- **Ball Faced for Batter (`is_ball_faced_batter`):** Defined as any delivery where `extras_type != 'wide'`. Batters face legal deliveries, no-balls (`Overstep`, `other`), byes, and leg-byes.
- **Bowler Conceded Runs (`runs_bowler`):** Strictly conforms to MCC Law 21:
  $$\text{runs\_bowler} = \text{runs\_off\_bat} + \text{extras1\_runs (if wide, Overstep, or other)}$$
  Byes, leg-byes, and penalty runs are categorized as team extras and are strictly excluded from the bowler's bowling analysis.
- **Bowler-Credited Wickets (`is_bowler_wicket`):** Only dismissals classified as `Caught`, `Bowled`, `LBW`, `Stump`, or `Hit Wicket` are credited to the bowler. Run-outs, retired-outs, and obstructing the field are excluded.

### 2.2 Chase State Reconstruction (2nd Innings)
For every delivery in the 2nd innings:
- **Target Runs ($T$):** If `matches.revised_target` is present and valid (rain/DLS matches), $T = \text{revised\_target}$. Otherwise, $T = \text{Inn1\_Total} + 1$.
- **Balls Remaining ($B_{\text{rem}}$):** Total scheduled legal balls minus cumulative legal balls bowled.
- **Runs Needed ($R_{\text{need}}$):** $\max(0, T - \text{Cumulative\_Innings\_Runs})$.
- **Required Run Rate ($\text{RRR}$):** $\frac{R_{\text{need}}}{\max(1, B_{\text{rem}})} \times 6.0$.

---

## 3. The Pressure Intelligence Engine ($0 - 100$)

Pressure is defined as a continuous scale from $0.0$ to $100.0$. Because the psychological and tactical challenges facing batters and bowlers are fundamentally asymmetric, distinct formulas are evaluated.

### 3.1 Batting Pressure Formulation

#### Second Innings (Chase Pressure):
$$\text{Pressure}_{\text{chase\_bat}} = 0.40 \cdot R_{\text{demand}} + 0.25 \cdot W_{\text{lost}} + 0.20 \cdot S_{\text{stage}} + 0.15 \cdot L_{\text{closeness}}$$

1. **Run Rate Demand ($R_{\text{demand}}$):**
   - $\text{RRR} \le 4.0 \rightarrow 10.0$ (Cruise phase)
   - $\text{RRR} = 8.5 \rightarrow 45.0$ (T20 Par rate)
   - $\text{RRR} = 14.0 \rightarrow 90.0$ (Demanding acceleration)
   - $\text{RRR} \ge 18.0 \rightarrow 100.0$ (Extreme desperation)
2. **Wickets Lost Urgency ($W_{\text{lost}}$):**
   $$W_{\text{lost}} = \min\left(100.0, \left(\frac{\text{wickets\_lost}}{9.0}\right)^{1.15} \times 100.0\right)$$
3. **Innings Stage ($S_{\text{stage}}$):**
   $$S_{\text{stage}} = \min\left(100.0, \frac{\text{legal\_balls\_bowled}}{120.0} \times 100.0\right)$$
4. **Match Closeness ($L_{\text{closeness}}$):** Peak leverage occurs when balls remaining $< 36$, wickets in hand $\ge 2$, and runs needed is within reach.

#### First Innings (Batting Pressure):
$$\text{Pressure}_{\text{1st\_bat}} = 0.45 \cdot W_{\text{crisis}} + 0.35 \cdot S_{\text{phase}} + 0.20 \cdot R_{\text{deficit}}$$

- **$W_{\text{crisis}}$:** Wickets lost ahead of the progression expectation curve.
- **$S_{\text{phase}}$:** Death overs (overs 16–20) demand aggressive run production against specialist death bowlers while protecting the tail.
- **$R_{\text{deficit}}$:** Current run rate trailing competition par (IPL par: 9.25 RPO; T20I par: 8.30 RPO).

#### Knockout Match Multiplier:
Deliveries in playoff and knockout matches receive a $1.08\times$ context multiplier.

---

### 3.2 Bowling Pressure Formulation

A bowler experiences peak pressure when defending tight target margins against set batters in late overs:

#### Second Innings (Defending Pressure):
$$\text{Pressure}_{\text{chase\_bowl}} = 0.35 \cdot R_{\text{threat}} + 0.25 \cdot S_{\text{stage}} + 0.20 \cdot W_{\text{opp\_hand}} + 0.20 \cdot M_{\text{margin}}$$

- **$R_{\text{threat}}$:** Threat peaks when the batting team needs an achievable run rate ($6.0 \le \text{RRR} \le 12.0$). If RRR exceeds 22.0 with 9 down, bowler pressure is minimal.
- **$W_{\text{opp\_hand}}$:** Opposition wickets in hand. More batting wickets remaining allows the opposition to swing without fear.
- **$M_{\text{margin}}$:** Margin stress in the final 36 balls when runs needed is small.

#### First Innings (Bowling Pressure):
$$\text{Pressure}_{\text{1st\_bowl}} = 0.45 \cdot P_{\text{phase}} + 0.30 \cdot W_{\text{opp\_strength}} + 0.25 \cdot T_{\text{tempo}}$$

- **$P_{\text{phase}}$:** Powerplay (field restrictions: only 2 outside ring) and Death overs.
- **$W_{\text{opp\_strength}}$:** Bowling against top/middle order with wickets intact.
- **$T_{\text{tempo}}$:** Opposition scoring tempo exceeding par rate.

---

## 4. Statistical Fairness & Reliability Model

### 4.1 Empirical Bayes Shrinkage
To guard against small-sample variance (e.g. a batter facing 20 balls hitting a couple of lucky boundaries), individual estimates are shrunk towards the empirical population mean:

$$\hat{\theta}_{\text{shrunk}} = w_i \cdot \hat{\theta}_i + (1 - w_i) \cdot \mu_{\text{pop}}$$

$$\text{Credibility Weight: } w_i = \frac{n_i}{n_i + K}$$

- Prior half-credibility constant: $K = 50.0$.
- Population Priors across dataset under High Pressure:
  - Batting Strike Rate Prior $\mu_{\text{pop\_sr}} = 138.51$
  - Batting Average Prior $\mu_{\text{pop\_avg}} = 16.92$
  - Bowling Economy Prior $\mu_{\text{pop\_econ}} = 10.14$
  - Bowling Strike Rate Prior $\mu_{\text{pop\_bsr}} = 14.93$

### 4.2 Composite Reliability Scoring Formula ($0 - 100$)

#### Batter Reliability Score ($R_{\text{bat}}$):
$$R_{\text{bat}} = \left[ 0.30 \cdot S_{\text{rate}} + 0.25 \cdot S_{\text{survival}} + 0.20 \cdot S_{\text{boundary\_dot}} + 0.15 \cdot S_{\text{clutch\_delta}} + 0.10 \cdot S_{\text{consistency}} \right] \times C_{\text{opp}}$$

Where:
- $S_{\text{rate}}$: Shrunk Strike Rate normalized between 95 and 195.
- $S_{\text{survival}}$: Shrunk Average normalized between 12 and 45.
- $S_{\text{boundary\_dot}}$: Boundary % rewarded ($2.2\times$) and Dot % penalized ($1.2\times$).
- $S_{\text{clutch\_delta}}$: Elevation delta: $50.0 + 0.7 \cdot (\text{SR}_{\text{hp}} - \text{SR}_{\text{norm}}) + 0.4 \cdot (\text{Avg}_{\text{hp}} - \text{Avg}_{\text{norm}})$.
- $S_{\text{consistency}}$: Match-by-match repeatability index.
- $C_{\text{opp}}$: Sample size credibility factor: $\min\left(1.0, 0.70 + 0.30 \cdot \frac{n_i}{180.0}\right)$.

#### Bowler Reliability Score ($R_{\text{bowl}}$):
$$R_{\text{bowl}} = \left[ 0.30 \cdot B_{\text{contain}} + 0.25 \cdot B_{\text{wicket\_threat}} + 0.20 \cdot B_{\text{dot\_suppress}} + 0.15 \cdot B_{\text{clutch\_delta}} + 0.10 \cdot B_{\text{consistency}} \right] \times C_{\text{opp}}$$

Where:
- $B_{\text{contain}}$: Shrunk Economy normalized (inverted: $100$ at $6.5$ RPO, $0$ at $12.5$ RPO).
- $B_{\text{wicket\_threat}}$: Shrunk Bowling Strike Rate normalized (inverted: $100$ at $8.0$ balls/wkt, $0$ at $26.0$ balls/wkt).
- $B_{\text{dot\_suppress}}$: High dot ball % rewarded and boundary concession % suppressed.
- $B_{\text{clutch\_delta}}$: Economy tightening delta: $50.0 + 10.0 \cdot (\text{Econ}_{\text{norm}} - \text{Econ}_{\text{hp}})$.
- $C_{\text{opp}}$: Sample size credibility factor: $\min\left(1.0, 0.70 + 0.30 \cdot \frac{n_i}{200.0}\right)$.

### 4.3 95% Confidence Intervals
Standard Error is computed dynamically from sample opportunity size:
$$SE_i = \frac{16.0}{\sqrt{n_i / 25.0}}$$
$$\text{95\% CI} = [\max(0, \text{Score} - 1.96 \cdot SE_i), \min(100, \text{Score} + 1.96 \cdot SE_i)]$$

---

## 5. Ranking Derivation & Composite Reliability Formulation

The final player leaderboards under high pressure ($P \ge 65.0$) are derived through a multi-factor composite scoring engine that combines Bayesian-regularized performance, clutch deltas, and sample opportunity weighting:

### 5.1 Composite Batting Reliability Score ($S_{\text{bat}} \in [0, 100]$)
$$S_{\text{bat}} = 0.40 \cdot \hat{\text{SR}}_{\text{shrunk}} + 0.25 \cdot \Delta\text{SR}_{\text{norm}} + 0.15 \cdot \text{Vol}_{\text{factor}} + 0.10 \cdot \text{Bnd}_{\text{pct}} + 0.10 \cdot \text{Consist}_{\text{rate}}$$

1. **Shrunk Performance ($\hat{\text{SR}}_{\text{shrunk}}$):** Empirical Bayes regularized strike rate mapped to a 0–100 percentile score against league-wide pressure distributions.
2. **Clutch Delta ($\Delta\text{SR}_{\text{norm}}$):** Measurement of gear shift under pressure ($\text{SR}_{\text{HP}} - \text{SR}_{\text{normal}}$), rewarding batters who elevate their scoring rate when match leverage rises.
3. **Volume Factor ($\text{Vol}_{\text{factor}}$):** Log-scaled opportunity weighting:
   $$\text{Vol}_{\text{factor}} = \min\left(1.0, 0.70 + 0.30 \cdot \frac{n_i}{180.0}\right)$$
4. **Boundary Conversion Rate ($\text{Bnd}_{\text{pct}}$):** Frequency of finding the boundary under high pressure without squandering dismissals.
5. **Impact Consistency ($\text{Consist}_{\text{rate}}$):** Proportion of high-pressure matches where the batter produced positive win-probability contributions.

### 5.2 Composite Bowling Reliability Score ($S_{\text{bowl}} \in [0, 100]$)
$$S_{\text{bowl}} = 0.40 \cdot \hat{\text{Econ}}_{\text{shrunk}} + 0.25 \cdot \Delta\text{Econ}_{\text{norm}} + 0.15 \cdot \text{Wkt}_{\text{strike}} + 0.10 \cdot \text{Dot}_{\text{pct}} + 0.10 \cdot \text{Vol}_{\text{factor}}$$

1. **Shrunk Economy ($\hat{\text{Econ}}_{\text{shrunk}}$):** Inverted and standardized Bayesian-smoothed economy rate under pressure.
2. **Clutch Economy Delta ($\Delta\text{Econ}_{\text{norm}}$):** Composure delta ($\text{Econ}_{\text{normal}} - \text{Econ}_{\text{HP}}$), rewarding bowlers who tighten boundary leakage under leverage.
3. **Breakthrough Capability ($\text{Wkt}_{\text{strike}}$):** High-pressure bowling strike rate (balls per wicket).
4. **Dot-Ball Frequency ($\text{Dot}_{\text{pct}}$):** Percentage of legal deliveries conceding zero runs under duress.

### 5.3 Opportunity Thresholds & Scope Separation
- **Minimum Threshold:** Players must have faced or bowled at least **60 legal deliveries** under high-pressure conditions ($P \ge 65.0$) to qualify for official leaderboard consideration.
- **Combined vs. IPL-Only Segregation:** Prior means ($\mu_{\text{pop}}$) and candidate eligibility pools are computed independently for franchise-only and combined international datasets to account for differing par scoring environments.

---

## 6. Strategic Takeaways & Auction Applications

The analytical framework directly informs franchise auction strategy:
1. **Finisher Archetypes:** Identifying batters with high clutch delta ($\Delta\text{SR} > +35.0$) and proven boundary rates who thrive in overs 17–20.
2. **Defensive Bowling Anchors:** Prioritizing bowlers with sub-7.00 HP economy rates and elevated dot-ball percentages who do not leak boundaries under duress.
3. **Venue-Specific Tactical Fit:** Aligning candidate execution profiles (e.g. boundary avoidance, wrist-spin grip, slower-ball deception) with home fortress ground dimensions (e.g., Sawai Mansingh Stadium's large square boundaries).

---

## 7. Reproducibility & Code Verification

All calculations are 100% reproducible directly from the supplied data:
```bash
python precompute.py
python -m pytest tests/ -v
python -m streamlit run app.py
```
No external APIs or synthetic figures were used. Every metric reflects verified historical performance from 2022 to 2026.
