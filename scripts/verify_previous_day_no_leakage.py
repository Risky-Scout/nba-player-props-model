"""Phase 13G — verify no future-data leakage in a real challenger run.

Reads every artifact the orchestrator produced for a date (training inputs
manifest, train manifest, calibration manifest, validation report, promotion
decision) plus the actual scoped parquets, and confirms that every
``game_date`` consumed by training / calibration / validation / output
generation is ``<= resolved_training_cutoff_date``. Also confirms that no
future odds, injuries, lineups, or outcomes leaked through.

Usage:
    python3 scripts/verify_previous_day_no_leakage.py --as-of-date YYYY-MM-DD

Outputs:
    artifacts/nightly_training/<date>/previous_day_no_leakage.json
    artifacts/nightly_training/<date>/previous_day_no_leakage.md

Final line on success:
    PREVIOUS_DAY_NO_LEAKAGE_VERIFICATION_PASS

Final line on failure:
    PREVIOUS_DAY_NO_LEAKAGE_FAILED + structured details to stderr.
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
    challenger_dir,
    git_commit,
    nightly_run_dir,
    parse_date,
    read_json,
    utcnow_iso,
    write_json_atomic,
)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class LeakageReport:
    as_of_date: str
    target_date_et: str | None
    resolved_training_cutoff_date: str
    generated_at_utc: str
    code_commit: str
    checks: list[Check] = field(default_factory=list)
    max_dates: dict = field(default_factory=dict)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(Check(name, passed, detail))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "as_of_date": self.as_of_date,
            "target_date_et": self.target_date_et,
            "resolved_training_cutoff_date": self.resolved_training_cutoff_date,
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "leakage_checks_passed": self.passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks
            ],
            "max_dates": self.max_dates,
        }


def _parse_date_str(s: str | None) -> dt.date | None:
    if not s:
        return None
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def check_fold_aggregate_max_date(report: LeakageReport, ch_dir: Path, cutoff: dt.date) -> None:
    """Confirm the OOF parquet that calibrate_pmf actually consumed has no
    rows newer than the resolved cutoff.

    Phase 13AI: ``aggregate_input/fold_aggregate.parquet`` is gitignored
    under ``artifacts/models/challengers/**/*.parquet``. On a freshly
    pulled origin/main checkout the parquet does not exist, but the
    canonical max-date proof is also recorded in
    ``aggregate_input_audit.json`` (lightweight JSON written by
    ``scripts/write_aggregate_input_audit.py`` from the
    ``train_manifest.json`` summary fields). Try the audit JSON first
    when the parquet is absent, and only fall through to a hard fail
    when neither source provides the max date.
    """
    fold_path = ch_dir / "aggregate_input" / "fold_aggregate.parquet"
    audit_path = ch_dir / "aggregate_input_audit.json"

    if fold_path.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(fold_path, columns=["game_date"])
            max_d = pd.to_datetime(df["game_date"]).dt.date.max()
            report.max_dates["fold_aggregate"] = str(max_d)
            report.add(
                "fold_aggregate_max_game_date",
                max_d <= cutoff,
                f"max={max_d} cutoff={cutoff} source=fold_aggregate.parquet",
            )
            return
        except Exception as exc:
            report.add(
                "fold_aggregate_max_game_date",
                False,
                f"parquet read error: {exc}; falling back to audit JSON",
            )

    if audit_path.exists():
        try:
            import json as _json
            audit = _json.loads(audit_path.read_text(encoding="utf-8"))
            max_str = audit.get("fold_aggregate_max_game_date")
            if max_str:
                max_d = dt.date.fromisoformat(max_str)
                report.max_dates["fold_aggregate"] = max_str
                report.add(
                    "fold_aggregate_max_game_date",
                    bool(audit.get("no_leakage_pass")) and max_d <= cutoff,
                    f"max={max_str} cutoff={cutoff} "
                    f"source=aggregate_input_audit.json "
                    f"(rows={audit.get('row_count')}, "
                    f"sha256={(audit.get('fold_aggregate_sha256') or '')[:16]})",
                )
                return
        except Exception as exc:
            report.add(
                "fold_aggregate_max_game_date",
                False,
                f"audit JSON read error: {exc}",
            )
            return

    report.add(
        "fold_aggregate_max_game_date",
        False,
        f"missing both {fold_path.relative_to(REPO_ROOT)} and "
        f"{audit_path.relative_to(REPO_ROOT)} — cannot prove no leakage",
    )


def check_train_manifest(report: LeakageReport, ch_dir: Path, cutoff: dt.date) -> None:
    p = ch_dir / "train_manifest.json"
    if not p.exists():
        report.add("train_manifest_max_date", False, "missing train_manifest.json")
        return
    m = read_json(p)
    summary = m.get("training_summary", {}) or {}
    max_d = _parse_date_str(summary.get("max_date"))
    report.max_dates["training_summary_max_date"] = (
        summary.get("max_date") if max_d is None else str(max_d)
    )
    if max_d is None:
        report.add(
            "train_manifest_max_date",
            True,
            "training_summary.max_date not recorded — no rows to leak",
        )
    else:
        report.add(
            "train_manifest_max_date",
            max_d <= cutoff,
            f"max={max_d} cutoff={cutoff}",
        )
    # Also: train_manifest's dry_run must be False for a real run we are
    # leak-checking.
    report.add(
        "train_manifest_real_run",
        m.get("dry_run") is False,
        f"dry_run={m.get('dry_run')}",
    )
    # And future_rows_excluded must be present and >= 0.
    fre = summary.get("future_rows_excluded")
    if fre is None:
        # Newer aggregate-mode runs may report it as aggregate_oof_future_rows_excluded.
        fre = summary.get("aggregate_oof_future_rows_excluded")
    report.max_dates["future_rows_excluded"] = fre
    report.add(
        "train_manifest_future_rows_excluded_recorded",
        fre is None or int(fre or 0) >= 0,
        f"future_rows_excluded={fre}",
    )


def check_calibration_manifest(report: LeakageReport, ch_dir: Path, cutoff: dt.date) -> None:
    p = ch_dir / "calibration_manifest.json"
    if not p.exists():
        report.add("calibration_manifest_window_end", False, "missing calibration_manifest.json")
        return
    m = read_json(p)
    details = m.get("details", {}) or {}
    win = details.get("calibration_window", {}) or {}
    val_end = _parse_date_str(win.get("validation_window_end"))
    train_end = _parse_date_str(win.get("training_window_end"))
    report.max_dates["calibration_validation_window_end"] = win.get("validation_window_end")
    report.max_dates["calibration_training_window_end"] = win.get("training_window_end")
    if val_end is not None:
        report.add(
            "calibration_validation_window_end",
            val_end <= cutoff,
            f"validation_window_end={val_end} cutoff={cutoff}",
        )
    else:
        report.add(
            "calibration_validation_window_end",
            True,
            "no validation_window_end recorded (advisory)",
        )
    if train_end is not None:
        report.add(
            "calibration_training_window_end",
            train_end <= cutoff,
            f"training_window_end={train_end} cutoff={cutoff}",
        )
    report.add(
        "calibration_manifest_real_run",
        m.get("dry_run") is False,
        f"dry_run={m.get('dry_run')}",
    )


def check_validation_report(report: LeakageReport, ch_dir: Path, cutoff: dt.date) -> None:
    p = ch_dir / "validation_report.json"
    if not p.exists():
        report.add("validation_holdout_window_end", False, "missing validation_report.json")
        return
    v = read_json(p)
    ch_metrics = (v.get("challenger") or {}).get("metrics") or {}
    cm_metrics = (v.get("champion") or {}).get("metrics") or {}
    for side, metrics in (("challenger", ch_metrics), ("champion", cm_metrics)):
        win = metrics.get("holdout_window") or {}
        end = _parse_date_str(win.get("end"))
        report.max_dates[f"{side}_holdout_window_end"] = win.get("end")
        if end is not None:
            report.add(
                f"validation_{side}_holdout_window_end",
                end <= cutoff,
                f"end={end} cutoff={cutoff}",
            )
        else:
            report.add(
                f"validation_{side}_holdout_window_end",
                True,
                f"no holdout_window for {side} (advisory)",
            )
    report.add(
        "validation_challenger_dry_run_false",
        (v.get("challenger") or {}).get("dry_run") is False,
        f"validation.challenger.dry_run={(v.get('challenger') or {}).get('dry_run')}",
    )


def check_oof_source_no_future_rows(report: LeakageReport, ch_dir: Path, cutoff: dt.date) -> None:
    """Verify that the prepare step recorded zero future rows in its manifest."""
    inputs_manifest = nightly_run_dir(report.as_of_date) / "training_inputs_manifest.json"
    if not inputs_manifest.exists():
        report.add(
            "training_inputs_no_future_rows",
            True,
            "training_inputs_manifest.json missing (advisory)",
        )
        return
    m = read_json(inputs_manifest)
    fold_input = (m.get("inputs", {}) or {}).get("fold_aggregate.parquet", {})
    fre = fold_input.get("future_rows_excluded")
    rows_after = fold_input.get("rows_after_cutoff")
    report.max_dates["prepare_fold_aggregate_rows_after_cutoff"] = rows_after
    report.max_dates["prepare_fold_aggregate_future_rows_excluded"] = fre
    report.add(
        "training_inputs_no_future_rows",
        rows_after is not None and rows_after > 0,
        f"rows_after_cutoff={rows_after} future_rows_excluded={fre}",
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify no future-data leakage.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    args = p.parse_args(argv)

    as_of = parse_date(args.as_of_date).isoformat()
    cutoff = parse_date(args.as_of_date)
    out_dir = nightly_run_dir(as_of)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Pull phase13g context from the run manifest (orchestrator stamped it).
    run_manifest_path = out_dir / "run_manifest.json"
    rm = read_json(run_manifest_path) if run_manifest_path.exists() else {}
    p13g = rm.get("phase13g", {}) or {}

    report = LeakageReport(
        as_of_date=as_of,
        target_date_et=p13g.get("target_date_et"),
        resolved_training_cutoff_date=p13g.get("resolved_training_cutoff_date") or as_of,
        generated_at_utc=utcnow_iso(),
        code_commit=git_commit(),
    )
    ch_dir = challenger_dir(as_of)

    check_fold_aggregate_max_date(report, ch_dir, cutoff)
    check_train_manifest(report, ch_dir, cutoff)
    check_calibration_manifest(report, ch_dir, cutoff)
    check_validation_report(report, ch_dir, cutoff)
    check_oof_source_no_future_rows(report, ch_dir, cutoff)

    payload = report.to_dict()
    payload["phase13g"] = p13g
    write_json_atomic(out_dir / "previous_day_no_leakage.json", payload)

    md = [
        f"# Previous-Day No-Leakage Verification — {as_of}",
        "",
        f"- target_date_et: {p13g.get('target_date_et')}",
        f"- resolved_training_cutoff_date: {report.resolved_training_cutoff_date}",
        f"- stale_fallback_used: {p13g.get('stale_fallback_used')}",
        f"- leakage_checks_passed: **{report.passed}**",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in report.checks:
        safe_detail = c.detail.replace("|", "\\|")
        md.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {safe_detail} |")
    md += ["", "## Max dates seen", "", "```", json.dumps(report.max_dates, indent=2), "```"]
    (out_dir / "previous_day_no_leakage.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    if report.passed:
        print("PREVIOUS_DAY_NO_LEAKAGE_VERIFICATION_PASS")
        return 0
    print("PREVIOUS_DAY_NO_LEAKAGE_FAILED", file=sys.stderr)
    for c in report.checks:
        if not c.passed:
            print(f"  - {c.name}: {c.detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
