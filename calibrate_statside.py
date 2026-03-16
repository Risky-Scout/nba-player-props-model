"""
calibrate_statside.py — Stat × Side Calibration

Upgrades from:
  - calibration_{stat}.pkl (stat-only isotonic)
  - platt_over.pkl / platt_under.pkl (global side Platt)

To:
  - calibration_{stat}_{side}.pkl (stat × side isotonic)

This directly targets the primary failure mode: strong side asymmetry
where UNDER CLV is persistently negative while OVER CLV is positive.

Usage:
    python3 calibrate_statside.py

Requires graded/performance_log.csv with at least 100 picks per stat×side cell.
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import calibration_curve
import warnings
warnings.filterwarnings('ignore')

MODEL_DIR = Path("model_cache")
GRADED_DIR = Path("graded")
LOG_PATH = GRADED_DIR / "performance_log.csv"

MIN_SAMPLES = 80  # Minimum picks per stat×side to fit calibrator

def brier_score(y_true, y_prob):
    return float(np.mean((np.array(y_prob) - np.array(y_true))**2))

def fit_statside_calibrators():
    """Fit isotonic calibrators per stat × side."""
    if not LOG_PATH.exists():
        print("No performance_log.csv found — run grader first")
        return

    df = pd.read_csv(LOG_PATH)
    df['hit'] = (df['result'] == 'HIT').astype(float)

    print("=== STAT × SIDE CALIBRATION ===\n")
    report = {}

    for stat in ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']:
        for side in ['OVER', 'UNDER']:
            subset = df[(df['stat'] == stat) & (df['side'] == side)].copy()

            if len(subset) < MIN_SAMPLES:
                print(f"{stat:6s} {side:5s}: {len(subset):4d} picks — SKIPPED (need {MIN_SAMPLES}+)")
                continue

            # Use model probability as the raw score
            prob_col = 'model_prob' if 'model_prob' in subset.columns else None
            if prob_col is None:
                # Reconstruct from EV if model_prob not stored
                print(f"{stat:6s} {side:5s}: no model_prob column — skipping")
                continue

            y_true = subset['hit'].values
            y_prob = subset[prob_col].values.clip(0.01, 0.99)

            # Brier before calibration
            brier_before = brier_score(y_true, y_prob)

            # Fit isotonic regression
            iso = IsotonicRegression(out_of_bounds='clip')
            iso.fit(y_prob, y_true)
            y_cal = iso.transform(y_prob)
            brier_after = brier_score(y_true, y_cal)

            # Save calibrator
            cal_path = MODEL_DIR / f"calibration_{stat}_{side.lower()}.pkl"
            joblib.dump(iso, cal_path)

            improvement = (brier_before - brier_after) / brier_before * 100
            print(f"{stat:6s} {side:5s}: n={len(subset):4d} | "
                  f"Brier {brier_before:.4f}→{brier_after:.4f} "
                  f"({improvement:+.1f}%) | saved {cal_path.name}")

            report[f"{stat}_{side}"] = {
                "n": len(subset),
                "brier_before": round(brier_before, 4),
                "brier_after": round(brier_after, 4),
                "improvement_pct": round(improvement, 2),
                "clv_mean": round(float(subset['clv_proxy'].mean()), 4),
                "hit_rate": round(float(y_true.mean()), 4),
            }

    # Save report
    report_path = GRADED_DIR / "calibration_statside_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved: {report_path}")

    return report


def print_calibration_summary():
    """Print current calibration quality by stat × side."""
    if not LOG_PATH.exists():
        return

    df = pd.read_csv(LOG_PATH)
    df['hit'] = (df['result'] == 'HIT').astype(float)

    print("\n=== CURRENT CALIBRATION QUALITY ===")
    print(f"{'Stat':6s} {'Side':5s} {'N':>5s} {'CLV':>8s} {'HR':>8s} {'LineDelta':>10s}")
    print("-" * 50)
    df['ld'] = df['line'] - df['q50']
    for stat in ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']:
        for side in ['OVER', 'UNDER']:
            s = df[(df['stat'] == stat) & (df['side'] == side)]
            if len(s) == 0:
                continue
            print(f"{stat:6s} {side:5s} {len(s):>5d} "
                  f"{s['clv_proxy'].mean():>8.3f} "
                  f"{s['hit'].mean():>8.1%} "
                  f"{s['ld'].mean():>10.3f}")

    print("\n=== PHASE READINESS ===")
    for stat in ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']:
        for side in ['OVER', 'UNDER']:
            n = len(df[(df['stat'] == stat) & (df['side'] == side)])
            status = "✓ READY" if n >= MIN_SAMPLES else f"✗ need {MIN_SAMPLES - n} more"
            print(f"  {stat} {side}: n={n} {status}")


if __name__ == "__main__":
    print_calibration_summary()
    fit_statside_calibrators()
