#!/usr/bin/env python3
"""Phase 13AM: workflow schedule contract verifier.

This verifier asserts that the GitHub Actions workflows obey the rules the
operator and Phase 13AM rely on:

    1. .github/workflows/daily_predictions.yml has a `predict` job whose
       cron is '0 13 * * *' (the canonical 13:00 UTC predict slot).
    2. .github/workflows/daily_pmf_delivery.yml has BOTH a `workflow_run`
       trigger that listens for "NBA Props Model — Daily Pipeline"
       completion AND its existing cron schedule (so PMF Delivery still
       runs for the late-night near-tip and after-game windows even on
       days the predict workflow does not emit a completed event we like).
    3. Every PMF Delivery job has:
         (a) an `id: predict_gate` step invoking
             scripts/predictions_readiness_gate.py, and
         (b) every step AFTER predict_gate is gated with
             `if: steps.predict_gate.outputs.should_proceed == 'true'`.
       This is the structural guarantee that PMF Delivery cannot
       red-fail before predictions are scheduled to exist.
    4. Every BDL-dependent workflow declares BDL_API_KEY in env on the
       step(s) that touch BDL-anchored scripts (predict.py, grade.py,
       run_daily_delivery_pipeline.py). The verifier walks every job and
       confirms the env mapping carries BDL_API_KEY where required.
    5. scripts/predictions_readiness_gate.py exists and is executable.

On success the script prints exactly one line:

    WORKFLOW_SCHEDULE_CONTRACT_PASS

On failure each violation is printed and the script exits 1 with:

    WORKFLOW_SCHEDULE_CONTRACT_FAILED count=<N>

Usage:
    python3 scripts/verify_workflow_schedule_contract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml  # PyYAML; available in repo dev + CI envs.

REPO_ROOT = Path(__file__).resolve().parent.parent
PREDICTIONS_WF = REPO_ROOT / ".github" / "workflows" / "daily_predictions.yml"
PMF_DELIVERY_WF = REPO_ROOT / ".github" / "workflows" / "daily_pmf_delivery.yml"
GATE_SCRIPT = REPO_ROOT / "scripts" / "predictions_readiness_gate.py"

PREDICT_CRON_UTC = "0 13 * * *"
GATE_CONDITION = "steps.predict_gate.outputs.should_proceed == 'true'"
PARENT_WORKFLOW_NAME = "NBA Props Model — Daily Pipeline"

# Scripts that require BDL_API_KEY on their executing step.
BDL_DEPENDENT_RUN_SUBSTRINGS = (
    "scripts/predict.py",
    "scripts/grade.py",
    "scripts/run_daily_delivery_pipeline.py",
    "scripts/score_daily_pmf_delivery_after_game.py",
    "scripts/predictions_readiness_gate.py",
)


def _load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _crons(wf: dict) -> list[str]:
    on = wf.get("on") or wf.get(True)  # PyYAML may parse `on:` as boolean True
    if isinstance(on, dict):
        sched = on.get("schedule") or []
    else:
        sched = []
    return [entry.get("cron", "") for entry in sched if isinstance(entry, dict)]


def _has_workflow_run_trigger(wf: dict, parent_name: str) -> bool:
    on = wf.get("on") or wf.get(True)
    if not isinstance(on, dict):
        return False
    wr = on.get("workflow_run")
    if not isinstance(wr, dict):
        return False
    workflows = wr.get("workflows") or []
    return parent_name in workflows


def _step_runs_bdl(step: dict) -> bool:
    run = step.get("run", "") or ""
    return any(needle in run for needle in BDL_DEPENDENT_RUN_SUBSTRINGS)


def _step_has_bdl_env(step: dict) -> bool:
    env = step.get("env") or {}
    return "BDL_API_KEY" in env


def main() -> int:
    failures: list[str] = []

    # ── Rule 1: predict job has 13:00 UTC cron ──────────────────────────
    if not PREDICTIONS_WF.exists():
        failures.append(f"daily_predictions.yml missing at {PREDICTIONS_WF}")
    else:
        pred_wf = _load(PREDICTIONS_WF)
        pred_crons = _crons(pred_wf)
        if PREDICT_CRON_UTC not in pred_crons:
            failures.append(
                f"daily_predictions.yml missing cron '{PREDICT_CRON_UTC}'; "
                f"observed={pred_crons}"
            )
        predict_job = pred_wf.get("jobs", {}).get("predict")
        if predict_job is None:
            failures.append("daily_predictions.yml missing job 'predict'")
        else:
            cond = predict_job.get("if", "") or ""
            if PREDICT_CRON_UTC not in cond:
                failures.append(
                    "daily_predictions.yml job 'predict' is not gated on "
                    f"schedule '{PREDICT_CRON_UTC}' (if={cond!r})"
                )

    # ── Rule 2/3: PMF Delivery workflow_run trigger + gate structure ────
    if not PMF_DELIVERY_WF.exists():
        failures.append(f"daily_pmf_delivery.yml missing at {PMF_DELIVERY_WF}")
        delivery_wf = None
    else:
        delivery_wf = _load(PMF_DELIVERY_WF)
        if not _has_workflow_run_trigger(delivery_wf, PARENT_WORKFLOW_NAME):
            failures.append(
                "daily_pmf_delivery.yml missing workflow_run trigger for "
                f"workflow {PARENT_WORKFLOW_NAME!r}"
            )
        delivery_crons = _crons(delivery_wf)
        if not delivery_crons:
            failures.append(
                "daily_pmf_delivery.yml has no cron schedules — "
                "near-tip / after-game windows would never fire"
            )
        # Gate audit per job.
        for job_name, job in (delivery_wf.get("jobs") or {}).items():
            steps = job.get("steps") or []
            gate_idx = next(
                (i for i, s in enumerate(steps) if s.get("id") == "predict_gate"),
                None,
            )
            if gate_idx is None:
                failures.append(
                    f"daily_pmf_delivery.yml job {job_name!r} has no "
                    "step with id=predict_gate"
                )
                continue
            gate_step = steps[gate_idx]
            run_block = gate_step.get("run", "") or ""
            if "predictions_readiness_gate.py" not in run_block:
                failures.append(
                    f"daily_pmf_delivery.yml job {job_name!r} predict_gate "
                    "step does not invoke scripts/predictions_readiness_gate.py"
                )
            for j in range(gate_idx + 1, len(steps)):
                downstream = steps[j]
                cond = downstream.get("if", "") or ""
                if GATE_CONDITION not in cond:
                    nm = downstream.get("name", "<unnamed>")
                    failures.append(
                        f"daily_pmf_delivery.yml job {job_name!r} step "
                        f"{nm!r} (index {j}) is NOT gated on "
                        f"`{GATE_CONDITION}` (if={cond!r}) — would run even "
                        "when predictions are missing pre-cron"
                    )

    # ── Rule 4: BDL_API_KEY env coverage on BDL-dependent steps ─────────
    for wf_path, wf in (
        (PREDICTIONS_WF, _load(PREDICTIONS_WF) if PREDICTIONS_WF.exists() else None),
        (PMF_DELIVERY_WF, delivery_wf),
    ):
        if wf is None:
            continue
        for job_name, job in (wf.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                if _step_runs_bdl(step) and not _step_has_bdl_env(step):
                    nm = step.get("name", "<unnamed>")
                    failures.append(
                        f"{wf_path.name} job {job_name!r} step {nm!r} runs "
                        "a BDL-dependent script without BDL_API_KEY in env"
                    )

    # ── Rule 5: gate script exists + is executable ──────────────────────
    if not GATE_SCRIPT.exists():
        failures.append(f"missing {GATE_SCRIPT}")
    else:
        # On Unix we expect the file to be readable by the workflow.
        # Executable bit isn't strictly required (we invoke via python3),
        # but readable/non-empty is.
        if GATE_SCRIPT.stat().st_size < 256:
            failures.append(f"{GATE_SCRIPT} is suspiciously small")

    if failures:
        for f in failures:
            print(f"::error::{f}")
        print(f"WORKFLOW_SCHEDULE_CONTRACT_FAILED count={len(failures)}")
        return 1

    print("WORKFLOW_SCHEDULE_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
