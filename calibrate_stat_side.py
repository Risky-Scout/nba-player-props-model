#!/usr/bin/env python3
"""
calibrate_stat_side.py — Stat×Side Platt Calibration with Walk-Forward OOF
============================================================================
Replaces in-sample fitting with true time-ordered OOF calibration.

Architecture:
  1. Load all graded rows sorted by date (temporal ordering)
  2. For each stat×side: TimeSeriesSplit(n_splits=5) walk-forward OOF
  3. Report OOF metrics (Brier, LogLoss, AUC, slope, intercept)
  4. Promote calibrator only if hard gate passes
  5. Fit final calibrator on ALL data for deployment
  6. Save .pkl + calibration_manifest.json + calibration_report_oof.csv

Calibrator: logit(p) → LogisticRegression (simpler, more stable than CalibratedClassifierCV)

Promotion gates:
  n_total >= 80
  n_oof >= 60
  brier_cal_oof < brier_raw
  logloss_cal_oof <= logloss_raw + 0.01
  0.8 <= slope_cal <= 1.2
"""

import csv, glob, json, logging, warnings
import numpy as np
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings('ignore')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

try:
    import joblib
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
except ImportError as e:
    raise SystemExit(f"Missing dependency: {e}. Run: pip install scikit-learn joblib")

GRADED_DIR  = Path("graded")
MODEL_DIR   = Path("model_cache")
MODEL_DIR.mkdir(exist_ok=True)

STATS = ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']
SIDES = ['OVER', 'UNDER']

# ── Promotion gates ────────────────────────────────────────────────────────────
GATE_N_TOTAL        = 80
GATE_N_OOF          = 60
GATE_SLOPE_LO       = 0.8
GATE_SLOPE_HI       = 1.2
GATE_LOGLOSS_TOL    = 0.01   # cal logloss must be <= raw + this


# ── Calibrator class ───────────────────────────────────────────────────────────
class PlattCalibrator:
    """
    Platt scaling via logit transform → LogisticRegression.
    Simpler and more stable than CalibratedClassifierCV passthrough.
    """
    def __init__(self, C=1.0):
        self.C   = C
        self.lr  = LogisticRegression(C=C, solver='lbfgs', max_iter=1000)
        self.fitted = False

    def _logit(self, p):
        p = np.clip(np.array(p, dtype=float), 1e-4, 1 - 1e-4)
        return np.log(p / (1 - p))

    def fit(self, probs, outcomes):
        X = self._logit(probs).reshape(-1, 1)
        y = np.array(outcomes, dtype=int)
        if len(np.unique(y)) < 2:
            raise ValueError("Need both classes to fit calibrator")
        self.lr.fit(X, y)
        self.fitted = True
        self.slope_     = float(self.lr.coef_[0][0])
        self.intercept_ = float(self.lr.intercept_[0])
        return self

    def predict_proba(self, probs):
        if not self.fitted:
            raise RuntimeError("Calibrator not fitted")
        X = self._logit(np.array(probs)).reshape(-1, 1)
        return self.lr.predict_proba(X)[:, 1]

    def predict_proba_2d(self, X):
        """sklearn-compatible interface: X is (n,1) raw probs."""
        cal = self.predict_proba(X[:, 0])
        return np.column_stack([1 - cal, cal])


class IsotonicCalibrator:
    """
    Isotonic regression calibrator — non-parametric, strictly superior to
    Platt scaling when the probability-outcome relationship is non-sigmoid.
    Uses sklearn IsotonicRegression with out-of-bounds clipping.
    """
    def __init__(self):
        from sklearn.isotonic import IsotonicRegression
        self.ir     = IsotonicRegression(out_of_bounds='clip', increasing=True)
        self.fitted = False

    def fit(self, probs, outcomes):
        probs    = np.clip(np.array(probs, dtype=float), 1e-4, 1 - 1e-4)
        outcomes = np.array(outcomes, dtype=float)
        if len(np.unique(outcomes)) < 2:
            raise ValueError("Need both classes to fit calibrator")
        self.ir.fit(probs, outcomes)
        self.fitted = True
        return self

    def predict_proba(self, probs):
        if not self.fitted:
            raise RuntimeError("Calibrator not fitted")
        probs = np.clip(np.array(probs, dtype=float), 1e-4, 1 - 1e-4)
        return np.clip(self.ir.predict(probs), 1e-4, 1 - 1e-4)

    def predict_proba_2d(self, X):
        cal = self.predict_proba(X[:, 0])
        return np.column_stack([1 - cal, cal])


def _compute_ece(probs, outcomes, n_bins=8):
    probs    = np.array(probs)
    outcomes = np.array(outcomes)
    bins     = np.linspace(0.4, 0.9, n_bins + 1)
    ece      = 0.0
    for i in range(len(bins) - 1):
        mask = (probs >= bins[i]) & (probs < bins[i + 1])
        if mask.sum() < 3:
            continue
        ece += (mask.sum() / len(probs)) * abs(probs[mask].mean() - outcomes[mask].mean())
    return float(ece)


def _calibration_slope(probs, outcomes):
    """Fit logit(p) ~ a + b*logit(raw) and return slope b."""
    lr = LogisticRegression(C=1.0, solver='lbfgs', max_iter=500)
    X  = np.clip(probs, 1e-4, 1 - 1e-4)
    X  = np.log(X / (1 - X)).reshape(-1, 1)
    y  = np.array(outcomes, dtype=int)
    if len(np.unique(y)) < 2:
        return 1.0, 0.0
    lr.fit(X, y)
    return float(lr.coef_[0][0]), float(lr.intercept_[0])


# ── Data loading ───────────────────────────────────────────────────────────────
def load_graded():
    rows = []
    for f in sorted(glob.glob(str(GRADED_DIR / 'graded_2026-*.csv'))):
        date = Path(f).stem.replace('graded_', '')
        for r in csv.DictReader(open(f)):
            try:
                result  = str(r.get('result', '')).strip().upper()
                outcome = 1 if result in ('HIT', 'WIN') else (
                          0 if result in ('MISS', 'LOSS') else None)
                if outcome is None:
                    continue
                prob = float(r.get('model_prob') or 0)
                if not (0.01 < prob < 0.99):
                    continue
                rows.append({
                    'date':    date,
                    'stat':    r.get('stat', '').lower(),
                    'side':    r.get('side', '').upper(),
                    'prob':    prob,
                    'outcome': outcome,
                })
            except Exception:
                pass
    rows.sort(key=lambda x: x['date'])   # temporal ordering — critical
    return rows


# ── OOF walk-forward evaluation ────────────────────────────────────────────────
def oof_evaluate(probs, outcomes, n_splits=5):
    """
    TimeSeriesSplit walk-forward: fit on past, predict on future.
    Returns oof_probs array aligned with input arrays.
    """
    probs    = np.array(probs)
    outcomes = np.array(outcomes)
    n        = len(probs)
    oof      = np.full(n, np.nan)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    for train_idx, val_idx in tscv.split(probs):
        if len(train_idx) < 10:
            continue
        y_tr = outcomes[train_idx]
        if len(np.unique(y_tr)) < 2:
            continue
        try:
            cal = IsotonicCalibrator()
            cal.fit(probs[train_idx], y_tr)
            oof[val_idx] = cal.predict_proba(probs[val_idx])
        except Exception:
            pass

    valid = ~np.isnan(oof)
    return oof, valid


# ── Metrics ────────────────────────────────────────────────────────────────────
def compute_metrics(probs_raw, probs_cal, outcomes):
    """Compute full metric suite for raw and calibrated probabilities."""
    probs_raw = np.array(probs_raw)
    outcomes  = np.array(outcomes)

    def safe_auc(p, y):
        try:
            return float(roc_auc_score(y, p)) if len(np.unique(y)) > 1 else 0.5
        except Exception:
            return 0.5

    slope_raw, int_raw = _calibration_slope(probs_raw, outcomes)
    metrics = {
        'brier_raw':      round(float(brier_score_loss(outcomes, probs_raw)), 5),
        'logloss_raw':    round(float(log_loss(outcomes, probs_raw)), 5),
        'auc_raw':        round(safe_auc(probs_raw, outcomes), 4),
        'ece_raw':        round(_compute_ece(probs_raw, outcomes), 5),
        'slope_raw':      round(slope_raw, 4),
        'intercept_raw':  round(int_raw, 4),
    }
    if probs_cal is not None:
        probs_cal = np.array(probs_cal)
        slope_cal, int_cal = _calibration_slope(probs_cal, outcomes)
        metrics.update({
            'brier_cal_oof':    round(float(brier_score_loss(outcomes, probs_cal)), 5),
            'logloss_cal_oof':  round(float(log_loss(outcomes, probs_cal)), 5),
            'auc_cal_oof':      round(safe_auc(probs_cal, outcomes), 4),
            'ece_cal_oof':      round(_compute_ece(probs_cal, outcomes), 5),
            'slope_cal':        round(slope_cal, 4),
            'intercept_cal':    round(int_cal, 4),
        })
    return metrics


# ── Promotion gate ─────────────────────────────────────────────────────────────
def check_promotion(metrics, n_total, n_oof):
    reasons = []
    if n_total < GATE_N_TOTAL:
        reasons.append(f"n_total={n_total} < {GATE_N_TOTAL}")
    if n_oof < GATE_N_OOF:
        reasons.append(f"n_oof={n_oof} < {GATE_N_OOF}")
    if metrics.get('brier_cal_oof', 1) >= metrics.get('brier_raw', 1):
        reasons.append("brier_cal_oof >= brier_raw")
    if metrics.get('logloss_cal_oof', 1) > metrics.get('logloss_raw', 0) + GATE_LOGLOSS_TOL:
        reasons.append("logloss_cal_oof too high")
    slope = metrics.get('slope_cal', 1.0)
    if not (GATE_SLOPE_LO <= slope <= GATE_SLOPE_HI):
        reasons.append(f"slope_cal={slope:.3f} outside [{GATE_SLOPE_LO},{GATE_SLOPE_HI}]")
    return len(reasons) == 0, reasons


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    logger.info("="*60)
    logger.info("CALIBRATE STAT×SIDE — Walk-Forward OOF Rebuild")
    logger.info("="*60)

    rows = load_graded()
    logger.info(f"Loaded {len(rows)} graded rows (sorted by date)")
    if not rows:
        logger.warning('No graded rows found — skipping calibration')
        return
    logger.info(f"Date range: {rows[0]['date']} → {rows[-1]['date']}")

    manifest    = {}
    report_rows = []

    # ── Stat×side calibrators ──────────────────────────────────────────────────
    logger.info("\n--- Stat×Side Calibrators ---")
    for stat in STATS:
        for side in SIDES:
            key    = f"{stat.upper()}_{side}"
            subset = [r for r in rows if r['stat'] == stat and r['side'] == side]
            n_total = len(subset)

            if n_total < 20:
                logger.info(f"  {key:<15} n={n_total:>4} — SKIP (too few rows)")
                continue

            probs    = np.array([r['prob']    for r in subset])
            outcomes = np.array([r['outcome'] for r in subset])

            # OOF evaluation
            oof_probs, valid = oof_evaluate(probs, outcomes)
            n_oof = int(valid.sum())

            # Metrics
            if n_oof >= 10:
                # Must filter probs_raw to same indices as oof_probs to avoid length mismatch
                metrics = compute_metrics(probs[valid], oof_probs[valid], outcomes[valid])
            else:
                metrics = compute_metrics(probs, None, outcomes)

            metrics['n_total'] = n_total
            metrics['n_oof']   = n_oof

            # Promotion check
            promoted, reasons = check_promotion(metrics, n_total, n_oof)

            # Fit final calibrator on ALL data
            try:
                final_cal = IsotonicCalibrator()
                final_cal.fit(probs, outcomes)
                metrics['slope_final']     = round(final_cal.slope_, 4)
                metrics['intercept_final'] = round(final_cal.intercept_, 4)
            except Exception as e:
                logger.warning(f"  {key} final fit failed: {e}")
                promoted = False
                reasons.append(f"final fit failed: {e}")

            gate_str = "✓ PROMOTED" if promoted else f"✗ NOT PROMOTED ({'; '.join(reasons)})"
            logger.info(
                f"  {key:<15} n={n_total:>4} oof={n_oof:>4} "
                f"Brier {metrics.get('brier_raw',0):.4f}→{metrics.get('brier_cal_oof',0):.4f} "
                f"ECE {metrics.get('ece_raw',0):.4f}→{metrics.get('ece_cal_oof',0):.4f} "
                f"slope={metrics.get('slope_cal',0):.3f} {gate_str}"
            )

            if promoted:
                path = MODEL_DIR / f"platt_{key}.pkl"
                joblib.dump(final_cal, path)

            manifest[key] = {
                'key':            key,
                'stat':           stat,
                'side':           side,
                'scope':          'stat_side',
                'n_total':        n_total,
                'n_oof':          n_oof,
                'promoted':       promoted,
                'promotion_reasons': reasons if not promoted else [],
                **metrics,
            }

            report_rows.append({
                'key': key, 'scope': 'stat_side',
                'n_total': n_total, 'n_oof': n_oof,
                'promoted': promoted,
                **metrics,
            })

    # ── Global side calibrators ────────────────────────────────────────────────
    logger.info("\n--- Global Side Calibrators ---")
    for side in SIDES:
        key     = f"global_{side}"
        subset  = [r for r in rows if r['side'] == side]
        n_total = len(subset)

        probs    = np.array([r['prob']    for r in subset])
        outcomes = np.array([r['outcome'] for r in subset])

        if len(probs) < 7:  # need at least n_splits+1 samples
            logger.warning("No graded rows found — skipping calibration")
            continue
        oof_probs, valid = oof_evaluate(probs, outcomes, n_splits=5)
        n_oof = int(valid.sum())
        if n_oof >= 10:
            metrics = compute_metrics(probs[valid], oof_probs[valid], outcomes[valid])
        else:
            metrics = compute_metrics(probs, None, outcomes)
        metrics['n_total'] = n_total
        metrics['n_oof']   = n_oof

        final_cal = IsotonicCalibrator()
        final_cal.fit(probs, outcomes)
        joblib.dump(final_cal, MODEL_DIR / f"platt_{side}.pkl")

        promoted = True  # always save global fallback
        logger.info(
            f"  {key:<15} n={n_total:>4} oof={n_oof:>4} "
            f"Brier {metrics.get('brier_raw',0):.4f}→{metrics.get('brier_cal_oof',0):.4f} "
            f"✓ SAVED (global fallback always saved)"
        )

        manifest[key] = {'key': key, 'scope': 'global', 'promoted': True,
                         'n_total': n_total, 'n_oof': n_oof, **metrics}
        report_rows.append({'key': key, 'scope': 'global', 'promoted': True,
                            'n_total': n_total, 'n_oof': n_oof, **metrics})

    # ── Save manifest and report ───────────────────────────────────────────────
    import datetime
    manifest['_meta'] = {
        'generated_at': datetime.datetime.now().isoformat(),
        'n_rows_total':  len(rows),
        'gate_n_total':  GATE_N_TOTAL,
        'gate_n_oof':    GATE_N_OOF,
        'gate_slope_lo': GATE_SLOPE_LO,
        'gate_slope_hi': GATE_SLOPE_HI,
    }

    manifest_path = MODEL_DIR / 'calibration_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(f"\nSaved calibration_manifest.json → {manifest_path}")

    report_path = MODEL_DIR / 'calibration_report_oof.csv'
    if report_rows:
        fieldnames = sorted(set(k for r in report_rows for k in r))
        with open(report_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in report_rows:
                w.writerow({k: r.get(k, '') for k in fieldnames})
    logger.info(f"Saved calibration_report_oof.csv → {report_path}")

    # ── Summary ────────────────────────────────────────────────────────────────
    promoted_keys = [k for k,v in manifest.items()
                     if k != '_meta' and v.get('promoted') and v.get('scope') == 'stat_side']
    skipped_keys  = [k for k,v in manifest.items()
                     if k != '_meta' and not v.get('promoted') and v.get('scope') == 'stat_side']

    print("\n" + "="*60)
    print("CALIBRATION REBUILD COMPLETE")
    print("="*60)
    print(f"  Promoted stat×side: {len(promoted_keys)}")
    for k in promoted_keys:
        m = manifest[k]
        print(f"    ✓ {k:<15} Brier {m.get('brier_raw',0):.4f}→{m.get('brier_cal_oof',0):.4f}")
    print(f"\n  Not promoted (falling back to global): {len(skipped_keys)}")
    for k in skipped_keys:
        reasons = manifest[k].get('promotion_reasons', [])
        print(f"    ✗ {k:<15} {'; '.join(reasons)}")
    print(f"\n  Global fallbacks saved: platt_OVER.pkl, platt_UNDER.pkl")
    print(f"  Manifest: {manifest_path}")
    print(f"  Report:   {report_path}")


if __name__ == '__main__':
    main()
