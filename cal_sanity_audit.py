#!/usr/bin/env python3
"""
Calibration sanity audit — explicit event orientation + decile tables
For each stat×side bucket:
  - n_total, n_oof, auc_raw, brier_raw, brier_cal_oof
  - mean raw prob, actual outcome rate
  - 10-bin reliability table
  - explicit event definition (OVER: y=1 if actual > line, UNDER: y=1 if actual < line)
"""
import csv, glob, warnings
import numpy as np
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings('ignore')

GRADED_DIR = Path("graded")

def load_graded():
    rows = []
    for f in sorted(glob.glob(str(GRADED_DIR / 'graded_2026-*.csv'))):
        for r in csv.DictReader(open(f)):
            try:
                result  = str(r.get('result','')).strip().upper()
                side    = str(r.get('side','')).strip().upper()
                # EXPLICIT event definition — no ambiguity
                if side == 'OVER':
                    outcome = 1 if result in ('HIT','WIN') else (0 if result in ('MISS','LOSS') else None)
                    event_def = "y=1 if actual > line (OVER hit)"
                elif side == 'UNDER':
                    outcome = 1 if result in ('HIT','WIN') else (0 if result in ('MISS','LOSS') else None)
                    event_def = "y=1 if actual < line (UNDER hit)"
                else:
                    continue
                if outcome is None: continue
                prob = float(r.get('model_prob') or 0)
                if not (0.01 < prob < 0.99): continue
                actual = float(r.get('actual') or 0) if r.get('actual','') != '' else None
                line   = float(r.get('line') or 0)
                rows.append({
                    'stat':       r.get('stat','').lower(),
                    'side':       side,
                    'prob':       prob,
                    'outcome':    outcome,
                    'actual':     actual,
                    'line':       line,
                    'event_def':  event_def,
                })
            except: pass
    rows.sort(key=lambda x: x.get('stat',''))
    return rows

def reliability_table(probs, outcomes, n_bins=10):
    probs    = np.array(probs)
    outcomes = np.array(outcomes)
    bins     = np.percentile(probs, np.linspace(0, 100, n_bins+1))
    bins     = np.unique(bins)
    rows     = []
    for i in range(len(bins)-1):
        lo, hi = bins[i], bins[i+1]
        if i == len(bins)-2:
            mask = (probs >= lo) & (probs <= hi)
        else:
            mask = (probs >= lo) & (probs < hi)
        if mask.sum() < 3: continue
        rows.append({
            'bin':       f"{lo:.3f}-{hi:.3f}",
            'n':         int(mask.sum()),
            'mean_pred': float(probs[mask].mean()),
            'mean_act':  float(outcomes[mask].mean()),
            'error':     float(probs[mask].mean() - outcomes[mask].mean()),
        })
    return rows

def auc_score(probs, outcomes):
    try:
        from sklearn.metrics import roc_auc_score
        if len(np.unique(outcomes)) < 2: return float('nan')
        return float(roc_auc_score(outcomes, probs))
    except: return float('nan')

def main():
    rows = load_graded()
    print(f"Loaded {len(rows)} graded rows")

    # Verify orientation independently
    print("\n=== ORIENTATION VERIFICATION ===")
    print("Checking: when model_prob is HIGH, does OVER actually hit more?")

    for stat in ['pts','reb','ast']:
        for side in ['OVER','UNDER']:
            subset = [r for r in rows if r['stat']==stat and r['side']==side
                     and r['actual'] is not None]
            if len(subset) < 30: continue
            probs    = np.array([r['prob']    for r in subset])
            outcomes = np.array([r['outcome'] for r in subset])
            actuals  = np.array([r['actual']  for r in subset])
            lines    = np.array([r['line']    for r in subset])

            # Direct orientation check: high prob → high outcome rate?
            hi_mask = probs > np.median(probs)
            lo_mask = ~hi_mask
            hi_rate = outcomes[hi_mask].mean() if hi_mask.sum() > 5 else float('nan')
            lo_rate = outcomes[lo_mask].mean() if lo_mask.sum() > 5 else float('nan')
            monotonic = "✓ CORRECT" if hi_rate > lo_rate else "✗ INVERTED"

            # Also check: for OVER, does high prob correlate with actual > line?
            if len(actuals) > 0 and not np.all(actuals == 0):
                direct_hit = (actuals > lines).astype(float) if side=='OVER' else (actuals < lines).astype(float)
                agreement  = float(np.mean(outcomes == direct_hit))
                result_consistency = f"result/actual agreement: {agreement:.3f}"
            else:
                result_consistency = "no actual data"

            print(f"  {stat}_{side}: hi_prob_rate={hi_rate:.3f} lo_prob_rate={lo_rate:.3f} → {monotonic} | {result_consistency}")

    # Full audit per stat×side
    stats_list = ['pts','reb','ast','fg3m','blk','stl']
    for stat in stats_list:
        for side in ['OVER','UNDER']:
            subset = [r for r in rows if r['stat']==stat and r['side']==side]
            if len(subset) < 20: continue
            probs    = np.array([r['prob']    for r in subset])
            outcomes = np.array([r['outcome'] for r in subset])
            n        = len(subset)
            event_def = subset[0]['event_def']

            # OOF AUC via TimeSeriesSplit
            try:
                from sklearn.model_selection import TimeSeriesSplit
                from sklearn.linear_model import LogisticRegression
                from sklearn.metrics import brier_score_loss
                tscv = TimeSeriesSplit(n_splits=5)
                oof  = np.full(n, np.nan)
                for tr, va in tscv.split(probs):
                    if len(tr) < 10: continue
                    y_tr = outcomes[tr]
                    if len(np.unique(y_tr)) < 2: continue
                    p_clip = np.clip(probs[tr], 1e-4, 1-1e-4)
                    X_tr = np.log(p_clip/(1-p_clip)).reshape(-1,1)
                    p_va = np.clip(probs[va], 1e-4, 1-1e-4)
                    X_va = np.log(p_va/(1-p_va)).reshape(-1,1)
                    lr = LogisticRegression(C=1.0,solver='lbfgs',max_iter=500)
                    lr.fit(X_tr, y_tr)
                    oof[va] = lr.predict_proba(X_va)[:,1]
                valid    = ~np.isnan(oof)
                n_oof    = int(valid.sum())
                auc_raw  = auc_score(probs, outcomes)
                brier_raw = float(brier_score_loss(outcomes, probs))
                brier_cal = float(brier_score_loss(outcomes[valid], oof[valid])) if n_oof > 10 else float('nan')
            except Exception as e:
                n_oof = 0; auc_raw = float('nan')
                brier_raw = float(np.mean((probs-outcomes)**2))
                brier_cal = float('nan')

            print(f"\n{'='*65}")
            print(f"  {stat.upper()}_{side}")
            print(f"  Event definition: {event_def}")
            print(f"  n_total={n}  n_oof={n_oof}")
            print(f"  auc_raw={auc_raw:.4f}  brier_raw={brier_raw:.5f}  brier_cal_oof={brier_cal:.5f}")
            print(f"  mean_raw_prob={probs.mean():.4f}  actual_outcome_rate={outcomes.mean():.4f}")
            print(f"  Overconfidence gap: {probs.mean()-outcomes.mean():+.4f}")
            print()
            print(f"  {'Bin':<16} {'n':>5} {'pred_prob':>10} {'act_rate':>10} {'error':>8} {'signal':>8}")
            print(f"  {'-'*60}")
            for row in reliability_table(probs, outcomes):
                signal = "✓" if abs(row['error']) < 0.05 else ("⚠ OVER" if row['error'] > 0 else "⚠ UNDER")
                print(f"  {row['bin']:<16} {row['n']:>5} {row['mean_pred']:>10.3f} {row['mean_act']:>10.3f} {row['error']:>+8.3f} {signal:>8}")

    print(f"\n{'='*65}")
    print("AUDIT COMPLETE")
    print(f"{'='*65}")
    print("\nConclusion key:")
    print("  AUC > 0.52 = model has some ranking signal")
    print("  AUC ≈ 0.50 = model has NO ranking signal (flat/random)")
    print("  AUC < 0.48 = model is INVERTED (betting opposite would help)")
    print("  Decile table monotone rising = calibration can help")
    print("  Decile table flat = base model broken, calibration cannot fix")

if __name__ == '__main__':
    main()
