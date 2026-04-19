# Migration — old path to rebuilt pipeline

This document captures what changed, how to cut over, the hacks that
were replaced, and a frank statement of what the rebuild did not solve.
Paired with `docs/ARCHITECTURE.md`.

## 1. Old path → new path, stat by stat

| Stat | Old model | New model |
|---|---|---|
| minutes | direct quantile ladder, point-interval | state-aware: binary classifier on {normal\|active} + conditional LIMITED / NORMAL quantile ladders; P(INACTIVE) sourced from availability.prob_active |
| pts, reb, ast, tov | direct-total quantile ladder | minutes × per-minute rate simulation with Poisson within-minute noise |
| stl, blk | direct-total quantile ladder (mis-specified) | hurdle: P(zero) classifier + conditional positive-count quantile ladder |
| stocks | independent direct-total model | component convolution of stl + blk PMFs |
| fg3m | three-stage archetype hurdle | same three-stage hurdle; now exposes full discrete PMF via `.pmf()` |
| pra, pr, pa, ra | direct-total quantile ladder per combo | derived from component main-stat PMFs (copula when correlation matrix is loadable, else independence convolution) |

## 2. Replaced temporary hacks

These are the explicit hacks from the pre-rebuild codebase that the
new pipeline retires or marks transitional. Each is safe to delete
once the first full CI retrain under the new layout regenerates every
artifact.

| Hack | Where | Replaced by |
|---|---|---|
| hardcoded per-stat bias constants in predict | predict.py `BIAS_CORRECTION` block | `calibration.residual_centering.ResidualCenterer` (learned from graded history) |
| side-level Platt scaling as primary correction | `model_cache/platt_{over,under}.pkl` loaded in predict | `calibration.pmf_calibration` (CDF-level isotonic, walk-forward OOF). Side-level Platt demoted to diagnostic-only fallback |
| `injury_map = {}` for all pre-snapshot training rows | train.py injury_snapshots_index fallback | `features.availability_asof` builds full historical table from nba_injury_reports.parquet + play history, with explicit confidence tiers |
| silent NaN in vacated_* features | feature_engineering.py | availability_asof emits confidence='LOW' + imputed prob_active rather than NaN |
| fg3m per-player sanity gate on predicted probability | predict.py fg3m filter at end of pipeline | captured inside bet_selection.SelectionThresholds.sparse_stat_probability_floor (transitional only) |
| Q50 bias corrections JSON | `model_cache/q50_bias_corrections.json` | obsoleted by the generative minutes × rate path + PMF calibration; file remains for back-compat during transition |
| minutes_bucket_corrections.json | model_cache | obsoleted by state-aware minutes architecture; file remains for back-compat during transition |
| `predict_backup.py`, `predict_calibrated{,_experiment}.py`, `apply_fix.py`, `apply_live_cal.py`, `fix_min_q50.py`, `live_props_*.php` | repo root | deleted during Phase 2 reorganization |

## 3. Cutover sequence

The rebuild was committed in an order that keeps the live path
functional at every step. To complete the cutover after this batch of
commits:

1. **Retrain under new layout.** Trigger `retrain.yml` manually so a
   full CI run under the new `src/` layout regenerates:
     * `minutes_state_*` (already committed from a local fit)
     * `minutes_q*` legacy ladder (still used as the fallback)
     * rate quantile ladders (`rate_{stat}_q{qpct}.pkl`)
     * sparse hurdle artifacts (`hurdle_{stat}_*.pkl`)
     * `fg3m_hurdle.pkl`
     * `within_player_corr_engine.pkl`
     * `residual_centerer_*.pkl`

   Before that run, update `scripts/train.py` (or
   `src/nba_props_model/pipelines/train.py`) to call two additional
   training functions at the end of the existing training block:

   ```python
   from nba_props_model.models.rate_models import train_rate_models
   from nba_props_model.models.sparse_hurdle import train_sparse_hurdle

   # training_df already has player-game rows with stat-specific slices;
   # the rate trainer wants one row per player-game with the raw stat
   # columns (pts/reb/ast/turnover) + min + feature columns. Build a
   # "wide" view from training_df[training_df["stat"] == "pts"] joined
   # to stats_df by (player_id, game_id) so raw stat columns appear.
   wide = (
       training_df[training_df["stat"] == "pts"]
         .drop(columns=["actual"])
         .merge(
             stats_df[["player_id", "game_id", "min",
                       "pts", "reb", "ast", "turnover", "stl", "blk"]],
             on=["player_id", "game_id"], how="left",
         )
   )
   train_rate_models(wide)
   train_sparse_hurdle(wide)
   ```

2. **Run OOF calibration.** After the retrain, generate OOF PMFs on a
   30-day holdout window and call
   `calibration.pmf_calibration.fit_all(...)` to write the
   `pmf_cal_*.pkl` artifacts.

3. **Run diagnostics.**
   ```
   python -m nba_props_model.evaluation.diagnostics   # wraps write_report
   ```
   Inspect `artifacts/docs/diagnostics_{date}.md` and ensure the new
   path posts better log-score, CRPS, and PIT metrics than the legacy
   direct-total path.

4. **Flip the live switch.** Edit `scripts/predict.py` so its `main()`
   invokes `pmf_predict.score_full_universe` first and falls back to
   the legacy quantile-ladder path only when PMF artifacts are
   missing. Example:

   ```python
   from nba_props_model.pipelines.pmf_predict import (
       build_prop_pmfs, score_full_universe,
   )
   # ... legacy feature build ...
   prop_pmfs_by_player = { ... }   # from build_prop_pmfs per player
   all_props_df = score_full_universe(universe_rows, prop_pmfs_by_player)
   if len(all_props_df) and all_props_df["model_prob"].notna().any():
       # Use PMF-first output
       ...
   else:
       # Fall back to legacy direct-total path
       ...
   ```

5. **Retire side-level Platt.** Once PMF calibration is posting better
   reliability than side-level Platt across every stat, delete the
   `platt_*` loading in `scripts/predict.py` and drop the
   `model_cache/platt_*.pkl` dependencies.

## 4. Reproducible commands

```
# Install dev dependencies
pip install -e '.[dev]'
export BDL_API_KEY=...
export ODDS_API_KEY=...

# Data refresh + availability table
python scripts/build_availability_table.py

# Full retrain (writes all artifacts to artifacts/models/)
python scripts/train.py

# Walk-forward Platt (diagnostic fallback only; retained during transition)
python scripts/calibrate.py

# Fit PMF-level CDF calibration (after retrain + OOF PMF generation)
# See step 2 of the cutover sequence for the driver script; once
# `scripts/calibrate_pmf.py` is added it will call
# `calibration.pmf_calibration.fit_all`.

# Tests
pytest -q

# Daily prediction
python scripts/predict.py

# Grading
python scripts/grade.py

# Diagnostics report
python - <<'PY'
from nba_props_model.evaluation.diagnostics import evaluate_fold, write_report
# ... build fold metrics ...
write_report(fold_metrics, run_date="YYYY-MM-DD")
PY
```

## 5. Frank statement — what is still not solved

The rebuild completes the structural replacement of every major
modeling defect flagged in `docs/PHASE1_AUDIT.md`, but the following
remain open:

- **Rate and sparse-hurdle artifacts are not yet trained.** The
  training code is in place and tested; `scripts/train.py` needs the
  two-line addition in the "Cutover sequence" step 1 before the next
  CI retrain will produce `rate_*.pkl` and `hurdle_*.pkl`. Until that
  retrain runs, `pmf_predict.build_prop_pmfs` returns an empty dict
  for main + sparse stats and the live path continues to use the
  legacy direct-total quantile ladder.

- **PMF calibration artifacts do not exist on disk.** The calibrator
  is tested and ready; it needs OOF PMFs from the new pipeline to fit
  against. Produced naturally once step 1 is complete.

- **DNP rows are absent from `player_game_stats.parquet`.** Box scores
  never record zero-minute entries, so the state-aware minutes model
  does not directly observe INACTIVE in training. P(INACTIVE) is
  sourced from `availability.prob_active` which encodes status on a
  continuous scale. An upgrade would be to impute zero-minute rows
  from the injury-report feed during training-table construction.

- **Name resolution for the availability pipeline is 94.5%.** The
  remaining 5.5% are rookies, two-way players, and NaN raw names.
  Acceptable today; a deterministic lookup table keyed by the BDL
  player-id feed would close the gap.

- **Opponent role-based defensive context (opp_allowed_X_to_guard/
  wing/big as EWMA features)** is not yet emitted by the availability
  pipeline. Deferred to Phase 3 proper — Phase 2 builds the feature
  plumbing; lighting it up in the feature gate is the next task for
  the minutes/rate models.

- **Combos use copula correlation only when a correlation matrix is
  loaded.** Default today is the conservative independence
  convolution. `combos.build_combo_pmf` accepts an explicit
  correlation argument; wire-up from `correlation.sgp_engine` into
  `pmf_predict` is a one-liner left for the integration PR that also
  migrates the live predict path.

- **Feature engineering monolith is still a 1932-line file.** It was
  intentionally not shattered in Phase 2 (see PHASE1_AUDIT.md §3).
  Split piece by piece as each feature family is touched by a phase.

- **scripts/predict.py still uses the legacy direct-total quantile
  path in main().** The PMF-first path is complete at
  `pmf_predict.score_full_universe` but the cutover switch has not
  been flipped. The switch is a small edit inside `predict.main()`
  as described in step 4 above.

- **Closing-line CLV for the rebuilt model.** CLV will be available
  once the new model starts emitting picks and the 6 PM ET closing
  snapshots accumulate against them. No forward numbers to report on
  the rebuilt model yet.

Treat this list as the Phase 10 backlog. The modeling architecture is
complete; the remaining items are integration and data hygiene.
