# NBA Player Props Prediction Model

A production-grade probabilistic forecasting system for NBA player proposition bets. The model generates full outcome distributions — not point estimates — for six individual stat markets daily, identifying positive expected value opportunities by comparing model-implied probabilities against sportsbook closing lines.

Built as a market-maker portfolio project. The system runs autonomously via GitHub Actions, grading itself each morning and tracking Closing Line Value as the primary performance metric.

Live predictions served at [dev.wizardofodds.com](https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-props.html).

---

## Architecture Overview

```
BallDontLie API  ──►  feature_engineering.py  ──►  train_v12.py
                                                         │
                              ┌──────────────────────────┘
                              ▼
                       predict_darko_v4.py  ──►  predictions/singles_{date}.json
                                                         │
                  snapshot_closing_lines.py              │  (7 PM ET)
                              │                          │
                              ▼                          ▼
                   graded/closing_lines_{date}.json ──► grade_darko_v4.py
                                                         │
                                                         ▼
                                              graded/performance_log.csv
                                                         │
                                                         ▼
                                              calibrate_models.py  (weekly)
```

**Automation:** Two GitHub Actions jobs run daily — a prediction job at 8 AM ET and a closing line snapshot at 7 PM ET before NBA tipoffs. All outputs commit directly to the repo and are served to the frontend via GitHub raw URLs.

---

## Modeling Approach

### Quantile Regression Ensemble

Each stat target is modeled with **11 independent LightGBM quantile regressors** trained at τ ∈ {0.10, 0.20, 0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75, 0.80, 0.90}, minimizing pinball loss at each quantile. This produces a full predicted distribution per player per game rather than a single point estimate.

The Q50 prediction anchors the synthetic line. The implied probability that a player exceeds any given sportsbook line is derived by interpolating across the quantile distribution — the same mathematical framework used by quantitative sportsbooks to price their own markets.

### Two-Stage Minutes Model

Minutes played is the dominant multiplier for all counting stats. Rather than treating minutes as a feature input from historical averages alone, the system trains a **dedicated upstream minutes model** (`minutes_model.py`) that outputs a full minutes distribution (Q10–Q90) before any stat model runs. These quantile outputs — `exp_mp`, `mp_q25`, `mp_q75`, `mp_vol`, and four more — are injected as first-class features into every downstream stat model.

This separation means the stat models learn conditional on an expected minutes distribution, not just a historical rolling mean.

### Post-Hoc Isotonic Calibration

Raw quantile model outputs are systematically overconfident at the tails for right-skewed distributions (fg3m, stl, blk). `calibrate_models.py` fits an **isotonic regression calibrator** per stat on graded results from `performance_log.csv`, mapping raw model probabilities to empirically calibrated probabilities. Calibrators are only saved when they improve Brier score on held-out picks — otherwise the raw model is used. This runs as a post-processing step and never requires retraining.

### Holdout and Leakage Prevention

Training uses a **strict temporal split**: the most recent 15% of dates form the holdout set. No shuffling. Every feature is computed using only games prior to the target game date. Advanced stats, injury snapshots, and opponent context are all filtered to pre-game data before feature construction.

### Stat-Specific Feature Gates

Each of the 12 stat targets (pts, reb, ast, fg3m, stl, blk, tov, pra, pr, pa, ra, stocks) uses a curated feature subset defined in `get_feature_cols_for_stat()`. Features are gated by relevance — the rebounds model does not receive three-point shooting history; the assists model does not receive rim-protection features. This prevents spurious correlations and reduces overfitting on smaller sparse-stat samples.

---

## Feature Engineering

Feature construction is handled entirely in `feature_engineering.py`. All features are computed per-player per-game with no lookahead.

### Minutes & Role Block
- Rolling means: last 3, 5, 10 games; season mean
- Volatility: standard deviation, coefficient of variation, IQR/median ratio
- EWMA (α = 0.3) and trend signal (mean\_last3 / mean\_last10)
- Quantile floor/ceiling: P10 and P90 of last-10 distribution
- Starter rate, games above/below minute thresholds, role stability index

### Per-Minute Rate Rolling (13 stats × 12 features)
All counting stats are converted to per-minute rates before rolling aggregation, removing the confound between volume and rate. Both per-minute rates and raw counts are included — rates capture efficiency, raw counts capture role volume.

### Advanced Stats Block (34 BDL fields)
Rolling last-10 mean and EWMA for: usage percentage, assist percentage, pace, true shooting, effective FG%, touches, passes, secondary assists, deflections, rebound chances (total/offensive/defensive), contested shots, matchup turnovers, and 20+ additional tracking fields.

### Line Movement (Sharp Money Signal)
Open-to-close line movement is one of the strongest predictors available to a market maker. When sharp money hits a side, the market moves. The magnitude and direction of that movement reveals which side the market respects. Ten line movement features are computed per game:

| Feature | Signal |
|---|---|
| `total_move` | Game total open → close delta |
| `spread_move` | Spread open → close delta |
| `total_move_abs` | Magnitude of total movement |
| `spread_move_abs` | Magnitude of spread movement |
| `total_move_dir` | +1 steamed up, −1 steamed down |
| `spread_move_dir` | Direction of spread steam |
| `sharp_action_flag` | 1 if total moved >1.5 or spread moved >1.0 |
| `has_line_movement` | Data availability flag |

All features are NaN-safe — LightGBM handles missing data natively for games without opening line history.

### Opponent Environment
Rolling 10-game defensive profile of the opponent team, computed from opponent box scores with strict no-leakage date filtering:

| Feature | Used by |
|---|---|
| `opp_reb_chances_allowed` | Rebounds model |
| `opp_oreb_chances_allowed` | Rebounds model |
| `opp_dreb_chances_allowed` | Rebounds model |
| `opp_ast_opportunities` | Assists model |
| `opp_pts_allowed` | Assists model |
| `opp_3pa_allowed` | 3-pointers model |
| `opp_3pm_allowed` | 3-pointers model |
| `opp_3p_rate_allowed` | 3-pointers model |
| `opp_pace_true` | Rebounds, assists, 3-pointers |

### Injury-Aware Vacated Opportunity
When teammates are ruled out, their statistical production redistributes. The system reads a daily injury snapshot and computes 15 role-conditioned opportunity features per player:

- `vacated_minutes` — total minutes lost by inactive teammates
- `vacated_fga`, `vacated_pts`, `vacated_ast`, `vacated_reb` — production vacated by inactive teammates
- `vacated_guard_minutes` / `vacated_big_minutes` — role-classified vacancy (guards affect AST, bigs affect REB)
- `vacated_creation_share`, `vacated_reb_share` — relative redistribution magnitude
- `num_teammates_inactive`, `has_injury_data`

### Game Context & Odds Features
- Implied team total and opponent implied total (derived from consensus spread using correct sportsbook sign convention)
- Game total, spread for team, blowout risk
- Interaction terms: usage × implied team total, FGA rate × implied team total
- Schedule features: rest days, back-to-back, three-in-four, games last 7

---

## Closing Line Value Tracking

CLV is the primary long-term performance metric — more informative than win rate because it measures edge against the sharpest available price rather than against a binary outcome.

Each evening at 7 PM ET, `snapshot_closing_lines.py` fetches player prop markets across DraftKings, FanDuel, BetMGM, BetRivers, and others. Vig is removed using the standard multiplicative method to produce fair implied probabilities, stored in `graded/closing_lines_{date}.json`.

The following morning, `grade_darko_v4.py` computes true CLV for each graded pick:

```
CLV (OVER)  = model_probability − fair_closing_over_probability
CLV (UNDER) = (1 − model_probability) − fair_closing_under_probability
```

Positive CLV means the model assigned higher probability to the outcome than where the closing market settled — the model was on the right side of where sharp money moved the line.

---

## Live In-Play Engine

`live_props.php` blends pregame model output with real-time BDL box scores using a **Bayesian quantile distribution update** — not linear pace extrapolation.

### How It Works

The pregame model outputs a full Q10–Q90 distribution per player. At any point during a live game, rather than projecting a final number and running a normal CDF around it, the live engine:

1. Computes a Bayesian blended rate: `trust = minutes_played / (minutes_played + 15)`, blending the pregame per-minute rate with the observed in-game rate
2. Applies context factors: foul trouble (minutes reduction), live pace (possession rate vs. league average), blowout garbage time (minutes distribution shift)
3. Scales the entire pregame quantile distribution by `live_projection / pregame_projection`
4. Queries `P(stat > line)` from the shifted distribution using piecewise linear CDF interpolation

This preserves the shape of the pregame distribution — its variance, skewness, and tail behavior — while updating the location parameter based on live evidence. A player's shifted Q10–Q90 in a blowout is narrower and lower than the pregame distribution, not just a truncated normal approximation.

### Webhook Infrastructure

`webhook_receiver.php` processes BDL play-by-play events (scores, rebounds, assists, fouls, injuries) in real time. The receiver includes:
- **Signature validation** — HMAC-SHA256 verification of all incoming payloads
- **Rate limiting** — 120 events per 60-second window per IP, with 429 responses and retry-after headers
- **Staleness detection** — rejects events with timestamps older than 5 minutes to prevent delayed replay
- **Duplicate deduplication** — event ID tracking prevents double-processing within a 5-minute window

---

## Performance (Holdout Metrics)

Training data: 2023–2025 NBA seasons · 56,438 training rows · 9,960 holdout rows · Temporal split

| Stat | Features | Holdout MAE | Max Calibration Error |
|------|----------|-------------|----------------------|
| Points | 79 | 4.53 | 0.033 |
| Rebounds | 80 | 1.92 | 0.036 |
| Assists | 79 | 1.34 | 0.040 |
| 3-Pointers Made | 65 | 0.86 | 0.075 |
| Steals | 60 | 0.68 | 0.022 |
| Blocks | 61 | 0.43 | 0.021 |
| Turnovers | 61 | 0.87 | 0.032 |
| PRA | 70 | 5.97 | 0.029 |

Calibration error is the maximum absolute deviation between predicted quantile and empirical quantile on the holdout set across all 11 quantile levels. Post-hoc isotonic calibration (`calibrate_models.py`) reduces this further as live performance data accumulates.

Live CLV tracking began March 10, 2026. Full results accumulate in `graded/performance_log.csv`.

---

## Repository Structure

```
├── train_v12.py                  # Training — minutes model first, then 12 stat models
├── predict_darko_v4.py           # Daily inference — generates singles_{date}.json
├── grade_darko_v4.py             # Grader — CLV, ROI, calibration tracking
├── calibrate_models.py           # Post-hoc isotonic calibration per stat
├── snapshot_closing_lines.py     # 7 PM ET closing line snapshot for true CLV
├── feature_engineering.py        # All feature construction (zero leakage)
├── minutes_model.py              # Standalone quantile minutes engine
├── bdl_client.py                 # BallDontLie API v2 client
├── correlation_engine.py         # Gaussian copula SGP correlation modeling
├── live_props.php                # Live in-play Bayesian distribution update engine
├── webhook_receiver.php          # BDL play-by-play event processor (hardened)
├── METHODOLOGY.md                # Mathematical framework — pricing, calibration, copula
├── PERFORMANCE.md                # Live graded results with CLV breakdown
├── requirements.txt              # Pinned Python dependencies
├── .github/workflows/
│   ├── daily_predictions.yml     # Two-job automation: 8 AM predict + 7 PM snapshot
│   └── retrain.yml               # Manual retrain dispatch
├── predictions/
│   ├── nba-props.html            # Bloomberg terminal frontend
│   ├── singles_{date}.json       # Daily prop picks with full quantile distribution
│   └── sgps_{date}.json          # Same-game parlay correlations
├── graded/
│   ├── performance_log.csv       # Cumulative graded results with CLV
│   ├── closing_lines_{date}.json # Vig-removed closing line snapshots
│   └── graded_{date}.csv         # Per-date graded detail
└── model_cache/
    ├── q{τ}_{stat}.pkl           # 11 quantile models × 12 stat targets = 132 models
    ├── minutes_q{τ}.pkl          # 11 quantile models for the minutes engine
    ├── calibration_{stat}.pkl    # Isotonic calibration maps per stat
    ├── training_meta.json        # Holdout metrics, calibration, feature counts
    └── feature_importance_{stat}.csv
```

---

## Pipeline Details

### Training (`train_v12.py`)
1. Fetch 3 seasons of BDL player game logs and advanced stats
2. Load injury snapshot index from `data/injury_snapshots.parquet`
3. Train minutes model first — 11 quantile LightGBM models on 22 minutes-specific features
4. For each of 12 stat targets: build temporally-split feature matrix, train 11 quantile models, evaluate calibration and MAE, save to `model_cache/`

### Inference (`predict_darko_v4.py`)
1. Fetch today's games, injury report, and prop odds
2. Build full feature vector per player including live injury map, opponent environment, and line movement
3. Load trained quantile models and isotonic calibrators, generate calibrated Q10–Q90 distribution
4. Compare model probability at sportsbook line to market implied probability
5. Output positive-EV picks above Kelly threshold to `singles_{date}.json`

### Calibration (`calibrate_models.py`)
1. Load `performance_log.csv` — all graded picks with model probabilities and outcomes
2. Per stat: fit isotonic regression on raw model prob → empirical hit rate
3. Save calibrator only if Brier score improves — otherwise keep raw model
4. Evaluate reliability diagrams per stat (`--mode eval`)

### Grading (`grade_darko_v4.py`)
1. Load previous day's picks and closing line snapshot
2. Fetch actual stats from BDL
3. Compute result (HIT/MISS/PUSH), profit, and true CLV
4. Append to `performance_log.csv` and `cumulative_report.json`

---

## Stack

| Component | Technology |
|---|---|
| Modeling | LightGBM (quantile regression), scikit-learn (isotonic calibration) |
| Data | BallDontLie API v2 (GOAT tier), The Odds API |
| Automation | GitHub Actions (two-job daily schedule) |
| Language | Python 3.11 / PHP 8 |
| Storage | Parquet (training data), JSON (predictions/closing lines), CSV (performance log) |
| Frontend | PHP + vanilla JS, Bloomberg terminal aesthetic |

---

## Key Design Decisions

**Why quantile regression instead of classification?** Sportsbook lines move. A model that outputs a full distribution can price any line — not just the one posted at pick time. This matches how a market maker thinks: the distribution is the product, the line is a query against it.

**Why a separate minutes model?** Minutes are the highest-variance input to every counting stat. A player projected at 34 minutes who plays 22 due to foul trouble or a blowout completely invalidates a point projection. Modeling minutes as an upstream distribution allows downstream models to learn conditional on minutes uncertainty rather than absorbing it as unexplained noise.

**Why isotonic calibration instead of temperature scaling?** Temperature scaling applies a single global scalar to all predictions. Isotonic regression learns a non-parametric monotone mapping that can correct systematic biases at any point in the probability range — critical for sparse-event stats like blocks and steals where the raw model is poorly calibrated at the tails but well-calibrated in the middle.

**Why Bayesian distribution shift for live updates instead of linear projection?** Linear extrapolation — `projected = (current / minutes_played) * 36` — assumes the per-minute rate is perfectly stationary and that the variance around the final outcome is symmetric. Neither is true. The Bayesian approach starts from the pregame distribution (which already encodes the player's variance, skewness, and tail behavior) and shifts it proportionally based on live evidence. A blowout that halves projected remaining minutes produces a narrower, lower distribution — not just a lower point estimate.

**Why CLV over win rate?** A 57% win rate on -110 lines is uninformative without knowing where those lines were when the bet was placed versus where they closed. CLV measures whether the model found edges that the sharpest market participants subsequently confirmed — the only signal that separates skill from variance over short samples.

**Why no lines in training?** The model trains on no sportsbook odds data. Odds are used only at inference time to compute EV against the model's distribution. This prevents the model from learning to mirror the market rather than forecast outcomes independently.
