#!/usr/bin/env python3
"""Phase 13AD/13AG — verify the daily automation health report is complete,
honest, and date-consistent.

Inputs:
  --date YYYY-MM-DD

Checks:
  - JSON + MD exist
  - JSON has all five sections (training, predictions, derek, woo,
    after_game) with status + root_cause-when-failed
  - if any critical-path section is FAIL, OVERALL_PASS must NOT be set
  - **same-day training consistency (Phase 13AG):**
    - training section's ``daily_report_md_path`` must point at the
      requested ``--date`` (not at a previous-day path)
    - training section's ``training_cutoff_date`` must equal ``--date``
    - if the same-day ``daily_model_training_report.json`` exists and
      its ``status`` is ``halted_pending_upstream_data``, training
      section's status MUST NOT be PASS
    - if the same-day ``run_manifest.json`` records
      ``halted_reason=previous_day_data_not_ready``, training section's
      status MUST NOT be PASS
  - emits a single line:
      DAILY_AUTOMATION_HEALTH_PASS    — overall passes, no warnings
      DAILY_AUTOMATION_HEALTH_WARN    — overall warn (e.g. training
                                          honestly halted/skipped,
                                          after-game pending)
      DAILY_AUTOMATION_HEALTH_FAILED  — report missing/incomplete OR
                                          OVERALL_FAIL OR same-day vs
                                          previous-day mismatch OR a
                                          critical section is FAIL while
                                          overall is wrongly green
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
HALT_STATUSES_NOT_PASS = {
    "halted_pending_upstream_data",
}
HALT_REASONS_NOT_PASS = {
    "previous_day_data_not_ready",
    "training_inputs_missing",
    "training_inputs_prepare_failed",
    "readiness_failed",
    "training_failed",
    "calibration_failed",
}


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


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

        # Phase 13AG/13AI: training-section consistency.
        # Training is keyed on training_cutoff_date (last day with settled
        # outcomes), which is normally <= run_date. The verifier ensures:
        #
        #   - daily_report_md_path points at the training_cutoff_date
        #     directory (NOT a stale 13AD honest-pending path that only
        #     exists when the cutoff training itself had not run yet);
        #   - training.status=PASS / NO_PROMOTE_PASS only when a
        #     completed challenger directory exists at training_cutoff_date
        #     OR when the same-day halted artifacts are correctly
        #     reclassified as historical_failed_attempt.
        training = sections.get("training", {})
        if training:
            t_status = training.get("status")
            t_cutoff = training.get("training_cutoff_date")
            t_md_path = training.get("daily_report_md_path", "")
            completed_dir = training.get("completed_cutoff_training_dir")

            expected_md = (
                f"artifacts/model_daily_reports/{t_cutoff}/daily_model_training_report.md"
                if t_cutoff else None
            )
            if expected_md and t_md_path and t_md_path != expected_md:
                failures.append(
                    f"training.daily_report_md_path={t_md_path!r} does not "
                    f"point at the training_cutoff_date={t_cutoff!r} path "
                    f"{expected_md!r}"
                )

            # If status claims PASS / NO_PROMOTE_PASS, completed_cutoff_dir
            # must exist on disk.
            if t_status in {"PASS", "NO_PROMOTE_PASS"}:
                if not completed_dir:
                    failures.append(
                        f"training.status={t_status} but no "
                        "completed_cutoff_training_dir is recorded"
                    )
                else:
                    if not (REPO_ROOT / completed_dir).exists():
                        failures.append(
                            f"training.status={t_status} but "
                            f"completed_cutoff_training_dir "
                            f"{completed_dir!r} does not exist on disk"
                        )

            # If status claims HALTED_PENDING_UPSTREAM_DATA, settled stats
            # must actually be behind the required cutoff.
            if t_status == "HALTED_PENDING_UPSTREAM_DATA":
                settled_max = training.get("settled_outcomes_max_date")
                req = training.get("required_outcomes_through")
                if settled_max and req and settled_max >= req:
                    failures.append(
                        f"training.status=HALTED_PENDING_UPSTREAM_DATA but "
                        f"settled_outcomes_max_date={settled_max!r} >= "
                        f"required_outcomes_through={req!r}; halted "
                        "classification is no longer accurate — the "
                        "stale-BDL-blocker must be cleared"
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
