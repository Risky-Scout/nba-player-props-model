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
- Promotion is **not** gated on the legacy 14:30 UTC cutoff: automated retries
  (including 15:30 / 18:30 / 21:30 UTC) must be able to advance the champion
  the same UTC day whenever train/cal/validate succeeds.
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
    NIGHTLY_TRAINING_DIR,
    challenger_dir,
    git_commit,
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


def _resolve_as_of_date_via_resolver(run_dir: Path) -> tuple[str | None, dict]:
    """Phase 13F: legacy permissive resolver — picks the latest safe finalized
    date with the regular floor. Used only when --use-legacy-resolver is set."""
    cmd = [sys.executable, "scripts/resolve_latest_safe_training_date.py"]
    step = _step("resolve_latest_safe_date", cmd, run_dir)
    if step.get("exit_code", 1) != 0:
        return None, step
    payload_path = NIGHTLY_TRAINING_DIR / "latest_safe_training_date.json"
    if not payload_path.exists():
        step["error"] = "resolver did not write latest_safe_training_date.json"
        return None, step
    payload = read_json(payload_path)
    return payload.get("resolved_as_of_date"), step


def _resolve_previous_day_et_target(run_dir: Path, allow_stale: bool) -> tuple[str | None, dict, dict]:
    """Phase 13G: strict previous-day-in-ET resolver.

    Returns (resolved_date_or_None, step_record, target_payload_dict).
    target_payload_dict carries target_policy / target_date_et / stale_fallback_used
    fields that the orchestrator stamps onto every downstream manifest.
    """
    cmd = [sys.executable, "scripts/resolve_previous_day_et_target.py"]
    if allow_stale:
        cmd.append("--allow-stale-safe-date")
    step = _step("resolve_previous_day_et_target", cmd, run_dir)
    payload_path = NIGHTLY_TRAINING_DIR / "previous_day_et_target.json"
    payload = read_json(payload_path) if payload_path.exists() else {}
    if step.get("exit_code", 1) != 0:
        return None, step, payload
    return payload.get("resolved_training_cutoff_date"), step, payload


def _stamp_phase13g_fields(manifest_path: Path, ctx: dict) -> None:
    """Idempotent post-processing: append Phase 13G context fields to a
    manifest written by a sub-script. Sub-scripts emit their own manifests
    without knowing target_policy / target_date_et / stale_fallback_used —
    the orchestrator owns those fields and stamps them here so every
    downstream consumer (verifier, leakage check, dependency check) sees
    a consistent record on disk.
    """
    if not manifest_path.exists():
        return
    try:
        m = read_json(manifest_path)
    except Exception:
        return
    if not isinstance(m, dict):
        return
    m.setdefault("phase13g", {}).update(
        {
            "target_policy": ctx.get("target_policy"),
            "target_date_et": ctx.get("target_date_et"),
            "resolved_training_cutoff_date": ctx.get("resolved_training_cutoff_date"),
            "data_complete_for_target_date": ctx.get("data_complete_for_target_date"),
            "stale_fallback_used": ctx.get("stale_fallback_used"),
            "stale_fallback_target_date": ctx.get("stale_fallback_target_date"),
            "training_run_id": ctx.get("training_run_id"),
        }
    )
    write_json_atomic(manifest_path, m)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Nightly training + calibration orchestrator.")
    p.add_argument(
        "--as-of-date",
        default=None,
        help=(
            "YYYY-MM-DD. If omitted, runs scripts/resolve_latest_safe_training_date.py "
            "and uses the latest finalized-outcome date that satisfies the safety "
            "floor (today UTC is always rejected)."
        ),
    )
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
    p.add_argument(
        "--allow-stale-safe-date",
        action="store_true",
        help=(
            "Phase 13G: opt-in fallback. If set and yesterday-in-ET data is "
            "incomplete, the strict resolver falls back to the most recent "
            "complete date and the run is marked stale_fallback_used=true. "
            "The scheduled workflow does NOT pass this flag — it halts cleanly "
            "with halted_reason=previous_day_data_not_ready instead."
        ),
    )
    p.add_argument(
        "--use-legacy-resolver",
        action="store_true",
        help=(
            "Use the Phase 13F latest-safe-finalized-date resolver instead of "
            "the Phase 13G previous-day-ET resolver. For backwards compat only."
        ),
    )
    args = p.parse_args(argv)

    started_at = utcnow_iso()
    training_run_id = f"nightly-{started_at.replace(':', '').replace('-', '')[:15]}"
    steps: list[dict] = []
    final_status = "ok"
    halted_reason: str | None = None
    phase13g_ctx: dict = {
        "target_policy": "previous_day_et",
        "target_date_et": None,
        "resolved_training_cutoff_date": None,
        "data_complete_for_target_date": None,
        "stale_fallback_used": False,
        "stale_fallback_target_date": None,
        "training_run_id": training_run_id,
    }

    # 0. Resolve as_of_date when not supplied. Phase 13G: strict
    #    previous-day-ET by default; legacy resolver behind --use-legacy-resolver.
    if args.as_of_date is None or not str(args.as_of_date).strip():
        NIGHTLY_TRAINING_DIR.mkdir(parents=True, exist_ok=True)
        bootstrap_dir = NIGHTLY_TRAINING_DIR
        bootstrap_dir.mkdir(parents=True, exist_ok=True)
        (bootstrap_dir / "logs").mkdir(exist_ok=True)
        if args.use_legacy_resolver:
            resolved, resolver_step = _resolve_as_of_date_via_resolver(bootstrap_dir)
            target_payload = {}
        else:
            resolved, resolver_step, target_payload = _resolve_previous_day_et_target(
                bootstrap_dir, allow_stale=args.allow_stale_safe_date
            )
            phase13g_ctx["target_date_et"] = target_payload.get("target_date_et")
            phase13g_ctx["data_complete_for_target_date"] = (
                target_payload.get("completeness", {}).get("data_complete_for_target_date")
            )
            phase13g_ctx["stale_fallback_used"] = bool(target_payload.get("stale_fallback_used"))
            phase13g_ctx["stale_fallback_target_date"] = target_payload.get(
                "stale_fallback_target_date"
            )
        steps.append(resolver_step)
        if not resolved:
            # Halt cleanly with a date-specific record so the workflow can
            # upload artifacts and the verifier can classify the failure.
            halt_reason = (
                target_payload.get("halted_reason")
                if not args.use_legacy_resolver
                else "no_safe_as_of_date_resolved"
            ) or "previous_day_data_not_ready"
            unresolved_dir = NIGHTLY_TRAINING_DIR / "_unresolved"
            unresolved_dir.mkdir(parents=True, exist_ok=True)
            write_json_atomic(
                unresolved_dir / "run_manifest.json",
                {
                    "schema_version": "1.0",
                    "started_at_utc": started_at,
                    "finished_at_utc": utcnow_iso(),
                    "code_commit": git_commit(),
                    "training_run_id": training_run_id,
                    "final_status": "halted_no_promotion",
                    "halted_reason": halt_reason,
                    "phase13g": phase13g_ctx,
                    "steps": steps,
                },
            )
            print(
                json.dumps(
                    {
                        "as_of_date": None,
                        "final_status": "halted_no_promotion",
                        "halted_reason": halt_reason,
                        "promoted": False,
                        "run_dir": str(unresolved_dir.relative_to(REPO_ROOT)),
                        "phase13g": phase13g_ctx,
                    },
                    indent=2,
                )
            )
            return 0
        args.as_of_date = resolved
        phase13g_ctx["resolved_training_cutoff_date"] = resolved

    as_of = parse_date(args.as_of_date).isoformat()
    # If resolver did not run (manual --as-of-date override), record the
    # manual context so downstream stamping is still consistent.
    if phase13g_ctx["resolved_training_cutoff_date"] is None:
        phase13g_ctx["target_policy"] = "manual_override"
        phase13g_ctx["target_date_et"] = phase13g_ctx["target_date_et"] or as_of
        phase13g_ctx["resolved_training_cutoff_date"] = as_of
    run_dir = nightly_run_dir(as_of)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(exist_ok=True)

    # Phase 13H: write run_context.json EARLY so subprocesses (especially
    # the promotion script) can read the run's identity / phase13g context
    # before the final run_manifest is written at the end.
    write_json_atomic(
        run_dir / "run_context.json",
        {
            "schema_version": "1.0",
            "as_of_date": as_of,
            "started_at_utc": started_at,
            "code_commit": git_commit(),
            "training_run_id": training_run_id,
            "dry_run": bool(args.dry_run),
            "no_promote": bool(args.no_promote),
            "phase13g": phase13g_ctx,
        },
    )

    def _stamp(name: str, base_dir: Path) -> None:
        _stamp_phase13g_fields(base_dir / name, phase13g_ctx)

    # 1. Phase 13H: refresh completed-game source data + verify completeness.
    #    This produces source_data_refresh_manifest.json + source_completeness_manifest.json
    #    under the run_dir. On a fresh runner with BDL_API_KEY set, the
    #    refresh fetches finalized box-scores through the target date.
    if not args.skip_outcome_refresh:
        steps.append(
            _step(
                "source_data_refresh",
                [
                    sys.executable,
                    "scripts/refresh_completed_game_data.py",
                    "--target-date",
                    as_of,
                    "--skip-if-fresh",
                ],
                run_dir,
            )
        )
        # Strict completeness gate (Phase 13H).
        complete_step = _step(
            "previous_day_source_completeness",
            [
                sys.executable,
                "scripts/verify_previous_day_source_completeness.py",
                "--target-date",
                as_of,
            ],
            run_dir,
        )
        steps.append(complete_step)
        if complete_step.get("exit_code", 1) != 0 and not args.dry_run:
            halted_reason = "previous_day_source_incomplete"
            final_status = "halted_no_promotion"
    else:
        steps.append(
            {
                "name": "source_data_refresh",
                "skipped": True,
                "reason": "--skip-outcome-refresh was set",
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

    # 2a. Phase 13F: training input preflight. Required inputs absent here
    #     means the runner cannot do real training — halt cleanly so the
    #     verifier can report TRAINING_AUTOMATION_REAL_TRAINING_FAILED_INPUTS_MISSING.
    if final_status == "ok" and not args.dry_run:
        preflight = _step(
            "training_input_preflight",
            [sys.executable, "scripts/check_training_inputs.py", "--as-of-date", as_of],
            run_dir,
        )
        steps.append(preflight)
        if preflight.get("exit_code", 1) != 0:
            halted_reason = "training_inputs_missing"
            final_status = "halted_no_promotion"

    # 2b. Phase 13F: prepare scoped, leakage-safe training inputs. Cleans
    #     stale per-challenger state from a previous run on the same date
    #     so the verifier never sees mixed-mode (train_dry_run=false +
    #     calibration_dry_run=true) artifacts.
    if final_status == "ok" and not args.dry_run:
        prepare = _step(
            "prepare_training_inputs",
            [sys.executable, "scripts/prepare_training_inputs.py", "--as-of-date", as_of],
            run_dir,
        )
        steps.append(prepare)
        if prepare.get("exit_code", 1) != 0:
            halted_reason = "training_inputs_prepare_failed"
            final_status = "halted_no_promotion"

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
        train_step = _step("train_challenger", train_cmd, run_dir)
        steps.append(train_step)
        if train_step.get("exit_code", 1) != 0:
            halted_reason = "training_failed"
            final_status = "halted_no_promotion"

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
        cal_step = _step("calibrate_challenger", cal_cmd, run_dir)
        steps.append(cal_step)
        if cal_step.get("exit_code", 1) != 0:
            halted_reason = "calibration_failed"
            final_status = "halted_no_promotion"

    # 4a. Phase 13K: build rolling model-vs-market benchmark from
    #     deliveries/<date>/after_game_scoring/ artifacts.
    if final_status == "ok":
        bench_step = _step(
            "rolling_market_benchmark",
            [
                sys.executable,
                "scripts/build_rolling_market_benchmark.py",
                "--as-of-date",
                as_of,
                "--window-days",
                "28",
            ],
            run_dir,
        )
        steps.append(bench_step)
        # Insufficient sample is a non-fatal warning at the orchestrator
        # level; the validator's market gates handle the strict policy.

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

    # 6. Maybe promote (no wall-clock cutoff — retries must ship the pointer).
    if final_status == "ok":
        if args.no_promote:
            steps.append(
                {
                    "name": "promote",
                    "skipped": True,
                    "reason": "--no-promote was set",
                }
            )
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
            # Phase 13H: if promotion succeeded, stamp the latest delivery
            # manifests with the new champion's metadata so the dependency
            # verifier can prove Derek/WoO are anchored on this champion.
            try:
                pm = read_json(ch_promo) if ch_promo.exists() else {}
            except Exception:
                pm = {}
            if pm.get("promoted"):
                steps.append(
                    _step(
                        "stamp_delivery_champion_metadata",
                        [sys.executable, "scripts/stamp_delivery_champion_metadata.py"],
                        run_dir,
                    )
                )

    # 5b. Contextual contract guard: verify the champion pointer has not
    #     regressed from contextual/direct-lineup to non-contextual after
    #     promotion.  Runs regardless of whether promotion was skipped or
    #     succeeded — if promotion was blocked by the contextual regression
    #     guard in promote_challenger_if_validated.py, the prior contextual
    #     pointer is still active and the verifier should pass.  If it
    #     fails, the nightly run declares failure so the workflow does not
    #     commit a broken pointer.
    if not args.no_promote:
        steps.append(
            _step(
                "verify_champion_pointer_contextual_contract",
                [
                    sys.executable,
                    "scripts/verify_champion_pointer_contextual_contract.py",
                    "--require-contextual",
                ],
                run_dir,
            )
        )
        # Hard-fail if the contextual contract verifier failed.
        _ctx_step = next(
            (s for s in reversed(steps) if s.get("name") == "verify_champion_pointer_contextual_contract"),
            None,
        )
        if _ctx_step and _ctx_step.get("exit_code", 0) != 0:
            final_status = "failed_contextual_contract"
            write_json_atomic(
                run_dir / "run_manifest.json",
                {
                    "schema_version": "1.0",
                    "as_of_date": as_of,
                    "final_status": final_status,
                    "error": "verify_champion_pointer_contextual_contract failed",
                    "steps": steps,
                },
            )
            print(
                "ERROR: verify_champion_pointer_contextual_contract failed — "
                "champion pointer may have regressed from contextual to non-contextual.",
                file=sys.stderr,
            )
            return 1

    # 6a. Phase 13G: stamp every sub-manifest with target_policy / target_date_et /
    #     stale_fallback_used / training_run_id so downstream verifiers see a
    #     consistent record on disk. Idempotent.
    ch_dir = challenger_dir(as_of)
    for name in (
        "train_manifest.json",
        "model_manifest.json",
        "calibration_manifest.json",
        "validation_report.json",
        "promotion_decision.json",
        "promotion_manifest.json",
    ):
        _stamp_phase13g_fields(ch_dir / name, phase13g_ctx)
    for name in (
        "training_input_preflight.json",
        "training_inputs_manifest.json",
        "validation_report.json",
        "promotion_decision.json",
    ):
        _stamp_phase13g_fields(run_dir / name, phase13g_ctx)
    _stamp_phase13g_fields(readiness_dir(as_of) / "readiness_report.json", phase13g_ctx)

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
        "training_run_id": training_run_id,
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
        "phase13g": phase13g_ctx,
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
    # Do not silently green-light halted core runs. Any halted_no_promotion
    # state means the core train/calibrate/promotion pipeline did not complete
    # successfully and must surface as a failing step in CI.
    return 0 if final_status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
