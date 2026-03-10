# NBA Player Props Model

**Automated quantile regression system for pricing NBA player proposition bets.**

Live at [dev.wizardofodds.com](https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-props.html)

---

## What It Does

This system builds a full probability distribution over each player's stat outcome for every game, compares that distribution to posted sportsbook lines, and identifies edges where the model's fair probability diverges from the no-vig market implied probability.

It is not a point estimate model. It prices lines.

---

## Architecture

### Training (`train_v12.py`)

- **Targets:** `pts`, `reb`, `ast`, `fg3m`, `stl`, `blk`, `tov`, and five combination stats (`pra`, `pr`, `pa`, `ra`, `stocks`) — 12 targets total
- **Models per target:** 11 LightGBM quantile regressors, Q10 through Q90, trained with pinball loss
- **Ensemble:** XGBoost, Random Forest, Gradient Boosting, and Neural Network with a Bayesian Ridge meta-learner on top of the LightGBM quantiles
- **Validation:** Temporal holdout — split at the (1 − 0.15) date percentile, never on random rows. Reports calibration error per quantile and MAE at Q50
- **Data:** BallDontLie API (GOAT tier), incremental fetch — only new games are pulled on each run
- **Training seasons:** 2023–2025

### Feature Engineering (`feature_engineering.py`)

Features are computed as-of the game date using only prior data. No leakage.

**Rolling windows per stat series (13 features each):**
- `mean_last5`, `mean_last10`, `median_last10`, `mean_last3`
- `std_last10`, `cv_last10` (coefficient of variation)
- `trend_3v10` (mean_last3 / mean_last10 — recency drift signal)
- `floor_last10` (P10), `ceiling_last10` (P90)
- `ewma` (alpha=0.3 — last game weighted at 30%)
- `mean_season` (EWMA-weighted full season)
- `games_in_window`, per-minute rate

**Minutes model features:**
- `starter_rate`, `games_30plus`, `games_35plus`, `games_20minus`, `role_stability_index`

**Advanced stats (34 BDL v2 fields, EWMA-rolled):**
- Usage percentage, pace, true shooting, eFG, assist/turnover ratio
- Touches, passes, rebound chances, deflections, contested shots
- Defended-at-rim, secondary assists, fouls drawn, matchup data

**Vacated opportunity features (role-conditioned):**
- Guard vs. big classification
- `vacated_guard_minutes`, `vacated_big_minutes`
- `vacated_creation_share`, `vacated_reb_share`
- Populated from live injury map at inference time

**Stat-specific upper-tail features:**
- Steals/blocks: `p_ge1_last10` (probability of 1+ in last 10)
- Threes: `fg3a_attempt_trend`, `is_low_3pa_last10`, `p_zero_last10`

**Game context:**
- `game_total`, `implied_team_total`, `opp_implied_total`
- `opp_pace_context`, `opp_defense_signal`
- `is_home`, `days_rest`, `b2b_flag`

**Injury snapshots:**
- Daily snapshot saved to `data/injury_snapshots.parquet` on each training run
- Historical rows before snapshot accumulation have `injury_map = {}` (BDL has no historical injury API)
- At inference, the live injury map is always populated

### Prediction (`predict_v12.py`)

For each player-game on today's slate:

1. Build the full feature vector using prior stats + today's game context + live injury map
2. Load all 11 quantile models for each target
3. Enforce monotonicity across Q10–Q90 (corrects quantile crossing)
4. Interpolate a full CDF from the quantile predictions
5. For each sportsbook line: read off `P(over)` and `P(under)` directly from the CDF
6. Remove vig from posted market odds (additive method)
7. Compute `edge = model_probability − no_vig_implied_probability`
8. Compute `EV = edge × (odds − 1) − (1 − edge)`
9. Compute Kelly fraction: `f* = (bp − q) / b`
10. Output picks with `edge`, `ev`, `kelly`, `fair_odds`, `model_prob`, `market_prob`

The model prices any line without retraining — the CDF is continuous.

### SGP Correlation Engine (`correlation_engine.py`)

Same-game parlay pricing requires joint probability estimation. Independent multiplication is wrong for correlated player stats.

**Method:**
- Compute residual z-scores from Q25/Q50/Q75 predictions for each stat
- Fit within-player correlation matrices segmented by usage bucket and minutes bucket
- Shrink toward a global prior (prevents overfitting on thin player samples)
- Enforce positive semi-definiteness via eigenvalue clipping
- Simulate joint outcomes via Gaussian copula
- SGP probability = fraction of simulations where all legs clear their lines

**Teammate correlations** are also modeled — a player's usage and shot volume are not independent of how teammates are performing.

### Grading (`grade_v12.py`)

After each game slate completes, the grader:

- Loads `predictions/singles_{date}.json`
- Fetches final box scores from BDL
- Records `result` (win/loss/push), `actual`, `line`, and `clv` (Closing Line Value)
- Appends to `graded/performance_log.csv`

**CLV is the primary long-term metric.** Beating the closing line at a positive rate is the most reliable indicator that the model is finding real inefficiencies rather than overfitting to historical patterns.

---

## Pipeline

Fully automated via GitHub Actions on a daily schedule.

```
06:00 AM ET  →  train_v12.py       (incremental data fetch + retrain)
08:00 AM ET  →  predict_v12.py     (today's slate → predictions JSON)
11:00 PM ET  →  grade_v12.py       (grade yesterday's picks)
```

Prediction output is committed directly to the repo. The frontend fetches from `raw.githubusercontent.com` — no manual deployment required.

**SGP stability gate:** If the singles count exceeds ~400, SGP generation is bypassed (`SKIP_SGPS=1`) to prevent combinatorial explosion and workflow timeout.

---

## Repository Structure

```
nba-player-props-model/
├── .github/workflows/
│   └── daily_predictions.yml     # GitHub Actions pipeline
├── data/
│   ├── player_game_stats.parquet
│   ├── advanced_stats.parquet
│   ├── game_odds.parquet
│   └── injury_snapshots.parquet
├── model_cache/
│   ├── q10_pts.pkl … q90_pts.pkl  # 11 quantile models × 12 targets = 132 models
│   ├── features_{target}.pkl      # Feature column lists per target
│   ├── feature_importance_{target}.csv
│   ├── within_player_corr_engine.pkl
│   └── training_meta.json
├── predictions/
│   ├── singles_{date}.json
│   └── sgps_{date}.json
├── graded/
│   └── performance_log.csv
├── train_v12.py
├── predict_v12.py
├── grade_v12.py
├── feature_engineering.py
├── correlation_engine.py
├── bdl_client.py
└── requirements.txt
```

---

## Output Format

Each pick in `singles_{date}.json`:

```json
{
  "player":        "Jayson Tatum",
  "team":          "BOS",
  "stat":          "pts",
  "line":          27.5,
  "side":          "over",
  "model_prob":    0.587,
  "market_prob":   0.476,
  "edge":          0.111,
  "ev":            0.083,
  "kelly":         0.047,
  "fair_odds":     -142,
  "posted_odds":   -110,
  "q10":           14.2,
  "q50":           28.8,
  "q90":           43.1
}
```

---

## Tech Stack

| Component | Technology |
|---|---|
| ML models | LightGBM (quantile), XGBoost, Random Forest, Neural Network |
| Meta-learner | Bayesian Ridge |
| Correlation engine | Gaussian copula |
| Data source | BallDontLie API v2 (GOAT tier) |
| Automation | GitHub Actions |
| Backend | PHP (live blend of pregame + BDL box scores) |
| Frontend | Vanilla JS, Bloomberg terminal style |
| Deployment | raw.githubusercontent.com → PHP cache → browser |

---

## Setup

```bash
git clone https://github.com/Risky-Scout/nba-player-props-model.git
cd nba-player-props-model
pip install -r requirements.txt
export BDL_API_KEY=your_key_here

# Full retrain
python train_v12.py

# Today's predictions (requires trained models)
python predict_v12.py

# Grade yesterday
python grade_v12.py
```

**Required secret in GitHub Actions:** `BDL_API_KEY`

---

## What Is Not Claimed

- No backtest P&L is reported. CLV is the primary validation metric because backtest returns depend on line shopping and stake sizing, not model quality alone.
- Injury features are NaN in training for historical rows. The vacated-opportunity block is populated at inference using the live injury map. As the daily snapshot table accumulates, training will progressively incorporate real injury state.
- SGP output is disabled by default in the live pipeline pending further validation of the correlation engine on live samples.

---

## License

MIT
