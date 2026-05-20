"""Workflow-shape assertions for ``.github/workflows/nba_pmf_delivery.yml``.

These tests lock in the structural contract from
``CURSOR_TASK_NBA_PMF_PRODUCTION_PIPELINE.md`` Phase 15. They parse the
workflow YAML with the stdlib + ``pyyaml`` (already a runtime dependency
of this repo) and assert structural invariants rather than rendered run
behavior. They are intentionally cheap so CI can run them on every PR.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "nba_pmf_delivery.yml"


@pytest.fixture(scope="module")
def workflow() -> dict:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    # ``yaml.safe_load`` parses the YAML key ``on:`` as the Python
    # boolean ``True`` (since YAML 1.1 ``on`` is a truthy alias). Reach
    # under either key so this test stays robust if pyyaml is later
    # bumped to a 1.2-compliant loader.
    on = data.get("on") or data.get(True)
    assert on is not None, "workflow has no 'on:' trigger block"
    data["__on__"] = on
    return data


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


# ── Cron schedule ───────────────────────────────────────────────────


def _crons(workflow: dict) -> list[str]:
    return [c["cron"] for c in workflow["__on__"]["schedule"]]


def test_workflow_has_predict_cron_at_1400_utc(workflow):
    """Brief Phase 2 mandates a daily 14:00 UTC prediction cron."""

    assert "0 14 * * *" in _crons(workflow)


@pytest.mark.parametrize(
    "cron",
    [
        # Brief Phase 2 mandated 15-cron list.
        "30 6 * * *",
        "30 9 * * *",
        "30 12 * * *",
        "0 14 * * *",
        "0 15 * * *",
        "30 15 * * *",
        "0 18 * * *",
        "30 18 * * *",
        "0 20 * * *",
        "30 21 * * *",
        "25 22 * * *",
        "40,55 22 * * *",
        "10,25,40,55 23,0,1,2 * * *",
        "10 3 * * *",
        "25 3 * * *",
    ],
)
def test_workflow_has_each_required_cron(workflow, cron):
    assert cron in _crons(workflow)


def test_workflow_has_exactly_fifteen_crons(workflow):
    assert len(_crons(workflow)) == 15


# ── workflow_dispatch inputs ────────────────────────────────────────


def test_workflow_dispatch_has_force_run_input(workflow):
    """Brief Phase 2: manual ``force_run`` choice input (default false)."""

    inputs = workflow["__on__"]["workflow_dispatch"]["inputs"]
    assert "force_run" in inputs
    force_run = inputs["force_run"]
    assert force_run.get("type") == "choice"
    # Default must be the literal string 'false' so the resolver's
    # bool-parsing treats it correctly.
    assert str(force_run.get("default", "")).lower() == "false"
    assert sorted(force_run.get("options", [])) == ["false", "true"]


def test_workflow_dispatch_has_required_stage_options(workflow):
    """``predict``, ``model_chain``, ``model_chain_no_promote`` must be choosable."""

    inputs = workflow["__on__"]["workflow_dispatch"]["inputs"]
    stage = inputs["stage"]
    opts = set(stage.get("options", []))
    for required in ("predict", "model_chain", "model_chain_no_promote"):
        assert required in opts, f"workflow_dispatch.stage missing option: {required}"


def test_workflow_dispatch_no_promote_default_true(workflow):
    inputs = workflow["__on__"]["workflow_dispatch"]["inputs"]
    assert str(inputs["no_promote"].get("default", "")).lower() == "true"


# ── Resolver wiring ─────────────────────────────────────────────────


def test_workflow_calls_resolve_nba_pmf_schedule(workflow_text):
    """Brief Phase 4: ``resolve_context`` invokes the Python resolver."""

    assert "scripts/resolve_nba_pmf_schedule.py" in workflow_text


def test_workflow_resolver_passes_all_required_inputs(workflow_text):
    """The resolver invocation must pass every flag the brief mandates."""

    required_flags = [
        "--event-name",
        "--schedule",
        "--manual-stage",
        "--manual-mode",
        "--manual-delivery-date",
        "--manual-as-of-date",
        "--manual-force-run",
        "--github-output",
    ]
    for flag in required_flags:
        assert flag in workflow_text, f"resolver call missing flag: {flag}"


# ── Concurrency posture ─────────────────────────────────────────────


def test_workflow_has_no_top_level_concurrency_group(workflow, workflow_text):
    """Brief Phase 3: top-level workflow concurrency must be removed.

    Long-running training/Phase 13 jobs are no longer allowed to block
    a Derek/WoO delivery refresh on the same ref.
    """

    assert "concurrency" not in workflow, (
        "workflow has top-level concurrency block; brief Phase 3 forbids it"
    )
    forbidden_token = "nba-pmf-delivery-${{ github.ref }}"
    # Token must not appear anywhere as a workflow-level concurrency
    # group. Substring scan keeps this robust if a future refactor
    # tries to reintroduce it via a different YAML key.
    assert forbidden_token not in workflow_text


def test_jobs_have_required_job_level_concurrency_groups(workflow):
    """Brief Phase 3: each long-running job must own its concurrency group."""

    expected = {
        "model_chain_training_calibration": "nba-pmf-model-chain-",
        "phase8_pmf_calibration_diagnostics_market_eval": "nba-pmf-phase8-",
        "phase13_live_context_contextual_lineup": "nba-pmf-phase13-",
        "predict_daily": "nba-pmf-predict-",
        "delivery_build": "nba-pmf-delivery-",
        "after_game_scoring": "nba-pmf-after-game-",
    }
    jobs = workflow["jobs"]
    for job_name, prefix in expected.items():
        assert job_name in jobs, f"missing job: {job_name}"
        conc = jobs[job_name].get("concurrency")
        assert conc is not None, f"{job_name} has no concurrency block"
        group = conc.get("group") if isinstance(conc, dict) else conc
        assert prefix in str(group), (
            f"{job_name} concurrency group should contain prefix {prefix!r}; got {group!r}"
        )


# ── predict_daily job ───────────────────────────────────────────────


def test_workflow_has_predict_daily_job(workflow):
    """Brief Phase 9: a dedicated ``predict_daily`` job exists."""

    assert "predict_daily" in workflow["jobs"]


def test_predict_daily_uses_resolver_outputs(workflow):
    predict = workflow["jobs"]["predict_daily"]
    cond = predict["if"]
    assert "needs.resolve_context.outputs.run_predict == 'true'" in cond
    assert "needs.resolve_context.outputs.valid_skip_reason == ''" in cond


def test_predict_daily_calls_predictions_readiness_gate(workflow):
    """predict_daily uses the same readiness gate as the delivery job."""

    steps = workflow["jobs"]["predict_daily"]["steps"]
    rendered = "\n".join(s.get("run", "") for s in steps if isinstance(s, dict))
    assert "scripts/predictions_readiness_gate.py" in rendered
    assert "--predict-cron-hour-utc 14" in rendered


def test_predict_daily_passes_force_run_predict_conditionally(workflow):
    steps = workflow["jobs"]["predict_daily"]["steps"]
    rendered = "\n".join(s.get("run", "") for s in steps if isinstance(s, dict))
    # The conditional --force-run-predict must be present, tied to the
    # resolver's force_run output.
    assert "--force-run-predict" in rendered
    assert "needs.resolve_context.outputs.force_run" in rendered


# ── delivery_build job ──────────────────────────────────────────────


def test_delivery_calls_predictions_readiness_gate_before_pipeline(workflow):
    """Brief Phase 10: delivery must run the readiness gate BEFORE the pipeline.

    The gate's ``run`` step must appear before the
    ``run_daily_delivery_pipeline.py`` step within the job's step list.
    """

    steps = workflow["jobs"]["delivery_build"]["steps"]
    gate_idx = None
    pipeline_idx = None
    for i, step in enumerate(steps):
        run_text = step.get("run", "") if isinstance(step, dict) else ""
        if "scripts/predictions_readiness_gate.py" in run_text and gate_idx is None:
            gate_idx = i
        if "scripts/run_daily_delivery_pipeline.py" in run_text and pipeline_idx is None:
            pipeline_idx = i
    assert gate_idx is not None, "delivery_build is missing the readiness gate step"
    assert pipeline_idx is not None, "delivery_build is missing run_daily_delivery_pipeline.py"
    assert gate_idx < pipeline_idx, (
        "Predictions readiness gate must run before run_daily_delivery_pipeline.py"
    )


def test_delivery_passes_force_run_conditionally(workflow):
    steps = workflow["jobs"]["delivery_build"]["steps"]
    rendered = "\n".join(s.get("run", "") for s in steps if isinstance(s, dict))
    assert "--force-run" in rendered
    assert "needs.resolve_context.outputs.force_run" in rendered


def test_delivery_calls_enforce_csv_size_contract(workflow):
    """Brief Phase 10: CSV size contract must run inside delivery."""

    steps = workflow["jobs"]["delivery_build"]["steps"]
    rendered = "\n".join(s.get("run", "") for s in steps if isinstance(s, dict))
    assert "scripts/enforce_delivery_csv_size_contract.py" in rendered


def test_delivery_preserves_derek_unique_summary(workflow_text):
    """Brief: ``derek_unique_props_summary.csv`` must be on the --preserve list."""

    assert (
        "--preserve derek_forward_feed/derek_unique_props_summary.csv"
        in workflow_text
    )


def test_delivery_hash_protects_derek_unique_summary(workflow):
    """The hash-before / hash-after / fail-on-change guard is wired in delivery."""

    steps = workflow["jobs"]["delivery_build"]["steps"]
    names = [s.get("name", "") for s in steps if isinstance(s, dict)]
    assert any("Preserve Derek unique summary hash" in n for n in names)
    assert any("Assert Derek unique summary was not changed" in n for n in names)


def test_delivery_depends_only_on_resolve_context_and_readiness(workflow):
    """Brief Phase 10: delivery must NOT block on training/phase8/phase13."""

    delivery = workflow["jobs"]["delivery_build"]
    needs = delivery.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    assert sorted(needs) == ["readiness", "resolve_context"]


# ── Phase 13 strict ordering ────────────────────────────────────────


def test_phase13_steps_are_in_strict_OPQRS_order(workflow):
    """Brief Phase 8 / Phase 15: 13O → 13P → 13Q → 13R → 13S."""

    job = workflow["jobs"]["phase13_live_context_contextual_lineup"]
    step_names = [s.get("name", "") for s in job["steps"] if isinstance(s, dict)]
    order_markers = {
        "13O": None,
        "13P": None,
        "13Q": None,
        "13R": None,
        "13S": None,
    }
    for i, name in enumerate(step_names):
        for marker in list(order_markers):
            if order_markers[marker] is None and marker in name:
                order_markers[marker] = i
    missing = [k for k, v in order_markers.items() if v is None]
    assert not missing, f"phase13 missing step markers: {missing}"
    indices = [order_markers[k] for k in ("13O", "13P", "13Q", "13R", "13S")]
    assert indices == sorted(indices), (
        f"phase13 sub-steps out of order: {dict(zip(['13O','13P','13Q','13R','13S'], indices))}"
    )


def test_phase8_requires_model_chain_success_not_always(workflow):
    """Brief Phase 7: Phase 8 may not run via ``always()``."""

    job = workflow["jobs"]["phase8_pmf_calibration_diagnostics_market_eval"]
    cond = job["if"]
    assert "always()" not in cond
    assert "needs.model_chain_training_calibration.result == 'success'" in cond


def test_phase13_requires_phase8_success_not_always(workflow):
    """Brief Phase 8: Phase 13 chain may not run via ``always()``."""

    job = workflow["jobs"]["phase13_live_context_contextual_lineup"]
    cond = job["if"]
    assert "always()" not in cond
    assert (
        "needs.phase8_pmf_calibration_diagnostics_market_eval.result == 'success'"
        in cond
    )


# ── Final verifiers strict gating ───────────────────────────────────


def test_final_verifiers_do_not_use_always(workflow):
    """Brief Phase 14: ``always()`` is banned for the final verifier job."""

    job = workflow["jobs"]["final_contract_verifiers"]
    cond = job["if"]
    assert "always()" not in cond


def test_final_verifiers_gate_on_each_upstream_result(workflow):
    """Brief Phase 14: each selected prerequisite must be success or skipped."""

    job = workflow["jobs"]["final_contract_verifiers"]
    cond = job["if"]
    for upstream in (
        "model_chain_training_calibration",
        "phase8_pmf_calibration_diagnostics_market_eval",
        "phase13_live_context_contextual_lineup",
        "predict_daily",
        "delivery_build",
        "after_game_scoring",
    ):
        assert f"needs.{upstream}.result" in cond
        # Must accept BOTH success and skipped (skipped is the valid
        # outcome when the resolver did not select that prerequisite).
        assert f"needs.{upstream}.result == 'success'" in cond
        assert f"needs.{upstream}.result == 'skipped'" in cond


def test_final_verifiers_depend_on_every_upstream_job(workflow):
    job = workflow["jobs"]["final_contract_verifiers"]
    needs = job.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    expected = {
        "resolve_context",
        "readiness",
        "model_chain_training_calibration",
        "phase8_pmf_calibration_diagnostics_market_eval",
        "phase13_live_context_contextual_lineup",
        "predict_daily",
        "delivery_build",
        "after_game_scoring",
    }
    assert expected.issubset(set(needs)), (
        f"final_contract_verifiers.needs missing: {expected - set(needs)}"
    )


# ── valid_skip_reason gating on every selectable job ────────────────


@pytest.mark.parametrize(
    "job_name",
    [
        "model_chain_training_calibration",
        "phase8_pmf_calibration_diagnostics_market_eval",
        "phase13_live_context_contextual_lineup",
        "predict_daily",
        "delivery_build",
        "after_game_scoring",
        "final_contract_verifiers",
    ],
)
def test_selectable_jobs_gate_on_valid_skip_reason_empty(workflow, job_name):
    """Each job that can be selected must valid-skip when the resolver said so."""

    cond = workflow["jobs"][job_name].get("if", "")
    assert "needs.resolve_context.outputs.valid_skip_reason == ''" in cond


# ── Commit/push retry-loop autostash regression guard ───────────────
#
# Regression context: predict smoke run 26159233882 (post PR #16 merge) failed
# at the "Commit prediction artifacts + automation health" step with
#   error: cannot pull with rebase: You have unstaged changes.
# The retry loop "git pull --rebase origin main && git push origin HEAD:main"
# was unable to fetch remote main because upstream steps in the same job
# (refresh_daily_inputs.py, BDL settled-stat refresh, and verifiers like
# verify_derek_woo_champion_dependency.py) mutate tracked files that the
# explicit `git add` allow-list intentionally does NOT commit. The fix is to
# use `git pull --rebase --autostash` in every commit/push retry loop so
# leftover unstaged mutations get stashed and restored automatically.
# The old `daily_pmf_delivery.yml` documents this as "Bug E" at e.g. lines
# 230-238, 498-506, 650-658, 850, 1016 and solves it with an explicit
# working-tree reset before the rebase loop.


def test_commit_retry_loops_use_autostash(workflow_text):
    """Every `git pull --rebase ... && git push` retry loop must use --autostash.

    The failure-prone pattern was `git pull --rebase origin main && git push`.
    The fixed pattern is `git pull --rebase --autostash origin main && git push`.
    Asserting on the raw `&& git push` shape lets the post-checkout standalone
    `git pull --rebase origin main || true` lines (which run against a clean
    working tree right after checkout) keep their original shape.
    """

    failing = "git pull --rebase origin main && git push"
    fixed = "git pull --rebase --autostash origin main && git push"
    assert failing not in workflow_text, (
        "commit/push retry loop missing --autostash; "
        "this is the Bug-E regression from predict run 26159233882"
    )
    assert workflow_text.count(fixed) >= 1, (
        "expected at least one autostashed commit/push retry loop"
    )
