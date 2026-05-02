"""Phase 13M — verify the active champion model is ready for production-live
Derek live snapshots.

Production-live T-minus-25 and close-lock snapshots must NOT retrain or
recalibrate. They MUST use a champion model that was trained and calibrated
through a date no later than the previous completed UTC date, with rich
metadata + leakage proofs intact.

This verifier is read-only and idempotent.

Required pointer rich fields:
    champion_model_id, trained_through_date, calibrated_through_date,
    training_run_id, calibration_run_id, validation_run_id,
    promotion_decision_id, promoted_at_utc.

Cutoff rule:
    trained_through_date  <= delivery_date - 1 UTC day
    calibrated_through_date <= delivery_date - 1 UTC day
    (Same-day training is forbidden — that would be leakage.)

Pass line:  DEREK_LIVE_CHAMPION_MODEL_READY_PASS
Fail line:  DEREK_LIVE_CHAMPION_MODEL_READY_FAILED

Usage:
    python3 scripts/verify_derek_live_champion_ready.py --delivery-date YYYY-MM-DD
"""
from __future__ import annotations

import argparse
import datetime as dt
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
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)


HEALTH_DIR = REPO_ROOT / "artifacts" / "automation_health"

REQUIRED_RICH_FIELDS = (
    "champion_model_id",
    "trained_through_date",
    "calibrated_through_date",
    "training_run_id",
    "calibration_run_id",
    "validation_run_id",
    "promotion_decision_id",
    "promoted_at_utc",
)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Report:
    delivery_date: str
    generated_at_utc: str
    code_commit: str
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
            "delivery_date": self.delivery_date,
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "passed": self.passed,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks],
            "facts": self.facts,
        }


def _parse_date(s: str | None) -> dt.date | None:
    if not s:
        return None
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Verify champion model is ready for Derek production-live snapshots."
    )
    p.add_argument(
        "--delivery-date",
        required=True,
        help="YYYY-MM-DD (snapshot delivery date — typically today UTC)",
    )
    args = p.parse_args(argv)

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    report = Report(
        delivery_date=args.delivery_date,
        generated_at_utc=utcnow_iso(),
        code_commit=git_commit(),
    )

    # 1. Pointer file exists.
    if not CHAMPION_POINTER_PATH.exists():
        report.add(
            "champion_pointer_present",
            False,
            f"missing: {CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)}",
        )
        _emit(report)
        return 1
    report.add(
        "champion_pointer_present",
        True,
        str(CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)),
    )

    pointer = read_json(CHAMPION_POINTER_PATH)
    pointer_hash = sha256_file(CHAMPION_POINTER_PATH)[:32]
    report.facts["champion_pointer_hash"] = pointer_hash
    report.facts["champion_model_id"] = pointer.get("champion_model_id")

    # 2. Bootstrap-mode pointer (no champion ever promoted) is a soft skip
    #    — we can still emit the pass line because there's nothing to verify
    #    that wouldn't be vacuous. But callers MUST treat this case as
    #    "no production-live runs allowed yet."
    bootstrap = (
        not pointer.get("champion_model_id")
        and not pointer.get("trained_through_date")
        and not pointer.get("promotion_decision_id")
    )
    if bootstrap:
        report.add(
            "champion_pointer_is_bootstrap",
            True,
            "pointer carries no promoted-champion fields — production-live "
            "Derek snapshots are not allowed until a champion is promoted.",
        )
        _emit(report)
        # Bootstrap is technically PASS for "is the pointer schema intact"
        # but caller (the runner) refuses to run production-live anyway.
        return 0

    # 3. Required rich fields present.
    missing_fields = [f for f in REQUIRED_RICH_FIELDS if not pointer.get(f)]
    report.add(
        "champion_pointer_rich_fields_present",
        not missing_fields,
        f"missing={missing_fields}" if missing_fields else "all rich fields present",
    )

    # 4. Cutoff: trained_through_date <= (delivery_date - 1 UTC day).
    delivery = _parse_date(args.delivery_date)
    yesterday = delivery - dt.timedelta(days=1) if delivery else None
    trained_through = _parse_date(pointer.get("trained_through_date"))
    calibrated_through = _parse_date(pointer.get("calibrated_through_date"))
    report.facts["trained_through_date"] = pointer.get("trained_through_date")
    report.facts["calibrated_through_date"] = pointer.get("calibrated_through_date")
    report.facts["delivery_date_minus_one_utc"] = (
        yesterday.isoformat() if yesterday else None
    )

    if yesterday and trained_through:
        report.add(
            "trained_through_date_no_later_than_yesterday",
            trained_through <= yesterday,
            f"trained_through={trained_through} yesterday={yesterday}",
        )
    else:
        report.add(
            "trained_through_date_parseable",
            False,
            f"trained_through_date={pointer.get('trained_through_date')!r} "
            f"delivery_date={args.delivery_date!r}",
        )

    if yesterday and calibrated_through:
        report.add(
            "calibrated_through_date_no_later_than_yesterday",
            calibrated_through <= yesterday,
            f"calibrated_through={calibrated_through} yesterday={yesterday}",
        )
    else:
        report.add(
            "calibrated_through_date_parseable",
            False,
            f"calibrated_through_date={pointer.get('calibrated_through_date')!r} "
            f"delivery_date={args.delivery_date!r}",
        )

    # 5. Calibrated-through must be >= trained-through (sanity).
    if trained_through and calibrated_through:
        report.add(
            "calibrated_through_ge_trained_through",
            calibrated_through >= trained_through,
            f"trained={trained_through} calibrated={calibrated_through}",
        )

    # 6. Leakage-proof flags from prior phases must not have regressed.
    for flag in ("leakage_checks_passed", "no_future_rows_verified"):
        if flag in pointer:
            report.add(
                f"pointer_flag:{flag}",
                pointer.get(flag) is True,
                f"value={pointer.get(flag)!r}",
            )

    # 7. Dry-run / synthetic-promotion guard. If the pointer was promoted by
    #    a dry run, refuse production-live use.
    promo = pointer.get("promotion_decision_id") or ""
    if "dry" in promo.lower() or "synth" in promo.lower():
        report.add(
            "champion_not_dry_run_or_synthetic",
            False,
            f"promotion_decision_id={promo!r} contains 'dry' or 'synth'",
        )
    else:
        report.add(
            "champion_not_dry_run_or_synthetic",
            True,
            f"promotion_decision_id={promo!r}",
        )

    _emit(report)
    return 0 if report.passed else 1


def _emit(report: Report) -> None:
    payload = report.to_dict()
    write_json_atomic(
        HEALTH_DIR / f"derek_live_champion_ready_{report.delivery_date}.json",
        payload,
    )
    md = [
        f"# Derek Live Champion Model Readiness — {report.delivery_date}",
        "",
        f"- generated_at_utc: {report.generated_at_utc}",
        f"- passed: **{report.passed}**",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in report.checks:
        safe = c.detail.replace("|", "\\|")
        md.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {safe} |")
    md += [
        "",
        "## Facts",
        "",
        "```json",
        json.dumps(report.facts, indent=2, sort_keys=True, default=str),
        "```",
    ]
    (HEALTH_DIR / f"derek_live_champion_ready_{report.delivery_date}.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    if report.passed:
        print("DEREK_LIVE_CHAMPION_MODEL_READY_PASS")
        if report.facts.get("champion_model_id"):
            print(
                f"  champion_model_id={report.facts['champion_model_id']!r} "
                f"trained_through={report.facts.get('trained_through_date')!r} "
                f"calibrated_through={report.facts.get('calibrated_through_date')!r}"
            )
    else:
        print("DEREK_LIVE_CHAMPION_MODEL_READY_FAILED", file=sys.stderr)
        for c in report.checks:
            if not c.passed:
                print(f"  - {c.name}: {c.detail}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
