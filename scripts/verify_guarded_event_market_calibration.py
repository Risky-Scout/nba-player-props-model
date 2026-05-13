#!/usr/bin/env python3
"""Verify guarded event calibration JSON schema and selection integrity."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument(
        "--model-path",
        type=Path,
        default=REPO_ROOT / "artifacts" / "models" / "guarded_event_calibration.json",
    )
    args = ap.parse_args()
    p = args.model_path
    if not p.is_file():
        print(f"MISSING_MODEL {p}", file=sys.stderr)
        return 2
    cal = json.loads(p.read_text(encoding="utf-8"))
    fails: list[str] = []
    if cal.get("market_prob_used_as_training_label") is True:
        fails.append("market_prob_used_as_training_label_must_be_false")
    if cal.get("market_pmf_used") is True:
        fails.append("market_pmf_used_must_be_false")
    if cal.get("event_calibration_source") != "guarded_oof_actuals_only":
        fails.append("wrong_event_calibration_source")
    segs = cal.get("segments") or {}
    if not isinstance(segs, dict):
        fails.append("segments_not_object")
    for k, v in segs.items():
        if not isinstance(v, dict):
            fails.append(f"bad_segment:{k}")
            continue
        t = str(v.get("type") or "").lower()
        if t == "platt":
            for fld in ("a", "b"):
                if fld not in v:
                    fails.append(f"missing_{fld}:{k}")
        elif t == "line_aware":
            for fld in ("a", "b", "c", "line_mu", "line_std"):
                if fld not in v:
                    fails.append(f"missing_{fld}:{k}")
        elif t == "isotonic":
            if "x_thresholds" not in v or "y_thresholds" not in v:
                fails.append(f"missing_iso_thresholds:{k}")
        else:
            fails.append(f"unsupported_type:{k}")
    if fails:
        print("GUARDED_EVENT_CALIBRATION_VERIFY_FAIL", file=sys.stderr)
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("GUARDED_EVENT_CALIBRATION_VERIFY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
