# Phase 1 Audit — NBA Props Model

**Purpose.** Identify the true production path, name dead code, and surface the
structural train/inference mismatches that Phases 2–7 must repair. Derived by
reading the code and CI workflows, not the aspirational documentation.

---

## 1. Live production path (source of truth)

The GitHub Actions workflows are the authoritative entry points.

### `.github/workflows/retrain.yml` — weekly / manual
1. `python train.py`
2. `python calibrate_stat_side.py` (may no-op if graded data is sparse)
3. Commit `model_cache/` and `data/` back to `main`

### `.github/workflows/daily_predictions.yml` — three cron triggers
- **09:00 ET** — `python snapshot_opening_lines.py` → commits `data/opening_lines_{date}.json`
- **08:00 ET** — `python grade.py` then `python predict.py`, then SFTP upload of `predictions/singles_{date}.json`, `predictions/sgps_{date}.json`, `predictions/pmf_display_{date}.json`
- **18:00 ET** — `python snapshot_closing_lines.py` → commits `graded/closing_lines_{date}.json`

### Source-of-truth files (imported by the live workflows)
| File | Role |
|---|---|
| `train.py` | Training orchestrator; calls minutes, quantile, FG3M hurdle, residual-center, Platt |
| `predict.py` | Daily inference; writes `predictions/singles_{date}.json`, `sgps_{date}.json`, `pmf_display_{date}.json`, `all_props_{date}.parquet` |
| `grade.py` | Yesterday-grading, CLV, performance log |
| `calibrate_stat_side.py` | Walk-forward Platt calibration (`IsotonicCalibrator` class also imported by `predict.py` for pickle loading) |
| `feature_engineering.py` | 1932-line monolith — rolling, opponent context, market, vacated/injury features |
| `minutes_model.py` | LightGBM quantile minutes model (single-stage, point-interval, not state-aware) |
| `fg3m_hurdle.py` | Two-part hurdle for made threes |
| `residual_centering.py` | Learned additive bias correction from graded history |
| `correlation_engine.py` | Within-player residual correlation → SGP Gaussian-copula pricing |
| `retrospective_features.py` | Role and absence features (called from `train.py:560`) |
| `bdl_client.py` | BallDontLie API client; also hosts `build_injury_map`, `merge_injury_sources` |
| `snapshot_opening_lines.py`, `snapshot_closing_lines.py` | Odds snapshots |

Artifact layout: `data/` (raw + as-of), `model_cache/` (pickles + manifests),
`predictions/` (daily outputs), `graded/` (graded history + closing lines).

---

## 2. Dead code (not referenced by workflows or live code)

| File | Status | Notes |
|---|---|---|
| `predict_backup.py` | Dead | Identical size and shape to `predict.py`; stale copy |
| `predict_calibrated_experiment.py` | Dead | Abandoned experiment, 1180 lines |
| `predict_calibrated.py` | Dead | One-shot calibration script |
| `apply_fix.py` | Dead | One-shot patch (17 lines) |
| `apply_live_cal.py` | Dead | One-shot patch (59 lines) |
| `fix_min_q50.py` | Dead | One-shot patch (10 lines) |
| `live_props_fixed.php` | Dead | Stray PHP from web front-end |
| `live_props_threshold_fix.php` | Dead | Stray PHP from web front-end |
| `__pycache__/` at repo root | Dead | Build artifact |

All will be deleted during the Phase 2 reorganization commit.

---

## 3. Train / inference mismatches (critical)

### 3.1 Injury map coverage — the headline defect
`feature_engineering.py` computes all vacated / teammate-absence features
(`vacated_minutes`, `vacated_fga`, `vacated_guard_minutes`, `num_teammates_inactive`,
`has_injury_data`, etc.) from an `injury_map` dict passed in by the caller.

- **Inference (`predict.py:625–629`).** `injury_map = build_injury_map(injury_raw)`
  merged with `nba_report` and `stats_df`. Always populated, covers every team.
- **Training (`train.py:445–461, 701`).** `injury_map` is read from
  `data/injury_snapshots.parquet` — an **accumulating forward-only snapshot** that
  only began writing after the pipeline was deployed. Historical rows silently get
  `injury_map = {}`. Comment at `train.py:19`: *"For historical rows (pre-snapshot):
  `injury_map = {}` — unavoidable."*

Consequence: during training, a large majority of rows have `has_injury_data=0`
and all vacated_* = 0/NaN, regardless of who was actually hurt that day. The model
learns that "no injury signal" is normal state and heavily underweights the effect
at inference, which is the mechanism behind the narrow PMFs the mission flags.

`data/nba_injury_reports.parquet` exists and is historically populated, but is not
joined into training `injury_map`. Phase 2 fixes this by building a proper as-of
availability table from `nba_injury_reports.parquet` + `injury_snapshots.parquet`
+ `player_game_stats.parquet` and using it for both paths.

### 3.2 Silent NaN propagation
When `injury_map = {}` at training time, `vacated_opportunity_features` returns
an all-NaN dict (`feature_engineering.py:724–743, 1287–1298`). LightGBM treats
NaN as "missing branch," so the model does not crash — it quietly routes these
rows through a default branch that effectively learns the unconditional mean.
No warning is emitted. Phase 2 will replace silent NaN with an explicit
confidence tier and an imputed `prob_active` derived from recent play rate.

### 3.3 Minutes model is point-interval, not state-aware
`minutes_model.py` predicts quantiles of total minutes directly. There is no
DNP / active-limited / active-normal state process. A player returning from a
7-day absence and a fully healthy starter both get predicted from the same
feature space, collapsing uncertainty in exactly the situations where it should
widen. Addressed in Phase 3.

### 3.4 Stocks / sparse stats modeled as plain quantile regression
`stl` and `blk` are trained as ordinary quantile regressors with the same
architecture as `pts` and `reb` (search `train.py` for `STAT_TARGETS` — all
stats share one loop). `stocks` is trained independently rather than derived
from the component distributions. Addressed in Phase 5.

### 3.5 Rate vs. total decomposition absent for main stats
`pts`, `reb`, `ast`, `tov` are trained as game-total quantile models. Per-minute
rates are computed in `feature_engineering.py` as *features* but not as
*targets*. The minutes × rate simulation layer does not exist. Addressed in
Phase 4.

---

## 4. Leakage risks to audit during phase work

- `feature_engineering.py` is 1932 lines and mixes rolling windows, EWMA, and
  same-day context. Any rolling that accidentally includes the current row leaks.
  Split into `rolling_player.py` / `opponent_context.py` / `market_features.py`
  incrementally as each is touched.
- `retrospective_features.py:build_retrospective_features` is called with a
  training DataFrame — verify it is strictly as-of prediction date and does not
  leak post-game outcomes back into pre-game features.
- Calibration: `calibrate_stat_side.py` is walk-forward by design; verify the
  fold boundaries respect season breaks.
- Closing-line snapshots must only be used for CLV computation, never as inputs
  to the model or calibration.

---

## 5. Calibration surface is side-level, not distribution-level

The calibration layer (`calibrate_stat_side.py` + `model_cache/platt_over.pkl`,
`platt_under.pkl`, `calibration_{stat}.pkl`, `live_calibration_table.json`,
`minutes_bucket_corrections.json`) operates on extracted over/under side
probabilities — *after* the PMF has been built from the quantiles. The
distribution itself is not calibrated.

This is exactly the "post-hoc side calibration as primary correction" pattern
the mission forbids as the permanent fix. Phase 6 replaces it with full-PMF /
CDF calibration over the persisted full-universe history.

---

## 6. Legacy naming

The product is the **NBA Props Model**. Prior-iteration legacy naming
persists in docstrings, log messages, and filenames across the live
source and several dead scripts. These are purged in the reorganization
commit.

---

## 7. What this audit commits the rebuild to

1. **Phase 2** — replace the empty-at-training `injury_map` with a historical
   as-of availability table; single feature definition across train and predict;
   explicit confidence tier; tests for no-leak and coverage.
2. **Phase 3** — replace the point-interval minutes model with a state-aware
   probabilistic minutes distribution.
3. **Phase 4** — replace direct-total quantile models for `pts`, `reb`, `ast`,
   `tov` with minutes × per-minute rate simulation.
4. **Phase 5** — rebuild `stl`, `blk` as hurdle / zero-inflated models; derive
   `stocks` from components.
5. **Phase 6** — persist the full evaluated universe, build out-of-fold PMF/CDF
   calibration, deprecate side-level Platt as the primary correction.
6. **Phase 7** — derive positive-EV bets from calibrated fair probabilities and
   separate model quality evaluation from bet-selection evaluation.

Each phase will ship with out-of-sample, date-respecting, full-universe
diagnostics. No phase is considered done on "code runs" alone.
