#!/usr/bin/env python3
"""
build_live_cal_table.py — Generates live_calibration_table.json
================================================================
Keyed by calibration_key schema matching live_pricing.py output.
For each key, stores:
  n, hit_rate, brier, logloss, recommended_prob_shrink/offset, reliability_tier
"""
import csv, glob, json, logging
import numpy as np
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

GRADED_DIR = Path("graded")
MODEL_DIR  = Path("model_cache")

TIER_THRESHOLDS = {
    'A': {'n_min': 100, 'brier_max': 0.23, 'hit_min': 0.52},
    'B': {'n_min': 50,  'brier_max': 0.26, 'hit_min': 0.49},
    'C': {'n_min': 20,  'brier_max': 0.30, 'hit_min': 0.45},
}

def load_graded():
    rows = []
    for f in sorted(glob.glob(str(GRADED_DIR / 'graded_2026-*.csv'))):
        for r in csv.DictReader(open(f)):
            try:
                result  = str(r.get('result','')).strip().upper()
                outcome = 1 if result in ('HIT','WIN') else (0 if result in ('MISS','LOSS') else None)
                if outcome is None: continue
                rows.append({
                    'stat':    r.get('stat','').lower(),
                    'side':    r.get('side','').upper(),
                    'mp_bucket': str(r.get('mp_bucket','')).strip(),
                    'prob':    float(r.get('model_prob') or 0),
                    'outcome': outcome,
                })
            except: pass
    return rows

def get_tier(n, brier, hit_rate):
    for tier, gates in TIER_THRESHOLDS.items():
        if n >= gates['n_min'] and brier <= gates['brier_max'] and hit_rate >= gates['hit_min']:
            return tier
    return 'D'

def main():
    rows = load_graded()
    logger.info(f"Loaded {len(rows)} graded rows")

    table = {}

    # Build by stat×side×mp_bucket (matches live_pricing calibration_key schema)
    buckets = defaultdict(list)
    for r in rows:
        key = f"{r['stat'].upper()}_{r['side']}_mp{r['mp_bucket']}"
        buckets[key].append(r)

    # Also build by stat×side only (broader keys)
    for r in rows:
        key = f"{r['stat'].upper()}_{r['side']}"
        buckets[key].append(r)

    for key, bucket_rows in sorted(buckets.items()):
        if len(bucket_rows) < 10: continue
        probs    = np.array([r['prob']    for r in bucket_rows])
        outcomes = np.array([r['outcome'] for r in bucket_rows])
        n        = len(outcomes)
        hit_rate = float(outcomes.mean())

        try:
            from sklearn.metrics import brier_score_loss, log_loss
            brier   = float(brier_score_loss(outcomes, probs))
            logloss = float(log_loss(outcomes, probs))
        except:
            brier   = float(np.mean((probs - outcomes)**2))
            logloss = -float(np.mean(outcomes * np.log(np.clip(probs,1e-6,1))
                                     + (1-outcomes) * np.log(np.clip(1-probs,1e-6,1))))

        tier = get_tier(n, brier, hit_rate)

        # Compute recommended shrink toward 0.5 based on calibration quality
        calibration_error = abs(probs.mean() - outcomes.mean())
        shrink = max(0.7, 1.0 - calibration_error * 2)

        # Offset: shift if systematic bias detected
        offset = float(np.clip(outcomes.mean() - probs.mean(), -0.05, 0.05))

        table[key] = {
            'key':               key,
            'n':                 n,
            'hit_rate':          round(hit_rate, 4),
            'brier':             round(brier, 5),
            'logloss':           round(logloss, 5),
            'avg_model_prob':    round(float(probs.mean()), 4),
            'reliability_tier':  tier,
            'recommended_prob_shrink': round(float(shrink), 4),
            'recommended_prob_offset': round(offset, 5),
        }
        logger.info(f"  {key:<25} n={n:>4} tier={tier} brier={brier:.4f} hit={hit_rate:.3f}")

    import datetime
    table['_meta'] = {
        'generated_at': datetime.datetime.now().isoformat(),
        'n_rows': len(rows),
    }

    out_path = MODEL_DIR / 'live_calibration_table.json'
    out_path.write_text(json.dumps(table, indent=2))
    logger.info(f"\nSaved {len(table)-1} entries to {out_path}")
    print(f"\n✓ live_calibration_table.json → {out_path}")

if __name__ == '__main__':
    main()
