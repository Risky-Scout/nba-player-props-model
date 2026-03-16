# NBA Props Model

**Research-grade probabilistic NBA player prop pricing system** with automated daily retraining, stat×side calibration, self-grading via Closing Line Value, and a live in-play model.

Built as a market-maker portfolio project targeting Sportradar / Pinnacle / FanDuel quant roles.

Live predictions: [dev.wizardofodds.com/tools/odds-scanner/predictions/nba-props.html](https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-props.html)

---

## Current Performance (Mar 9–15, 2026 — 1,978 graded picks)

| Metric | Value |
|--------|-------|
| OVER CLV | +9.8% |
| UNDER CLV | −11.5% |
| OVER Hit Rate | 43.1% |
| UNDER Hit Rate | 49.1% |

**Status:** The OVER side shows consistent positive CLV — a real pricing edge. The UNDER side remains structurally broken due to systematic q50 under-centering (pts −2.34, ast −0.82 below actual). This is the active repair priority.

**Line delta by stat (book line − model q50, lower = better):**

| Stat | Line Delta |
|------|-----------|
| pts | +1.015 |
| ast | +0.610 |
| blk | +0.377 |
| fg3m | +0.316 |
| reb | +0.313 |
| stl | +0.158 |

---

## Architecture

```
BallDontLie API (GOAT tier)
        │
        ▼
feature_engineering.py          ← 4-layer feature stack per stat
        │
        ▼
train_v12.py                    ← LightGBM quantile ensemble (11 quantiles × 13 targets)
        │                          opp_env_map built from stats_df (30 teams)
        ▼
model_cache/
  q10_{stat}.pkl  …  q90_{stat}.pkl   ← quantile models
  features_{stat}.pkl                  ← feature manifests
  calibration_{stat}.pkl               ← isotonic calibration per stat
  platt_over.pkl / platt_under.pkl     ← Platt scaling per side
        │
        ▼
predict_darko_v4.py             ← daily prediction engine
        │
        ├── predictions/singles_{date}.json     ← full pricing universe
        └── predictions/high_conviction_{date}.json  ← deployment subset
                │
                ▼ (grade_darko_v4.py — next morning)
        graded/performance_log.csv              ← CLV, HR, ROI by stat/side
        graded/retrain_report_{date}.json       ← red-flag audit artifact
```

**GitHub Actions (daily):**
- `09:00 ET` — opening line snapshot (sharp money baseline)
- `08:00 ET` — predict + grade + red-flag report
- `18:00 ET` — closing line snapshot (post-injury-report)
- Weekly — retrain on full history

---

## Feature Engineering — 4-Layer Stack

All six stat targets (pts, reb, ast, fg3m, blk, stl) share the same 4-layer architecture. Features are built by `build_player_game_features()` per player-game row.

### Layer 1 — Minutes / Availability
*Minutes played is the dominant multiplier for all counting stats.*

| Feature | Formula | Notes |
|---------|---------|-------|
| `mp_ewma_10` | EWMA(min, α=0.85, n=10) | Recency-weighted minutes estimate |
| `mp_mean_last10` | mean(min, last 10) | Rolling average |
| `mp_vol_last10` | std(min, last 10) | Rotation instability signal |
| `mp_trend_3v10` | mean(min[-3:]) / mean(min[-10:]) | Coach usage trend |
| `cv_min` | std/mean over season | Long-run consistency |
| `above_mean_pct_min` | % games above season avg min | Role signal |
| `games_20minus_last10` | Count of <20 min games in last 10 | DNP/bench risk |

### Layer 2 — Possession Environment
*Game-level context + stat-specific opponent defensive features.*

**Game context (all stats):**
- `implied_team_total` — team's expected score from spread + total
- `consensus_total` — market game total
- `market_pace_proxy` — possession proxy from odds
- `spread_for_team` — team spread
- `is_home` — home court flag

**Opponent defensive context (stat-specific, EWMA last 10 games):**

| Stat | Opponent Features | Causal Logic |
|------|------------------|--------------|
| pts | `opp_allowed_pts_ewma`, `opp_allowed_pts_mean`, `opp_allowed_pts_factor` | Weak defense → scoring opportunity |
| reb | `opp_allowed_reb_ewma`, `opp_allowed_reb_mean`, `opp_allowed_reb_factor` | Miss volume → rebound chances |
| ast | `opp_allowed_ast_ewma`, `opp_allowed_ast_mean`, `opp_allowed_ast_factor` | Creation environment |
| fg3m | `opp_allowed_fg3m_ewma`, `opp_allowed_fg3m_mean`, `opp_allowed_fg3m_factor` | 3P defense weakness |
| blk | `opp_allowed_blk_ewma`, `opp_allowed_blk_mean`, `opp_allowed_blk_factor` | Rim attack volume |
| stl | `opp_allowed_stl_ewma`, `opp_allowed_stl_mean`, `opp_allowed_stl_factor` | Turnover tendency |

*Opponent context is computed from `stats_df` grouped by `opp_team_id` (derived from `home_team_id`/`visitor_team_id`). No broken API endpoint.*

### Layer 3 — Role / Opportunity

| Feature | Notes |
|---------|-------|
| `adv_mean_usage_percentage_last10` | Possession usage rate (EWMA) |
| `rest_days` | Recovery / fatigue |
| `back_to_back` | B2B flag |
| `n_teammates_injured` | Team injury context |
| `top_scorer_injured` | Targeted injury transfer (pts/ast) |
| `top_rebounder_injured` | Targeted injury transfer (reb) |
| `blowout_risk` | Garbage time suppression |
| `blowout_x_min_vol` | Interaction: blowout × minutes instability |

### Layer 4 — Stat-Specific Mechanics

**Points:**
- `pts_per_min_mean_last10`, `pts_per_min_trend_3v10` — scoring rate + trend
- `fga_per_min_trend_3v10` — shot volume trend
- `fta_per_min_mean_last10` — free throw opportunity rate

**Rebounds:**
- `reb_per_min_mean_last5`, `reb_per_min_trend_3v10` — rebound rate + trend
- `reb_per_min_vol_last10` — variance (rebounds are noisy)
- `oreb_per_min_mean_last10`, `dreb_per_min_mean_last10` — offensive/defensive split

**Assists:**
- `ast_per_min_trend_3v10`, `ast_per_min_mean_last5/last10` — creation rate
- `adv_mean_passes_last10` — ball movement volume

**3-Pointers Made:**
- `per_min_fg3a_last10` — attempt rate (opportunity driver)
- `fg3a_per_min_trend_3v10` — attempt trend
- `fg3_pct_safe` — Bayesian-shrunk 3P% (k=50 toward 36% prior)
- `fg3m_p_zero_last10`, `fg3m_p_ge3_last10` — zero/multi-make probability

**Blocks:**
- `blk_per_min_vol_last10` — high variance → sparse stat treatment
- `blk_p_zero_last10`, `blk_p_ge2_last10` — zero/multi-block probability
- `adv_mean_defended_at_rim_fga_last10` — rim protection opportunities

**Steals:**
- `stl_per_min_vol_last10` — high variance → sparse stat treatment
- `stl_p_zero_last10`, `stl_p_ge2_last10` — zero/multi-steal probability
- `adv_mean_deflections_last10` — steal opportunity proxy

---

## Top Features by Stat (Current Model — Mar 16, 2026)

| Rank | pts | reb | ast | fg3m | blk | stl |
|------|-----|-----|-----|------|-----|-----|
| 1 | opp_allowed_pts_ewma | mp_trend_3v10 | ast_per_min_trend_3v10 | per_min_fg3a_last10 | blk_per_min_vol | stl_per_min_vol |
| 2 | pts_per_min_trend_3v10 | reb_per_min_trend_3v10 | mp_ewma_10 | fg3a_per_min_trend_3v10 | cv_min | mp_mean_last10 |
| 3 | pts_per_min_mean_last10 | reb_per_min_vol_last10 | mp_trend_3v10 | mp_trend_3v10 | mp_trend_3v10 | mp_trend_3v10 |
| 4 | fga_per_min_trend_3v10 | reb_per_min_mean_last5 | ast_per_min_mean_last5 | fg3_pct_safe | mp_ewma_10 | mp_ewma_10 |
| 5 | mp_trend_3v10 | opp_allowed_reb_ewma | ast_per_min_mean_last10 | mp_ewma_10 | mp_mean_last10 | cv_min |
| 6 | pts_per_min_mean_last5 | oreb_per_min_mean | cv_min | mp_mean_last10 | mp_vol_last10 | opp_allowed_stl_ewma |
| 7 | mp_ewma_10 | dreb_per_min_mean | opp_allowed_ast_ewma | opp_allowed_fg3m_ewma | opp_allowed_blk_ewma | mp_vol_last10 |

---

## Modeling Approach

### Quantile Regression Ensemble

Each stat target is modeled with **11 independent LightGBM quantile regressors** at τ ∈ {0.10, 0.20, 0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75, 0.80, 0.90}, minimizing pinball loss. This produces a full predicted distribution per player-game rather than a point estimate.

The Q50 prediction is the model's median projection. Implied probability that a player exceeds a sportsbook line is derived by interpolating across the quantile CDF:

```
P(X > line) = 1 - interpolated_CDF(line | q_preds)
```

### Two-Stage Calibration

**Stage 1 — Isotonic regression per stat** (`calibration_{stat}.pkl`): corrects quantile ordering violations and systematic bias within each stat family.

**Stage 2 — Platt scaling per side** (`platt_over.pkl`, `platt_under.pkl`): corrects asymmetric overconfidence on the UNDER side — the primary observed failure mode.

**Active development — stat×side calibration** (`pts_over.pkl`, `pts_under.pkl`, etc.): the next calibration upgrade targeting the remaining stat-level CLV asymmetry.

### Empirical Bias Correction

The model trains on all players but predicts only for players with sportsbook lines (starters/key players who produce more). This causes systematic q50 under-centering corrected by empirically-derived per-stat offsets:

| Stat | Bias Correction Applied |
|------|------------------------|
| pts | +2.34 |
| ast | +0.82 |
| fg3m | +0.52 |
| reb | +0.50 |
| blk | +0.32 |
| stl | +0.30 |

### Sparse Stat Treatment (blk, stl)

Blocks and steals are modeled as zero-inflated distributions. Zero-game probability (`blk_p_zero_last10`) and multi-event probability (`blk_p_ge2_last10`) are explicit features, not derived. BLK OVER and STL OVER picks are currently suppressed in the deployment layer pending calibration evidence.

---

## Deployment Policy

The system produces two output tiers:

**Full pricing universe** (`predictions/singles_{date}.json`): all model prices against available lines — the scanner output.

**High-conviction subset** (`predictions/high_conviction_{date}.json`): filtered by:
- Calibrated probability ≥ 0.60 (OVER) or ≥ 0.68 (UNDER)
- EV ≥ 2.5% at standard juice
- BLK OVER / STL OVER: suppressed
- Portfolio caps: max 2 picks/player, 4/game, 15/stat, 60 total

---

## Retrain Red-Flag Report

After every retrain, `retrain_report_{date}.json` is committed to `graded/` with:
- Feature count and opponent feature count per stat
- MAE and calibration error per stat
- Top 10 features by gain per stat
- Non-null rate by feature family
- Missing feature audit vs expected feature list

---

## Repo Structure

```
├── .github/workflows/
│   ├── daily_predictions.yml    # Daily pipeline (snapshot → predict → grade)
│   └── retrain.yml              # Weekly full retrain
├── data/                        # Parquet caches (stats, advanced, odds)
├── graded/
│   ├── performance_log.csv      # All graded picks with CLV
│   └── retrain_report_*.json    # Red-flag audit per retrain
├── model_cache/                 # Trained models + feature manifests
├── predictions/                 # Daily prediction outputs
├── feature_engineering.py       # 4-layer feature builder
├── train_v12.py                 # Training pipeline
├── predict_darko_v4.py          # Prediction engine
├── grade_darko_v4.py            # CLV grader
├── calibrate_models.py          # Calibration workflow
└── bdl_client.py                # BallDontLie API client
```

---

## Data Source

**BallDontLie API (GOAT tier)** — box scores, advanced stats, injuries, betting odds, player props.

Opponent defensive context is computed from player stats grouped by opposing team — not from a team season averages endpoint (which does not exist in BDL). Per-team, per-stat rolling EWMA over the last 10 games played.

---

## Known Limitations & Active Work

| Issue | Status |
|-------|--------|
| pts q50 under-centered by ~1.0 | Bias correction applied; monitoring |
| ast q50 under-centered by ~0.6 | Bias correction applied; monitoring |
| UNDER CLV consistently negative | Stat×side calibration in development |
| BLK/STL OVER hit rate <25% | Picks suppressed; sparse model treatment |
| 1,978 picks/week too broad | High-conviction deployment filter added |
| Calibration: stat-only + global-side | Upgrading to stat×side |

---

## CLV as Primary Metric

Closing Line Value measures whether the model's probability estimates were sharper than the closing sportsbook line — the same standard used internally at sharp books. A positive CLV confirms the model identified edges that the market subsequently moved to price out.

```
CLV = (model_prob - implied_closing_prob) / implied_closing_prob
```

This is more informative than hit rate or ROI on small samples because it measures pricing quality against the sharpest available signal rather than realized outcomes.
