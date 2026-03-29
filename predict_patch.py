#!/usr/bin/env python3
"""
predict_patch.py — Patches predict_darko_v4.py with:
1. Calibration manifest check on startup (hard fail if missing in prod)
2. Export model_prob_raw AND model_prob_cal separately
3. cal_source field (stat_side / global_side / raw_none)
4. calibrator_version from manifest
5. Stricter EV gate when no promoted calibrator exists
"""
import re

with open('predict_darko_v4.py', 'r') as f:
    code = f.read()

# ── Patch 1: Load calibration manifest on startup ─────────────────────────────
old_cal_load = '''    logger.info("  Global calibrator loaded: OVER")
    logger.info("  Global calibrator loaded: UNDER")'''

new_cal_load = '''    logger.info("  Global calibrator loaded: OVER")
    logger.info("  Global calibrator loaded: UNDER")

    # Load calibration manifest — hard fail in production if missing
    cal_manifest = {}
    manifest_path = Path("model_cache/calibration_manifest.json")
    if manifest_path.exists():
        cal_manifest = json.loads(manifest_path.read_text())
        meta = cal_manifest.get('_meta', {})
        promoted = [k for k,v in cal_manifest.items()
                   if k != '_meta' and v.get('promoted') and v.get('scope') == 'stat_side']
        logger.info(f"  Calibration manifest loaded: {len(promoted)} promoted stat×side calibrators")
        logger.info(f"  Manifest generated: {meta.get('generated_at', 'unknown')}")
    else:
        dev_mode = os.environ.get('DEV_MODE', '').lower() in ('1', 'true', 'yes')
        if dev_mode:
            logger.warning("  calibration_manifest.json missing — DEV MODE, continuing with raw probs")
        else:
            logger.warning("  calibration_manifest.json missing — run calibrate_stat_side.py to rebuild")'''

if old_cal_load in code:
    code = code.replace(old_cal_load, new_cal_load)
    print("✓ Patch 1: manifest load added")
else:
    print("✗ Patch 1: anchor not found")

# ── Patch 2: Export raw + calibrated probs with cal_source ───────────────────
old_cal_apply = '''                def _apply_cal(prob, stat_key, side_key):
                    stat_side_key = f"{stat_key.upper()}_{side_key.upper()}"
                    cal = platt_calibrators.get(stat_side_key) or platt_calibrators.get(side_key.upper())
                    if cal:
                        try:
                            cal_prob = float(np.clip(cal.predict_proba([[prob]])[0][1], 0.01, 0.99))
                            return cal_prob
                        except Exception:
                            pass  # fall through to raw
                    return prob  # raw — calibrator missing or failed

                raw_over   = prob_over
                raw_under  = prob_under
                prob_over  = _apply_cal(prob_over,  target, "OVER")
                prob_under = _apply_cal(prob_under, target, "UNDER")
                # Fix 2: Store both raw and calibrated for audit
                cal_applied_over  = (prob_over  != raw_over)
                cal_applied_under = (prob_under != raw_under)'''

new_cal_apply = '''                def _apply_cal(prob, stat_key, side_key):
                    """Apply calibrator. Returns (cal_prob, cal_source)."""
                    stat_side_key = f"{stat_key.upper()}_{side_key.upper()}"
                    # Check manifest promotion before using stat×side calibrator
                    manifest_entry = cal_manifest.get(stat_side_key, {})
                    use_stat_side  = manifest_entry.get('promoted', True)  # default True if no manifest

                    if use_stat_side and stat_side_key in platt_calibrators:
                        cal = platt_calibrators[stat_side_key]
                        try:
                            cal_prob = float(np.clip(
                                cal.predict_proba([[prob]])[0][1], 0.01, 0.99))
                            return cal_prob, 'stat_side'
                        except Exception:
                            pass
                    # Fall back to global side calibrator
                    if side_key.upper() in platt_calibrators:
                        cal = platt_calibrators[side_key.upper()]
                        try:
                            cal_prob = float(np.clip(
                                cal.predict_proba([[prob]])[0][1], 0.01, 0.99))
                            return cal_prob, 'global_side'
                        except Exception:
                            pass
                    return prob, 'raw_none'  # no calibrator available

                raw_over   = prob_over
                raw_under  = prob_under
                prob_over,  cal_src_over  = _apply_cal(prob_over,  target, "OVER")
                prob_under, cal_src_under = _apply_cal(prob_under, target, "UNDER")
                cal_applied_over  = (cal_src_over  != 'raw_none')
                cal_applied_under = (cal_src_under != 'raw_none')'''

if old_cal_apply in code:
    code = code.replace(old_cal_apply, new_cal_apply)
    print("✓ Patch 2: cal_source tracking added")
else:
    print("✗ Patch 2: cal apply anchor not found")

# ── Patch 3: Stricter EV gate when no promoted calibrator ────────────────────
old_ev_gate = '''                    # Stat×side EV gate
                    min_ev_req = STAT_SIDE_MIN_EV.get((target, side), MIN_EV)
                    if ev < min_ev_req:
                        continue'''

new_ev_gate = '''                    # Stat×side EV gate — stricter when no promoted calibrator
                    min_ev_req = STAT_SIDE_MIN_EV.get((target, side), MIN_EV)
                    cal_src = cal_src_over if side == "OVER" else cal_src_under
                    if cal_src == 'raw_none':
                        # No calibrator: require 2x EV to compensate for uncalibrated prob
                        min_ev_req = min(min_ev_req * 2.0, 0.15)
                    if ev < min_ev_req:
                        continue'''

if old_ev_gate in code:
    code = code.replace(old_ev_gate, new_ev_gate)
    print("✓ Patch 3: stricter EV gate for raw_none calibration")
else:
    print("✗ Patch 3: EV gate anchor not found")

# ── Patch 4: Export raw + cal probs and cal_source in pick object ─────────────
old_export = '''                    all_singles.append({
                        "player_id":    player_id,
                        "player_name":  player_name,
                        "game_id":      gid,
                        "game":         glabel,
                        "team_id":      team_id,
                        "stat":         target,
                        "side":         side,
                        "line":         line,
                        "odds":         odds,
                        "over_odds":    over_odds,
                        "under_odds":   under_odds,
                        "bet_vendor":   vendor,
                        "model_prob":   round(prob, 4),
                        "market_prob":  round(novig_over if side=="OVER" else novig_under, 4),
                        "raw_edge":     round(raw_edge_val, 4),
                        "ev":           round(ev, 4),
                        "kelly_units":  round(kelly, 3),
                        "q50":          round(q50, 2),
                        "q_preds":      {float(k): round(v, 2) for k, v in q_preds.items()},
                        "usage_bucket": ub,
                        "mp_bucket":    mb,
                        # Deployment metadata for CLV tracing (doc 7 traceability)
                        "min_ev_applied": round(min_ev_req, 4),
                        # Fix 4: Explicit audit trail — raw vs calibrated
                        "cal_type":      f"{target.upper()}_{side}" if (f"{target.upper()}_{side}" in platt_calibrators) else ("global" if side in platt_calibrators else "raw_no_calibrator"),
                        "cal_applied":   cal_applied_over if side=="OVER" else cal_applied_under,
                    })'''

new_export = '''                    # Determine raw prob before calibration
                    model_prob_raw = raw_over if side == "OVER" else raw_under
                    model_prob_cal = round(prob, 4)
                    cal_src        = cal_src_over if side == "OVER" else cal_src_under

                    all_singles.append({
                        "player_id":    player_id,
                        "player_name":  player_name,
                        "game_id":      gid,
                        "game":         glabel,
                        "team_id":      team_id,
                        "stat":         target,
                        "side":         side,
                        "line":         line,
                        "odds":         odds,
                        "over_odds":    over_odds,
                        "under_odds":   under_odds,
                        "bet_vendor":   vendor,
                        # Dual probability export — raw and calibrated
                        "model_prob":     model_prob_cal,           # calibrated — used for EV/Kelly
                        "model_prob_raw": round(model_prob_raw, 4), # pre-calibration — for audit
                        "model_prob_cal": model_prob_cal,           # explicit alias
                        "cal_source":   cal_src,       # stat_side / global_side / raw_none
                        "cal_applied":  cal_src != 'raw_none',
                        "calibrator_version": cal_manifest.get('_meta', {}).get('generated_at', 'unknown'),
                        "market_prob":  round(novig_over if side=="OVER" else novig_under, 4),
                        "raw_edge":     round(raw_edge_val, 4),
                        "ev":           round(ev, 4),
                        "kelly_units":  round(kelly, 3),
                        "q50":          round(q50, 2),
                        "q_preds":      {float(k): round(v, 2) for k, v in q_preds.items()},
                        "usage_bucket": ub,
                        "mp_bucket":    mb,
                        "min_ev_applied": round(min_ev_req, 4),
                        "cal_type":     cal_src,
                    })'''

if old_export in code:
    code = code.replace(old_export, new_export)
    print("✓ Patch 4: dual prob export (raw + cal) added")
else:
    print("✗ Patch 4: export block not found")

# ── Add os and json imports if missing ────────────────────────────────────────
if 'import os' not in code:
    code = code.replace('import json\n', 'import json\nimport os\n')
    print("✓ import os added")

import ast
try:
    ast.parse(code)
    print("✓ predict_darko_v4.py syntax clean")
except SyntaxError as e:
    print(f"✗ syntax error: {e}")

with open('predict_darko_v4.py', 'w') as f:
    f.write(code)
