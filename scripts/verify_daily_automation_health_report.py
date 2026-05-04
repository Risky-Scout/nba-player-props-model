#!/usr/bin/env python3
"""Phase 13AD — verify the daily automation health report is complete
and honest.

Inputs:
  --date YYYY-MM-DD

Checks:
  - JSON + MD exist
  - JSON has all five sections (training, predictions, derek, woo,
    after_game) with status + root_cause-when-failed
  - if any critical-path section is FAIL, OVERALL_PASS must NOT be set
  - emits a single line:
      DAILY_AUTOMATION_HEALTH_PASS    — overall passes, no warnings
      DAILY_AUTOMATION_HEALTH_WARN    — overall warn (e.g. training
                                          skipped, after-game pending)
      DAILY_AUTOMATION_HEALTH_FAILED  — report missing/incomplete OR
                                          OVERALL_FAIL OR a critical
                                          section is FAIL while overall
                                          is wrongly green
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ART_DIR = REPO_ROOT / "artifacts" / "automation_health"

REQUIRED_SECTIONS = ("training", "predictions", "derek", "woo", "after_game")
CRITICAL_SECTIONS = ("predictions", "derek", "woo")
TERMINAL_FAIL_STATUSES = {"FAIL"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args(argv)
    date = args.date
    json_path = ART_DIR / f"daily_automation_health_{date}.json"
    md_path = ART_DIR / f"daily_automation_health_{date}.md"

    failures: list[str] = []
    if not json_path.exists():
        failures.append(f"missing {json_path.relative_to(REPO_ROOT)}")
    if not md_path.exists():
        failures.append(f"missing {md_path.relative_to(REPO_ROOT)}")

    payload = None
    if json_path.exists():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            failures.append(f"json parse error: {e}")

    if payload is not None:
        sections = payload.get("sections", {})
        for name in REQUIRED_SECTIONS:
            if name not in sections:
                failures.append(f"section missing: {name}")
                continue
            sec = sections[name]
            if "status" not in sec:
                failures.append(f"section {name}: missing status")
            if sec.get("status") in TERMINAL_FAIL_STATUSES and not sec.get("root_cause"):
                failures.append(
                    f"section {name}: status={sec['status']} but no root_cause"
                )

        overall = payload.get("overall", {})
        overall_status = overall.get("status")
        # Honesty: if any critical section is FAIL, overall must not be PASS.
        critical_fail = any(
            sections.get(k, {}).get("status") in TERMINAL_FAIL_STATUSES
            for k in CRITICAL_SECTIONS
        )
        if critical_fail and overall_status == "OVERALL_PASS":
            failures.append(
                "overall=OVERALL_PASS while a critical section is FAIL — "
                "report is dishonest"
            )

    if failures:
        print("DAILY_AUTOMATION_HEALTH_FAILED  "
              f"date={date}  failures={len(failures)}", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    overall_status = (payload or {}).get("overall", {}).get("status", "")
    if overall_status == "OVERALL_FAIL":
        print(f"DAILY_AUTOMATION_HEALTH_FAILED  date={date}  overall=OVERALL_FAIL")
        return 1
    if overall_status == "OVERALL_WARN":
        print(f"DAILY_AUTOMATION_HEALTH_WARN  date={date}  "
              f"summary={(payload or {}).get('overall', {}).get('summary')!r}")
        return 0
    print(f"DAILY_AUTOMATION_HEALTH_PASS  date={date}  "
          f"summary={(payload or {}).get('overall', {}).get('summary')!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
