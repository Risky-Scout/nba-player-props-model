#!/usr/bin/env python3
"""
calibrate_stat_side.py — Stat×Side Calibration File Generator
==============================================================
Generates platt_{stat}_{side}.pkl for each stat/side combination
with sufficient sample size.

Per the permanent architecture document:
  "stat × side calibration, so unders are fixed in the probability
   layer instead of by blunt suppression forever"

Usage:
    python3 calibrate_stat_side.py

Output files (in model_cache/):
    platt_pts_OVER.pkl
    platt_pts_UNDER.pkl
    platt_ast_OVER.pkl
    platt_ast_UNDER.pkl
    platt_reb_OVER.pkl
    platt_reb_UNDER.pkl
    platt_fg3m_OVER.pkl
    platt_fg3m_UNDER.pkl
    platt_OVER.pkl    (global fallback)
    platt_UNDER.pkl   (global fallback)
    calibration_report.json
"""

import csv
import glob
import json
import logging
import warnings
from pathlib import Path
from collections import defaultdict

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, log_loss

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GRADED_DIR   = Path("graded")
MODEL_DIR    = Path("model_cache")
MIN_SAMPLES  = 40    # minimum samples to fit a stat×side calibrator
MIN_SAMPLES_GLOBAL = 100

CALIBRATE_STATS = ["pts", "ast", "reb", "fg3m", "pra", "pr", "pa", "ra"]
SIDES = ["OVER", "UNDER"]


class StatSideCalibrator:
    """
    Platt (logistic) calibrator per stat×side combination.
    Falls back to global side calibrator when sample is insufficient.
    """

    def __init__(self):
        self.calibrators = {}   # key: "pts_OVER", "pts_UNDER", "OVER", "UNDER"
        self.metadata    = {}

    def fit(self, graded_dir: Path = GRADED_DIR):
        rows = self._load_graded(graded_dir)
        logger.info(f"Loaded {len(rows)} graded rows")

        # Group by stat×side
        buckets = defaultdict(lambda: {"probs": [], "outcomes": []})
        global_buckets = defaultdict(lambda: {"probs": [], "outcomes": []})

        for r in rows:
            stat    = r["stat"]
            side    = r["side"]
            prob    = r["model_prob"]
            outcome = r["outcome"]
            if prob <= 0 or prob >= 1: continue
            if outcome not in (0, 1): continue

            key = f"{stat}_{side}"
            buckets[key]["probs"].append(prob)
            buckets[key]["outcomes"].append(outcome)
            global_buckets[side]["probs"].append(prob)
            global_buckets[side]["outcomes"].append(outcome)

        report = {}

        # Fit stat×side calibrators
        for stat in CALIBRATE_STATS:
            for side in SIDES:
                key = f"{stat}_{side}"
                d   = buckets[key]
                n   = len(d["probs"])
                if n < MIN_SAMPLES:
                    logger.info(f"  {key}: n={n} < {MIN_SAMPLES} — skipping (will use global)")
                    continue

                X = np.array(d["probs"]).reshape(-1, 1)
                y = np.array(d["outcomes"])

                cal = self._fit_platt(X, y)
                raw_brier = brier_score_loss(y, d["probs"])
                cal_brier = brier_score_loss(y, cal.predict_proba(X)[:, 1])

                self.calibrators[key] = cal
                self.metadata[key] = {
                    "n":          n,
                    "raw_brier":  round(raw_brier, 4),
                    "cal_brier":  round(cal_brier, 4),
                    "improvement": round(raw_brier - cal_brier, 4),
                    "hit_rate":   round(float(y.mean()), 4),
                    "mean_prob":  round(float(np.mean(d["probs"])), 4),
                }
                logger.info(f"  {key}: n={n}  brier {raw_brier:.4f} → {cal_brier:.4f}"
                            f"  hit_rt={y.mean():.3f}  mean_prob={np.mean(d['probs']):.3f}")
                report[key] = self.metadata[key]

        # Fit global fallback calibrators
        for side in SIDES:
            d = global_buckets[side]
            n = len(d["probs"])
            if n < MIN_SAMPLES_GLOBAL:
                logger.warning(f"  Global {side}: only {n} samples")
                continue

            X = np.array(d["probs"]).reshape(-1, 1)
            y = np.array(d["outcomes"])

            cal = self._fit_platt(X, y)
            raw_brier = brier_score_loss(y, d["probs"])
            cal_brier = brier_score_loss(y, cal.predict_proba(X)[:, 1])

            self.calibrators[side] = cal
            key_g = f"global_{side}"
            self.metadata[key_g] = {
                "n": n,
                "raw_brier":  round(raw_brier, 4),
                "cal_brier":  round(cal_brier, 4),
                "improvement": round(raw_brier - cal_brier, 4),
                "hit_rate":   round(float(y.mean()), 4),
                "mean_prob":  round(float(np.mean(d["probs"])), 4),
            }
            logger.info(f"  Global {side}: n={n}  brier {raw_brier:.4f} → {cal_brier:.4f}")
            report[key_g] = self.metadata[key_g]

        return report

    def save(self, model_dir: Path = MODEL_DIR):
        model_dir.mkdir(exist_ok=True)
        for key, cal in self.calibrators.items():
            # key is either "pts_OVER" or "OVER" (global)
            fname = f"platt_{key}.pkl"
            joblib.dump(cal, model_dir / fname)

        (model_dir / "calibration_report.json").write_text(
            json.dumps(self.metadata, indent=2))
        logger.info(f"Saved {len(self.calibrators)} calibrators to {model_dir}/")
        return list(self.calibrators.keys())

    def _fit_platt(self, X, y):
        """Fit Platt scaling (logistic regression on probabilities)."""
        lr = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
        # Wrap in CalibratedClassifierCV for proper probability output
        # Use sigmoid (Platt) method
        from sklearn.base import BaseEstimator, ClassifierMixin
        class ProbaPassthrough(BaseEstimator, ClassifierMixin):
            """Dummy classifier that passes through probabilities."""
            def fit(self, X, y): self.classes_ = np.array([0,1]); return self
            def predict_proba(self, X): return np.column_stack([1-X[:,0], X[:,0]])
            def predict(self, X): return (X[:,0] > 0.5).astype(int)

        # Walk-forward OOF ECE check before fitting final calibrator
        n = len(y)
        if n >= 40:
            oof_preds = []
            oof_actuals = []
            for split in range(20, n):
                _X_tr = X[:split]; _y_tr = y[:split]
                if len(set(_y_tr)) < 2: continue
                _lr = LogisticRegression(C=1.0, solver="lbfgs", max_iter=500)
                _lr.fit(_X_tr, _y_tr)
                oof_preds.append(_lr.predict_proba(X[split:split+1])[0][1])
                oof_actuals.append(y[split])
            if len(oof_preds) > 10:
                oof_p = np.array(oof_preds); oof_a = np.array(oof_actuals)
                oof_ece = _compute_ece(oof_p, oof_a)
                gate = "PASS" if oof_ece < 0.05 else "ABOVE GATE"
                logger.info(f"    OOF ECE: {oof_ece:.4f} ({gate}) — fitting final calibrator on all data")

        cal = CalibratedClassifierCV(
            ProbaPassthrough(), method="sigmoid", cv="prefit"
        )
        cal.fit(X, y)
        return cal

    def _load_graded(self, graded_dir: Path) -> list:
        rows = []
        for f in sorted(graded_dir.glob("graded_2026-*.csv")):
            try:
                for r in csv.DictReader(open(f)):
                    try:
                        stat = r.get("stat","").lower()
                        side = r.get("side","").upper()
                        prob = float(r.get("model_prob") or 0)
                        res  = str(r.get("result","")).strip().upper()
                        outcome = 1 if res in ("HIT","WIN") else 0 if res in ("MISS","LOSS","NO") else -1
                        if outcome == -1: continue
                        if not stat or side not in SIDES: continue
                        if prob <= 0 or prob >= 1: continue
                        rows.append({
                            "stat":       stat,
                            "side":       side,
                            "model_prob": prob,
                            "outcome":    outcome,
                            "line":       float(r.get("line") or 0),
                            "q50":        float(r.get("q50") or 0),
                        })
                    except: continue
            except: continue
        return rows


# ═══════════════════════════════════════════════════════════════════════════════
# Calibration evaluation helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_ece(probs, outcomes, n_bins=8):
    """Expected Calibration Error — used for OOF reporting."""
    probs = np.array(probs)
    outcomes = np.array(outcomes)
    bins = np.linspace(0.5, 0.85, n_bins)
    ece = 0.0
    for i in range(len(bins)-1):
        mask = (probs >= bins[i]) & (probs < bins[i+1])
        if mask.sum() < 3: continue
        ece += (mask.sum()/len(probs)) * abs(probs[mask].mean() - outcomes[mask].mean())
    return float(ece)


def evaluate_calibration(rows: list, calibrators: dict) -> dict:
    """
    Compare raw vs calibrated Brier scores per stat×side.
    Use to confirm calibration actually helps before deploying.
    """
    results = {}
    buckets = defaultdict(lambda: {"probs":[],"cal_probs":[],"outcomes":[]})

    for r in rows:
        key = f"{r['stat']}_{r['side']}"
        cal = calibrators.get(key) or calibrators.get(r["side"])
        if cal is None: continue
        raw_prob = r["model_prob"]
        cal_prob = float(cal.predict_proba([[raw_prob]])[0][1])
        buckets[key]["probs"].append(raw_prob)
        buckets[key]["cal_probs"].append(cal_prob)
        buckets[key]["outcomes"].append(r["outcome"])

    for key, d in sorted(buckets.items()):
        if len(d["probs"]) < 10: continue
        raw_b = brier_score_loss(d["outcomes"], d["probs"])
        cal_b = brier_score_loss(d["outcomes"], d["cal_probs"])
        results[key] = {
            "n":          len(d["probs"]),
            "raw_brier":  round(raw_b, 4),
            "cal_brier":  round(cal_b, 4),
            "improvement": round(raw_b - cal_b, 4),
            "better":     cal_b < raw_b,
        }

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--graded-dir", default="graded")
    parser.add_argument("--model-dir",  default="model_cache")
    parser.add_argument("--min-samples", type=int, default=MIN_SAMPLES)
    args = parser.parse_args()

    MIN_SAMPLES = args.min_samples

    cal = StatSideCalibrator()
    report = cal.fit(Path(args.graded_dir))
    saved  = cal.save(Path(args.model_dir))

    print("\n" + "="*60)
    print("CALIBRATION RESULTS")
    print("="*60)
    print(f"{'key':<18} {'n':>6} {'raw_brier':>10} {'cal_brier':>10} {'improvement':>12} {'hit_rt':>8}")
    print("-"*66)
    for key, m in sorted(report.items()):
        better = "✓" if m.get("improvement",0) > 0 else "✗"
        print(f"{key:<18} {m['n']:>6} {m['raw_brier']:>10.4f} {m['cal_brier']:>10.4f}"
              f" {m['improvement']:>+12.4f} {m['hit_rate']:>8.3f}  {better}")

    print(f"\nSaved {len(saved)} calibrators: {saved}")
    print("\nNext: run predict_darko_v4.py — it will auto-load stat×side calibrators")
    print("  Priority: platt_pts_OVER.pkl > platt_OVER.pkl > raw probability")
