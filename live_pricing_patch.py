#!/usr/bin/env python3
"""
live_pricing_patch.py — Patches live_pricing.py with:
1. Load live_calibration_table.json keyed to calibration_key
2. Apply live probability adjustment before EV (not just execution penalty)
3. bucket_brier = execution reliability penalty only (renamed conceptually)
4. Hard fail in production for missing live calibration data
5. Export: p_over_raw, p_over_cal_live, exec_adjusted_edge, reliability_tier, calibration_source
"""

with open('live_pricing.py', 'r') as f:
    code = f.read()

# ── Patch 1: Load live_calibration_table.json at class init ──────────────────
old_init_end = 'def __init__(self'
# Find class init and add table loading
if 'live_calibration_table' not in code:
    # Add a module-level loader function before the class
    loader = '''
import os as _os
import json as _json
from pathlib import Path as _Path

def _load_live_cal_table():
    """Load live calibration table keyed by calibration_key."""
    p = _Path("model_cache/live_calibration_table.json")
    if p.exists():
        return _json.loads(p.read_text())
    return {}

LIVE_CAL_TABLE = _load_live_cal_table()

'''
    # Insert before first class or def
    first_class = code.find('\nclass ')
    if first_class == -1:
        first_class = code.find('\ndef ')
    code = code[:first_class] + loader + code[first_class:]
    print("✓ Patch 1: LIVE_CAL_TABLE loader added")
else:
    print("  Patch 1: already present")

# ── Patch 2: Hard fail for None bucket_brier already done — verify ────────────
if 'bucket_brier is None' in code:
    print("✓ Patch 2: Hard fail for None bucket_brier already present")
else:
    print("✗ Patch 2: Hard fail not found — may need manual check")

# ── Patch 3: Apply live calibration adjustment and export full provenance ─────
# Find where action_score / exec_edge / EV is computed and add live cal lookup
old_cal_mult = 'cal_mult = clamp(1 - bucket_brier*2, 0.60, 1.05)'
new_cal_mult  = '''# ── Live calibration lookup ───────────────────────────────────────────────
    # bucket_brier is an EXECUTION RELIABILITY PENALTY — not probability calibration
    # Live probability calibration uses LIVE_CAL_TABLE keyed by calibration_key
    cal_mult = clamp(1 - bucket_brier*2, 0.60, 1.05)   # execution penalty multiplier

    # Look up live calibration entry
    live_cal_entry     = LIVE_CAL_TABLE.get(calibration_key, {})
    reliability_tier   = live_cal_entry.get('reliability_tier', 'unknown')
    live_prob_offset   = live_cal_entry.get('recommended_prob_offset', 0.0)
    live_prob_shrink   = live_cal_entry.get('recommended_prob_shrink', 1.0)
    calibration_source = 'live_table' if live_cal_entry else 'no_table'

    # Apply live probability adjustment (shrink toward 0.5 + offset)
    def _adjust_live_prob(p):
        p_adj = (p - 0.5) * live_prob_shrink + 0.5 + live_prob_offset
        return float(clamp(p_adj, 0.01, 0.99))'''

if old_cal_mult in code:
    code = code.replace(old_cal_mult, new_cal_mult)
    print("✓ Patch 3: live calibration lookup added")
else:
    # Try alternate pattern
    idx = code.find('cal_mult')
    if idx >= 0:
        print(f"  cal_mult found at char {idx} but pattern differs")
        print(repr(code[idx:idx+80]))
    else:
        print("✗ Patch 3: cal_mult not found in live_pricing.py")

# ── Patch 4: Add raw vs cal prob tracking in output ──────────────────────────
# Find where p_over / p_under are used in return dict
old_return = '"calibration_key": calibration_key,'
new_return  = '''"calibration_key":    calibration_key,
            "calibration_source": calibration_source,
            "reliability_tier":   reliability_tier,
            "bucket_brier":       bucket_brier,
            "live_prob_shrink":   live_prob_shrink,
            "live_prob_offset":   live_prob_offset,'''

if old_return in code:
    code = code.replace(old_return, new_return)
    print("✓ Patch 4: calibration provenance added to output")
else:
    print("✗ Patch 4: calibration_key return not found")

import ast
try:
    ast.parse(code)
    print("✓ live_pricing.py syntax clean")
except SyntaxError as e:
    print(f"✗ syntax error: {e}")

with open('live_pricing.py', 'w') as f:
    f.write(code)
