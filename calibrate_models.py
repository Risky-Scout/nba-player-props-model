#!/usr/bin/env python3
from __future__ import annotations
"""
calibrate_models.py — NBA Props Model: Post-hoc Per-Stat Calibration
VERSION: 2026-03-11-v1
=======================================================================
Problem: Raw LightGBM quantile outputs are systematically biased at the
tails for skewed distributions (fg3m, stl, blk). This post-processor
applies isotonic regression calibration per stat per quantile level,
fitted on holdout predictions vs actuals from performance_log.csv.

Method:
  - For each stat × quantile: fit IsotonicRegression(increasing=True)
    mapping raw_prob -> calibrated_prob on holdout data
  - Calibration is applied AT INFERENCE TIME in predict_darko_v4.py
    by loading the saved calibration maps from model_cache/

Two operating modes:
  1. fit   — fits calibration maps from performance_log.csv, saves to
             model_cache/calibration_{stat}.pkl
  2. eval  — evaluates Brier score and calibration error before/after

Usage:
  python3 calibrate_models.py --mode fit
  python3 calibrate_models.py --mode eval

Architecture principle:
  Calibration is ALWAYS post-processing. The quantile models are not
  retrained. This means calibration maps can be updated daily as the
  performance log accumulates without triggering a full retrain.
"""

import argparse
import json
import logging
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PERF_LOG   = Path("graded/performance_log.csv")
MODEL_DIR  = Path("model_cache")
STATS      = ["pts", "reb", "ast", "fg3m", "stl", "blk"]

# Minimum graded samples per stat before calibration is considered reliable
MIN_SAMPLES_PER_STAT = 50


def load_performance_log() -> pd.DataFrame:
    """Load and validate performance log."""
    if not PERF_LOG.exists():
        raise FileNotFoundError(f"Performance log not found: {PERF_LOG}")
    df = pd.read_csv(PERF_LOG)
    required = ["stat", "side", "model_prob", "result", "actual", "line"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Performance log missing columns: {missing}")
    df = df[df["result"].isin(["HIT", "MISS"])].copy()
    df["hit"] = (df["result"] == "HIT").astype(int)
    logger.info(f"Loaded {len(df)} graded picks (excl. pushes)")
    return df


def compute_brier_score(probs: np.ndarray, actuals: np.ndarray) -> float:
    """Brier score: lower = better. 0.25 = random, 0.0 = perfect."""
    return float(np.mean((probs - actuals) ** 2))


def compute_calibration_error(probs: np.ndarray, actuals: np.ndarray,
                               n_bins: int = 10) -> float:
    """Expected Calibration Error (ECE): mean |predicted - empirical| per bin."""
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total = len(probs)
    for i in range(n_bins):
        mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
        if mask.sum() == 0:
            continue
        bin_prob  = probs[mask].mean()
        bin_actual = actuals[mask].mean()
        ece += (mask.sum() / total) * abs(bin_prob - bin_actual)
    return float(ece)


def fit_isotonic_calibrator(probs: np.ndarray,
                             actuals: np.ndarray) -> IsotonicRegression:
    """
    Fit isotonic regression calibrator.
    IsotonicRegression(increasing=True, out_of_bounds='clip') ensures
    monotone output and handles edge probabilities gracefully.
    """
    ir = IsotonicRegression(increasing=True, out_of_bounds="clip")
    ir.fit(probs, actuals)
    return ir


def fit_all(df: pd.DataFrame) -> dict:
    """
    Fit one isotonic calibrator per stat.
    Returns dict: {stat: {'calibrator': ir, 'n': int,
                           'brier_before': float, 'brier_after': float,
                           'ece_before': float, 'ece_after': float}}
    """
    results = {}

    for stat in STATS:
        stat_df = df[df["stat"] == stat].copy()
        n = len(stat_df)

        if n < MIN_SAMPLES_PER_STAT:
            logger.warning(
                f"{stat}: only {n} samples (need {MIN_SAMPLES_PER_STAT}) "
                f"— skipping calibration, using identity"
            )
            results[stat] = {"calibrator": None, "n": n,
                             "brier_before": None, "brier_after": None,
                             "ece_before": None, "ece_after": None,
                             "skipped": True}
            continue

        # model_prob is always P(OVER). For UNDER picks, invert.
        probs = stat_df["model_prob"].values.astype(float)
        under_mask = stat_df["side"] == "UNDER"
        probs[under_mask] = 1.0 - probs[under_mask]
        # Clip to valid probability range
        probs = np.clip(probs, 0.01, 0.99)
        actuals = stat_df["hit"].values.astype(float)

        brier_before = compute_brier_score(probs, actuals)
        ece_before   = compute_calibration_error(probs, actuals)

        calibrator = fit_isotonic_calibrator(probs, actuals)
        cal_probs  = calibrator.predict(probs)

        brier_after = compute_brier_score(cal_probs, actuals)
        ece_after   = compute_calibration_error(cal_probs, actuals)

        improvement_brier = brier_before - brier_after
        improvement_ece   = ece_before   - ece_after

        logger.info(
            f"{stat:6s} n={n:4d} | "
            f"Brier: {brier_before:.4f} → {brier_after:.4f} "
            f"({'↓' if improvement_brier > 0 else '↑'}{abs(improvement_brier):.4f}) | "
            f"ECE: {ece_before:.4f} → {ece_after:.4f} "
            f"({'↓' if improvement_ece > 0 else '↑'}{abs(improvement_ece):.4f})"
        )

        # Only save calibrator if it actually improves Brier score
        if brier_after < brier_before:
            save_path = MODEL_DIR / f"calibration_{stat}.pkl"
            joblib.dump(calibrator, save_path)
            logger.info(f"  ✓ Saved {save_path}")
        else:
            logger.warning(
                f"  ⚠ {stat}: calibration did not improve Brier score — "
                f"using identity (raw model probs)"
            )
            calibrator = None

        results[stat] = {
            "calibrator": calibrator,
            "n": n,
            "brier_before": round(brier_before, 5),
            "brier_after":  round(brier_after, 5),
            "ece_before":   round(ece_before, 5),
            "ece_after":    round(ece_after, 5),
            "skipped": False,
        }

    return results


def eval_calibration(df: pd.DataFrame) -> None:
    """Print calibration report per stat using saved calibrators."""
    logger.info("\n" + "=" * 70)
    logger.info("CALIBRATION EVALUATION REPORT")
    logger.info("=" * 70)

    for stat in STATS:
        stat_df = df[df["stat"] == stat].copy()
        n = len(stat_df)

        if n == 0:
            logger.info(f"{stat}: no data")
            continue

        probs = stat_df["model_prob"].values.astype(float)
        under_mask = stat_df["side"] == "UNDER"
        probs[under_mask] = 1.0 - probs[under_mask]
        probs = np.clip(probs, 0.01, 0.99)
        actuals = stat_df["hit"].values.astype(float)

        brier_raw = compute_brier_score(probs, actuals)
        ece_raw   = compute_calibration_error(probs, actuals)
        win_rate  = actuals.mean()

        cal_path = MODEL_DIR / f"calibration_{stat}.pkl"
        if cal_path.exists():
            calibrator = joblib.load(cal_path)
            cal_probs  = calibrator.predict(probs)
            brier_cal  = compute_brier_score(cal_probs, actuals)
            ece_cal    = compute_calibration_error(cal_probs, actuals)
            status = "CALIBRATED"
        else:
            brier_cal = ece_cal = None
            status = "RAW (no calibrator saved)"

        logger.info(
            f"\n{stat.upper()} ({status}) n={n} win_rate={win_rate:.3f}\n"
            f"  Brier raw={brier_raw:.4f}" +
            (f" | cal={brier_cal:.4f}" if brier_cal else "") + "\n"
            f"  ECE   raw={ece_raw:.4f}" +
            (f" | cal={ece_cal:.4f}" if ece_cal else "")
        )

        # Reliability diagram buckets
        logger.info("  Reliability (raw):")
        bin_edges = np.linspace(0, 1, 6)
        for i in range(len(bin_edges) - 1):
            mask = (probs >= bin_edges[i]) & (probs < bin_edges[i+1])
            if mask.sum() == 0:
                continue
            logger.info(
                f"    [{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}] "
                f"n={mask.sum():4d} "
                f"pred={probs[mask].mean():.3f} "
                f"actual={actuals[mask].mean():.3f}"
            )


def save_calibration_meta(results: dict) -> None:
    """Save calibration metadata to model_cache/calibration_meta.json."""
    meta = {}
    for stat, r in results.items():
        meta[stat] = {
            "n": r["n"],
            "brier_before": r["brier_before"],
            "brier_after":  r["brier_after"],
            "ece_before":   r["ece_before"],
            "ece_after":    r["ece_after"],
            "calibrated":   r.get("calibrator") is not None,
            "skipped":      r.get("skipped", False),
        }
    out_path = MODEL_DIR / "calibration_meta.json"
    with open(out_path, "w") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Calibration meta saved to {out_path}")


def load_calibrator(stat: str) -> IsotonicRegression | None:
    """
    Load saved calibrator for a stat. Returns None if not found.
    Called at inference time in predict_darko_v4.py.
    """
    cal_path = MODEL_DIR / f"calibration_{stat}.pkl"
    if cal_path.exists():
        return joblib.load(cal_path)
    return None


def apply_calibration(raw_prob: float, stat: str,
                       calibrators: dict | None = None) -> float:
    """
    Apply calibration to a raw model probability.
    calibrators: pre-loaded dict {stat: calibrator} (avoids disk reads in loop)
    Falls back to raw_prob if no calibrator available.
    """
    if calibrators is None:
        calibrators = {}

    cal = calibrators.get(stat)
    if cal is None:
        cal = load_calibrator(stat)
        if cal is None:
            return float(np.clip(raw_prob, 0.01, 0.99))
        if calibrators is not None:
            calibrators[stat] = cal

    return float(np.clip(cal.predict([raw_prob])[0], 0.01, 0.99))


def main():
    parser = argparse.ArgumentParser(description="NBA Props Model Calibration")
    parser.add_argument("--mode", choices=["fit", "eval"], default="fit",
                        help="fit: fit and save calibrators | eval: evaluate only")
    args = parser.parse_args()

    df = load_performance_log()

    by_stat = df.groupby("stat").size()
    logger.info("Samples per stat in performance log:")
    for stat in STATS:
        n = by_stat.get(stat, 0)
        logger.info(f"  {stat}: {n}")

    if args.mode == "fit":
        logger.info("\nFitting isotonic calibrators per stat...")
        results = fit_all(df)
        save_calibration_meta(results)
        logger.info("\n✓ Calibration fit complete")
    else:
        eval_calibration(df)


if __name__ == "__main__":
    main()
