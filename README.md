# NBA Player Props Model

Quantile regression pipeline for NBA player prop markets. Produces calibrated probability distributions across 12 stat targets, compares them to sportsbook implied probabilities, and surfaces positive expected value opportunities.

**Live dashboard:** [dev.wizardofodds.com](https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-live-props.html)

---

## Architecture

### Training (`train.py`)
- **Data:** BallDontLie GOAT API — box scores, advanced stats, injuries, game context
- **Scale:** 833k training rows | 654 players | 2023–present
- **Models:** 11 LightGBM quantile models per stat (Q10→Q90), pinball loss, temporal holdout
- **Stats:** PTS, REB, AST, FG3M, STL, BLK, TOV + combos (PRA, PR, PA, RA, STL+BLK)
- **Features:** ~30 per stat — rolling windows (L1/L3/L5/L10/L20), EWMA, per-minute rates, opponent defensive environment, rest and schedule context

### Prediction (`predict_darko_v4.py`)
1. Project full Q10→Q90 distribution per player/stat/game using trained quantile ensemble
2. Apply per-stat residual centering learned from graded history
3. Convert distribution to fair probability at the posted line
4. Apply Platt scaling calibration
5. Compute EV against vig-free implied odds
6. Apply per-player fg3m gate (removes picks where model diverges >20pp from observed hit rate)
7. Portfolio caps: 25 picks/day, 2/player, 4/game

### FG3M (`fg3m_hurdle.py`)
Two-part hurdle model replacing direct quantile regression for three-point makes:
- **Part 1:** P(player attempts ≥ 1 three) — calibrated gradient boosting with archetype-aware shrinkage
- **Part 2:** P(fg3m ≥ k | attempts) — Binomial(shrunk\_fg3a, shrunk\_fg3\_pct)
- **Archetypes:** non-shooting big / low-volume wing / moderate shooter / high-volume shooter
- **Hard constraints:** Q50=0 when P(zero)≥0.50; P(fg3m>0) bounded by P(fg3a>0)

### SGPs (`correlation_engine.py`)
Gaussian copula with within-player correlation engine. Leg probabilities estimated jointly. Capped at 3 legs.

---

## Calibration

Holdout ECE after most recent retrain (833k rows):

| Stat | ECE | Status |
|---|---|---|
| PTS | 0.022 | ✓ |
| REB | 0.020 | ✓ |
| AST | 0.021 | ✓ |
| STL | 0.022 | ✓ |
| BLK | 0.023 | ✓ |
| PRA | 0.035 | ✓ |
| PR  | 0.028 | ✓ |
| PA  | 0.042 | ✓ |
| RA  | 0.018 | ✓ |
| STL+BLK | 0.028 | ✓ |
| FG3M | 0.058 | ⚠ transitioning to hurdle model |
| TOV  | 0.064 | ⚠ discrete-aware evaluation pending |

TOV and FG3M calibration is evaluated with discrete-aware diagnostics (randomized PIT / `[P(Y<q), P(Y≤q)]` bounds) to account for zero-inflation. Standard continuous ECE is not appropriate for these stats.

---

## Performance

Primary metric is CLV (Closing Line Value) — whether model probabilities beat the closing line independent of short-run outcomes.

Full tracking: `graded/performance_log.csv` | `graded/cumulative_report.json`

---

## Daily Pipeline

| Time (ET) | Script | Purpose |
|---|---|---|
| 8:00 AM | `predict_darko_v4.py` | Grade yesterday, generate today's picks |
| 9:00 AM | `snapshot_opening_lines.py` | Capture opening lines |
| 6:00 PM | `snapshot_closing_lines.py` | Capture closing lines for CLV |

Automated via GitHub Actions. Retrain runs weekly or on demand.

---

## Setup
```bash
git clone https://github.com/Risky-Scout/nba-player-props-model
cd nba-player-props-model
pip install -r requirements.txt

export BDL_API_KEY=your_key
python3 predict_darko_v4.py
```

Post-retrain:
```bash
python3 residual_centering.py --train
python3 calibrate_stat_side.py
python3 predict_darko_v4.py
python3 grade.py
```

**Required GitHub Secrets:** `BDL_API_KEY`

---

## Repository

| File | Purpose |
|---|---|
| `train.py` | Full training pipeline |
| `predict_darko_v4.py` | Daily prediction and export |
| `grade.py` | Grading and CLV tracking |
| `fg3m_hurdle.py` | Two-part hurdle model for FG3M |
| `residual_centering.py` | Per-stat bias correction |
| `calibrate_stat_side.py` | Stat×side Platt calibration |
| `feature_engineering.py` | Feature construction |
| `correlation_engine.py` | Within-player correlation engine |
| `bdl_client.py` | BallDontLie API client |
| `snapshot_opening_lines.py` | Opening line capture |
| `snapshot_closing_lines.py` | Closing line capture |
| `minutes_bias_fix.py` | Minutes bucket correction |
| `METHODOLOGY.md` | Model design and mathematical detail |
