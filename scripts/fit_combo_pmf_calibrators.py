#!/usr/bin/env python3
"""M6.2 — Fit role-aware PMF calibrators for the 4 mission combo stats.

Reads data/oof_combo_pmfs.parquet, iterates
MISSION_REQUIRED_COMBOS_CANONICAL = ("stocks", "pa", "pr", "pra"),
calls fit_all() with 4-tuple (pmfs, outcomes, dates, role_buckets)
inputs per combo, and writes:

    artifacts/models/pmf_cal_role_stocks.pkl
    artifacts/models/pmf_cal_role_pa.pkl
    artifacts/models/pmf_cal_role_pr.pkl
    artifacts/models/pmf_cal_role_pra.pkl

Important: fit_all() unconditionally overwrites
artifacts/models/pmf_cal_meta.json. This script reads the existing
meta first (containing the 7 base-stat entries written earlier in
the same aggregate-calibration job by `calibrate_pmf.py
--aggregate-mode`), calls fit_all() for the 4 combos only, then
merges the base entries back in so the final meta.json contains all
11 mission-required canonical stats:

    pts, reb, ast, fg3m, tov, stl, blk, stocks, pa, pr, pra

The merged meta is tagged with combo-calibration provenance fields:

    combo_calibration_status: "fitted_m6_role_aware"
    combo_target_stats_canonical: ["stocks", "pa", "pr", "pra"]
    combo_target_stats_mission:   ["stl_blk", "pts_ast", "pts_reb", "pts_reb_ast"]

Invariants (drift guards from 02_CLAUDE_CONTROL_NOTES.md):
  #4 — Never fits 'ra' / 'reb_ast'. Uses MISSION_REQUIRED_COMBOS_CANONICAL,
       not the codebase-compat COMBO_STATS_CANONICAL (which contains 'ra').
  #6 — Produces RoleAwarePMFCalibrator instances via fit_all → loadable
       with joblib.load, exposes .apply(pmf, role_bucket) API.
  #8 — Never uses pickle.load; only joblib (indirectly via fit_all).
  #9 — Never uses `git add -A`; this script does no git ops.

Usage:
    python scripts/fit_combo_pmf_calibrators.py
    python scripts/fit_combo_pmf_calibrators.py --oof data/oof_combo_pmfs.parquet --seed 0
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure src is on PYTHONPATH when invoked as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.targets import (  # noqa: E402
    MISSION_REQUIRED_COMBOS_CANONICAL,
    MISSION_REQUIRED_COMBOS_MISSION,
)
from nba_props_model.calibration.pmf_calibration import fit_all  # noqa: E402
from nba_props_model.paths import MODEL_DIR  # noqa: E402

DEFAULT_OOF_PATH = REPO_ROOT / "data" / "oof_combo_pmfs.parquet"
CAL_META_PATH = MODEL_DIR / "pmf_cal_meta.json"
CAL_META_BACKUP_PATH = MODEL_DIR / "pmf_cal_meta_base_only.json.bak"

# Match calibrate_pmf.py's aggregate-mode thresholds so combo cells use
# the same data-volume gates as base cells.
MIN_VAL_ROWS_PER_STAT = 500
FINAL_CAL_MIN_TRAIN_DAYS = 180

# Required columns in the combo OOF parquet (M6.2 spec requirement #5).
REQUIRED_COLUMNS = ("stat", "pmf", "outcome", "game_date", "role_bucket")

# PMF validity tolerance (M6.2 spec requirement #7).
PMF_SUM_TOL = 1e-6

# Mission-required canonical 11 stats — the union M6.2's merged meta
# MUST contain at job end.
MISSION_REQUIRED_CANONICAL_11 = (
    "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
    "stocks", "pa", "pr", "pra",
)

logger = logging.getLogger("fit_combo_pmf_calibrators")


def _load_existing_meta() -> dict | None:
    """Load the base-stat-only pmf_cal_meta.json written earlier in the job.

    Returns None if the file does not exist. In Phase 8 this file IS
    expected to exist because calibrate_pmf.py --aggregate-mode runs
    in the same aggregate-calibration job, BEFORE this script.
    """
    if not CAL_META_PATH.exists():
        logger.warning(
            f"No existing pmf_cal_meta.json at {CAL_META_PATH}. "
            "In Phase 8 this is unexpected — calibrate_pmf.py "
            "--aggregate-mode should have written it earlier in the same "
            "job. Continuing; merged meta will lack base-stat entries "
            "and the M6.2 self-check at end-of-run will warn."
        )
        return None
    with open(CAL_META_PATH) as f:
        return json.load(f)


def _validate_columns(df: pd.DataFrame) -> int:
    """Verify the combo OOF parquet has all required columns.

    Returns 0 on success, nonzero on missing columns.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        logger.error(
            f"Combo OOF parquet missing required columns: {missing}. "
            f"Required: {list(REQUIRED_COLUMNS)}. "
            f"Got: {list(df.columns)}"
        )
        return 10
    return 0


def _validate_pmfs(pmfs: np.ndarray, stat: str) -> int:
    """Verify PMFs are finite, nonnegative, and sum to 1 within tolerance.

    Returns 0 on success, nonzero on validity failure.
    """
    if not np.isfinite(pmfs).all():
        bad_n = int((~np.isfinite(pmfs)).any(axis=1).sum())
        logger.error(
            f"  {stat}: {bad_n} PMF rows contain non-finite values"
        )
        return 20
    if (pmfs < -1e-12).any():
        bad_n = int((pmfs < -1e-12).any(axis=1).sum())
        logger.error(
            f"  {stat}: {bad_n} PMF rows contain negative entries "
            f"(tolerance: -1e-12)"
        )
        return 21
    sums = pmfs.sum(axis=1)
    abs_err = np.abs(sums - 1.0)
    max_err = float(abs_err.max())
    if max_err > PMF_SUM_TOL:
        bad_n = int((abs_err > PMF_SUM_TOL).sum())
        logger.error(
            f"  {stat}: {bad_n} PMF rows fail sum tolerance "
            f"(max_err={max_err:.2e} > {PMF_SUM_TOL:.0e})"
        )
        return 22
    logger.info(
        f"  {stat}: PMF validity OK "
        f"(max_sum_err={max_err:.2e}, all finite, all nonnegative)"
    )
    return 0


def _build_per_stat_inputs(df: pd.DataFrame) -> tuple[dict[str, tuple], int]:
    """Build the fit_all input dict for the 4 mission combos.

    Returns ({combo: (pmfs, outcomes, dates, role_buckets)}, exit_code).
    exit_code is 0 on success; nonzero if any combo has missing rows,
    invalid PMFs, or other hard failures. (Insufficient rows are a
    warning, not a hard fail — that combo is skipped and remaining
    combos proceed.)
    """
    per_stat: dict[str, tuple] = {}
    for combo in MISSION_REQUIRED_COMBOS_CANONICAL:
        sub = df[df["stat"] == combo]
        if len(sub) == 0:
            logger.error(f"  {combo}: ZERO rows in combo OOF")
            return per_stat, 30
        # Drop rows whose PMF was flagged invalid upstream.
        if "pmf_valid" in sub.columns:
            valid_mask = sub["pmf_valid"] == True  # noqa: E712
            dropped = int((~valid_mask).sum())
            if dropped > 0:
                logger.warning(
                    f"  {combo}: dropping {dropped} rows with pmf_valid=False"
                )
            sub = sub[valid_mask]
        if len(sub) < MIN_VAL_ROWS_PER_STAT:
            logger.warning(
                f"  {combo}: only {len(sub)} valid rows < "
                f"MIN_VAL_ROWS_PER_STAT ({MIN_VAL_ROWS_PER_STAT}) — "
                "skipping (NEEDS_MORE_DATA)"
            )
            continue
        # Stack PMF arrays into a 2D float64 matrix.
        pmf_arrays = [np.asarray(p, dtype=np.float64) for p in sub["pmf"].values]
        lengths = {len(p) for p in pmf_arrays}
        if len(lengths) > 1:
            max_len = max(lengths)
            logger.warning(
                f"  {combo}: PMF support lengths vary "
                f"({sorted(lengths)}); right-padding all to max={max_len}"
            )
            pmf_arrays = [
                (np.concatenate([p, np.zeros(max_len - len(p))])
                 if len(p) < max_len else p)
                for p in pmf_arrays
            ]
        pmfs = np.stack(pmf_arrays, axis=0)
        # Explicit PMF validity check (M6.2 spec requirement #7).
        rc = _validate_pmfs(pmfs, combo)
        if rc != 0:
            return per_stat, rc
        outcomes = sub["outcome"].astype(int).to_numpy()
        dates = np.array([
            pd.Timestamp(str(d)) for d in sub["game_date"].to_numpy()
        ])
        role_buckets = sub["role_bucket"].astype(str).to_numpy()
        per_stat[combo] = (pmfs, outcomes, dates, role_buckets)
        logger.info(
            f"  {combo}: n={len(pmfs):,} support={pmfs.shape[1]} "
            f"role_buckets_present={sorted(set(role_buckets))}"
        )
    return per_stat, 0


def _merge_meta(base_meta: dict | None, combo_meta: dict) -> dict:
    """Merge combo meta entries into the base-only meta.

    Strategy:
      - Preserve all base-meta top-level keys (e.g. calibration_target,
        pmf_active_available, calibration_version).
      - Union meta["stats"]: base entries first, combo entries layered
        on top.
      - Surface combo-only top-level fields ONLY IF the base did not
        already set them.
      - Tag with combo-calibration provenance fields per M6.2 spec.
    """
    if base_meta is None:
        merged = dict(combo_meta)
    else:
        merged = dict(base_meta)
        merged_stats = dict(base_meta.get("stats", {}))
        merged_stats.update(combo_meta.get("stats", {}))
        merged["stats"] = merged_stats
        for k, v in combo_meta.items():
            if k == "stats":
                continue
            if k not in merged:
                merged[k] = v
    # M6.2 provenance fields — per locked spec requirement #12.
    merged["combo_calibration_fitter"] = "fit_combo_pmf_calibrators.py"
    merged["combo_calibration_source_oof"] = "data/oof_combo_pmfs.parquet"
    merged["combo_calibration_status"] = "fitted_m6_role_aware"
    merged["combo_target_stats_canonical"] = list(MISSION_REQUIRED_COMBOS_CANONICAL)
    merged["combo_target_stats_mission"] = list(MISSION_REQUIRED_COMBOS_MISSION)
    merged["combo_calibration_combos_fitted"] = sorted(
        combo_meta.get("stats", {}).keys()
    )
    return merged


def main() -> int:
    ap = argparse.ArgumentParser(
        description="M6.2 — fit role-aware combo PMF calibrators."
    )
    ap.add_argument(
        "--oof",
        default=str(DEFAULT_OOF_PATH),
        help=f"Combo OOF parquet (default: {DEFAULT_OOF_PATH}).",
    )
    ap.add_argument(
        "--fold-days", type=int, default=28,
        help="Walk-forward fold size (default: 28).",
    )
    ap.add_argument(
        "--seed", type=int, default=0,
        help="RNG seed (default: 0).",
    )
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    oof_path = Path(args.oof)
    if not oof_path.exists():
        logger.error(f"OOF combo parquet not found: {oof_path}")
        return 2

    logger.info("=" * 60)
    logger.info("M6.2 fit_combo_pmf_calibrators — start")
    logger.info("=" * 60)
    logger.info(f"Reading combo OOF: {oof_path}")
    df = pd.read_parquet(oof_path)
    logger.info(f"  rows: {len(df):,}")
    logger.info(f"  columns: {list(df.columns)}")
    logger.info(f"  stats present: {sorted(df['stat'].unique())}")

    # Required columns (M6.2 spec requirement #5).
    rc = _validate_columns(df)
    if rc != 0:
        return rc

    # Drift guard #4: never fit ra / reb_ast.
    forbidden = {"ra", "reb_ast"} & set(df["stat"].unique())
    if forbidden:
        logger.error(
            f"Combo OOF contains forbidden stat(s): {sorted(forbidden)} — "
            "DRIFT GUARD #4 VIOLATION. Mission combos must be only "
            "stocks/pa/pr/pra. Investigate "
            "scripts/build_combo_oof_pmfs_from_base_oof.py COMBO_DEFS."
        )
        return 3

    # M6.2 spec requirement #6: validate each combo stat is present.
    missing_combos = set(MISSION_REQUIRED_COMBOS_CANONICAL) - set(df["stat"].unique())
    if missing_combos:
        logger.error(
            f"Combo OOF missing mission combos: {sorted(missing_combos)}. "
            "Phase 8 aggregate-calibration must produce all 4 of "
            f"{MISSION_REQUIRED_COMBOS_CANONICAL}."
        )
        return 4

    per_stat_inputs, build_rc = _build_per_stat_inputs(df)
    if build_rc != 0:
        return build_rc
    if not per_stat_inputs:
        logger.error(
            "All combos failed MIN_VAL_ROWS_PER_STAT — aborting before "
            "fit_all to avoid overwriting pmf_cal_meta.json with an "
            "empty stats dict."
        )
        return 5

    # Back up the existing base-only meta BEFORE fit_all overwrites it.
    base_meta = _load_existing_meta()
    if base_meta is not None:
        shutil.copy2(CAL_META_PATH, CAL_META_BACKUP_PATH)
        logger.info(
            f"Backed up existing base meta "
            f"({len(base_meta.get('stats', {}))} stat entries) "
            f"to {CAL_META_BACKUP_PATH}"
        )

    logger.info(
        f"Calling fit_all() for combos: "
        f"{sorted(per_stat_inputs.keys())}"
    )
    rng = np.random.default_rng(args.seed)
    combo_meta = fit_all(
        per_stat_inputs,
        fold_days=args.fold_days,
        min_train_days=FINAL_CAL_MIN_TRAIN_DAYS,
        rng=rng,
    )
    logger.info(
        f"fit_all wrote {len(combo_meta.get('stats', {}))} combo stat "
        "entries and overwrote pmf_cal_meta.json with combo-only meta."
    )

    # M6.2 spec requirement #13: log written pickle paths and sizes.
    for combo in per_stat_inputs.keys():
        pkl = MODEL_DIR / f"pmf_cal_role_{combo}.pkl"
        if pkl.exists():
            size = pkl.stat().st_size
            logger.info(f"  wrote {pkl} ({size:,} bytes)")
        else:
            logger.error(
                f"  EXPECTED pkl missing after fit_all: {pkl}"
            )

    # Merge base + combo and rewrite pmf_cal_meta.json with all 11.
    merged_meta = _merge_meta(base_meta, combo_meta)
    with open(CAL_META_PATH, "w") as f:
        json.dump(merged_meta, f, indent=2, default=str)
    merged_stats = sorted(merged_meta.get("stats", {}).keys())
    logger.info(
        f"Rewrote {CAL_META_PATH} with merged meta "
        f"({len(merged_stats)} stats total: {merged_stats})"
    )

    # M6.2 spec requirement #14: nonzero exit if any combo pkl missing.
    missing_pkls = []
    empty_pkls = []
    for combo in per_stat_inputs.keys():
        pkl = MODEL_DIR / f"pmf_cal_role_{combo}.pkl"
        if not pkl.exists():
            missing_pkls.append(combo)
        elif pkl.stat().st_size == 0:
            empty_pkls.append(combo)
    if missing_pkls or empty_pkls:
        logger.error(
            f"Combo pkl validation FAILED — missing: {missing_pkls}, "
            f"empty: {empty_pkls}"
        )
        return 6

    # M6 acceptance self-check: merged meta should cover all 11.
    missing_in_merged = (
        set(MISSION_REQUIRED_CANONICAL_11) - set(merged_stats)
    )
    if missing_in_merged:
        logger.warning(
            f"Merged meta is missing {sorted(missing_in_merged)} from "
            "the 11-stat mission set. This indicates calibrate_pmf.py "
            "--aggregate-mode did not produce one of the base stats "
            "earlier in the job. M6 acceptance §'all 11 fitted stats in "
            "pmf_cal_meta.json' will fail downstream — investigate "
            "before promoting to production."
        )
    else:
        logger.info(
            "Merged meta covers all 11 mission canonical stats: "
            f"{sorted(MISSION_REQUIRED_CANONICAL_11)}"
        )

    logger.info("=" * 60)
    logger.info("M6.2 fit_combo_pmf_calibrators — done")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
