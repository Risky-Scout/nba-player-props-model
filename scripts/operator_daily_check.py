#!/usr/bin/env python3
"""Phase 13AH — operator daily check.

One-command dashboard that calls
``scripts/verify_full_daily_production_contract.py`` and prints a clean
PASS/WARN/FAIL grid plus a single OPERATOR_DAILY_CHECK_PASS/WARN/FAILED
final line.

Usage:
    python3 scripts/operator_daily_check.py \\
        --date 2026-05-04 \\
        --derek-date 2026-05-03 \\
        --required-outcomes-through 2026-05-03
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


SECTION_LABEL_MAP = (
    ("training_automation",      "TRAINING       "),
    ("recalibration_automation", "RECALIBRATION  "),
    ("daily_predictions",        "PREDICTIONS    "),
    ("woo_snapshot_state_machine", "WOO STATE M/C  "),
    ("woo_morning_snapshot",     "WOO MORNING    "),
    ("woo_t_minus_25",           "WOO T-25       "),
    ("woo_close_lock",           "WOO CLOSE      "),
    ("derek_current_live",       "DEREK CURRENT  "),
    ("derek_live_snapshots",     "DEREK T-25     "),
    ("derek_production_live_e2e","DEREK CLOSE    "),
    ("derek_after_game_scoring", "DEREK SCORING  "),
    ("woo_after_game_scoring",   "WOO SCORING    "),
    ("pmf_variance_calibration_study", "CALIBRATION    "),
    ("human_readable_reports",   "HUMAN REPORTS  "),
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    ap.add_argument("--derek-date", required=True)
    ap.add_argument("--required-outcomes-through", required=True)
    args = ap.parse_args(argv)

    cmd = [
        sys.executable,
        "scripts/verify_full_daily_production_contract.py",
        "--date", args.date,
        "--derek-date", args.derek_date,
        "--required-outcomes-through", args.required_outcomes_through,
    ]
    rc = subprocess.run(cmd, cwd=REPO_ROOT).returncode

    payload_path = REPO_ROOT / "artifacts" / "automation_health" / f"full_daily_production_contract_{args.date}.json"
    if not payload_path.exists():
        print("OPERATOR_DAILY_CHECK_FAILED  reason=contract_payload_not_found",
              file=sys.stderr)
        return 1
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    checks = {c["name"]: c for c in payload.get("checks", [])}

    print()
    print("=" * 60)
    print(f" OPERATOR DAILY CHECK — date={args.date}  "
          f"derek={args.derek_date}")
    print("=" * 60)
    for key, label in SECTION_LABEL_MAP:
        sec = checks.get(key, {"status": "MISSING"})
        print(f" {label}: {sec['status']}")
    print("-" * 60)
    overall = payload.get("overall", "FULL_DAILY_PRODUCTION_CONTRACT_FAILED")
    if overall.endswith("_PASS"):
        op = "OPERATOR_DAILY_CHECK_PASS"
    elif overall.endswith("_WARN"):
        op = "OPERATOR_DAILY_CHECK_WARN"
    else:
        op = "OPERATOR_DAILY_CHECK_FAILED"
    print(f" OVERALL:        {overall.replace('FULL_DAILY_PRODUCTION_CONTRACT_', '')}")
    print("=" * 60)
    print(op)
    return 0 if op != "OPERATOR_DAILY_CHECK_FAILED" else 1


if __name__ == "__main__":
    sys.exit(main())
