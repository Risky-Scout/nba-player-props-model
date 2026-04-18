# NBA Props Model

Probabilistic model for NBA player prop markets. Outputs full PMF/CDF per
(player, game, stat) combination, converts them to fair over/under
probabilities at posted lines, and surfaces positive-EV bets against live
market prices.

CLV is the primary performance metric. Win rate on -110 juice is close to
meaningless at sample sizes under a few thousand picks.

**Live output:** [dev.wizardofodds.com](https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-props.html)

---

## Repository layout

```
nba-player-props-model/
├── src/nba_props_model/               source package
│   ├── paths.py                       canonical repo paths
│   ├── data/bdl_client.py             BallDontLie GOAT API client
│   ├── features/
│   │   ├── engineering.py             rolling, EWMA, market, vacated features
│   │   └── retrospective.py           role and absence features
│   ├── models/
│   │   ├── minutes.py                 minutes quantile ensemble (Phase 3 target)
│   │   └── fg3m_hurdle.py             two-part hurdle for FG3M
│   ├── calibration/
│   │   ├── stat_side_platt.py         walk-forward Platt (transition-only)
│   │   └── residual_centering.py      learned additive bias correction
│   ├── correlation/sgp_engine.py      within-player / teammate correlation
│   ├── evaluation/grading.py          nightly grading + CLV
│   └── pipelines/
│       ├── train.py                   training pipeline
│       └── predict.py                 prediction pipeline
├── scripts/                           thin CLI entrypoints (what CI invokes)
│   ├── train.py
│   ├── predict.py
│   ├── grade.py
│   ├── calibrate.py
│   ├── snapshot_opening_lines.py
│   └── snapshot_closing_lines.py
├── data/                              raw + as-of historical data
├── artifacts/
│   ├── models/                        trained model pickles + manifests
│   └── graded/                        graded history + closing-line snapshots
├── predictions/                       daily outputs (web dashboard reads this)
├── tests/                             pytest suite
├── config/                            explicit YAML configs
├── docs/                              audit notes, methodology, coverage reports
├── .github/workflows/                 daily + retrain CI
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Running locally

```bash
pip install -r requirements.txt
export BDL_API_KEY=...
export ODDS_API_KEY=...

# Generate today's predictions from the current model cache
python scripts/predict.py

# Grade yesterday's picks
python scripts/grade.py

# Capture opening / closing line snapshots
python scripts/snapshot_opening_lines.py
python scripts/snapshot_closing_lines.py

# Full retrain from scratch
python scripts/train.py
python scripts/calibrate.py

# Tests
pip install -e '.[dev]'
pytest
```

---

## What the model does today

Trains LightGBM quantile regressors per stat target at
tau in {0.10, 0.20, 0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75, 0.80, 0.90},
yielding a conditional distribution for each player-game-stat combination.
P(over/under) is recovered by piecewise linear CDF interpolation between
adjacent quantile knots.

FG3M gets a two-part hurdle: classifier for P(attempts >= 1), Binomial for
P(makes >= k | attempts), with archetype-aware shrinkage priors.

Minutes runs first and injects its full projected distribution as features
into every downstream stat model.

Calibration: walk-forward 28-day folds with season boundaries respected.
Predictions refit on all data through yesterday before deployment.

---

## Daily schedule

- 08:00 ET — grade yesterday, generate today's predictions, SFTP to web
- 09:00 ET — opening lines snapshot
- 18:00 ET — closing lines snapshot (post-injury-report)

All automated via `.github/workflows/daily_predictions.yml`.

---

## Rebuild in flight

This repo is mid-rebuild. See `docs/PHASE1_AUDIT.md` for the current defect
inventory and the seven-phase plan to replace narrow PMFs, mis-specified
sparse stats, the point-interval minutes model, and post-hoc side-level
calibration with generative minutes x rate simulation, hurdle models, and
full-PMF out-of-fold calibration.
