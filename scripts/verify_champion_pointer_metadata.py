"""Phase 13H — verify champion_pointer.json carries the required rich metadata.

After a successful promotion, ``artifacts/models/registry/champion_pointer.json``
must contain a complete provenance record so downstream consumers (Derek/WoO
delivery, dependency verifier, audit logs) can identify exactly which
challenger artifacts back the active champion and how they were produced.

Usage:
    python3 scripts/verify_champion_pointer_metadata.py
    python3 scripts/verify_champion_pointer_metadata.py --strict-bootstrap

Outputs:
    artifacts/automation_health/champion_pointer_metadata.json
    artifacts/automation_health/champion_pointer_metadata.md

Exit codes / final stdout line:
    0 + CHAMPION_POINTER_METADATA_PASS
    1 + CHAMPION_POINTER_METADATA_FAILED + per-field failure list to stderr.

Default behavior is lenient toward the bootstrap pointer — a freshly
bootstrapped pointer (no real promotion yet) lacks several Phase 13H
fields by design and is reported as ``passed_with_bootstrap_caveat`` rather
than failed. Pass ``--strict-bootstrap`` to force a hard failure on bootstrap
pointers (use only for promotion-capable runs).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_POINTER_PATH,
    git_commit,
    read_json,
    utcnow_iso,
    write_json_atomic,
)


HEALTH_DIR = REPO_ROOT / "artifacts" / "automation_health"

REQUIRED_FIELDS = (
    "champion_model_id",
    "champion_artifact_dir",
    "champion_calibrator_paths",
    "trained_through_date",
    "calibrated_through_date",
    "training_run_id",
    "calibration_run_id",
    "validation_run_id",
    "promotion_decision_id",
    "promoted_at_utc",
    "promoted_from_challenger_id",
    "train_manifest_path",
    "calibration_manifest_path",
    "validation_report_path",
    "promotion_decision_path",
    "source_data_refresh_manifest_path",
    "source_completeness_manifest_path",
    "training_input_manifest_path",
    "target_policy",
    "target_date_et",
    "resolved_training_cutoff_date",
    "no_future_rows_verified",
    "no_partial_rows_verified",
    "leakage_checks_passed",
    "dry_run_training",
    "dry_run_calibration",
    "data_hashes",
)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Report:
    generated_at_utc: str
    code_commit: str
    bootstrap_caveat: bool
    checks: list[Check] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(Check(name, ok, detail))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "bootstrap_caveat": self.bootstrap_caveat,
            "passed": self.passed,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks],
            "facts": self.facts,
        }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify champion_pointer metadata.")
    p.add_argument(
        "--strict-bootstrap",
        action="store_true",
        help=(
            "Treat a bootstrap-only pointer (pre-Phase-13H promotion) as a "
            "hard failure. Default: lenient (pass with bootstrap_caveat=true)."
        ),
    )
    args = p.parse_args(argv)
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)

    if not CHAMPION_POINTER_PATH.exists():
        report = Report(
            generated_at_utc=utcnow_iso(),
            code_commit=git_commit(),
            bootstrap_caveat=False,
        )
        report.add("champion_pointer_present", False, str(CHAMPION_POINTER_PATH))
        write_json_atomic(HEALTH_DIR / "champion_pointer_metadata.json", report.to_dict())
        print("CHAMPION_POINTER_METADATA_FAILED", file=sys.stderr)
        print("  - champion_pointer_present: missing", file=sys.stderr)
        return 1

    pointer = read_json(CHAMPION_POINTER_PATH)
    schema_version = pointer.get("schema_version", "1.0")
    is_bootstrap = (
        schema_version == "1.0"
        and "champion_model_id" not in pointer
        and "trained_through_date" not in pointer
    )
    report = Report(
        generated_at_utc=utcnow_iso(),
        code_commit=git_commit(),
        bootstrap_caveat=is_bootstrap and not args.strict_bootstrap,
    )

    report.add("champion_pointer_present", True, str(CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)))
    report.facts["schema_version"] = schema_version
    report.facts["is_bootstrap_pointer"] = is_bootstrap
    report.facts["model_version"] = pointer.get("model_version")
    report.facts["promoted_at_utc"] = pointer.get("promoted_at_utc")

    # Field-by-field presence checks.
    missing: list[str] = []
    for f in REQUIRED_FIELDS:
        present = f in pointer and pointer[f] is not None and pointer[f] != ""
        if not present:
            missing.append(f)
    report.facts["missing_fields"] = missing
    report.facts["present_field_count"] = len(REQUIRED_FIELDS) - len(missing)
    report.facts["total_required_fields"] = len(REQUIRED_FIELDS)

    if is_bootstrap and not args.strict_bootstrap:
        # A bootstrap pointer (post-Phase-13A, pre-Phase-13H) lacks the rich
        # fields by design. Report it explicitly and pass the gate so the
        # nightly pipeline can run end-to-end without forcing a promotion.
        report.add(
            "champion_pointer_metadata_complete_or_bootstrap",
            True,
            f"bootstrap pointer; missing {len(missing)}/{len(REQUIRED_FIELDS)} Phase 13H fields "
            f"(will populate after first real promotion)",
        )
    else:
        report.add(
            "champion_pointer_metadata_complete",
            not missing,
            f"missing={missing}" if missing else "all Phase 13H fields present",
        )
        # Sanity checks on key fields when present.
        for stat in ("pts", "reb", "ast", "fg3m", "tov"):
            cal_path = (pointer.get("champion_calibrator_paths") or {}).get(stat)
            if cal_path:
                resolved = REPO_ROOT / cal_path
                report.add(
                    f"champion_calibrator_path_present_{stat}",
                    resolved.exists(),
                    f"{cal_path}",
                )
        if pointer.get("dry_run_training") is True:
            report.add(
                "dry_run_training_is_false",
                False,
                "dry_run_training=true on champion is invalid for production",
            )
        if pointer.get("dry_run_calibration") is True:
            report.add(
                "dry_run_calibration_is_false",
                False,
                "dry_run_calibration=true on champion is invalid for production",
            )

    payload = report.to_dict()
    write_json_atomic(HEALTH_DIR / "champion_pointer_metadata.json", payload)

    md = [
        "# Champion Pointer Metadata Verification",
        "",
        f"- generated_at_utc: {report.generated_at_utc}",
        f"- bootstrap_caveat: {report.bootstrap_caveat}",
        f"- passed: **{report.passed}**",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in report.checks:
        safe_detail = c.detail.replace("|", "\\|")
        md.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {safe_detail} |")
    md += ["", "## Facts", "", "```", json.dumps(report.facts, indent=2, default=str), "```"]
    (HEALTH_DIR / "champion_pointer_metadata.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    if report.passed:
        print("CHAMPION_POINTER_METADATA_PASS")
        return 0
    print("CHAMPION_POINTER_METADATA_FAILED", file=sys.stderr)
    for c in report.checks:
        if not c.passed:
            print(f"  - {c.name}: {c.detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
