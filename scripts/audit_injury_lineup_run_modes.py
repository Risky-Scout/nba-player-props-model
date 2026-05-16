#!/usr/bin/env python3
"""Run-mode-aware injury/lineup audit with explicit blockers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.injury_lineup_features import build_injury_lineup_features
from nba_props_model.features.player_prop_feature_contract import RunMode


def demote_injury_lineup_failures_for_woo_morning(failures: list[dict]) -> bool:
    """WoO morning monetization audits only ``morning_expected`` for the slate date.

    Downgrade hard failures for other run modes to warnings so unrelated missing
    t25/t5/final_after_game rows do not block morning delivery.

    Returns True when any finding was demoted (caller may emit a log marker).
    """
    demoted = False
    for f in failures:
        if f.get("run_mode") == RunMode.MORNING_EXPECTED.value:
            continue
        if f.get("severity") != "fail":
            continue
        prev_code = str(f.get("blocker_code") or "")
        f["severity"] = "warn"
        f["blocker_code"] = "INJURY_LINEUP_RUN_MODE_NONCURRENT_WARN"
        f["detail"] = (
            "[scoped under woo_morning_monetization — non-current run mode] "
            f"(was {prev_code}) {f.get('detail', '')}"
        )
        demoted = True
    return demoted


def _make_row(
    *,
    run_mode: str,
    audit_date: str,
    severity: str,
    blocker_code: str,
    detail: str,
    n_rows: int | None = None,
) -> dict:
    return {
        "run_mode": run_mode,
        "audit_date": audit_date,
        "severity": severity,
        "blocker_code": blocker_code,
        "detail": detail,
        "n_rows": n_rows,
    }


def _audit_mode(
    *,
    run_mode: RunMode,
    date: str,
) -> tuple[pd.DataFrame | None, dict | None, list[dict]]:
    failures: list[dict] = []
    try:
        result = build_injury_lineup_features(REPO_ROOT, date, run_mode)
    except Exception as exc:
        failures.append(
            _make_row(
                run_mode=run_mode.value,
                audit_date=date,
                severity="fail",
                blocker_code="INJURY_LINEUP_FEATURE_BUILD_FAILED",
                detail=f"{type(exc).__name__}: {exc}",
            )
        )
        return None, None, failures

    frame = result.frame.copy()
    summary = dict(result.summary)
    n_rows = int(len(frame))

    # same-day source missing must be explicit and fatal
    if n_rows == 0:
        failures.append(
            _make_row(
                run_mode=run_mode.value,
                audit_date=date,
                severity="fail",
                blocker_code="SAME_DAY_SOURCE_INPUTS_MISSING",
                detail=(
                    "No injury/lineup feature rows were produced; canonical or source "
                    "inputs are missing for this run mode/date."
                ),
                n_rows=n_rows,
            )
        )
        return frame, summary, failures

    if run_mode == RunMode.MORNING_EXPECTED:
        if "official_lineup_available" in frame.columns and bool(frame["official_lineup_available"].fillna(False).any()):
            failures.append(
                _make_row(
                    run_mode=run_mode.value,
                    audit_date=date,
                    severity="warn",
                    blocker_code="MORNING_HAS_OFFICIAL_LINEUP_AVAILABLE",
                    detail="morning_expected should not require official lineups; availability should remain optional.",
                    n_rows=n_rows,
                )
            )
        if "unavailable_reason" in frame.columns and "availability_status" in frame.columns:
            missing_explicit = frame["availability_status"].isna() & (
                frame["unavailable_reason"].astype(str).str.strip() == ""
            )
            if bool(missing_explicit.any()):
                failures.append(
                    _make_row(
                        run_mode=run_mode.value,
                        audit_date=date,
                        severity="fail",
                        blocker_code="SOURCE_AVAILABILITY_NOT_EXPLICIT",
                        detail="Rows with missing availability_status must carry explicit unavailable_reason.",
                        n_rows=int(missing_explicit.sum()),
                    )
                )

    if run_mode in {RunMode.T25, RunMode.T5}:
        if "official_lineup_available" in frame.columns and "unavailable_reason" in frame.columns:
            missing_official = ~frame["official_lineup_available"].fillna(False)
            missing_named_blocker = missing_official & ~frame["unavailable_reason"].astype(str).str.contains(
                "official_lineup_not_available_yet",
                case=False,
                na=False,
            )
            if bool(missing_named_blocker.any()):
                failures.append(
                    _make_row(
                        run_mode=run_mode.value,
                        audit_date=date,
                        severity="fail",
                        blocker_code="OFFICIAL_LINEUP_REQUIRED_BLOCKER_MISSING",
                        detail=(
                            "t25/t5 rows without official lineup availability must carry "
                            "official_lineup_not_available_yet in unavailable_reason."
                        ),
                        n_rows=int(missing_named_blocker.sum()),
                    )
                )

    if run_mode == RunMode.FINAL_AFTER_GAME:
        if "actual" in frame.columns:
            failures.append(
                _make_row(
                    run_mode=run_mode.value,
                    audit_date=date,
                    severity="warn",
                    blocker_code="POSTGAME_FIELD_PRESENT",
                    detail="final_after_game may include postgame fields; ensure they are excluded from pregame training features.",
                    n_rows=n_rows,
                )
            )

    return frame, summary, failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--latest-completed-date", required=True)
    ap.add_argument(
        "--delivery-pipeline-mode",
        default=None,
        help="When woo_morning_monetization, only morning_expected gates exit status.",
    )
    ap.add_argument(
        "--active-run-mode",
        choices=[m.value for m in RunMode],
        default=None,
        help=(
            "Legacy compat alias retained for orchestrator callers; "
            "demotion is driven by --delivery-pipeline-mode."
        ),
    )
    args = ap.parse_args()

    out = REPO_ROOT / "artifacts" / "model_diagnostics" / "injury_lineup_run_modes"
    out.mkdir(parents=True, exist_ok=True)
    debug_out = REPO_ROOT / "artifacts" / "model_diagnostics" / "injury_lineup_run_mode_debug"
    debug_out.mkdir(parents=True, exist_ok=True)

    failures: list[dict] = []
    summaries: list[dict] = []
    run_plan = [
        (RunMode.MORNING_EXPECTED, args.date),
        (RunMode.T25, args.latest_completed_date),
        (RunMode.T5, args.latest_completed_date),
        (RunMode.FINAL_AFTER_GAME, args.latest_completed_date),
    ]

    for mode, mode_date in run_plan:
        _, summary, mode_failures = _audit_mode(run_mode=mode, date=mode_date)
        failures.extend(mode_failures)
        summaries.append(
            {
                "run_mode": mode.value,
                "audit_date": mode_date,
                "n_rows": int((summary or {}).get("n_rows", 0)),
                "official_lineup_available_any": bool((summary or {}).get("official_lineup_available_any", False)),
                "stale_injury_rows": int((summary or {}).get("stale_injury_rows", 0)),
                "stale_lineup_rows": int((summary or {}).get("stale_lineup_rows", 0)),
            }
        )

    if args.delivery_pipeline_mode == "woo_morning_monetization":
        if demote_injury_lineup_failures_for_woo_morning(failures):
            print("INJURY_LINEUP_RUN_MODE_NONCURRENT_WARN")

    failures_df = pd.DataFrame(
        failures,
        columns=["run_mode", "audit_date", "severity", "blocker_code", "detail", "n_rows"],
    )
    summaries_df = pd.DataFrame(
        summaries,
        columns=[
            "run_mode",
            "audit_date",
            "n_rows",
            "official_lineup_available_any",
            "stale_injury_rows",
            "stale_lineup_rows",
        ],
    )
    failures_df.to_csv(debug_out / "latest_run_mode_failures.csv", index=False)
    summaries_df.to_csv(out / "source_inventory.csv", index=False)

    run_mode_contract = pd.DataFrame(
        [
            {"run_mode": "morning_expected", "official_lineup_required": False, "named_blocker_required_if_missing": False},
            {"run_mode": "t25", "official_lineup_required": True, "named_blocker_required_if_missing": True},
            {"run_mode": "t5", "official_lineup_required": True, "named_blocker_required_if_missing": True},
            {"run_mode": "final_after_game", "official_lineup_required": False, "named_blocker_required_if_missing": False},
        ]
    )
    run_mode_contract.to_csv(out / "run_mode_contract.csv", index=False)
    pd.DataFrame(columns=["check", "detail"]).to_csv(out / "stale_availability_risks.csv", index=False)

    fail_count = int((failures_df["severity"] == "fail").sum()) if not failures_df.empty else 0
    pass_all = fail_count == 0
    summary_payload = {
        "date": args.date,
        "latest_completed_date": args.latest_completed_date,
        "run_mode_rows": summaries,
        "failure_count": int(len(failures_df)),
        "hard_failure_count": fail_count,
        "pass_all": pass_all,
    }
    (out / "summary.json").write_text(json.dumps(summary_payload, indent=2) + "\n", encoding="utf-8")

    summary_lines = [
        f"# Injury / lineup run-mode audit ({args.date})",
        "",
        f"- pass_all: `{pass_all}`",
        f"- hard_failure_count: `{fail_count}`",
        f"- total_findings: `{int(len(failures_df))}`",
        "",
        "## Run modes",
    ]
    for row in summaries:
        summary_lines.append(
            f"- {row['run_mode']} ({row['audit_date']}): n_rows={row['n_rows']}, "
            f"official_lineup_available_any={row['official_lineup_available_any']}, "
            f"stale_injury_rows={row['stale_injury_rows']}, stale_lineup_rows={row['stale_lineup_rows']}"
        )
    if not failures_df.empty:
        summary_lines.extend(["", "## Findings"])
        for row in failures_df.itertuples(index=False):
            summary_lines.append(
                f"- [{row.severity}] {row.run_mode} {row.blocker_code}: {row.detail}"
            )
    (out / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    (debug_out / "latest_run_mode_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    if pass_all:
        print("INJURY_LINEUP_RUN_MODE_AUDIT_PASS")
    else:
        print("INJURY_LINEUP_RUN_MODE_AUDIT_FAIL")
    return 0 if pass_all else 2


if __name__ == "__main__":
    raise SystemExit(main())
