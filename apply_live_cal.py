content = open('predict.py').read()
changes = 0

# ── Change 1: Load live_cal_table in load_models() and add to return ──
old1 = "    return models, within_engine, teammate_engine, platt_calibrators, fg3m_hurdle_model, _centerer"
new1 = (
    "    # Load live calibration table (built from 2534 rows — shrinks overconfident raw probs)\n"
    "    _live_cal_path = Path(\"model_cache\") / \"live_calibration_table.json\"\n"
    "    live_cal_table = {}\n"
    "    try:\n"
    "        live_cal_table = json.load(open(_live_cal_path))\n"
    "        n = len([k for k in live_cal_table if not k.startswith('_')])\n"
    "        logger.info(f\"  Live calibration table loaded: {n} entries\")\n"
    "    except Exception as e:\n"
    "        logger.warning(f\"  Live calibration table not found: {e}\")\n"
    "\n"
    "    return models, within_engine, teammate_engine, platt_calibrators, fg3m_hurdle_model, _centerer, live_cal_table"
)
if old1 in content:
    content = content.replace(old1, new1, 1)
    changes += 1
    print("✓ Change 1 applied: live_cal_table loading added to load_models()")
else:
    print("✗ Change 1 FAILED — return statement not found")

# ── Change 2: Update call site to unpack live_cal_table ──
old2 = "    models, within_engine, teammate_engine, platt_calibrators, fg3m_hurdle_model, _centerer = load_models()"
new2 = "    models, within_engine, teammate_engine, platt_calibrators, fg3m_hurdle_model, _centerer, live_cal_table = load_models()"
if old2 in content:
    content = content.replace(old2, new2, 1)
    changes += 1
    print("✓ Change 2 applied: call site unpacks live_cal_table")
else:
    print("✗ Change 2 FAILED — call site not found")

# ── Change 3: Apply shrink+offset in _apply_cal before raw fallback ──
old3 = "                    return prob, 'raw_none'"
new3 = (
    "                    cal_key = f\"{stat_key.upper()}_{side_key.upper()}\"\n"
    "                    if cal_key in live_cal_table:\n"
    "                        entry = live_cal_table[cal_key]\n"
    "                        shrink = entry.get('recommended_prob_shrink', 1.0)\n"
    "                        offset = entry.get('recommended_prob_offset', 0.0)\n"
    "                        cp = float(np.clip(prob * shrink + offset, 0.01, 0.99))\n"
    "                        return cp, 'live_cal'\n"
    "                    return prob, 'raw_none'"
)
if old3 in content:
    content = content.replace(old3, new3, 1)
    changes += 1
    print("✓ Change 3 applied: live_cal shrink+offset applied in _apply_cal")
else:
    print("✗ Change 3 FAILED — raw_none fallback not found")

if changes == 3:
    open('predict.py', 'w').write(content)
    print("\n✓ All 3 changes applied. Run syntax check next.")
else:
    print(f"\n✗ Only {changes}/3 changes applied — file NOT written.")
