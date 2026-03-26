# NBA Player Props Model

Automated NBA player props prediction system built for market-maker portfolio development. Identifies positive expected value betting opportunities by comparing model probabilities to sportsbook odds.

**Live dashboard:** dev.wizardofodds.com/tools/odds-scanner/predictions/nba-live-props.html

**API endpoint:** dev.wizardofodds.com/tools/odds-scanner/predictions/api/live_props.php?mode=pregame

## Architecture

Four-layer pipeline:

**1. Projection layer** — LightGBM quantile regression ensemble (11 quantile models per stat) producing a full P10→P90 distribution per player/stat/game.

**2. Residual centering layer** — Per-stat bias correction trained on median(actual - q50) from 2,737 graded rows. Minutes-bucket-aware corrections for buckets 1+2 (75% application for pts). `residual_centering.py` is the permanent learned replacement for hardcoded corrections.

**3. Probability layer** — Converts projected distribution to fair probability at the posted line using vig-free market math and 12 stat×side Platt calibrators.

**4. Deployment layer** — Hard pre-export assertions blocking banned markets, side-specific EV thresholds, probability bounds, bad-line sanity checks, portfolio caps.

## Daily Pipeline

| Time (ET) | Job | Purpose |
|---|---|---|
| 8:00 AM | predict | Grade yesterday, generate today's predictions |
| 9:00 AM | snapshot_opening | Capture opening lines |
| 6:00 PM | snapshot_closing | Capture closing lines post-injury-report |

The predict job is independent — snapshot failures never cause predictions to skip. The workflow hard-fails with a visible red Action if singles_YYYY-MM-DD.json is not written.

**Required GitHub Secrets:** `BDL_API_KEY`, `ODDS_API_KEY`

## Model Details

**Stats:** PTS, REB, AST, FG3M, STL, BLK, TOV, PRA, PR, PA, RA, STL+BLK

**Ensemble:** LightGBM quantile regression (11 quantile levels per stat) + XGBoost, Random Forest, Gradient Boosting, Neural Network with Bayesian Ridge meta-learner.

**SGPs:** Gaussian copula with within-player correlation engine. Capped at 6 singles/game, 60 total candidates.

**Kelly sizing:** Quarter-Kelly pregame (0.25), eighth-Kelly live (0.125).

## Bias Corrections (v15 — learned 2026-03-26)

Fitted from median(actual - q50) on 2,737 graded rows using GradientBoostingRegressor per stat. Applied to the full quantile ladder.

| Stat | Correction | Source |
|---|---|---|
| pts | +1.135 | learned: GBR on 534 graded rows; +75% minutes-bucket correction buckets 1+2 |
| ast | +0.190 | learned: GBR on 483 graded rows |
| reb | +0.010 | learned: near-zero confirmed |
| fg3m | -0.010 | learned: no material correction |
| blk | 0.00 | not corrected — targets disagree directionally |
| stl | 0.00 | not corrected — targets disagree directionally |

Run `python3 residual_centering.py --train` after each retrain to update these values.

## Deployment Gates (v15)

**OVER:** probability >= 0.56-0.60 (stat-specific), EV >= 2.5%

**UNDER (restricted):**

| Stat | Min prob | Min EV |
|---|---|---|
| pts | 0.72 | 6.0% |
| ast | 0.70 | 5.0% |
| reb | BANNED | — |
| fg3m | BANNED | — |

**Permanently banned:** STL OVER, BLK OVER, REB UNDER, FG3M UNDER, STL UNDER

**Suppressed:** PTS UNDER, AST UNDER, FG3M OVER, BLK UNDER

**Hard pre-export assertion:** Any banned market reaching the export step is removed and logged as an ASSERTION FAILED error. The gate is binding at the code level.

Additional filters: bad-line filter (line > q50 x 1.75), alt-line guard (pts q50 < 17 and line > q50 x 1.5), min Q50 floors (pts >= 12, reb >= 3.5, ast >= 2.5), MIN_GAMES_SEASON = 20.

Portfolio caps: max 25/day, max 2/player, max 4/game, max 1/player/stat.

## Performance (v15 deployment era, 2026-03-20 to present)

| Metric | Value |
|---|---|
| Graded picks | 26 |
| Hit rate | 69.2% |
| Mean CLV | +4.51% |
| CLV+ % | 76.9% |
| Brier score | 0.2178 |
| Max drawdown | 6.80 units |

CLV (Closing Line Value) is the primary metric. Positive CLV means the model consistently prices props better than the closing line — the professional standard for demonstrating genuine edge.

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
python3 minutes_bias_fix.py
```

## Data Sources

- **BallDontLie API** (GOAT tier) — stats, box scores, live data, injuries, lineups, webhooks
- **The Odds API** — sportsbook odds for line snapshots and CLV measurement
