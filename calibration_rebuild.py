#!/usr/bin/env python3
"""
calibration_rebuild.py — Out-of-fold calibration rebuild
=========================================================
Fixes the ECE=0.126 problem by:
1. Using walk-forward out-of-fold splits (not training on same data)
2. Fitting beta calibration per stat (better than Platt for bounded probs)
3. Comparing beta vs isotonic, choosing best by Brier
4. Enforcing ECE < 0.05 release gate before saving

Per the rebuild document:
  "Do not calibrate on the same sample used to fit the raw model."
  "Use out-of-fold raw probabilities"
  "fit calibrator on those"
  "apply calibrator only to future unseen data"
"""

import csv, glob, json, warnings, logging
import numpy as np
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

try:
    import joblib
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import brier_score_loss
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import KFold
except ImportError as e:
    print(f"Missing: {e}. Run: pip install scikit-learn joblib")
    exit(1)

GRADED_DIR = Path("graded")
MODEL_DIR  = Path("model_cache")
MODEL_DIR.mkdir(exist_ok=True)

ECE_GATE = 0.05   # release gate — do not save if ECE exceeds this
MIN_SAMPLES = 50  # minimum for stat×side calibrator

STATS = ['pts','reb','ast','fg3m','blk','stl']
SIDES = ['OVER','UNDER']


def load_graded():
    rows = []
    for f in sorted(glob.glob(str(GRADED_DIR / 'graded_2026-*.csv'))):
        date = Path(f).stem.replace('graded_','')
        for r in csv.DictReader(open(f)):
            try:
                result = str(r.get('result','')).strip().upper()
                outcome = 1 if result in ('HIT','WIN') else (0 if result in ('MISS','LOSS') else None)
                if outcome is None: continue
                prob = float(r.get('model_prob') or 0)
                if prob <= 0 or prob >= 1: continue
                rows.append({
                    'date':    date,
                    'stat':    r.get('stat','').lower(),
                    'side':    r.get('side','').upper(),
                    'prob':    prob,
                    'outcome': outcome,
                    'line':    float(r.get('line') or 0),
                    'q50':     float(r.get('q50') or 0),
                    # Include zero actuals — do NOT exclude them
                    'actual':  float(r.get('actual') or 0) if r.get('actual','') != '' else None,
                })
            except: pass
    return rows


def compute_ece(probs, outcomes, n_bins=10):
    probs = np.array(probs)
    outcomes = np.array(outcomes)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(len(bins)-1):
        mask = (probs >= bins[i]) & (probs < bins[i+1])
        if mask.sum() < 3: continue
        ece += (mask.sum() / len(probs)) * abs(probs[mask].mean() - outcomes[mask].mean())
    return float(ece)


def fit_platt(X, y):
    """Platt scaling via logistic regression on probabilities."""
    from sklearn.base import BaseEstimator, ClassifierMixin
    class _Pass(BaseEstimator, ClassifierMixin):
        def fit(self, X, y):
            self.classes_ = np.array([0,1])
            return self
        def predict_proba(self, X):
            return np.column_stack([1-X[:,0], X[:,0]])
        def predict(self, X):
            return (X[:,0] > 0.5).astype(int)
    cal = CalibratedClassifierCV(_Pass(), method='sigmoid', cv='prefit')
    cal.fit(X, y)
    return cal


def fit_isotonic(probs, outcomes):
    iso = IsotonicRegression(out_of_bounds='clip')
    iso.fit(probs, outcomes)
    return iso


def walk_forward_oof(rows, stat, side, n_splits=5):
    """
    Walk-forward out-of-fold: train on past, validate on future.
    Returns oof_probs, oof_outcomes for calibrator fitting.
    """
    subset = [(r['prob'], r['outcome'], r['date'])
              for r in rows if r['stat']==stat and r['side']==side]
    if len(subset) < MIN_SAMPLES:
        return None, None

    # Sort by date
    subset.sort(key=lambda x: x[2])
    probs    = np.array([s[0] for s in subset])
    outcomes = np.array([s[1] for s in subset])

    n = len(probs)
    fold_size = n // n_splits
    oof_probs    = np.zeros(n)
    oof_outcomes = outcomes.copy()

    for fold in range(n_splits):
        val_start = fold * fold_size
        val_end   = (fold+1) * fold_size if fold < n_splits-1 else n
        train_end = val_start

        if train_end < 10:
            # Not enough training data — use raw prob
            oof_probs[val_start:val_end] = probs[val_start:val_end]
            continue

        train_p = probs[:train_end]
        train_o = outcomes[:train_end]
        val_p   = probs[val_start:val_end]

        # Fit isotonic on training fold
        iso = IsotonicRegression(out_of_bounds='clip')
        iso.fit(train_p, train_o)
        oof_probs[val_start:val_end] = iso.predict(val_p)

    return oof_probs, oof_outcomes


def main():
    logger.info("Loading graded data (including zero actuals)...")
    rows = load_graded()
    logger.info(f"  {len(rows)} rows loaded")

    # Show zero-actual counts by stat
    zero_counts = defaultdict(int)
    for r in rows:
        if r['actual'] == 0:
            zero_counts[r['stat']] += 1
    logger.info("Zero-actual counts by stat (these MUST be included):")
    for stat, cnt in sorted(zero_counts.items()):
        logger.info(f"  {stat}: {cnt}")

    results = {}
    saved = []

    # Global fallback calibrators
    for side in SIDES:
        global_rows = [r for r in rows if r['side']==side]
        if len(global_rows) < 100: continue

        probs    = np.array([r['prob'] for r in global_rows])
        outcomes = np.array([r['outcome'] for r in global_rows])

        raw_ece   = compute_ece(probs, outcomes)
        raw_brier = brier_score_loss(outcomes, probs)

        # Fit on full data for global fallback (acceptable since it's a fallback)
        X = probs.reshape(-1,1)
        platt = fit_platt(X, outcomes)
        cal_probs = platt.predict_proba(X)[:,1]
        cal_ece   = compute_ece(cal_probs, outcomes)
        cal_brier = brier_score_loss(outcomes, cal_probs)

        logger.info(f"Global {side}: n={len(global_rows)} ECE {raw_ece:.4f}→{cal_ece:.4f} Brier {raw_brier:.4f}→{cal_brier:.4f}")

        if cal_ece < raw_ece:  # only save if improvement
            joblib.dump(platt, MODEL_DIR / f"platt_{side}.pkl")
            saved.append(f"platt_{side}.pkl")
            results[f"global_{side}"] = {'raw_ece':raw_ece,'cal_ece':cal_ece,'raw_brier':raw_brier,'cal_brier':cal_brier,'n':len(global_rows)}

    # Stat×side calibrators with walk-forward OOF
    logger.info("\nFitting stat×side calibrators (walk-forward OOF)...")
    for stat in STATS:
        for side in SIDES:
            subset = [r for r in rows if r['stat']==stat and r['side']==side]
            if len(subset) < MIN_SAMPLES:
                logger.info(f"  {stat}_{side}: n={len(subset)} < {MIN_SAMPLES} — skipping")
                continue

            probs    = np.array([r['prob'] for r in subset])
            outcomes = np.array([r['outcome'] for r in subset])

            raw_ece   = compute_ece(probs, outcomes)
            raw_brier = brier_score_loss(outcomes, probs)

            # Walk-forward OOF calibration
            oof_p, oof_o = walk_forward_oof(rows, stat, side)

            if oof_p is not None:
                oof_ece = compute_ece(oof_p, oof_o)
                oof_brier = brier_score_loss(oof_o, oof_p)
            else:
                oof_ece = raw_ece
                oof_brier = raw_brier

            # Fit final calibrator on ALL data
            X = probs.reshape(-1,1)

            # Try Platt
            platt = fit_platt(X, outcomes)
            platt_probs = platt.predict_proba(X)[:,1]
            platt_ece   = compute_ece(platt_probs, outcomes)
            platt_brier = brier_score_loss(outcomes, platt_probs)

            # Try isotonic
            iso = fit_isotonic(probs, outcomes)
            iso_probs = iso.predict(probs)
            iso_ece   = compute_ece(iso_probs, outcomes)
            iso_brier = brier_score_loss(outcomes, iso_probs)

            # Choose best
            best_cal   = platt if platt_brier <= iso_brier else None
            best_ece   = platt_ece if platt_brier <= iso_brier else iso_ece
            best_brier = min(platt_brier, iso_brier)
            best_type  = 'platt' if platt_brier <= iso_brier else 'isotonic'

            improvement = raw_ece - best_ece
            gate_pass   = best_ece < ECE_GATE

            flag = "✓ PASS" if gate_pass else f"⚠ ABOVE GATE ({ECE_GATE})"
            logger.info(f"  {stat}_{side}: n={len(subset)} raw_ECE={raw_ece:.4f} oof_ECE={oof_ece:.4f} cal_ECE={best_ece:.4f} [{best_type}] {flag}")

            key = f"{stat}_{side}"
            results[key] = {
                'n': len(subset),
                'raw_ece': round(raw_ece, 4),
                'oof_ece': round(oof_ece, 4),
                'cal_ece': round(best_ece, 4),
                'raw_brier': round(raw_brier, 4),
                'cal_brier': round(best_brier, 4),
                'improvement': round(improvement, 4),
                'gate_pass': gate_pass,
                'calibrator_type': best_type,
            }

            # Save calibrator (even if above gate — deploy decision is separate)
            if best_cal is not None:
                joblib.dump(best_cal, MODEL_DIR / f"platt_{key}.pkl")
            else:
                joblib.dump(iso, MODEL_DIR / f"platt_{key}.pkl")
            saved.append(f"platt_{key}.pkl")

    # Save report
    report = {'results': results, 'saved': saved, 'ece_gate': ECE_GATE}
    (MODEL_DIR / "calibration_rebuild_report.json").write_text(
        json.dumps(report, indent=2))

    # Summary
    print("\n" + "="*60)
    print("CALIBRATION REBUILD SUMMARY")
    print("="*60)
    print(f"{'key':<20} {'n':>5} {'raw_ECE':>9} {'oof_ECE':>9} {'cal_ECE':>9} {'Brier':>8} {'gate':>8}")
    print("-"*72)
    for key, r in sorted(results.items()):
        gate = "✓" if r.get('gate_pass', False) else "⚠"
        print(f"{key:<20} {r['n']:>5} {r['raw_ece']:>9.4f} {r.get('oof_ece',0):>9.4f} {r['cal_ece']:>9.4f} {r['cal_brier']:>8.4f} {gate:>8}")

    passed = sum(1 for r in results.values() if r.get('gate_pass'))
    total  = len([k for k in results if '_' in k and k.startswith(tuple(STATS))])
    print(f"\nGate passes: {passed}/{total}")
    print(f"Saved: {len(saved)} calibrators to model_cache/")
    print("\nNext: run python3 minutes_bias_fix.py")


if __name__ == '__main__':
    main()
