#!/usr/bin/env python3
"""M6.3 — Build the 11-stat x 6-role-bucket calibration A/B report.

Reads:
    data/oof_pmfs.parquet         -> 7 base stats: pts, reb, ast, fg3m, tov, stl, blk
    data/oof_combo_pmfs.parquet   -> 4 combo stats: stocks, pa, pr, pra

Applies the 11 role-aware calibrators from artifacts/models/:
    pmf_cal_role_{pts,reb,ast,fg3m,tov,stl,blk,stocks,pa,pr,pra}.pkl

Emits a dense 66-row matrix (11 stats x 6 role buckets) with raw-vs-calibrated
metrics per cell:

    artifacts/docs/m6_3_stat_role_calibration_matrix_{run_date}.csv
    artifacts/docs/m6_3_stat_role_calibration_report_{run_date}.md
    artifacts/docs/m6_3_stat_role_calibration_report_{run_date}.meta.json

Status thresholds per packet 03_ACCEPTANCE_CRITERIA §3 + M6 acceptance:
    n < 200                        -> NEEDS_MORE_DATA
    delta_nll = cal_nll - raw_nll <= bucket_threshold  -> PASS  (else REVIEW)
    bucket thresholds:
        starter:        +0.003
        core/rotation/bench/fringe/inactive_risk: +0.005

Caveats (informational at M6.3, hard gates at M7):
    sparse stats (stl, blk): calibrated p0 error must not worsen by > 0.01
    combo stats (stocks, pa, pr, pra): calibrated |mean bias| must not worsen by > 0.5

Hard verification at end:
    - exactly 66 rows
    - all 11 expected stats present
    - all 6 expected role buckets present
    - pa, pr, pra present
    - ra and reb_ast absent
    - no missing cells, no cells with n < 200
    - market_eval_available = false (we do not claim market superiority)

Prints `M6_3_STAT_ROLE_REPORT_PASS` on success. Nonzero exit on failure.

Drift guards (per 02_CLAUDE_CONTROL_NOTES.md):
    #4  Mission canonical set only (no `ra` / `reb_ast`).
    #6  Role-aware calibrators loaded via load_calibrator() and applied via
        .apply(pmf, role_bucket=...).
    #8  Calibrator load is via joblib (indirectly through load_calibrator);
        this script never calls pickle.load.
    #9  No git operations anywhere in this script.

Usage:
    PYTHONPATH=src python scripts/build_m6_3_stat_role_calibration_report.py
    PYTHONPATH=src python scripts/build_m6_3_stat_role_calibration_report.py --run-date 2026-05-11
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# -- Path setup ------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.calibration.pmf_calibration import load_calibrator  # noqa: E402

# -- Constants -------------------------------------------------------------
BASE_STATS = ("pts", "reb", "ast", "fg3m", "tov", "stl", "blk")
COMBO_STATS = ("stocks", "pa", "pr", "pra")
EXPECTED_STATS = BASE_STATS + COMBO_STATS  # 11 mission canonical
EXPECTED_ROLE_BUCKETS = (
    "inactive_risk", "fringe", "bench", "rotation", "core", "starter",
)
FORBIDDEN_STATS = ("ra", "reb_ast")
MIN_CELL_N = 200
EPS = 1e-9

# Role-bucket NLL regression thresholds per packet 03_ACCEPTANCE §3 +
# M6 acceptance. starter is the strictest; all other buckets get the
# core threshold by default (the packet only explicitly names starter
# and core, so non-starter buckets inherit core's looser threshold).
BUCKET_NLL_THRESHOLD = {
    "starter": 0.003,
    "core": 0.005,
    "rotation": 0.005,
    "bench": 0.005,
    "fringe": 0.005,
    "inactive_risk": 0.005,
}

# Sparse-stat and combo-stat caveat thresholds (informational at M6.3,
# hard gates at M7 per packet structure).
SPARSE_P0_REGRESSION_LIMIT = 0.01
COMBO_MEAN_BIAS_REGRESSION_LIMIT = 0.5

DATA_DIR = REPO_ROOT / "data"
MODEL_DIR = REPO_ROOT / "artifacts" / "models"
DOCS_DIR = REPO_ROOT / "artifacts" / "docs"
BASE_OOF_PATH = DATA_DIR / "oof_pmfs.parquet"
COMBO_OOF_PATH = DATA_DIR / "oof_combo_pmfs.parquet"

# Market evaluation is deliberately unavailable in M6.3. Real opening-line
# de-vigged over/under probabilities are NOT joined onto OOF rows in this
# milestone. Wiring that is a separate workstream gated on the
# market_eval_not_wired warning in artifacts/docs/diagnostics_*.md.
MARKET_EVAL_AVAILABLE = False
BASELINE_FOR_M6_3 = "raw_uncalibrated_pmf"
STATUS_THRESHOLD_POLICY = "starter +0.003 NLL, all other role buckets +0.005 NLL"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("m6_3_report")


# -- PMF metric helpers (self-contained; no internal imports) --------------

def _pmf_to_array(p) -> np.ndarray:
    """Coerce whatever pandas/parquet returned to a 1-D float ndarray."""
    return np.asarray(p, dtype=float)


def _safe_log(p: float) -> float:
    return float(np.log(max(p, EPS)))


def _nll_one(pmf: np.ndarray, outcome: int) -> float:
    """Negative log-likelihood of the realized outcome under the PMF."""
    y = int(min(max(outcome, 0), len(pmf) - 1))
    return -_safe_log(float(pmf[y]))


def _rps_one(pmf: np.ndarray, outcome: int) -> float:
    """Discrete ranked probability score / discrete CRPS.

    Sum over k of (CDF_pred(k) - 1{k >= y})^2.
    """
    cdf = np.cumsum(pmf)
    y = int(min(max(outcome, 0), len(pmf) - 1))
    indicator = np.zeros(len(pmf), dtype=float)
    indicator[y:] = 1.0
    return float(np.sum((cdf - indicator) ** 2))


def _mean_one(pmf: np.ndarray) -> float:
    """Expected value of a PMF supported on 0..len(pmf)-1."""
    return float(np.sum(pmf * np.arange(len(pmf), dtype=float)))


def _p0_one(pmf: np.ndarray) -> float:
    return float(pmf[0]) if len(pmf) > 0 else float("nan")


def _randomized_pit_one(pmf: np.ndarray, outcome: int, rng: np.random.Generator) -> float:
    """Randomized PIT value in [0,1] for one discrete observation."""
    cdf = np.cumsum(pmf)
    y = int(min(max(outcome, 0), len(pmf) - 1))
    lower = float(cdf[y - 1]) if y > 0 else 0.0
    upper = float(cdf[y])
    return lower + float(rng.uniform(0.0, 1.0)) * (upper - lower)


def _pit_ks_distance(pits: np.ndarray) -> float:
    """Two-sided one-sample KS distance from Uniform(0,1)."""
    n = len(pits)
    if n == 0:
        return float("nan")
    sorted_pits = np.sort(np.asarray(pits, dtype=float))
    d_plus = float(np.max((np.arange(1, n + 1) / n) - sorted_pits))
    d_minus = float(np.max(sorted_pits - (np.arange(0, n) / n)))
    return max(d_plus, d_minus)


def _ece_binary(probs: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> float:
    """Standard binary ECE on (probabilities, binary outcomes)."""
    probs = np.asarray(probs, dtype=float)
    outcomes = np.asarray(outcomes, dtype=int)
    n_total = len(probs)
    if n_total == 0:
        return float("nan")
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idx = np.clip(np.digitize(probs, bin_edges[1:-1], right=False), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        mask = bin_idx == b
        if not np.any(mask):
            continue
        w = float(np.sum(mask)) / n_total
        p_mean = float(np.mean(probs[mask]))
        o_mean = float(np.mean(outcomes[mask]))
        ece += w * abs(p_mean - o_mean)
    return float(ece)


def _binary_over_at_median(pmfs: list[np.ndarray], outcomes: np.ndarray):
    """Compute P(X > median+0.5) per row and the corresponding indicator."""
    if len(outcomes) == 0:
        return np.array([]), np.array([])
    ref_line = float(np.median(outcomes)) + 0.5
    over_probs = np.empty(len(pmfs), dtype=float)
    for i, pmf in enumerate(pmfs):
        cdf = np.cumsum(pmf)
        k = int(np.floor(ref_line))
        k = min(max(k, 0), len(pmf) - 1)
        over_probs[i] = 1.0 - float(cdf[k])
    over_realised = (outcomes > ref_line).astype(int)
    return over_probs, over_realised


# -- Cell metric computation -----------------------------------------------

def _compute_cell(
    stat: str,
    role_bucket: str,
    sub: pd.DataFrame,
    pmf_col: str,
    calibrator,
    rng_seed: int,
) -> dict:
    """Compute all M6.3 metrics for one (stat, role_bucket) cell."""
    pmfs_raw = [_pmf_to_array(p) for p in sub[pmf_col].tolist()]
    outcomes = sub["outcome"].astype(int).to_numpy()
    n = len(outcomes)

    pmfs_cal = [
        _pmf_to_array(calibrator.apply(p, role_bucket=role_bucket))
        for p in pmfs_raw
    ]

    raw_nll = float(np.mean([_nll_one(p, y) for p, y in zip(pmfs_raw, outcomes)]))
    cal_nll = float(np.mean([_nll_one(p, y) for p, y in zip(pmfs_cal, outcomes)]))
    raw_rps = float(np.mean([_rps_one(p, y) for p, y in zip(pmfs_raw, outcomes)]))
    cal_rps = float(np.mean([_rps_one(p, y) for p, y in zip(pmfs_cal, outcomes)]))

    raw_mean = float(np.mean([_mean_one(p) for p in pmfs_raw]))
    cal_mean = float(np.mean([_mean_one(p) for p in pmfs_cal]))
    actual_mean = float(np.mean(outcomes))

    raw_p0 = float(np.mean([_p0_one(p) for p in pmfs_raw]))
    cal_p0 = float(np.mean([_p0_one(p) for p in pmfs_cal]))
    actual_p0 = float(np.mean(outcomes == 0))

    rng = np.random.default_rng(rng_seed)
    pits_cal = np.array([
        _randomized_pit_one(p, y, rng) for p, y in zip(pmfs_cal, outcomes)
    ])
    pit_mean = float(np.mean(pits_cal))
    pit_std = float(np.std(pits_cal))
    pit_ks = _pit_ks_distance(pits_cal)

    over_probs_cal, over_realised = _binary_over_at_median(pmfs_cal, outcomes)
    ece = _ece_binary(over_probs_cal, over_realised)

    # Status per packet §3 + M6 acceptance:
    #   n < 200          -> NEEDS_MORE_DATA
    #   role-bucket NLL regression threshold (delta_nll = cal_nll - raw_nll):
    #     starter: +0.003,  core/rotation/bench/fringe/inactive_risk: +0.005
    #   PASS if delta_nll <= threshold; REVIEW otherwise.
    # Sparse-stat (stl, blk) and combo-stat caveats are reported in a
    # separate `caveats` field — informational at M6.3 stage; they become
    # hard gates at M7 promotion.
    delta_nll = cal_nll - raw_nll
    threshold = BUCKET_NLL_THRESHOLD.get(role_bucket, 0.005)

    caveats: list[str] = []
    if stat in ("stl", "blk"):
        p0_err_increase = abs(cal_p0 - actual_p0) - abs(raw_p0 - actual_p0)
        if p0_err_increase > SPARSE_P0_REGRESSION_LIMIT:
            caveats.append(f"sparse_p0_worsened_{p0_err_increase:+.3f}")
    if stat in ("stocks", "pa", "pr", "pra"):
        mean_bias_increase = (
            abs(cal_mean - actual_mean) - abs(raw_mean - actual_mean)
        )
        if mean_bias_increase > COMBO_MEAN_BIAS_REGRESSION_LIMIT:
            caveats.append(f"combo_mean_bias_worsened_{mean_bias_increase:+.2f}")

    if n < MIN_CELL_N:
        status = "NEEDS_MORE_DATA"
    elif delta_nll <= threshold:
        status = "PASS"
    else:
        status = "REVIEW"

    return {
        "stat": stat,
        "role_bucket": role_bucket,
        "n": int(n),
        "raw_nll": raw_nll,
        "calibrated_nll": cal_nll,
        "delta_nll_cal_minus_raw": delta_nll,
        "raw_rps": raw_rps,
        "calibrated_rps": cal_rps,
        "delta_rps_cal_minus_raw": cal_rps - raw_rps,
        "raw_mean": raw_mean,
        "calibrated_mean": cal_mean,
        "actual_mean": actual_mean,
        "raw_mean_bias": raw_mean - actual_mean,
        "calibrated_mean_bias": cal_mean - actual_mean,
        "raw_p0": raw_p0,
        "calibrated_p0": cal_p0,
        "actual_p0": actual_p0,
        "raw_p0_error": raw_p0 - actual_p0,
        "calibrated_p0_error": cal_p0 - actual_p0,
        "pit_mean": pit_mean,
        "pit_std": pit_std,
        "pit_ks": pit_ks,
        "ece": ece,
        "nll_threshold": threshold,
        "caveats": ";".join(caveats) if caveats else "",
        "status": status,
    }


def _empty_cell(stat: str, role_bucket: str) -> dict:
    """A NaN-filled placeholder when no rows exist for a (stat, role_bucket)."""
    nan_keys = (
        "raw_nll", "calibrated_nll", "delta_nll_cal_minus_raw",
        "raw_rps", "calibrated_rps", "delta_rps_cal_minus_raw",
        "raw_mean", "calibrated_mean", "actual_mean",
        "raw_mean_bias", "calibrated_mean_bias",
        "raw_p0", "calibrated_p0", "actual_p0",
        "raw_p0_error", "calibrated_p0_error",
        "pit_mean", "pit_std", "pit_ks", "ece",
        "nll_threshold",
    )
    cell = {"stat": stat, "role_bucket": role_bucket, "n": 0}
    cell.update({k: float("nan") for k in nan_keys})
    cell["caveats"] = ""
    cell["status"] = "NEEDS_MORE_DATA"
    return cell


# -- Output writers --------------------------------------------------------

def _fmt_num(x) -> str:
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    if not np.isfinite(v):
        return "—"
    if abs(v) < 1e-4 or abs(v) >= 1e4:
        return f"{v:.3e}"
    return f"{v:.4f}"


def _write_csv(path: Path, matrix: pd.DataFrame) -> None:
    matrix.to_csv(path, index=False)


def _write_markdown(path: Path, matrix: pd.DataFrame, run_date: str) -> None:
    stat_order = {s: i for i, s in enumerate(EXPECTED_STATS)}
    rb_order = {r: i for i, r in enumerate(EXPECTED_ROLE_BUCKETS)}
    sorted_matrix = matrix.assign(
        _so=matrix["stat"].map(stat_order),
        _ro=matrix["role_bucket"].map(rb_order),
    ).sort_values(["_so", "_ro"]).drop(columns=["_so", "_ro"])

    n_pass = int((matrix["status"] == "PASS").sum())
    n_review = int((matrix["status"] == "REVIEW").sum())
    n_need = int((matrix["status"] == "NEEDS_MORE_DATA").sum())
    n_with_caveats = int((matrix["caveats"].astype(str).str.len() > 0).sum())

    lines = []
    lines.append(f"# M6.3 — Stat × Role-Bucket Calibration A/B Report — {run_date}")
    lines.append("")
    lines.append(f"_Generated {datetime.now(timezone.utc).isoformat()}_")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    lines.append(
        f"- Base OOF: `{BASE_OOF_PATH.relative_to(REPO_ROOT)}` "
        f"({len(BASE_STATS)} base stats: {', '.join(BASE_STATS)})"
    )
    lines.append(
        f"- Combo OOF: `{COMBO_OOF_PATH.relative_to(REPO_ROOT)}` "
        f"({len(COMBO_STATS)} combo stats: {', '.join(COMBO_STATS)})"
    )
    lines.append(
        f"- Calibrators: `{MODEL_DIR.relative_to(REPO_ROOT)}/pmf_cal_role_*.pkl` "
        f"(all {len(EXPECTED_STATS)} mission canonical stats)"
    )
    lines.append(f"- Baseline for M6.3: `{BASELINE_FOR_M6_3}`")
    lines.append(f"- Status threshold policy: {STATUS_THRESHOLD_POLICY}")
    lines.append("")
    lines.append("## Market evaluation status")
    lines.append("")
    lines.append(
        "**Market-relative evaluation unavailable**: opening-line de-vigged "
        "over/under probabilities are not joined onto OOF rows in this "
        "milestone. `market_eval_available = false`. No market superiority "
        "claim is implied by this report."
    )
    lines.append("")
    lines.append(
        f"## Per-cell metrics ({len(matrix)} rows = "
        f"{len(EXPECTED_STATS)} stats × {len(EXPECTED_ROLE_BUCKETS)} role buckets)"
    )
    lines.append("")
    header_cols = [
        "stat", "role_bucket", "n",
        "raw_nll", "cal_nll", "Δ_nll",
        "raw_rps", "cal_rps", "Δ_rps",
        "raw_mean", "cal_mean", "actual_mean",
        "raw_bias", "cal_bias",
        "raw_p0", "cal_p0", "actual_p0",
        "raw_p0_err", "cal_p0_err",
        "pit_mean", "pit_std", "pit_ks", "ece",
        "threshold", "caveats",
        "status",
    ]
    align = (
        ["---", "---"]    # stat, role_bucket
        + ["---:"]        # n
        + ["---:"] * 20   # 20 numeric metric columns through ece
        + ["---:"]        # threshold
        + ["---", "---"]  # caveats, status
    )
    lines.append("| " + " | ".join(header_cols) + " |")
    lines.append("|" + "|".join(align) + "|")
    for _, r in sorted_matrix.iterrows():
        row_cells = [
            r["stat"],
            r["role_bucket"],
            str(int(r["n"])),
            _fmt_num(r["raw_nll"]),
            _fmt_num(r["calibrated_nll"]),
            _fmt_num(r["delta_nll_cal_minus_raw"]),
            _fmt_num(r["raw_rps"]),
            _fmt_num(r["calibrated_rps"]),
            _fmt_num(r["delta_rps_cal_minus_raw"]),
            _fmt_num(r["raw_mean"]),
            _fmt_num(r["calibrated_mean"]),
            _fmt_num(r["actual_mean"]),
            _fmt_num(r["raw_mean_bias"]),
            _fmt_num(r["calibrated_mean_bias"]),
            _fmt_num(r["raw_p0"]),
            _fmt_num(r["calibrated_p0"]),
            _fmt_num(r["actual_p0"]),
            _fmt_num(r["raw_p0_error"]),
            _fmt_num(r["calibrated_p0_error"]),
            _fmt_num(r["pit_mean"]),
            _fmt_num(r["pit_std"]),
            _fmt_num(r["pit_ks"]),
            _fmt_num(r["ece"]),
            _fmt_num(r["nll_threshold"]),
            (r["caveats"] if isinstance(r["caveats"], str) and r["caveats"] else "—"),
            r["status"],
        ]
        lines.append("| " + " | ".join(row_cells) + " |")
    lines.append("")
    lines.append("## Status legend")
    lines.append("")
    lines.append(
        "- **PASS**: `delta_nll <= bucket_threshold` (starter: +0.003, "
        "core/rotation/bench/fringe/inactive_risk: +0.005). Role-aware "
        "calibration does not regress NLL beyond the bucket-specific tolerance."
    )
    lines.append(
        "- **REVIEW**: `delta_nll > bucket_threshold` — calibration regresses "
        "NLL beyond tolerance for this role bucket; needs human review for "
        "M7 promotion decision."
    )
    lines.append(
        f"- **NEEDS_MORE_DATA**: cell has n < {MIN_CELL_N}; insufficient OOF "
        "rows for a confident calibration judgment."
    )
    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "Caveats are informational quality flags at M6.3 reporting stage. "
        "They do not change PASS/REVIEW here but become hard gates at M7 "
        "promotion (per packet §3 sparse-stat and combo-stat sections):"
    )
    lines.append("")
    lines.append(
        f"- `sparse_p0_worsened_<delta>` (stl, blk): calibrated p0 error "
        f"worsens by > {SPARSE_P0_REGRESSION_LIMIT} vs raw."
    )
    lines.append(
        f"- `combo_mean_bias_worsened_<delta>` (stocks, pa, pr, pra): "
        f"calibrated |mean bias| worsens by > {COMBO_MEAN_BIAS_REGRESSION_LIMIT} vs raw."
    )
    lines.append("")
    lines.append("## Aggregate verdict")
    lines.append("")
    lines.append(f"- Total cells: {len(matrix)} (expected 66)")
    lines.append(
        f"- Status counts: PASS={n_pass}, REVIEW={n_review}, "
        f"NEEDS_MORE_DATA={n_need}"
    )
    lines.append(f"- Cells with caveats: {n_with_caveats}")
    lines.append("")

    path.write_text("\n".join(lines) + "\n")


def _write_meta(
    path: Path, matrix: pd.DataFrame, run_date: str,
    verification_errors: list[str],
) -> None:
    # -- Cell coverage --
    expected_pairs = {(s, r) for s in EXPECTED_STATS for r in EXPECTED_ROLE_BUCKETS}
    seen_pairs = set(
        zip(matrix["stat"].astype(str), matrix["role_bucket"].astype(str))
    )
    # missing_cells: expected stat x role_bucket pairs that either do not
    # appear in the matrix at all OR appear only as a NaN placeholder with
    # n = 0. With the current loop emitting a placeholder for empty cells,
    # the n == 0 check is the dominant source of "missing" semantics.
    missing_pairs_list = sorted(
        [list(p) for p in (expected_pairs - seen_pairs)]
    )
    zero_n_rows = matrix[matrix["n"] == 0]
    zero_n_pairs = sorted(
        [
            [str(r["stat"]), str(r["role_bucket"])]
            for _, r in zero_n_rows.iterrows()
        ]
    )
    missing_cells_list = missing_pairs_list + zero_n_pairs

    # cells_with_0_n_lt_200: cells present in the matrix with 0 < n < MIN_CELL_N.
    sparse_rows = matrix[(matrix["n"] > 0) & (matrix["n"] < MIN_CELL_N)]
    cells_with_0_n_lt_200_list = sorted(
        [
            [str(r["stat"]), str(r["role_bucket"]), int(r["n"])]
            for _, r in sparse_rows.iterrows()
        ]
    )

    # -- Observed structure --
    observed_stats = sorted(set(matrix["stat"].astype(str)))
    observed_role_buckets = sorted(set(matrix["role_bucket"].astype(str)))
    forbidden_stats_present = sorted(
        set(observed_stats) & set(FORBIDDEN_STATS)
    )

    # -- n stats --
    n_int = matrix["n"].astype(int)
    min_n = int(n_int.min()) if len(n_int) > 0 else 0
    max_n = int(n_int.max()) if len(n_int) > 0 else 0

    # -- Status / caveats --
    status_counts = {
        "PASS": int((matrix["status"] == "PASS").sum()),
        "REVIEW": int((matrix["status"] == "REVIEW").sum()),
        "NEEDS_MORE_DATA": int((matrix["status"] == "NEEDS_MORE_DATA").sum()),
    }
    caveat_cells_count = int(
        (matrix["caveats"].astype(str).str.len() > 0).sum()
    )

    # -- Verification verdict --
    m6_3_report_pass = len(verification_errors) == 0

    meta = {
        # Run identification
        "run_date": run_date,
        "report_date": run_date,  # back-compat
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),

        # Row coverage
        "rows": int(len(matrix)),
        "expected_rows": len(EXPECTED_STATS) * len(EXPECTED_ROLE_BUCKETS),
        "n_cells": int(len(matrix)),  # back-compat

        # Expected vs observed structure
        "expected_stats": list(EXPECTED_STATS),
        "expected_stats_canonical": list(EXPECTED_STATS),  # back-compat
        "observed_stats": observed_stats,
        "expected_role_buckets": list(EXPECTED_ROLE_BUCKETS),
        "observed_role_buckets": observed_role_buckets,

        # Cell coverage
        "missing_cells": missing_cells_list,
        "cells_with_0_n_lt_200": cells_with_0_n_lt_200_list,
        "min_n": min_n,
        "max_n": max_n,

        # Status / caveats
        "status_counts": status_counts,
        "review_cells_count": status_counts["REVIEW"],
        "caveat_cells_count": caveat_cells_count,
        "n_cells_with_caveats": caveat_cells_count,  # back-compat

        # Policy / config
        "baseline_for_m6_3": BASELINE_FOR_M6_3,
        "market_eval_available": MARKET_EVAL_AVAILABLE,
        "status_threshold_policy": STATUS_THRESHOLD_POLICY,
        "bucket_nll_thresholds": dict(BUCKET_NLL_THRESHOLD),
        "sparse_p0_regression_limit": SPARSE_P0_REGRESSION_LIMIT,
        "combo_mean_bias_regression_limit": COMBO_MEAN_BIAS_REGRESSION_LIMIT,
        "min_cell_n": MIN_CELL_N,

        # Sources
        "base_oof_source": str(BASE_OOF_PATH.relative_to(REPO_ROOT)),
        "combo_oof_source": str(COMBO_OOF_PATH.relative_to(REPO_ROOT)),
        "calibrator_dir": str(MODEL_DIR.relative_to(REPO_ROOT)),

        # Drift / forbidden-stat sentinel
        "forbidden_stats": list(FORBIDDEN_STATS),
        "forbidden_stats_present": forbidden_stats_present,

        # Verification verdict
        "m6_3_report_pass": m6_3_report_pass,
        "verification_passed": m6_3_report_pass,  # back-compat
        "verification_errors": verification_errors,
    }
    path.write_text(json.dumps(meta, indent=2))


# -- Hard verification -----------------------------------------------------

def _verify(matrix: pd.DataFrame) -> list[str]:
    errs: list[str] = []
    if len(matrix) != 66:
        errs.append(f"row count {len(matrix)} != 66")

    seen_stats = set(matrix["stat"].astype(str).unique())
    expected_stats = set(EXPECTED_STATS)
    missing_stats = expected_stats - seen_stats
    extra_stats = seen_stats - expected_stats
    if missing_stats:
        errs.append(f"missing stats: {sorted(missing_stats)}")
    if extra_stats:
        errs.append(f"unexpected stats: {sorted(extra_stats)}")

    seen_rb = set(matrix["role_bucket"].astype(str).unique())
    expected_rb = set(EXPECTED_ROLE_BUCKETS)
    if seen_rb != expected_rb:
        errs.append(
            f"role bucket mismatch: missing={sorted(expected_rb - seen_rb)}, "
            f"unexpected={sorted(seen_rb - expected_rb)}"
        )

    forbidden_present = seen_stats & set(FORBIDDEN_STATS)
    if forbidden_present:
        errs.append(f"forbidden stats present: {sorted(forbidden_present)}")

    for combo_stat in ("pa", "pr", "pra"):
        if combo_stat not in seen_stats:
            errs.append(f"required combo stat absent: {combo_stat}")

    expected_pairs = {(s, r) for s in EXPECTED_STATS for r in EXPECTED_ROLE_BUCKETS}
    seen_pairs = set(zip(matrix["stat"].astype(str), matrix["role_bucket"].astype(str)))
    missing_pairs = expected_pairs - seen_pairs
    if missing_pairs:
        errs.append(f"missing cells: {sorted(missing_pairs)}")

    low_n = matrix[matrix["n"] < MIN_CELL_N]
    if len(low_n) > 0:
        listing = ", ".join(
            f"{r['stat']}|{r['role_bucket']}(n={int(r['n'])})"
            for _, r in low_n.iterrows()
        )
        errs.append(f"{len(low_n)} cells with n < {MIN_CELL_N}: {listing}")

    if MARKET_EVAL_AVAILABLE:
        errs.append(
            "MARKET_EVAL_AVAILABLE is True but M6.3 spec requires false; "
            "do not claim market superiority"
        )

    return errs


# -- Main ------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--run-date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="Run date label used in output filenames (default: today UTC)",
    )
    args = ap.parse_args()
    run_date = args.run_date

    logger.info("=" * 64)
    logger.info(f"M6.3 stat × role_bucket calibration report — {run_date}")
    logger.info("=" * 64)
    logger.info(f"baseline_for_m6_3 = {BASELINE_FOR_M6_3}")
    logger.info(f"market_eval_available = {MARKET_EVAL_AVAILABLE}")
    logger.info(f"status_threshold_policy = {STATUS_THRESHOLD_POLICY}")

    # -- Load OOFs --
    for label, path in (("base", BASE_OOF_PATH), ("combo", COMBO_OOF_PATH)):
        if not path.exists():
            logger.error(f"missing required input ({label} OOF): {path}")
            sys.exit(1)
    base_oof = pd.read_parquet(BASE_OOF_PATH)
    combo_oof = pd.read_parquet(COMBO_OOF_PATH)
    logger.info(
        f"base OOF: {len(base_oof):,} rows, stats="
        f"{sorted(base_oof['stat'].astype(str).unique())}"
    )
    logger.info(
        f"combo OOF: {len(combo_oof):,} rows, stats="
        f"{sorted(combo_oof['stat'].astype(str).unique())}"
    )

    # -- Schema sanity --
    for label, df, required in (
        ("base", base_oof, ("stat", "outcome", "role_bucket", "pmf_active")),
        ("combo", combo_oof, ("stat", "outcome", "role_bucket", "pmf")),
    ):
        missing = [c for c in required if c not in df.columns]
        if missing:
            logger.error(f"{label} OOF missing required columns: {missing}")
            sys.exit(1)

    # Forbidden-stat preflight on raw inputs (before filtering)
    seen_stats_input = set(base_oof["stat"].astype(str).unique()) | set(
        combo_oof["stat"].astype(str).unique()
    )
    forbidden_seen = seen_stats_input & set(FORBIDDEN_STATS)
    if forbidden_seen:
        logger.error(
            f"forbidden stats present in OOF inputs: {sorted(forbidden_seen)}"
        )
        sys.exit(1)

    # -- Restrict each source to its mission-canonical slice --
    base_oof = base_oof[base_oof["stat"].astype(str).isin(BASE_STATS)].copy()
    combo_oof = combo_oof[combo_oof["stat"].astype(str).isin(COMBO_STATS)].copy()

    # -- Compute cells --
    rows: list[dict] = []
    for stat in EXPECTED_STATS:
        if stat in BASE_STATS:
            df_stat = base_oof[base_oof["stat"].astype(str) == stat]
            pmf_col = "pmf_active"
        else:
            df_stat = combo_oof[combo_oof["stat"].astype(str) == stat]
            pmf_col = "pmf"

        if len(df_stat) == 0:
            logger.error(f"no OOF rows for stat={stat}")
            sys.exit(1)

        try:
            cal = load_calibrator(stat)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"load_calibrator({stat!r}) raised: {exc}")
            sys.exit(1)
        if cal is None:
            logger.error(f"calibrator missing for stat={stat}")
            sys.exit(1)
        cal_version = getattr(cal, "version", None)
        if cal_version != "role_aware_pmf_cal_v1":
            logger.error(
                f"non-role-aware calibrator for stat={stat}: "
                f"version={cal_version!r}"
            )
            sys.exit(1)

        for rb in EXPECTED_ROLE_BUCKETS:
            sub = df_stat[df_stat["role_bucket"].astype(str) == rb]
            if len(sub) == 0:
                rows.append(_empty_cell(stat, rb))
                logger.warning(f"  {stat:<6} | {rb:<13} | n=0 (empty cell)")
                continue
            seed_bytes = hashlib.sha256(
                f"{stat}|{rb}|m6.3".encode("utf-8")
            ).digest()[:8]
            seed = int.from_bytes(seed_bytes, "little") % (2**32)
            row = _compute_cell(stat, rb, sub, pmf_col, cal, seed)
            rows.append(row)
            caveat_tag = f" caveats={row['caveats']}" if row["caveats"] else ""
            logger.info(
                f"  {stat:<6} | {rb:<13} | n={row['n']:>5} | "
                f"raw_nll={row['raw_nll']:.4f} | cal_nll={row['calibrated_nll']:.4f} | "
                f"Δ={row['delta_nll_cal_minus_raw']:+.4f} (thr=+{row['nll_threshold']:.3f}) | "
                f"status={row['status']}{caveat_tag}"
            )

    matrix = pd.DataFrame(rows)

    # -- Write outputs (always, so verification failures are inspectable) --
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DOCS_DIR / f"m6_3_stat_role_calibration_matrix_{run_date}.csv"
    md_path = DOCS_DIR / f"m6_3_stat_role_calibration_report_{run_date}.md"
    meta_path = DOCS_DIR / f"m6_3_stat_role_calibration_report_{run_date}.meta.json"

    errs = _verify(matrix)

    _write_csv(csv_path, matrix)
    logger.info(f"wrote {csv_path} ({csv_path.stat().st_size} bytes)")
    _write_markdown(md_path, matrix, run_date)
    logger.info(f"wrote {md_path} ({md_path.stat().st_size} bytes)")
    _write_meta(meta_path, matrix, run_date, errs)
    logger.info(f"wrote {meta_path} ({meta_path.stat().st_size} bytes)")

    # -- Pass / fail --
    if errs:
        logger.error("VERIFICATION FAILED:")
        for e in errs:
            logger.error(f"  - {e}")
        sys.exit(1)

    print()
    print("M6_3_STAT_ROLE_REPORT_PASS")


if __name__ == "__main__":
    main()
