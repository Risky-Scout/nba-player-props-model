# Methodology

**NBA Player Props Prediction System — Technical Framework**

This document describes the mathematical and statistical foundations of the prediction pipeline. It is intended for readers familiar with probability theory, quantitative finance, and sports betting markets. All design decisions are explained with their tradeoffs made explicit.

---

## 1. Problem Framing

The core task is not prediction — it is **pricing**. The market already has a probability estimate for any player prop, implied by the posted odds. The question is whether the model's estimate is systematically different from the market's in ways that produce positive expected value *before* the market converges to its closing price.

Formally: given a player *i*, stat *s*, and sportsbook line *L* with posted odds *o*, does:

```
P_model(stat_i > L) − P_market(stat_i > L | vig removed)  >  0
```

sufficiently often, and by a sufficient margin, to produce positive edge after vig?

The primary long-run validation metric is **Closing Line Value (CLV)**, not win rate. CLV measures whether the model found prices that the sharpest participants in the market subsequently confirmed by moving the line in the predicted direction. A model with positive mean CLV is finding real inefficiencies. A model with a high win rate but negative CLV may simply be running hot.

---

## 2. Output: Full Probability Mass Function

The model does not output a point estimate. It outputs a **full conditional distribution** over the outcome space for each player-game-stat combination.

Specifically: 11 quantile regressors trained at τ ∈ {0.10, 0.20, 0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75, 0.80, 0.90} define the predicted CDF at 11 knot points. The implied probability that a player exceeds any arbitrary line *L* is recovered by **piecewise linear CDF interpolation** between adjacent quantile knots:

```
P(stat > L) = 1 − F̂(L)

where F̂(L) = (L − q_{τ_k}) / (q_{τ_{k+1}} − q_{τ_k}) × (τ_{k+1} − τ_k) + τ_k
for τ_k : q_{τ_k} ≤ L < q_{τ_{k+1}}
```

Boundary behavior: L < q_0.10 → P(over) = 0.90; L > q_0.90 → P(over) = 0.10.

This distribution-first approach means the model can price **any line** against **any movement** without retraining. A line that shifts from 24.5 to 26.5 intraday is just two queries against the same distribution.

**Monotonicity enforcement:** Before any probability computation, quantile outputs are isotonically projected to ensure q_{τ_k} ≤ q_{τ_{k+1}} for all k. Raw LightGBM quantile outputs occasionally cross, particularly at low-count stats (blocks, steals) — crossing violates the fundamental property of a CDF and produces nonsensical probabilities.

---

## 3. Quantile Regression Training

### Loss Function

Each quantile model minimizes the **pinball loss** (also called the quantile loss or check function):

```
L_τ(y, ŷ) = τ(y − ŷ)     if y ≥ ŷ
           = (τ − 1)(y − ŷ) if y < ŷ
```

At τ = 0.50 this reduces to mean absolute error. At τ = 0.90, the model is penalized 9× more heavily for under-prediction than over-prediction, causing it to learn the 90th percentile of the conditional distribution. The asymmetric penalty is what forces convergence to the true conditional quantile.

### Model Architecture

Each quantile model is a **LightGBM gradient boosting regressor** with the following configuration:

- Objective: `quantile` with `alpha = τ`
- 500 estimators, learning rate 0.05, early stopping on held-out validation loss
- Max depth 6, min child samples 30 (prevents overfitting on low-sample stats)
- Feature fraction 0.8, bagging fraction 0.8 (variance reduction)
- LightGBM's native NaN handling — missing features are not imputed

11 models are trained independently per stat target. Independence is intentional: each model learns the optimal split structure for its quantile, which differs across the distribution. The median model learns splits that minimize MAE; the Q90 model learns splits that minimize over-prediction at the tail.

### Temporal Holdout

Training uses a **strict temporal split**: the most recent 15% of game-dates form the holdout set. The split point is computed on sorted unique dates, not rows, to prevent games from the same date appearing in both sets. No shuffling is applied at any stage.

This is not negotiable from a validity standpoint. Cross-validation with shuffling on time-series panel data produces optimistic calibration estimates because future games can inform the model about past ones via shared player history in rolling features.

---

## 4. Two-Stage Minutes Architecture

Minutes played is the dominant multiplier for all counting stats:

```
E[pts | features] ≈ E[pts/min | features] × E[min | features]
```

Rather than treating minutes as a single-feature input (e.g., a rolling 10-game average), the system trains a **dedicated upstream quantile minutes model** that outputs the full minutes distribution before any stat model runs. The minutes model outputs:

- `exp_mp` — expected minutes (Q50)
- `mp_q10`, `mp_q25`, `mp_q75`, `mp_q90` — distribution bounds
- `mp_vol` — coefficient of variation of the minutes distribution
- `mp_pred_floor`, `mp_pred_ceiling` — conditional P10 and P90

These 8 values are injected as first-class features into every downstream stat model.

**Why this matters:** A player with a rolling 10-game average of 32 minutes but Q10 of 18 minutes has enormous downside variance — he is someone who is occasionally benched in blowouts or plays through foul trouble. The stat models learn to price this uncertainty rather than assume minutes stability. Without the upstream distribution, the variance is absorbed as unexplained residual noise, degrading calibration at the tails.

---

## 5. Feature Engineering

All features are computed in `feature_engineering.py` with strict no-lookahead enforcement. Every rolling window, EWMA, and opponent aggregation is filtered to games strictly prior to the target game date.

### Rolling Minutes and Per-Minute Rate Block

For each of 13 tracked stats, per-minute rates are computed and rolled over windows of 3, 5, 10, and season-to-date games. Both raw counts and per-minute rates are included. The distinction matters:

- **Raw count rolling average** captures role volume (a player averaging 30 points per game is playing 36 minutes)
- **Per-minute rate rolling average** captures efficiency independently of role (a player averaging 1.1 pts/min whether he plays 18 or 36)

Separating these prevents the models from conflating a hot-shooting stretch (rate signal) with a role expansion (volume signal).

EWMA (α = 0.3) and a trend signal (rolling_last_3 / rolling_last_10) capture recency effects and directional momentum.

### Sharp Money Signal (Line Movement Features)

Open-to-close line movement is one of the strongest available signals in sports betting markets. Sharp money — informed institutional bettors — moves lines measurably and predictably. When a game total steams from 224 to 226.5, it reflects significant capital on the over side from participants with information advantages.

Ten features encode this signal per game:

| Feature | Construction |
|---|---|
| `total_move` | close_total − open_total |
| `spread_move` | close_spread_home − open_spread_home |
| `total_move_abs` | \|close_total − open_total\| |
| `spread_move_abs` | \|close_spread_home − open_spread_home\| |
| `total_move_dir` | sign(total_move) |
| `spread_move_dir` | sign(spread_move) |
| `sharp_action_flag` | 1 if total_move_abs > 1.5 or spread_move_abs > 1.0 |
| `has_line_movement` | 1 if opening line data available |

All features are NaN-safe. LightGBM handles missing values natively via the `min_data_in_bin` parameter — games without opening line history produce valid predictions with degraded but not invalid line movement features.

### Opponent Environment Features

Defensive context is computed from rolling 10-game opponent box scores:

- `opp_reb_chances_allowed`, `opp_oreb_chances_allowed`, `opp_dreb_chances_allowed` — used by rebounds model
- `opp_ast_opportunities`, `opp_pts_allowed` — used by assists model
- `opp_3pa_allowed`, `opp_3pm_allowed`, `opp_3p_rate_allowed` — used by 3-pointers model
- `opp_pace_true` — used by rebounds, assists, and 3-pointers models

These are stat-gated: the rebounds model does not receive `opp_3p_rate_allowed`. This prevents spurious correlations from noise patterns in the training data and reduces effective feature dimensionality for lower-sample stats.

### Vacated Opportunity (Injury-Aware Redistribution)

When rotation players are ruled out, their statistical production redistributes to remaining players. The magnitude of redistribution depends on the missing player's role, the target player's position, and the positional overlap between them.

Fifteen features capture this:

- `vacated_minutes` — total minutes lost by inactive teammates
- `vacated_fga`, `vacated_pts`, `vacated_ast`, `vacated_reb` — production vacated
- `vacated_guard_minutes`, `vacated_big_minutes` — role-classified vacancy
- `vacated_creation_share` — vacated assists relative to team total (affects AST model)
- `vacated_reb_share` — vacated rebounds relative to team total (affects REB model)
- `num_teammates_inactive`, `has_injury_data`

These features are computed daily from the injury snapshot. A team missing two rotation bigs produces a large `vacated_big_minutes` signal that the rebounds model can leverage.

---

## 6. Probability Computation and Edge Calculation

### Vig Removal

Sportsbook implied probabilities sum to greater than 1.0 due to the bookmaker's margin (vig). The fair market probability is recovered using the multiplicative vig removal method:

```
p_over_raw  = 1 / decimal_over
p_under_raw = 1 / decimal_under

p_over_fair  = p_over_raw  / (p_over_raw + p_under_raw)
p_under_fair = p_under_raw / (p_over_raw + p_under_raw)
```

This is the correct method for two-sided markets. The additive method (subtracting vig symmetrically from each side) is only valid when both sides carry equal vig, which is not true for player props with asymmetric juice.

### Edge and Expected Value

```
edge = P_model(over) − P_market(over | vig removed)

EV  = (decimal_odds − 1) × P_model − (1 − P_model)
    = decimal_odds × P_model − 1
```

EV is the expected return per unit wagered under the model's probability estimate. A pick is included in the output only when EV > 2.5% (MIN_EV = 0.025).

### Kelly Sizing

Position size is computed using the fractional Kelly criterion:

```
f* = (b × p − q) / b

where:
  b = decimal_odds − 1
  p = P_model
  q = 1 − p
```

Full Kelly is theoretically optimal for log-wealth maximization but requires exact probability estimates and ignores estimation error. The system applies **quarter-Kelly** (KELLY_FRAC = 0.25), capping at 2 units per single and 1 unit per SGP leg. This accounts for model uncertainty and prevents ruin from calibration error at extreme probabilities.

---

## 7. SGP Correlation Modeling

### Problem Statement

Same-game parlay pricing requires the joint probability:

```
P(leg_1 ∩ leg_2 ∩ ... ∩ leg_n)
```

Naively multiplying independent probabilities produces an upper bound on the true joint probability when legs are positively correlated (as most within-player stat combinations are). A three-leg SGP at naive 5% is worth nothing if the true joint probability is 2%.

### Gaussian Copula Framework

The system uses a **Gaussian copula** to model the joint distribution:

1. Estimate the within-player correlation matrix **R** from residual z-scores (not raw stat values) using Pearson correlation on winsorized (±3σ) standardized residuals
2. For a set of SGP legs with marginal CDFs {F₁, ..., Fₙ} from the quantile models, sample Z ~ N(0, R) using Cholesky decomposition
3. Convert to uniform marginals: U = Φ(Z) where Φ is the standard normal CDF
4. Map back to stat space via the inverse quantile CDF for each leg
5. Evaluate the joint event P(stat₁ > L₁, stat₂ > L₂, ...) as the empirical frequency across N = 50,000 Monte Carlo samples

**Why residual-based correlation:** Raw correlations between points and assists overstate the true within-distribution correlation because they are driven by shared exposure to minutes variance. A player who plays 38 minutes tends to score and assist more than in 22 minutes — but this is a minutes effect, not a structural PTS-AST relationship. Residual z-scores partial out the minutes effect and capture the remaining co-movement.

### Cholesky Decomposition and PSD Enforcement

The sampled correlation matrix may not be positive semi-definite when estimated on limited data. Before Cholesky decomposition:

```python
R_psd = nearestPD(R)  # Higham's algorithm via scipy
L = np.linalg.cholesky(R_psd)
Z = np.random.standard_normal((50_000, n_legs)) @ L.T
```

The nearest PSD projection ensures valid decomposition without distorting the correlation structure more than necessary.

---

## 8. Post-Hoc Isotonic Calibration

### Motivation

LightGBM quantile models trained at τ = 0.75 should, in theory, produce predictions where the actual stat exceeds the prediction exactly 25% of the time (the over-probability at Q75 is 0.25). In practice, calibration error varies by stat.

Right-skewed distributions (fg3m, stl, blk) are systematically miscalibrated at the tails: the Q90 prediction is too conservative, making the model underestimate the probability of extreme outcomes.

### Method

`calibrate_models.py` fits an **isotonic regression** on graded picks:

```
x: raw model probability for each graded pick
y: empirical outcome (1 = hit, 0 = miss)
```

Isotonic regression finds the best-fit monotone non-decreasing step function mapping raw probabilities to empirical hit rates. This is strictly more expressive than temperature scaling (which applies a single global scalar) while remaining monotone (preserving the probability ordering).

**Brier score gating:** The calibrator is saved only if it improves Brier score on a held-out portion of graded picks. If isotonic regression overfits the graded sample (common when fewer than 50 picks per stat are available), the raw model is used unchanged. This requires approximately 8–10 weeks of live data before calibrators are reliable.

---

## 9. Live In-Play Engine

### Bayesian Distribution Update

Rather than linear pace extrapolation (`projected = current_stat / minutes_played × 36`), the live engine shifts the pregame quantile distribution proportionally based on the observed per-minute rate.

The blended live rate uses a **Bayesian trust weight**:

```
trust = minutes_played / (minutes_played + 15)

live_rate     = stat_current / minutes_played
pregame_rate  = q50_pregame / exp_minutes_pregame

blended_rate  = trust × live_rate + (1 − trust) × pregame_rate

live_proj     = blended_rate × (minutes_played + minutes_remaining)
scale_factor  = live_proj / pregame_proj

q_live[τ] = q_pregame[τ] × scale_factor  for all τ
```

The trust weight of 15 means that at 15 minutes played (roughly halftime), observed and pregame rates are weighted equally. With fewer minutes of evidence the pregame prior dominates; with more, the observed rate dominates.

**Why not linear extrapolation:** Linear pace extrapolation assumes (a) the per-minute rate is perfectly stationary, and (b) variance around the final outcome is symmetric. Both are false. A player who has scored 18 points in 15 minutes on 40% field goal shooting is more likely to regress than to maintain that rate. The Bayesian approach starts from the pregame distribution — which encodes the player's historical variance, skewness, and typical floor/ceiling — and shifts it proportionally rather than replacing it.

**Context adjustments applied before scaling:**

- **Foul trouble:** minutes distribution is shifted down by `fouls × 3.5` minutes expected lost
- **Blowout:** pregame minutes are multiplied by 0.75 when point differential exceeds 20
- **Live pace:** scale factor adjusted by observed possession rate vs. league average

---

## 10. Closing Line Value — Primary Performance Metric

CLV is computed nightly for every graded pick:

```
CLV_over  = P_model(over)  − P_closing_over_fair
CLV_under = P_model(under) − P_closing_under_fair
```

where `P_closing_*_fair` is the vig-removed implied probability from the closing line snapshot taken at 7 PM ET by `snapshot_closing_lines.py`.

**Interpretation:** Positive CLV means the model assigned higher probability to an outcome than where the sharpest participants drove the final price. Consistently positive mean CLV is the most reliable indicator that the model is finding genuine inefficiencies rather than exploiting short-term variance.

**Known calibration issue (live since 2026-03-10):** OVER picks show mean CLV of +10.3% and UNDER picks show mean CLV of −14.1% across the first graded week. This reflects systematic UNDER bias — the model over-bets UNDER positions that the market subsequently steams toward OVER. This is consistent with retail OVER volume in player prop markets driving post-pick line movement against UNDER positions. The isotonic calibration pipeline is designed to correct this once sufficient graded data accumulates (~50+ UNDER picks per stat). An interim fix is an OVER-side weighting filter at inference time, which is tracked in the improvement backlog.

---

## 11. No Lines in Training

The model is trained entirely on game outcomes — actual box score statistics. Sportsbook odds are used only at inference time to compute EV against the model's distribution.

This is a deliberate architectural choice. A model trained on odds data learns to mirror the market's probability estimates rather than form independent forecasts. Such a model would have near-zero CLV by construction — it would reproduce the market's opinion, not find departures from it. The system's value comes entirely from its independent distribution estimates being better calibrated than the public market in specific situations (injury-adjusted environments, unusual lineup configurations, sharp line movement in the same direction as the model).

---

## 12. Known Limitations

**Data:** BallDontLie API v2 provides box scores and advanced tracking data but does not include second-spectrum player tracking, SportVU data, or defensive matchup assignments at the player level. These would materially improve the blocks, steals, and 3-pointers models.

**Calibration sample size:** Isotonic calibrators are not reliable until approximately 50+ graded picks per stat. Full calibration requires an entire season of live predictions (~4–5 months). Current calibrators are held out until this threshold is met.

**Odds coverage:** The Odds API provides coverage for DraftKings, FanDuel, and BetMGM reliably. Coverage for Bovada, BetUS, and BetOnline is inconsistent. This limits the ability to find the best available line for each pick.

**Live engine pace model:** The current live engine uses a single linear trust weight. A proper Kalman filter would update the rate estimate with uncertainty bounds that shrink as more evidence accumulates, rather than the fixed 15-minute prior weight.

**SGP combinatorics:** With 400+ singles, naive SGP generation is computationally infeasible. The current system caps the SGP candidate pool to the top 6 picks by EV per game before running the copula simulation. This misses potentially optimal cross-game combinations but prevents 30-minute GitHub Actions timeouts.
