# NBA Props Model

Automated NBA player props prediction system built for market-maker portfolio development. Identifies positive expected value betting opportunities by comparing model probabilities to sportsbook odds.

**Live dashboard:** [dev.wizardofodds.com/tools/odds-scanner/predictions/nba-live-props.html](https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-live-props.html)

**API endpoint:** [dev.wizardofodds.com/tools/odds-scanner/predictions/api/live_props.php?mode=pregame](https://dev.wizardofodds.com/tools/odds-scanner/predictions/api/live_props.php?mode=pregame)

---

## Architecture

Four-layer pipeline:

**1. Projection layer** — LightGBM quantile regression ensemble (11 quantile models per stat) producing a full P10→P90 distribution per player/stat/game.

**2. Residual centering layer** — Per-stat bias correction trained on `median(actual - q50)` from graded outcomes. Shifts the entire quantile ladder consistently. `residual_centering.py` is the permanent learned replacement for hardcoded corrections.

**3. Probability layer** — Converts projected distribution to fair probability at the posted line using vig-free market math and stat×side Platt calibration.

**4. Deployment layer** — Side-specific EV thresholds, probability bounds, line-gap filters, bad-line sanity checks (skip if `line > q50 × 2.5`), portfolio caps (max 25 total, max 2/player, max 4/game, max 1/player/stat).

---

## Repository Structure

```
.github/workflows/
    daily_predictions.yml     Pipeline: 8AM predict, 9AM/6PM snapshots
    retrain.yml               Weekly retrain

data/
    opening_lines_*.json      Opening line snapshots

graded/
    graded_2026-*.csv         Daily graded results
    closing_lines_*.json      Closing lines for CLV measurement
    performance_log.csv       Aggregated performance metrics
    cumulative_report.json    Running portfolio summary

model_cache/
    *.pkl                     Trained LightGBM quantile models
    platt_OVER.pkl            Global OVER Platt calibrator
    platt_UNDER.pkl           Global UNDER Platt calibrator

predictions/
    singles_YYYY-MM-DD.json   Daily picks with full quantile distributions
    sgps_YYYY-MM-DD.json      Same-game parlay candidates (Gaussian copula)
    paper_trade_log.csv       Paper trade log

bdl_client.py                 BallDontLie API client
calibrate_models.py           Global Platt calibration
calibrate_stat_side.py        Stat×side calibration file generator
calibrate_statside.py         Legacy calibration script
correlation_engine.py         Within-player correlation for SGP generation
feature_engineering.py        Feature construction pipeline
grade.py                      Daily grader
live_pricing.py               Python live pricing engine
minutes_model.py              Minutes projection model
predict.py                    Workflow target (copy of predict_darko_v4.py)
predict_darko_v4.py           Main prediction script
replay_live.py                Live CLV backtest tool
residual_centering.py         Learned residual corrector (permanent bias fix)
snapshot_closing_lines.py     Closing line snapshots
snapshot_opening_lines.py     Opening line snapshots
state_bucket_calibration.py   Live state-bucket calibration
train.py                      Training script
```

---

## Daily Pipeline

| Time (ET) | Job | Purpose |
|---|---|---|
| 8:00 AM | `predict` | Grade yesterday, generate today's predictions |
| 9:00 AM | `snapshot_opening` | Capture opening lines |
| 6:00 PM | `snapshot_closing` | Capture closing lines post-injury-report |

The `predict` job is independent — snapshot failures never cause predictions to skip. The workflow hard-fails with a visible red Action if `singles_YYYY-MM-DD.json` is not written.

**Required GitHub Secrets:**
- `BDL_API_KEY` — BallDontLie GOAT tier key
- `ODDS_API_KEY` — The Odds API key

---

## Model Details

**Stats:** PTS, REB, AST, FG3M, STL, BLK, TOV, PRA, PR, PA, RA, STL+BLK

**Ensemble:** LightGBM quantile regression (11 quantile levels per stat) + XGBoost, Random Forest, Gradient Boosting, Neural Network with Bayesian Ridge meta-learner.

**SGPs:** Gaussian copula with within-player correlation engine. Capped at 6 singles/game, 60 total candidates.

**Kelly sizing:** Quarter-Kelly pregame (0.25), eighth-Kelly live (0.125).

---

## Bias Corrections

Fitted from `median(actual - q50)` on 2,624 graded rows. Applied to the full quantile ladder (all quantiles shift equally). `blk` and `stl` are not corrected — their two targets disagree directionally.

| Stat | Correction |
|---|---|
| pts | +1.50 |
| ast | +0.57 |
| reb | +0.29 |
| fg3m | +0.50 |
| blk | 0.00 |
| stl | 0.00 |

Run `python3 residual_centering.py --train` after each retrain to replace these hardcoded values with learned per-stat models.

---

## Deployment Gates

**OVER:** probability ≥ 0.60, EV ≥ 2.5%

**UNDER:**

| Stat | Min prob | Min line-q50 gap | Min EV |
|---|---|---|---|
| pts | 0.72 | 1.25 | 6.0% |
| ast | 0.70 | 0.75 | 5.0% |
| reb | 0.67 | 0.60 | 5.0% |
| fg3m | 0.66 | 0.50 | 5.0% |
| blk | 0.74 | — | 7.0% |

**Permanently banned:** STL OVER (HR 0.216), BLK OVER (HR 0.260), STL UNDER (CLV -0.073)

---

## Performance (2026-03-09 to 2026-03-17, 2,624 graded rows)

| Stat | Side | n | Hit Rate | CLV |
|---|---|---|---|---|
| pts | OVER | 190 | 0.489 | +0.086 |
| pts | UNDER | 306 | 0.438 | -0.102 |
| ast | OVER | 147 | 0.408 | +0.093 |
| reb | OVER | 210 | 0.452 | +0.103 |
| reb | UNDER | 306 | 0.464 | -0.112 |
| blk | OVER | 269 | 0.260 | +0.094 |

OVER CLV is positive across all major stats. UNDER CLV is negative — under deployment is restricted until residual centering and stat×side calibration are fully deployed.

---

## Remaining Build Items

1. Run `python3 residual_centering.py --train` after each retrain — replaces hardcoded bias corrections with learned GBR models per stat
2. Run `python3 calibrate_stat_side.py` — generates `platt_pts_OVER.pkl` etc.; currently falls back to global calibrators
3. Affiliate sub-IDs — placeholder `WOO` in all links; real IDs needed from affiliate partner
4. Cron job for `quote_archive.php` — needs server-side cron every minute during games for live CLV tracking
5. Separate sparse models for BLK/STL — these stats need zero-inflated discrete treatment

---

## Setup

```bash
git clone https://github.com/Risky-Scout/nba-player-props-model
cd nba-player-props-model
pip install lightgbm scikit-learn pandas numpy requests pyarrow joblib scipy

export BDL_API_KEY=your_key
python3 predict_darko_v4.py

# After retrain:
python3 residual_centering.py --train
python3 calibrate_stat_side.py
```

---

## Data Sources

- **BallDontLie API** (GOAT tier) — stats, box scores, live data, injuries, lineups, webhooks
- **The Odds API** — sportsbook odds for line snapshots and CLV measurement
