#!/usr/bin/env python3
"""
minutes_bias_fix.py — Minutes Model Bias Correction
=====================================================
Fixes the systematic under-projection in minutes buckets 1 and 2:
  Bucket 1: pts median residual = +3.56 (UNDER-PROJ)
  Bucket 2: pts median residual = +2.82 (UNDER-PROJ)
  Bucket 3: pts median residual = -0.07 (OK)

Approach:
  1. Compute median(actual - q50) per stat × minutes_bucket
  2. Apply bounded correction per bucket (not global)
  3. This replaces the single global BIAS_CORRECTION with a
     minutes-bucket-aware correction
  4. Validate: residuals should be near-zero after correction

Per the rebuild document:
  "add a points q50 uplift by problematic minutes buckets"
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
MODEL_DIR.mkdir(exist_ok=True)

# Caps per stat to prevent overcorrection
CORRECTION_CAPS = {
    'pts':  3.0,
    'reb':  1.5,
    'ast':  1.5,
    'fg3m': 0.8,
    'blk':  0.5,
    'stl':  0.5,
}


def load_graded():
    rows = []
    for f in sorted(glob.glob(str(GRADED_DIR / 'graded_2026-*.csv'))):
        for r in csv.DictReader(open(f)):
            try:
                actual_str = r.get('actual','')
                # CRITICAL: include zero actuals — do not exclude them
                actual = float(actual_str) if actual_str != '' else None
                if actual is None: continue
                q50 = float(r.get('q50') or 0)
                if q50 <= 0: continue
                rows.append({
                    'stat':       r.get('stat','').lower(),
                    'mp_bucket':  str(r.get('mp_bucket','')).strip(),
                    'actual':     actual,
                    'q50':        q50,
                    'residual':   actual - q50,
                })
            except: pass
    return rows


def main():
    logger.info("Loading graded data (zero actuals included)...")
    rows = load_graded()
    logger.info(f"  {len(rows)} rows")

    # Compute median residual per stat × mp_bucket
    buckets = defaultdict(list)
    for r in rows:
        key = (r['stat'], r['mp_bucket'])
        buckets[key].append(r['residual'])

    corrections = {}
    print("\n" + "="*70)
    print("MINUTES BUCKET BIAS ANALYSIS")
    print("="*70)
    print(f"{'stat':<8} {'mp_bucket':<12} {'n':>5} {'median_resid':>14} {'mean_resid':>12} {'correction':>12} {'capped?':>8}")
    print("-"*75)

    for stat in ['pts','reb','ast','fg3m','blk','stl']:
        cap = CORRECTION_CAPS.get(stat, 1.0)
        for bucket in sorted(set(b for (s,b) in buckets if s==stat)):
            resids = buckets[(stat, bucket)]
            if len(resids) < 8:
                continue
            arr = np.array(resids)
            med  = float(np.median(arr))
            mean = float(np.mean(arr))
            # Use trimmed mean (10% trim) as correction — more robust than median
            trimmed = float(np.mean(sorted(arr)[int(len(arr)*0.1):int(len(arr)*0.9)]))
            # Clip to cap
            corr = float(np.clip(trimmed, -cap, cap))
            capped = "YES" if abs(trimmed) > cap else "no"
            print(f"{stat:<8} {bucket:<12} {len(resids):>5} {med:>+14.3f} {mean:>+12.3f} {corr:>+12.3f} {capped:>8}")
            corrections[(stat, bucket)] = corr

    # Save corrections
    save_data = {
        str(k): v for k, v in corrections.items()
    }
    out_path = MODEL_DIR / "minutes_bucket_corrections.json"
    out_path.write_text(json.dumps(save_data, indent=2))
    logger.info(f"\nSaved corrections to {out_path}")

    # Validation — simulate post-correction residuals
    print("\n" + "="*70)
    print("POST-CORRECTION VALIDATION")
    print("="*70)
    print(f"{'stat':<8} {'mp_bucket':<12} {'n':>5} {'pre_median':>12} {'post_median':>12} {'improved?':>10}")
    print("-"*65)

    for stat in ['pts','reb','ast']:
        for bucket in sorted(set(b for (s,b) in buckets if s==stat)):
            resids = buckets[(stat, bucket)]
            if len(resids) < 8: continue
            corr = corrections.get((stat, bucket), 0)
            pre  = float(np.median(resids))
            post = float(np.median([r - corr for r in resids]))
            improved = "✓ YES" if abs(post) < abs(pre) else "✗ NO"
            print(f"{stat:<8} {bucket:<12} {len(resids):>5} {pre:>+12.3f} {post:>+12.3f} {improved:>10}")

    print("\n✓ Minutes bucket corrections saved.")
    print("Next: run python3 validate_all_phases.py to confirm all fixes work together")


if __name__ == '__main__':
    main()
