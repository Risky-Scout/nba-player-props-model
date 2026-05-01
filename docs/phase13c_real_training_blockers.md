# Phase 13C — Real Training Blockers (Updated Analysis)

**Status:** Real nightly retraining is **still NOT live**. Phase 13C reread the
production training and calibration code in detail and found two new things:

1. The Phase 13B framing of "daily training = full retrain via
   `pipelines/train.py`" was **wrong for this codebase**. The daily-training
   surface that production was actually built around is
   `scripts/calibrate_pmf.py`, which already does per-fold partial-refit of
   minutes / rate / hurdle / fg3m AND fits the final role-aware PMF
   calibrators. The existing `phase8.yml` workflow runs it manually for that
   exact purpose.
2. The Phase 13C session could not produce a real `TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS`
   because (a) the input `data/training_table.parquet` was not present on
   the dev machine, and (b) the partial-refit + walk-forward calibration
   takes ~30–45 minutes (`--core-props-only --max-folds 1`) up to several
   hours (full fold count) per run, which exceeds an interactive session
   budget. Per the strict rule "*Do not claim daily real retraining is
   live unless TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS printed*,"
   the workflow default remains dry-run.

The Phase 13A/B framework is unchanged and continues to print
`TRAINING_AUTOMATION_VERIFICATION_PASS` +
`TRAINING_AUTOMATION_DRY_RUN_VERIFICATION_PASS` and `DAILY_AUTOMATION_HEALTH_PASS`
on every run.

---

## Corrected diagnosis: what "daily training" should mean

The agent inventory in Phase 13B treated `src/nba_props_model/pipelines/train.py::main()`
as the trainer and treated `scripts/calibrate_pmf.py` as a separate calibration
step. Re-reading `calibrate_pmf.py` more carefully shows:

- **Per-fold partial-refit** lives at `scripts/calibrate_pmf.py::_refit_models_for_fold`
  (lines 199–290). It refits `minutes`, `rate`, `hurdle`, and `fg3m` on data
  strictly before each `fold_start`, writes them into a temp per-fold artifact
  dir, and uses them to score the fold's validation rows.
- **Final calibrator fit** happens after the fold loop in
  `_fit_final_calibrators_and_emit_report` and writes `pmf_cal_role_<stat>.pkl`
  via `nba_props_model.calibration.pmf_calibration.fit_all` → `joblib.dump(MODEL_DIR / ...)` at `pmf_calibration.py:385`.
- **`MODEL_DIR` swap helper** already exists at `calibrate_pmf.py:152`
  (`_swap_model_dir`). It patches `MODEL_DIR` on six modules and clears their
  caches. Pattern is sound; just needs to cover one more module
  (`nba_props_model.calibration.pmf_calibration`) to be complete.
- **Pre-existing production backup** at `calibrate_pmf.py:990`: the script
  already backs up production artifacts to
  `artifacts/models/archive/pre_calibrate_pmf_<timestamp>/` before any swap
  churn — it knows it is destructive to production.
- **Q-models are not retrained** by `calibrate_pmf.py`. Those (`q50_pts.pkl`
  etc.) come from the heavier `pipelines/train.py::main()` and are loaded
  read-only during fold refits. Heavy q-model retraining is monthly/quarterly,
  not daily.

So daily-training in this codebase = walk-forward calibrate with per-fold
partial-refit. Phase 13C should redirect that pipeline to challenger paths,
not the heavier `pipelines/train.py`.

---

## The five blockers, re-stated against the corrected target

### Blocker 1 (corrected) — `calibrate_pmf.py` has no `--as-of-date`

**Where:** `scripts/calibrate_pmf.py::main()` near line 774.

**Today:** The walker reads three parquets at lines 949–953 and uses
`make_walk_forward_folds(all_dates, ...)` against whatever dates are in the
input. There is no upper-bound cutoff.

**Required fix (small, low-risk):**

```python
parser.add_argument("--as-of-date", default=None,
    help="Inclusive upper bound on game_date for all loaded data. "
         "Required for nightly challenger runs.")
# After loading the three dataframes and constructing all_dates / training_game_date_ts:
if args.as_of_date:
    cutoff = pd.Timestamp(args.as_of_date)
    stats_df = stats_df[pd.to_datetime(stats_df["game_date"]) <= cutoff]
    availability_df = availability_df[pd.to_datetime(availability_df["game_date"]) <= cutoff]
    training_df = training_df[training_game_date_ts <= cutoff]
    training_game_date_ts = training_game_date_ts[training_game_date_ts <= cutoff]
    all_dates = pd.to_datetime(stats_df["game_date"])
```

Default behavior with no flag is unchanged.

### Blocker 2 (corrected) — Final calibrator fit writes to production `MODEL_DIR`

**Where:** `nba_props_model/calibration/pmf_calibration.py:385`:
```python
joblib.dump(bundle, MODEL_DIR / f"pmf_cal_role_{stat}.pkl")
```

**Required fix (small, low-risk):**

1. Add `pmf_calibration` to `_PATCHED_MODULES` at `calibrate_pmf.py:142`.
2. Add `--output-dir` to `calibrate_pmf.py::main`. When set, wrap the
   `_fit_final_calibrators_and_emit_report` call in a `_swap_model_dir(output_dir)`
   block so the final calibrators land in the challenger directory. The
   per-fold loop already swaps to a temp dir; this just adds one more swap
   for the final-fit phase.

```python
parser.add_argument("--output-dir", default=None,
    help="Directory for final pmf_cal_role_*.pkl artifacts. "
         "Default: artifacts/models/ (production behavior).")

# Replace the bare _fit_final_calibrators_and_emit_report(...) call near line 939 with:
if args.output_dir:
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    final_originals = _swap_model_dir(Path(args.output_dir))
    try:
        _fit_final_calibrators_and_emit_report(...)
    finally:
        _restore_model_dir(final_originals)
else:
    _fit_final_calibrators_and_emit_report(...)
```

### Blocker 3 (corrected) — `_PATCHED_MODULES` does not cover `pmf_calibration`

**Where:** `scripts/calibrate_pmf.py:142–149`.

**Required fix:** add the line `"nba_props_model.calibration.pmf_calibration",`.
This is a one-line addition that makes Blocker 2's fix actually take effect.
Without it, `pmf_calibration.MODEL_DIR` stays bound at import time and
`fit_all` will write to production regardless of any swap.

### Blocker 4 — `data/training_table.parquet` is shared

**Where:** Read at `calibrate_pmf.py:953`; written by
`pipelines/train.py::build_training_table()` (called via
`scripts/train.py --build-table-only`).

The blocker remains real. For a challenger run we need either:

(a) a snapshot in the challenger dir:
   `artifacts/models/challengers/<as_of_date>/training_table.parquet`,
   built by `train.py --build-table-only` with output redirected, OR

(b) a copy of the existing shared `data/training_table.parquet` into the
   challenger dir, with the cutoff filter applied at load time
   (Blocker 1's fix already covers the cutoff).

**Recommended fix (path b, smallest):**

```python
# In scripts/train_daily_challenger_model.py::_train_full_candidate
import shutil
src = REPO_ROOT / "data" / "training_table.parquet"
if not src.exists():
    raise RuntimeError("data/training_table.parquet missing; run "
                       "scripts/train.py --build-table-only first.")
dst = out_dir / "training_table.parquet"
shutil.copy2(src, dst)
# hash + record path in train_manifest.json
```

This lets the challenger calibrate against a snapshot without ever overwriting
the shared baseline. The `--as-of-date` cutoff in calibrate_pmf.py then
naturally filters the snapshot to leakage-safe rows.

### Blocker 5 — Validator does not score real challenger PMFs

**Where:** `scripts/validate_champion_vs_challenger.py::metrics_placeholder()`.

**Required fix (moderate, ~150–250 LOC):**

Implement `score_pmfs(model_dir: Path, training_df_holdout: pd.DataFrame) -> dict`
that:

1. Calls `_swap_model_dir(model_dir)` to point all consumer modules at the
   challenger artifacts.
2. Iterates the holdout rows and calls
   `nba_props_model.pipelines.predict.build_prop_pmfs` (or the equivalent
   internal helper used by `predict.py`).
3. For each PMF, computes against the row's actual outcome:
   - `nll = -log(pmf[outcome])`
   - `rps = sum_k (cumsum(pmf)[k] - I(outcome <= k))^2`
   - `p0_error = abs(pmf[0] - I(outcome == 0))`
   - `mean_bias = expected(pmf) - outcome`
4. Aggregates by stat, role bucket, and overall.
5. Restores `MODEL_DIR` via `_restore_model_dir` in a `finally` block.

The validator then calls this twice — once with champion `model_dir`, once
with challenger `model_dir` — and feeds the real numbers into the existing
gate logic. The current `metrics_placeholder()` becomes the dry-run-only
fallback.

---

## What Phase 13C did NOT change

Per Part J ("If real training is still blocked: do not fake success... do not
flip scheduled workflow to real training"):

- **No production code was modified.** `scripts/calibrate_pmf.py`,
  `src/nba_props_model/pipelines/train.py`,
  `src/nba_props_model/calibration/pmf_calibration.py`, and
  `src/nba_props_model/paths.py` are unchanged.
- **Workflow default is still `dry_run=true`.**
- The Phase 13A/B framework — registry, atomic promotion, lockfile, 14:30 UTC
  cutoff, secret + overlay scanners, mode-aware verifier, daily automation
  health probe — is unchanged and verified.

The reason: every fix above touches code that I cannot end-to-end verify in
this session because:

1. `data/training_table.parquet` is not present locally; building it requires
   running `scripts/train.py --build-table-only` which needs the full BDL
   data fetch pipeline plus ~5–15 minutes of build time.
2. Even with that table, a real `--no-dry-run` run takes 30–45 min for a
   single fold and longer for multi-fold. Verifying
   `TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS` requires that real
   run to complete and produce challenger pickles + scored metrics that the
   verifier can inspect.
3. The strict rule forbids declaring real retraining live without that
   verification.

Doing the wiring without verification would deliver code that compiles and
preserves dry-run, but cannot be claimed as "real training works." Per the
prompt's intent that takes us back to Path J anyway. Better to land the
corrected analysis here, leave the code untouched until an operator can run
the verification, and let Phase 13D be a small, well-scoped landing.

---

## Acceptance criteria for Phase 13D

Phase 13D should make these specific edits and verify end-to-end on
infrastructure that has the data + 60-minute compute budget:

1. **Edit `scripts/calibrate_pmf.py`** — add `--as-of-date`, `--output-dir`;
   add `nba_props_model.calibration.pmf_calibration` to `_PATCHED_MODULES`;
   wrap final-fit call in `_swap_model_dir(output_dir)` when `--output-dir`
   is set. (~25 LOC.)
2. **Edit `scripts/train_daily_challenger_model.py::_train_full_candidate`**
   — pre-filter `data/player_game_stats.parquet` and copy
   `data/training_table.parquet` into the challenger dir, then call
   `scripts/calibrate_pmf.py --as-of-date <date> --output-dir <challenger_dir> --core-props-only --max-folds 1`.
   Hash the snapshot and record in `train_manifest.json`. Exit 0 only if the
   challenger dir contains real `pmf_cal_role_*.pkl`. (~80 LOC.)
3. **Edit `scripts/calibrate_daily_challenger_pmfs.py::_calibrate_full`** —
   if the calibrators were already produced by step 2, this becomes a
   verifier (count pickles, hash them) rather than a re-run. (~30 LOC.)
4. **Edit `scripts/validate_champion_vs_challenger.py`** — implement
   `score_pmfs(model_dir, holdout_df)` and use it in real-training mode.
   Choose holdout = last 14 days strictly before `as_of_date - fold_days`
   to keep walk-forward leakage-safety. (~200 LOC.)
5. **Run end-to-end** on a real recent date with completed outcomes:
   ```
   python3 scripts/train.py --build-table-only       # ensures training_table is fresh
   python3 scripts/run_nightly_training_and_calibration.py \
       --as-of-date <recent date> --no-dry-run --no-promote
   python3 scripts/verify_training_automation.py --as-of-date <recent date>
   ```
   Confirm `TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS`.
6. **Only then** flip `.github/workflows/nightly_training_calibration.yml`
   to default `dry_run=false`, and add a one-line comment in the workflow
   pointing to the verifier output.
7. Update this document to mark blockers resolved.

The total code change to land Phase 13D is ~335 LOC plus the operator's
end-to-end run. None of it modifies the daily delivery path — Derek and WoO
continue to read only `champion_pointer.json`.
