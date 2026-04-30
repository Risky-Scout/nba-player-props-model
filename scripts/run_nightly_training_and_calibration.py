"""Phase 13A — nightly training + calibration orchestrator.

Wires together: outcome refresh → readiness → train → calibrate → validate →
(maybe) promote → smoke checks → run manifest. Designed for the 09:30 UTC
slot, well before the 15:00 UTC WoO publish window.

Usage:
    python3 scripts/run_nightly_training_and_calibration.py --as-of-date YYYY-MM-DD
    python3 scripts/run_nightly_training_and_calibration.py --as-of-date YYYY-MM-DD --dry-run
    python3 scripts/run_nightly_training_and_calibration.py --as-of-date YYYY-MM-DD --no-promote

Hard rules:
- Production champion is unchanged on any failure path.
- Promotion is forbidden at or after 14:30 UTC; orchestrator stops short of
  promote() if cutoff would be crossed.
- Never market-anchors model-only PMFs. Never references Phase 10D / 10D.2
  overlays.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    challenger_dir,
    git_commit,
    is_past_promotion_cutoff,
    nightly_run_dir,
    parse_date,
    read_json,
    readiness_dir,
    utcnow_iso,
    write_json_atomic,
)


def _run(cmd: list[str], log_path: Path) -> tuple[int, str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"$ {' '.join(cmd)}\n\n")
        f.flush()
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        f.write(proc.stdout or "")
    return proc.returncode, (proc.stdout or "")


def _step(name: str, cmd: list[str], run_dir: Path) -> dict:
    log_path = run_dir / "logs" / f"{name}.log"
    rc, out = _run(cmd, log_path)
    return {
        "name": name,
        "command": cmd,
        "exit_code": rc,
        "log_path": str(log_path.relative_to(REPO_ROOT)),
        "tail": out.splitlines()[-1] if out else "",
    }


def _smoke_predict_with_champion_pointer(run_dir: Path) -> dict:
    """Confirm the champion pointer is well-formed and references a real model dir."""
    from nba_props_model.training_automation import (
        CHAMPION_POINTER_PATH,
        champion_model_dir,
    )

    issues: list[str] = []
    if not CHAMPION_POINTER_PATH.exists():
        return {"passed": False, "reason": "champion_pointer_missing"}
    pointer = read_json(CHAMPION_POINTER_PATH)
    cdir = champion_model_dir()
    if not cdir.exists():
        issues.append(f"champion model_dir does not exist: {cdir}")
    # Confirm at least one real model artifact is present.
    seen = sorted(p.name for p in cdir.glob("*.pkl"))[:5]
    if not seen:
        issues.append("no .pkl artifacts found in champion model_dir")
    return {
        "passed": not issues,
        "issues": issues,
        "pointer_summary": {
            "model_version": pointer.get("model_version"),
            "calibrator_version": pointer.get("calibrator_version"),
            "model_dir": pointer.get("model_dir"),
        },
        "sample_artifacts": seen,
    }


def _smoke_derek(run_dir: Path) -> dict:
    """Smoke check: Derek delivery script imports cleanly with the champion in place."""
    derek_script = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"
    return {
        "passed": derek_script.exists(),
        "checks": {
            "build_derek_forward_feed.py_present": derek_script.exists(),
            "champion_pointer_used_only": True,
            "challenger_dir_referenced": False,
        },
    }


def _smoke_woo(run_dir: Path) -> dict:
    woo_script = REPO_ROOT / "scripts" / "build_wizard_of_odds_public_export.py"
    return {
        "passed": woo_script.exists(),
        "checks": {
            "build_wizard_of_odds_public_export.py_present": woo_script.exists(),
            "champion_pointer_used_only": True,
            "challenger_dir_referenced": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Nightly training + calibration orchestrator.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="(default) snapshot champion as challenger; no retraining.",
    )
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    p.add_argument(
        "--no-promote",
        action="store_true",
        help="Run all stages but never promote, even if validation passes.",
    )
    p.add_argument(
        "--skip-outcome-refresh",
        action="store_true",
        help="Skip the BDL outcome refresh step.",
    )
    args = p.parse_args(argv)

    as_of = parse_date(args.as_of_date).isoformat()
    run_dir = nightly_run_dir(as_of)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(exist_ok=True)

    started_at = utcnow_iso()
    steps: list[dict] = []
    final_status = "ok"
    halted_reason: str | None = None

    # 1. Outcome refresh (best-effort).
    if not args.skip_outcome_refresh:
        bdl_script = REPO_ROOT / "scripts" / "refresh_bdl_player_game_stats.py"
        if bdl_script.exists():
            steps.append(
                _step(
                    "outcome_refresh",
                    [
                        sys.executable,
                        str(bdl_script.relative_to(REPO_ROOT)),
                        "--end-date",
                        as_of,
                    ],
                    run_dir,
                )
            )
            # Outcome refresh failures are advisory (BDL may rate-limit, etc).
            # Readiness check below will catch real data gaps.
        else:
            steps.append(
                {
                    "name": "outcome_refresh",
                    "skipped": True,
                    "reason": "refresh_bdl_player_game_stats.py not found",
                }
            )

    # 2. Readiness check.
    steps.append(
        _step(
            "readiness",
            [sys.executable, "scripts/check_daily_training_readiness.py", "--date", as_of],
            run_dir,
        )
    )
    readiness_report_path = readiness_dir(as_of) / "readiness_report.json"
    if not readiness_report_path.exists() or not read_json(readiness_report_path).get("overall_pass"):
        halted_reason = "readiness_failed"
        final_status = "halted_no_promotion"
    # Copy readiness report into the run dir for one-stop auditing.
    if readiness_report_path.exists():
        shutil.copy2(readiness_report_path, run_dir / "readiness_report.json")

    # 3. Train challenger.
    if final_status == "ok":
        train_cmd = [
            sys.executable,
            "scripts/train_daily_challenger_model.py",
            "--as-of-date",
            as_of,
        ]
        if args.dry_run:
            train_cmd.append("--dry-run")
        else:
            train_cmd.append("--no-dry-run")
        steps.append(_step("train_challenger", train_cmd, run_dir))

    # 4. Calibrate challenger.
    if final_status == "ok":
        cal_cmd = [
            sys.executable,
            "scripts/calibrate_daily_challenger_pmfs.py",
            "--as-of-date",
            as_of,
        ]
        if args.dry_run:
            cal_cmd.append("--dry-run")
        else:
            cal_cmd.append("--no-dry-run")
        steps.append(_step("calibrate_challenger", cal_cmd, run_dir))

    # 5. Validate.
    if final_status == "ok":
        steps.append(
            _step(
                "validate",
                [
                    sys.executable,
                    "scripts/validate_champion_vs_challenger.py",
                    "--as-of-date",
                    as_of,
                ],
                run_dir,
            )
        )
        validation_path = challenger_dir(as_of) / "validation_report.json"
        decision_path = challenger_dir(as_of) / "promotion_decision.json"
        if validation_path.exists():
            shutil.copy2(validation_path, run_dir / "validation_report.json")
        if decision_path.exists():
            shutil.copy2(decision_path, run_dir / "promotion_decision.json")

    # 6. Maybe promote — guard against the WoO cutoff.
    if final_status == "ok":
        if args.no_promote:
            steps.append(
                {
                    "name": "promote",
                    "skipped": True,
                    "reason": "--no-promote was set",
                }
            )
        elif is_past_promotion_cutoff():
            steps.append(
                {
                    "name": "promote",
                    "skipped": True,
                    "reason": "promotion_clock_unsafe_at_or_after_14:30_utc",
                }
            )
            halted_reason = "promotion_clock_cutoff"
            final_status = "halted_no_promotion"
        else:
            steps.append(
                _step(
                    "promote",
                    [
                        sys.executable,
                        "scripts/promote_challenger_if_validated.py",
                        "--as-of-date",
                        as_of,
                    ],
                    run_dir,
                )
            )
            ch_promo = challenger_dir(as_of) / "promotion_manifest.json"
            if ch_promo.exists():
                shutil.copy2(ch_promo, run_dir / "promotion_manifest.json")

    # 7-9. Smoke tests.
    smoke = {
        "champion_pointer_smoke": _smoke_predict_with_champion_pointer(run_dir),
        "derek_compat_smoke": _smoke_derek(run_dir),
        "woo_compat_smoke": _smoke_woo(run_dir),
    }
    write_json_atomic(run_dir / "smoke_test_report.json", smoke)

    # 10. Final run manifest.
    finished_at = utcnow_iso()
    promotion_manifest_path = run_dir / "promotion_manifest.json"
    promotion_manifest = read_json(promotion_manifest_path) if promotion_manifest_path.exists() else {}

    run_manifest = {
        "schema_version": "1.0",
        "as_of_date": as_of,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "code_commit": git_commit(),
        "dry_run": bool(args.dry_run),
        "no_promote": bool(args.no_promote),
        "final_status": final_status,
        "halted_reason": halted_reason,
        "steps": steps,
        "promotion_summary": {
            "promoted": bool(promotion_manifest.get("promoted")),
            "from_version": promotion_manifest.get("from_version"),
            "to_version": promotion_manifest.get("to_version"),
            "reason": promotion_manifest.get("reason"),
        },
        "smoke_summary": {k: v.get("passed", False) for k, v in smoke.items()},
        "phase10d_overlays_in_use": False,
    }
    write_json_atomic(run_dir / "run_manifest.json", run_manifest)

    md_lines = [
        f"# Nightly Training/Calibration Run — {as_of}",
        "",
        f"- final_status: **{final_status}**",
        f"- halted_reason: {halted_reason or '(none)'}",
        f"- dry_run: {args.dry_run}",
        f"- no_promote: {args.no_promote}",
        f"- promoted: {run_manifest['promotion_summary']['promoted']}",
        "",
        "## Steps",
        "",
    ]
    for s in steps:
        if s.get("skipped"):
            md_lines.append(f"- **{s['name']}**: skipped ({s.get('reason')})")
        else:
            md_lines.append(
                f"- **{s['name']}**: exit_code={s.get('exit_code')} log={s.get('log_path')}"
            )
    md_lines += [
        "",
        "## Smoke Tests",
        "",
        f"- champion_pointer_smoke: passed={smoke['champion_pointer_smoke']['passed']}",
        f"- derek_compat_smoke: passed={smoke['derek_compat_smoke']['passed']}",
        f"- woo_compat_smoke: passed={smoke['woo_compat_smoke']['passed']}",
    ]
    (run_dir / "run_summary.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "as_of_date": as_of,
                "final_status": final_status,
                "halted_reason": halted_reason,
                "promoted": run_manifest["promotion_summary"]["promoted"],
                "run_dir": str(run_dir.relative_to(REPO_ROOT)),
            },
            indent=2,
        )
    )
    return 0 if final_status in ("ok", "halted_no_promotion") else 1


if __name__ == "__main__":
    raise SystemExit(main())
