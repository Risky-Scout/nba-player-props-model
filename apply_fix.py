content = open('predict.py').read()

old = (
    "                    if side_key.upper() in platt_calibrators:\n"
    "                        cp = _safe_cal(platt_calibrators[side_key.upper()], prob)\n"
    "                        if cp is not None:\n"
    "                            return cp, 'global_side'\n"
    "                    return prob, 'raw_none'"
)

new = "                    return prob, 'raw_none'"

if old not in content:
    print("MATCH FAILED — file not changed. Do not proceed.")
else:
    open('predict.py', 'w').write(content.replace(old, new, 1))
    print("✓ Applied")
