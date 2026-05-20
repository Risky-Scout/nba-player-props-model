#!/usr/bin/env python3
import json
import sys
from datetime import date
from pathlib import Path

p = Path("artifacts/models/registry/champion_pointer.json")
if not p.exists():
    print("REAL_CHAMPION_POINTER_FAIL missing champion_pointer.json")
    sys.exit(1)

j = json.loads(p.read_text())

bad = []
text = json.dumps(j, sort_keys=True)

for field in ["champion_model_id", "model_version", "trained_through_date", "calibrated_through_date", "training_run_id", "calibration_run_id"]:
    v = str(j.get(field, ""))
    if "2099" in v or "sim-2099" in v:
        bad.append(f"{field}={v}")

if j.get("dry_run_training") is True:
    bad.append("dry_run_training=true")
if j.get("dry_run_calibration") is True:
    bad.append("dry_run_calibration=true")

for field in ["trained_through_date", "calibrated_through_date", "resolved_training_cutoff_date"]:
    v = j.get(field)
    if isinstance(v, str) and v[:4].isdigit():
        try:
            d = date.fromisoformat(v[:10])
            if d > date.today():
                bad.append(f"{field}_future={v}")
        except Exception:
            pass

if bad:
    print("REAL_CHAMPION_POINTER_FAIL")
    for x in bad:
        print("bad:", x)
    sys.exit(1)

print("REAL_CHAMPION_POINTER_PASS")
print("champion_model_id:", j.get("champion_model_id") or j.get("model_version"))
print("trained_through_date:", j.get("trained_through_date"))
print("calibrated_through_date:", j.get("calibrated_through_date"))
