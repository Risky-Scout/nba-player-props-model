#!/usr/bin/env python3
"""
validate_all_phases.py — Full validation of all four fixes
==========================================================
Checks that each phase actually improved the model:
  Phase 0: Zero actuals included (BLK/STL/FG3M not corrupted)
  Phase 1: ECE improved (calibration rebuild worked)
  Phase 2: Minutes bucket residuals near-zero (bias fix worked)
  Phase 3: FG3M OVER suppressed, UNDER suppressed
  Phase 4: Deployment gates holding

Run after all fixes are applied.
"""

import csv, glob, json, warnings, logging
import numpy as np
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

GRADED_DIR = Path("graded")
MODEL_DIR  = Path("model_cache")

try:
    import joblib
    from sklearn.metrics import brier_score_loss
    HAS_SKLEARN = True
except:
    HAS_SKLEARN = False


def load_graded_full():
    """Load ALL rows including zero actuals."""
    rows = []
    zero_excluded = 0
    for f in sorted(glob.glob(str(GRADED_DIR / 'graded_2026-*.csv'))):
        for r in csv.DictReader(open(f)):
            try:
                actual_str = r.get('actual','')
                actual = float(actual_str) if actual_str != '' else None
                if actual is None:
                    zero_excluded += 1
                    continue
                rows.append({
                    'stat':       r.get('stat','').lower(),
                    'side':       r.get('side','').upper(),
                    'mp_bucket':  str(r.get('mp_bucket','')).strip(),
                    'prob':       float(r.get('model_prob') or 0),
                    'outcome':    1 if str(r.get('result','')).strip().upper() in ('HIT','WIN') else 0,
                    'actual':     actual,
                    'q50':        float(r.get('q50') or 0),
                    'clv':        float(r.get('clv_proxy') or 0),
                })
            except: pass
    return rows, zero_excluded


def compute_ece(probs, outcomes, n_bins=10):
    probs = np.array(probs)
    outcomes = np.array(outcomes)
    bins = np.linspace(0.5, 0.85, n_bins)
    ece = 0.0
    for i in range(len(bins)-1):
        mask = (probs >= bins[i]) & (probs < bins[i+1])
        if mask.sum() < 3: continue
        ece += (mask.sum()/len(probs)) * abs(probs[mask].mean() - outcomes[mask].mean())
    return float(ece)


def main():
    print("=" * 70)
    print("FULL VALIDATION — ALL FOUR PHASES")
    print("=" * 70)

    rows, zero_excluded = load_graded_full()
    print(f"\nTotal rows loaded: {len(rows)}")
    print(f"Zero-actual rows: {sum(1 for r in rows if r['actual']==0)}")
    print(f"Rows excluded (None actual): {zero_excluded}")

    # ── PHASE 0: Zero actual check ─────────────────────────────────────────
    print("\n" + "─"*60)
    print("PHASE 0: Zero-actual inclusion check")
    print("─"*60)
    for stat in ['blk','stl','fg3m']:
        zero = sum(1 for r in rows if r['stat']==stat and r['actual']==0)
        total = sum(1 for r in rows if r['stat']==stat)
        pct = zero/total*100 if total > 0 else 0
        expected = stat in ['blk','stl']
        flag = "✓ OK" if (zero > 0 or not expected) else "⚠ MISSING ZEROS"
        print(f"  {stat}: {zero}/{total} zero actuals ({pct:.1f}%) {flag}")

    # ── PHASE 1: Calibration check ─────────────────────────────────────────
    print("\n" + "─"*60)
    print("PHASE 1: Calibration ECE check (target: < 0.05)")
    print("─"*60)

    if HAS_SKLEARN:
        for stat in ['pts','reb','ast','fg3m']:
            for side in ['OVER','UNDER']:
                key = f"{stat}_{side}"
                cal_path = MODEL_DIR / f"platt_{key}.pkl"
                subset = [r for r in rows if r['stat']==stat and r['side']==side
                         and 0 < r['prob'] < 1 and r['outcome'] in (0,1)]
                if len(subset) < 20: continue
                probs    = np.array([r['prob'] for r in subset])
                outcomes = np.array([r['outcome'] for r in subset])
                raw_ece  = compute_ece(probs, outcomes)

                if cal_path.exists():
                    cal = joblib.load(cal_path)
                    try:
                        cal_probs = cal.predict_proba(probs.reshape(-1,1))[:,1]
                        cal_ece   = compute_ece(cal_probs, outcomes)
                        gate = "✓ PASS" if cal_ece < 0.05 else "⚠ ABOVE GATE"
                        print(f"  {key:<15} n={len(subset):>4} raw_ECE={raw_ece:.4f} cal_ECE={cal_ece:.4f} {gate}")
                    except Exception as e:
                        print(f"  {key:<15} cal load error: {e}")
                else:
                    print(f"  {key:<15} NO CALIBRATOR FILE")
    else:
        print("  sklearn not available — skipping")

    # ── PHASE 2: Minutes bucket residual check ─────────────────────────────
    print("\n" + "─"*60)
    print("PHASE 2: Minutes bucket residual check (target: near zero)")
    print("─"*60)

    corrections_path = MODEL_DIR / "minutes_bucket_corrections.json"
    if corrections_path.exists():
        raw_corrections = json.loads(corrections_path.read_text())
        corrections = {eval(k): v for k, v in raw_corrections.items()}

        buckets = defaultdict(list)
        for r in rows:
            if r['q50'] > 0:
                buckets[(r['stat'], r['mp_bucket'])].append(r['actual'] - r['q50'])

        print(f"  {'stat':<8} {'bucket':<10} {'n':>5} {'pre_resid':>10} {'post_resid':>11} {'ok?':>6}")
        for stat in ['pts','reb','ast']:
            for bucket in sorted(set(b for (s,b) in buckets if s==stat)):
                resids = buckets[(stat,bucket)]
                if len(resids) < 8: continue
                corr = corrections.get((stat,bucket), 0)
                pre  = float(np.median(resids))
                post = float(np.median([r - corr for r in resids]))
                ok   = "✓" if abs(post) < abs(pre) * 0.7 else "⚠"
                print(f"  {stat:<8} {bucket:<10} {len(resids):>5} {pre:>+10.3f} {post:>+11.3f} {ok:>6}")
    else:
        print("  minutes_bucket_corrections.json not found — run minutes_bias_fix.py first")

    # ── PHASE 3: FG3M/Sparse suppression check ─────────────────────────────
    print("\n" + "─"*60)
    print("PHASE 3: FG3M/Sparse OVER suppression check")
    print("─"*60)
    for stat in ['fg3m','blk','stl']:
        over_rows = [r for r in rows if r['stat']==stat and r['side']=='OVER']
        n = len(over_rows)
        if n > 0:
            hr = np.mean([r['outcome'] for r in over_rows])
            clv = np.mean([r['clv'] for r in over_rows])
            should_suppress = hr < 0.48 or clv < 0.02
            flag = "⚠ SUPPRESS" if should_suppress else "✓ OK to deploy"
            print(f"  {stat} OVER: n={n} hit_rate={hr:.3f} CLV={clv:+.4f} → {flag}")
        else:
            print(f"  {stat} OVER: n=0 (suppressed) ✓")

    # ── PHASE 4: Deployment gate check ─────────────────────────────────────
    print("\n" + "─"*60)
    print("PHASE 4: Deployment gate effectiveness")
    print("─"*60)

    # Check recent picks only (last 7 days)
    recent_dates = sorted(set(r.get('date','') for r in rows
                             if hasattr(r,'get')))[-7:]
    # Load predictions to check what passed gates
    import os
    pred_files = sorted(glob.glob('predictions/singles_2026-03-2*.json'))[-7:]
    all_picks = []
    for pf in pred_files:
        try:
            d = json.loads(open(pf).read())
            all_picks.extend(d.get('picks',[]))
        except: pass

    if all_picks:
        stat_counts = defaultdict(int)
        for p in all_picks:
            stat_counts[f"{p.get('stat','')}_{p.get('side','')}"] += 1
        print(f"  Picks in last 7 days: {len(all_picks)}")
        for key, cnt in sorted(stat_counts.items()):
            print(f"    {key}: {cnt}")

        # Check for banned stats appearing
        banned = [k for k in stat_counts if any(b in k for b in ['stl_OVER','blk_OVER','fg3m_UNDER'])]
        if banned:
            print(f"  ⚠ BANNED stats appearing: {banned}")
        else:
            print(f"  ✓ No banned stats in recent picks")
    else:
        print("  No recent prediction files found")

    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)
    print("\nIf all phases show ✓, run:")
    print("  python3 predict_darko_v4.py")
    print("  to generate new predictions with all fixes applied")


if __name__ == '__main__':
    main()
