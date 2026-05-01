# Phase 13B — Real Training & Calibration Blockers

> **SUPERSEDED by `docs/phase13c_real_training_blockers.md`.** Phase 13C
> reread the production code and found that the framing below — "daily
> training = full retrain via `pipelines/train.py`" — is the wrong target
> for this codebase. The actual daily-training surface production was built
> around is `scripts/calibrate_pmf.py` (per-fold partial-refit + final
> calibration). This document is kept for historical context. The Phase 13C
> doc replaces it as the source of truth for what needs to be unblocked
> and how.

**Status:** Real nightly retraining is **NOT** wired. The Phase 13A framework
remains in place and runs in `--dry-run` mode (challenger snapshots the current
champion). This document records the precise blockers and the minimal,
isolated changes needed to clear them.

The strict rule is: *"If real training cannot be safely wired, do not fake
it."* The blockers below are real, not aesthetic, and each one would require
modifying working production code with high blast radius onto Derek and
Wizard of Odds delivery jobs. They have been left for a deliberate Phase 13C
that owns those code changes specifically.

---

## Blocker 1 — Trainer has no as-of-date cutoff

**Where:** `src/nba_props_model/pipelines/train.py::main(build_table_only=False)`

**Signature today:**

```python
def main(build_table_only: bool = False):
    ...
```

**Problem:** The trainer fetches data through `pd.Timestamp.today()` (see the
season-fetch loop near `pipelines/train.py` lines 290–369) and trains LightGBM
quantile models on whatever rows are in `data/player_game_stats.parquet`. There
is no `as_of_date` arg, so a nightly invocation on date *D* could pick up
intra-day or future-leaked data if the input parquet has been refreshed past
*D*.

In practice the BDL refresh script (`scripts/refresh_bdl_player_game_stats.py`)
appends only finalized box scores, so the leakage risk is small at 09:30 UTC.
However, "small" is not "zero," and the framework is required to be
demonstrably leakage-safe.

**Required fix:** Add an `as_of_date: dt.date | None = None` parameter to
`main()`, plumb it through `_fetch_or_load_stats()` and the training-table
build, and apply a `df = df[df["game_date"] <= as_of_date]` filter at every
data-load site in the pipeline (stats, training table, availability tables,
DARKO features).

---

## Blocker 2 — Trainer writes directly to the champion model directory

**Where:** `src/nba_props_model/pipelines/train.py` (every `joblib.dump(...,
MODEL_DIR / "...")` call) and supporting modules that use the
`from nba_props_model.paths import MODEL_DIR` import-time constant.

**Specific writes (a partial list):**
- `q{q*100:02d}_{target}.pkl` (line 1231) — quantile models
- `features_{target}.pkl` (line 1239)
- `feature_importance_{target}.csv` (line 1294)
- `training_meta.json` (line 1455)
- `fg3m_hurdle.pkl` (line 1483)
- `within_player_corr_engine.pkl` (line 1361)
- residual centerer state (line 1553)

`MODEL_DIR` is `artifacts/models/` per `src/nba_props_model/paths.py`. Calling
the trainer would directly overwrite the current champion's pickles, violating
the Phase 13A non-interference rule:

> "Daily challenger artifacts must not overwrite champion."
> "Production champion changes only through atomic champion_pointer.json
>  promotion after validation gates pass."

**Pattern that already exists (and must be elevated):**
`scripts/calibrate_pmf.py` lines 153–181 define `_swap_module_model_dir(new_dir)`
which monkey-patches `MODEL_DIR` on every consumer module that imported it.
This pattern is internally used for fold-isolated training. It is the right
shape for what we need but is not exposed as a public API.

**Required fix:**
1. Promote `_swap_module_model_dir` (or a context-manager equivalent) into
   `src/nba_props_model/paths.py` or a new `src/nba_props_model/training_io.py`
   so it is callable from new automation entrypoints.
2. Add `--output-dir` to `scripts/train.py` and route `pipelines/train.py::main`
   through that swap so writes go to
   `artifacts/models/challengers/<as_of_date>/` instead of `artifacts/models/`.
3. Equivalently for `scripts/calibrate_pmf.py` — add `--output-dir` so the
   eventual `pmf_cal_role_*.pkl` writes land in the challenger directory.

---

## Blocker 3 — PMF calibrator reads the full training table without a cutoff

**Where:** `scripts/calibrate_pmf.py` line 953

```python
training_df = pd.read_parquet(DATA_DIR / "training_table.parquet")
```

**Problem:** The walk-forward fold logic (lines 112–136) generates `(fold_start,
fold_end)` windows correctly, but the *input* table itself is not date-bounded.
If `training_table.parquet` has been built with rows past `as_of_date` (which
happens whenever `train.py --build-table-only` runs against the current
`player_game_stats.parquet`), the calibrator can include those rows in
`fold_end`-bounded training windows. This is a leakage path even though the
fold walker is correct.

**Required fix:** Either (a) add `--as-of-date` to `calibrate_pmf.py` and
filter `training_df` after load, or (b) ensure the upstream
`train.py --build-table-only` step has already accepted the same cutoff and
that the table on disk does not exceed it.

Approach (a) is simpler and isolated. Approach (b) is the same fix as Blocker 1
plus a contract that the calibrator trusts the upstream cutoff.

---

## Blocker 4 — `data/training_table.parquet` is a shared input

**Where:** `scripts/calibrate_pmf.py` line 953,
`scripts/build_stat_grid_pmfs.py` and other consumers; produced by
`pipelines/train.py::build_training_table` (called via
`scripts/train.py --build-table-only`).

**Problem:** The training table is a singleton at `data/training_table.parquet`.
A nightly challenger build that ran `--build-table-only` would overwrite the
production-baseline training table. Even if the trainer's models were
redirected to the challenger dir, this shared parquet would not be.

**Required fix:** Make `build_training_table()` accept and honor an
`output_path` argument. The challenger run would write to
`artifacts/models/challengers/<as_of_date>/training_table.parquet`; the
production calibration baseline at `data/training_table.parquet` would remain
untouched until promotion.

---

## Blocker 5 — Validator does not score real challenger artifacts

**Where:** `scripts/validate_champion_vs_challenger.py::metrics_placeholder()`

The current validator returns `None`-valued metric dicts for both champion and
challenger because, in dry-run, the two artifact sets are identical and there
is nothing to compute. Real-training mode requires actually loading both
artifact sets, generating PMFs over a leakage-safe holdout window, and
computing NLL / RPS / ECE / Brier / TOV-p0 / role-bucket metrics.

**Required fix:** Implement a `score_pmfs(model_dir, holdout_df) -> Metrics`
helper that uses the existing `nba_props_model.pipelines.predict.build_prop_pmfs`
shape against a held-out date range. Then call it twice — once with the
champion `model_dir`, once with the challenger `model_dir` — and apply the
existing gate logic against real numbers.

This change is moderate (~150–250 LOC) but depends on Blocker 2 being cleared
first so that the challenger has a real `model_dir` to score against.

---

## Why this is not being shipped in 13B

Each of Blockers 1–5 is a modification to working production code. Together
they are a multi-day refactor of `pipelines/train.py`,
`calibration/pmf_calibration.py`, `scripts/calibrate_pmf.py`, the artifact
producer, and the validator. The blast radius touches:

- the manual `retrain.yml` workflow (which currently runs `train.py` end-to-end),
- the `phase8.yml` calibration workflow,
- every consumer that imports `MODEL_DIR` at module scope,
- the canonical `data/training_table.parquet` baseline used by all current
  delivery scripts.

Doing this hastily inside a daily-automation PR would risk silent regressions
in the 15:00 / 18:00 / 20:00 / 22:25 / 03:25 / 06:30 UTC delivery jobs. Per
the Phase 13A non-interference rule, that is unacceptable.

---

## What Phase 13B *did* ship

- `docs/phase13b_real_training_blockers.md` — this document.
- `scripts/verify_daily_automation_health.py` — a 14-check daily health probe
  that prints `DAILY_AUTOMATION_HEALTH_PASS` when every production delivery
  surface is intact and the nightly training surface is non-interfering.
- `scripts/verify_training_automation.py` — updated to distinguish
  `TRAINING_AUTOMATION_DRY_RUN_VERIFICATION_PASS` from
  `TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS`. The real-training
  line is gated behind `dry_run=false` plus the existence of real challenger
  artifacts; until Blockers 1–5 are cleared it cannot fire by accident.
- `docs/nightly_training_calibration_runbook.md` — operator runbook covering
  both the dry-run path and the (still-blocked) real path.

The Phase 13A framework (registry, atomic promotion, lockfile, 14:30 UTC
cutoff, no-overlay scanner, secret scanner, failure-mode simulation) remains
unchanged and verified.

---

## Acceptance criteria for Phase 13C (whoever takes it)

To declare real nightly retraining live, all of the following must be true:

1. `pipelines/train.py::main` accepts `as_of_date` and `output_dir`, applies
   the date filter at every load site, and routes every `joblib.dump` through
   the swap.
2. `scripts/calibrate_pmf.py` accepts `--as-of-date` and `--output-dir` and
   does not write to `artifacts/models/`.
3. `data/training_table.parquet` is no longer overwritten by challenger runs.
4. `scripts/validate_champion_vs_challenger.py` scores real PMFs from both
   `model_dir`s on a leakage-safe holdout and computes real NLL / RPS / ECE /
   p0 / TOV / role-bucket / market-comparison metrics.
5. `scripts/run_nightly_training_and_calibration.py` `--no-dry-run` runs
   end-to-end on a real recent date in under 240 minutes and exits 0.
6. `scripts/verify_training_automation.py --as-of-date <date>` prints
   `TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS`.
7. The 09:30 UTC cron runs with `dry_run=false` and the manual `retrain.yml`
   workflow still succeeds independently.
8. Derek and Wizard of Odds delivery jobs continue to run without referencing
   any challenger directory.
