#!/usr/bin/env python3
from __future__ import annotations
"""
calibrate_models.py — NBA Props Model: Post-hoc Calibration Pipeline
VERSION: 2026-03-12-v2
=======================================================================
Two-stage calibration strategy:

STAGE 1 — Platt scaling per side (OVER / UNDER):
  Fits a logistic regression (2 parameters: slope + intercept) mapping
  raw model_prob → empirical hit rate, fitted separately for OVER and
  UNDER picks across all stats. Works reliably with 50+ samples per
  side. Applied first at inference time.

  Diagnostic finding (2026-03-12): UNDER picks in the 0.60-0.75 range
  show systematic overconfidence — model prob 0.67, empirical hit 0.48.
  Platt scaling corrects this: f(p) = sigmoid(a*p + b) where a < 1
  compresses the overconfident range and b shifts toward the true rate.

STAGE 2 — Isotonic regression per stat (requires 50+ samples per stat):
  Fits a non-parametric monotone step function per stat on graded picks.
  More expressive than Platt but needs larger samples. Applied after
  Platt as a residual correction. Gated by Brier score improvement.

Four operating modes:
  platt    — fit Platt calibrators per side, save to model_cache/
  fit      — fit isotonic calibrators per stat, save to model_cache/
  eval     — full calibration diagnostic report
  diagnose — reliability diagram data by side and probability bucket

Usage:
  python3 calibrate_models.py --mode platt      (run tonight)
  python3 calibrate_models.py --mode fit        (run at 50+ per stat)
  python3 calibrate_models.py --mode diagnose   (inspect calibration)

Architecture principle:
  Calibration is always post-processing. Quantile models are never
  retrained. Calibration maps update as performance_log.csv grows.
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
from sklearn.linear_model import LogisticRegression
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


# ── Stage 1: Platt scaling per side ───────────────────────────────────────────

def fit_platt_calibrators(df: pd.DataFrame) -> dict:
    """
    Fit Platt scaling (logistic regression) calibrators per side.

    Rationale: Isotonic regression needs 50+ samples per stat. Platt
    scaling has only 2 free parameters (slope + intercept) and fits
    reliably on 50+ picks per side across all stats combined.

    Diagnostic finding (2026-03-12):
      UNDER picks 0.60-0.75: model_prob=0.67, empirical=0.48 → overconfident 19pp
      OVER picks: model_prob=0.57, empirical=0.57 → well calibrated

    Saves: model_cache/platt_over.pkl and model_cache/platt_under.pkl
    Applied BEFORE EV calculation so falsely-confident picks are filtered.
    """
    results = {}

    for side in ["OVER", "UNDER"]:
        side_df = df[df["side"] == side].copy()
        n = len(side_df)

        if n < 30:
            logger.warning(f"{side}: only {n} samples — skipping Platt (need 30+)")
            results[side] = {"calibrator": None, "n": n, "skipped": True}
            continue

        probs   = side_df["model_prob"].values.astype(float).reshape(-1, 1)
        actuals = side_df["hit"].values.astype(float)

        brier_before = compute_brier_score(probs.ravel(), actuals)
        ece_before   = compute_calibration_error(probs.ravel(), actuals)

        lr = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
        lr.fit(probs, actuals)
        cal_probs = lr.predict_proba(probs)[:, 1]

        brier_after = compute_brier_score(cal_probs, actuals)
        ece_after   = compute_calibration_error(cal_probs, actuals)

        slope     = round(float(lr.coef_[0][0]), 4)
        intercept = round(float(lr.intercept_[0]), 4)

        improved = brier_after < brier_before

        logger.info(
            f"{side:6s} n={n:4d} | "
            f"Brier: {brier_before:.4f} → {brier_after:.4f} "
            f"({'↓' if improved else '↑'}{abs(brier_before - brier_after):.4f}) | "
            f"ECE: {ece_before:.4f} → {ece_after:.4f} | "
            f"slope={slope:.3f} intercept={intercept:.3f}"
        )

        if improved:
            save_path = MODEL_DIR / f"platt_{side.lower()}.pkl"
            joblib.dump(lr, save_path)
            logger.info(f"  ✓ Saved {save_path} (slope={slope}, intercept={intercept})")
        else:
            logger.warning(f"  ⚠ {side}: Platt did not improve Brier — raw probs unchanged")

        results[side] = {
            "calibrator": lr if improved else None,
            "n": n,
            "brier_before": round(brier_before, 5),
            "brier_after":  round(brier_after, 5),
            "ece_before":   round(ece_before, 5),
            "ece_after":    round(ece_after, 5),
            "slope":        slope,
            "intercept":    intercept,
            "improved":     improved,
            "skipped":      False,
        }

    return results


def load_platt_calibrator(side: str) -> LogisticRegression | None:
    """Load saved Platt calibrator for a side. Returns None if not found."""
    path = MODEL_DIR / f"platt_{side.lower()}.pkl"
    if path.exists():
        return joblib.load(path)
    return None


def apply_platt_calibration(raw_prob: float, side: str,
                              platt_calibrators: dict | None = None) -> float:
    """
    Apply Platt calibration to a raw model probability.
    platt_calibrators: pre-loaded dict {'OVER': lr, 'UNDER': lr}
    Falls back to raw_prob if no calibrator available for this side.
    """
    if platt_calibrators is None:
        platt_calibrators = {}

    cal = platt_calibrators.get(side)
    if cal is None:
        cal = load_platt_calibrator(side)
        if cal is None:
            return float(np.clip(raw_prob, 0.01, 0.99))
        platt_calibrators[side] = cal

    result = cal.predict_proba([[raw_prob]])[0][1]
    return float(np.clip(result, 0.01, 0.99))


def diagnose_calibration(df: pd.DataFrame) -> None:
    """
    Print reliability diagram data by side and probability bucket.
    Shows exactly where the model is over/under-confident.
    """
    logger.info("\n" + "=" * 70)
    logger.info("CALIBRATION DIAGNOSTIC — RELIABILITY DIAGRAM DATA")
    logger.info("=" * 70)

    for side in ["OVER", "UNDER"]:
        s = df[df["side"] == side].copy()
        n = len(s)
        mean_prob = s["model_prob"].mean()
        hit_rate  = s["hit"].mean()

        logger.info(f"\n{side} (n={n}): mean_model_prob={mean_prob:.3f}, "
                    f"empirical_hit_rate={hit_rate:.3f}, "
                    f"overconfidence={mean_prob - hit_rate:+.3f}")

        # Check for Platt calibrator
        platt_cal = load_platt_calibrator(side)
        if platt_cal is not None:
            cal_probs = platt_cal.predict_proba(
                s["model_prob"].values.reshape(-1, 1))[:, 1]
            brier_raw = compute_brier_score(s["model_prob"].values, s["hit"].values)
            brier_cal = compute_brier_score(cal_probs, s["hit"].values)
            logger.info(f"  Platt calibrator loaded — Brier raw={brier_raw:.4f} "
                        f"cal={brier_cal:.4f}")

        # Reliability buckets
        buckets = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.01]
        logger.info(f"  {'Bucket':<15} {'N':>5} {'Model P':>10} {'Empirical':>10} {'Gap':>8}")
        logger.info(f"  {'-'*50}")
        for i in range(len(buckets) - 1):
            lo, hi = buckets[i], buckets[i + 1]
            mask = (s["model_prob"] >= lo) & (s["model_prob"] < hi)
            bucket_df = s[mask]
            if len(bucket_df) == 0:
                continue
            model_p = bucket_df["model_prob"].mean()
            emp_p   = bucket_df["hit"].mean()
            gap     = model_p - emp_p
            flag    = " ← OVERCONFIDENT" if gap > 0.08 else ""
            logger.info(f"  [{lo:.2f}, {hi:.2f})   {len(bucket_df):>5}   "
                        f"{model_p:>8.3f}   {emp_p:>8.3f}   {gap:>+7.3f}{flag}")

    # Summary by stat
    logger.info("\n" + "-" * 70)
    logger.info("BRIER SCORE BY STAT")
    for stat in STATS:
        stat_df = df[df["stat"] == stat]
        if len(stat_df) < 5:
            continue
        brier = compute_brier_score(stat_df["model_prob"].values,
                                     stat_df["hit"].values)
        logger.info(f"  {stat:8s} n={len(stat_df):4d}  Brier={brier:.4f}")


# ── Stage 2: Isotonic regression per stat ─────────────────────────────────────

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
    parser.add_argument(
        "--mode",
        choices=["platt", "fit", "eval", "diagnose"],
        default="diagnose",
        help=(
            "platt: fit Platt (logistic) calibrators per side — run first; "
            "fit: fit isotonic calibrators per stat (needs 50+ per stat); "
            "eval: evaluate saved calibrators; "
            "diagnose: print reliability diagram data"
        ),
    )
    args = parser.parse_args()

    df = load_performance_log()

    logger.info("Samples per stat in performance log:")
    by_stat = df.groupby("stat").size()
    for stat in STATS:
        n = by_stat.get(stat, 0)
        logger.info(f"  {stat}: {n}")
    logger.info(f"  OVER: {(df.side=='OVER').sum()}  UNDER: {(df.side=='UNDER').sum()}")

    if args.mode == "platt":
        logger.info("\nFitting Platt calibrators per side...")
        results = fit_platt_calibrators(df)
        meta = {
            "platt_calibration": {
                side: {k: v for k, v in r.items() if k != "calibrator"}
                for side, r in results.items()
            }
        }
        meta_path = MODEL_DIR / "platt_calibration_meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"\n✓ Platt calibration complete. Meta saved to {meta_path}")
        logger.info("\nIMPORTANT: Re-run predict_darko_v4.py tomorrow — it will")
        logger.info("automatically load platt_over.pkl / platt_under.pkl at startup.")

    elif args.mode == "fit":
        logger.info("\nFitting isotonic calibrators per stat...")
        results = fit_all(df)
        save_calibration_meta(results)
        logger.info("\n✓ Isotonic calibration fit complete")

    elif args.mode == "diagnose":
        diagnose_calibration(df)

    else:
        eval_calibration(df)


if __name__ == "__main__":
    main()
