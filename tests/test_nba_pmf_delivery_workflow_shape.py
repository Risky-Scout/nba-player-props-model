"""Workflow-shape assertions for ``.github/workflows/nba_pmf_delivery.yml``.

These tests lock in the structural contract from
``CURSOR_TASK_NBA_PMF_PRODUCTION_PIPELINE.md`` Phase 15. They parse the
workflow YAML with the stdlib + ``pyyaml`` (already a runtime dependency
of this repo) and assert structural invariants rather than rendered run
behavior. They are intentionally cheap so CI can run them on every PR.
"""

from __future__ import annotations

from pathlib import Path
import re

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


# ── Resolve-context tip-time recovery plumbing ──────────────────────
#
# Phase 13U upstream tip-time recovery (follow-on to PR #31's
# loud-failure path): `resolve_context` must install `requirements.txt`
# BEFORE the resolver step (so the resolver's recovery hook can
# subprocess out to `scripts/resolve_game_start_times.py` and use
# pandas/pyarrow to read predictions parquet), AND must expose
# `BDL_API_KEY` / `ODDS_API_KEY` on the resolver step's env so the
# subprocess inherits them.


def test_resolve_context_installs_requirements_before_resolver(workflow):
    """``resolve_context`` must run ``pip install -r requirements.txt``
    in a step that precedes the resolver invocation.

    Required so the resolver's tip-time recovery hook can spawn the
    Phase 13U generator (`scripts/resolve_game_start_times.py`),
    which lazy-imports pandas for the predictions-parquet cascade.
    """

    steps = workflow["jobs"]["resolve_context"]["steps"]
    install_idx = None
    resolve_idx = None
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        run_text = step.get("run", "") or ""
        if "pip install -r requirements.txt" in run_text and install_idx is None:
            install_idx = i
        if (
            "scripts/resolve_nba_pmf_schedule.py" in run_text
            and resolve_idx is None
        ):
            resolve_idx = i
    assert install_idx is not None, (
        "resolve_context is missing a `pip install -r requirements.txt` "
        "step required for the tip-time recovery hook"
    )
    assert resolve_idx is not None, (
        "resolve_context is missing the schedule resolver step"
    )
    assert install_idx < resolve_idx, (
        f"requirements install (idx {install_idx}) must precede the "
        f"resolver invocation (idx {resolve_idx})"
    )


def test_resolve_context_exposes_tip_time_secrets_to_resolver(workflow):
    """The resolver step's ``env:`` must include both ``BDL_API_KEY``
    and ``ODDS_API_KEY``, so the recovery hook's subprocess inherits
    them when hitting the real BDL / Odds API endpoints.
    """

    steps = workflow["jobs"]["resolve_context"]["steps"]
    resolver_step = None
    for step in steps:
        if not isinstance(step, dict):
            continue
        run_text = step.get("run", "") or ""
        if "scripts/resolve_nba_pmf_schedule.py" in run_text:
            resolver_step = step
            break
    assert resolver_step is not None, "resolver step not found"
    env_block = resolver_step.get("env") or {}
    assert "BDL_API_KEY" in env_block, (
        "resolver step must expose BDL_API_KEY for tip-time recovery"
    )
    assert "ODDS_API_KEY" in env_block, (
        "resolver step must expose ODDS_API_KEY for tip-time recovery"
    )
    # Values must be secret references — never hardcoded.
    for key in ("BDL_API_KEY", "ODDS_API_KEY"):
        value = str(env_block[key])
        assert "secrets." in value, (
            f"{key} must be sourced from `secrets.` reference, not a literal"
        )


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


_AVAILABILITY_PREFLIGHT_CMD = (
    'python3 scripts/build_availability_table.py --slate-date "$D" '
    "--out data/player_availability_asof.parquet"
)
_AVAILABILITY_PREFLIGHT_DATE = (
    'D="${{ needs.resolve_context.outputs.delivery_date }}"'
)


def _job_steps(workflow: dict, job_name: str) -> list[dict]:
    return [s for s in workflow["jobs"][job_name]["steps"] if isinstance(s, dict)]


def _first_step_index_with_run_marker(steps: list[dict], marker: str) -> int | None:
    for i, step in enumerate(steps):
        if marker in (step.get("run", "") or ""):
            return i
    return None


def _availability_preflight_step(steps: list[dict]) -> tuple[int, dict]:
    matches = [
        (i, step)
        for i, step in enumerate(steps)
        if "scripts/build_availability_table.py" in (step.get("run", "") or "")
    ]
    assert matches, "availability preflight step not found"
    assert len(matches) == 1, (
        f"expected exactly one availability preflight step, found {len(matches)}"
    )
    return matches[0]


def _assert_availability_preflight_command_contract(step: dict):
    run_text = step.get("run", "") or ""
    assert _AVAILABILITY_PREFLIGHT_DATE in run_text
    assert _AVAILABILITY_PREFLIGHT_CMD in run_text
    assert "build_availability_table.py --slate-date" in run_text
    assert "build_availability_table.py || true" not in run_text
    assert "--slate-date \"$D\"" in run_text
    assert re.search(r"--slate-date\\s+\"20\\d\\d-\\d\\d-\\d\\d\"", run_text) is None, (
        "availability preflight must not hardcode a date literal"
    )


def _assert_availability_preflight_not_suppressed(step: dict):
    run_text = step.get("run", "") or ""
    for line in run_text.splitlines():
        if "build_availability_table.py" in line:
            assert "|| true" not in line, (
                "availability preflight build command must not be suppressed"
            )


def test_availability_preflight_in_jobs_uses_required_command_contract(workflow):
    """Predict and delivery jobs must preflight with delivery_date-driven slate-date."""

    for job_name in ("predict_daily", "delivery_build"):
        _, step = _availability_preflight_step(_job_steps(workflow, job_name))
        _assert_availability_preflight_command_contract(step)
        _assert_availability_preflight_not_suppressed(step)
        assert step.get("name", "") == "Preflight slate-date availability table"


def test_availability_preflight_precedes_predict_daily_paths(workflow):
    """predict_daily availability preflight must run before scripts/predict.py."""

    steps = _job_steps(workflow, "predict_daily")
    avail_idx, _ = _availability_preflight_step(steps)
    predict_idx = _first_step_index_with_run_marker(steps, "scripts/predict.py")
    assert predict_idx is not None, "predict_daily missing scripts/predict.py step"
    assert avail_idx < predict_idx, (
        "predict_daily availability preflight must precede scripts/predict.py"
    )


def test_availability_preflight_precedes_delivery_pipeline_and_markers(workflow):
    """delivery_build preflight must run before pipeline and feature/stat-grid markers."""

    steps = _job_steps(workflow, "delivery_build")
    avail_idx, _ = _availability_preflight_step(steps)

    pipeline_markers = (
        "scripts/run_daily_delivery_pipeline.py",
        "scripts/build_daily_pmf_delivery.py",
    )
    pipeline_indices = [
        _first_step_index_with_run_marker(steps, marker)
        for marker in pipeline_markers
    ]
    pipeline_indices = [i for i in pipeline_indices if i is not None]
    assert pipeline_indices, (
        "delivery_build missing run_daily_delivery_pipeline/build_daily_pmf_delivery"
    )
    assert all(avail_idx < i for i in pipeline_indices), (
        "delivery_build availability preflight must precede delivery pipeline invocation"
    )

    optional_same_day_markers = (
        "build_stat_grid_pmfs",
        "build_player_prop_feature_snapshot",
        "build_daily_pmf_delivery",
        "scripts/build_stat_grid_pmfs.py",
        "scripts/build_player_prop_feature_snapshot.py",
        "scripts/build_daily_pmf_delivery.py",
    )
    for marker in optional_same_day_markers:
        marker_idx = _first_step_index_with_run_marker(steps, marker)
        if marker_idx is not None:
            assert avail_idx < marker_idx, (
                f"availability preflight must precede same-day marker {marker!r}"
            )


def test_model_chain_preflight_refreshes_availability_before_training_table_paths(workflow):
    """model_chain must preflight availability before training-table-producing paths."""

    steps = _job_steps(workflow, "model_chain_training_calibration")
    avail_idx, step = _availability_preflight_step(steps)
    _assert_availability_preflight_command_contract(step)
    _assert_availability_preflight_not_suppressed(step)

    nightly_idx = _first_step_index_with_run_marker(
        steps, "scripts/run_nightly_training_and_calibration.py"
    )
    assert nightly_idx is not None, (
        "model_chain missing run_nightly_training_and_calibration.py step"
    )
    assert avail_idx < nightly_idx, (
        "model_chain availability preflight must precede nightly training/calibration run"
    )

    # If model-chain ever gains a direct train/build-table call, preflight
    # must still run first.
    for marker in ("scripts/train.py", "--build-table-only", "data/training_table.parquet"):
        marker_idx = _first_step_index_with_run_marker(steps, marker)
        if marker_idx is not None:
            assert avail_idx < marker_idx, (
                f"model_chain availability preflight must precede {marker!r}"
            )


def test_phase8_preflight_refreshes_availability_before_build_training_table(workflow):
    """phase8 must preflight availability before 'Build training table if absent'."""

    steps = _job_steps(workflow, "phase8_pmf_calibration_diagnostics_market_eval")
    avail_idx, step = _availability_preflight_step(steps)
    _assert_availability_preflight_command_contract(step)
    _assert_availability_preflight_not_suppressed(step)

    build_table_idx = _first_step_index_with_run_marker(
        steps, "python3 scripts/train.py --build-table-only"
    )
    assert build_table_idx is not None, (
        "phase8 missing build-training-table command"
    )
    assert avail_idx < build_table_idx, (
        "phase8 availability preflight must precede build-table-only command"
    )


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


def test_delivery_csv_rounding_runs_in_correct_post_processing_order(
    workflow_text,
):
    """The new display-rounding step must run after ``strip_empty_delivery_columns``
    and before ``write_delivery_review_previews`` / ``enforce_delivery_csv_size_contract``,
    and must pass ``--places 4`` plus the Derek unique summary preserve flag.
    """

    text = workflow_text

    assert "scripts/round_delivery_csv_numeric_display.py" in text
    assert "--places 4" in text
    assert "--preserve derek_forward_feed/derek_unique_props_summary.csv" in text

    strip_idx = text.index("scripts/strip_empty_delivery_columns.py")
    round_idx = text.index("scripts/round_delivery_csv_numeric_display.py")
    previews_idx = text.index("scripts/write_delivery_review_previews.py")
    size_idx = text.index("scripts/enforce_delivery_csv_size_contract.py")

    assert strip_idx < round_idx < previews_idx < size_idx, (
        f"rounding step out of order: strip={strip_idx} round={round_idx} "
        f"previews={previews_idx} size={size_idx}"
    )


def test_delivery_hash_protects_derek_unique_summary(workflow):
    """The hash-after-pipeline / hash-after-postprocess / fail-on-change guard
    is wired in delivery. The pre-pipeline note step is informational only and
    must NOT block current-date generation by the delivery pipeline; the
    failure semantics live in the post-processing guard.
    """

    steps = workflow["jobs"]["delivery_build"]["steps"]
    names = [s.get("name", "") for s in steps if isinstance(s, dict)]
    assert any("Note existing Derek unique summary hash" in n for n in names)
    assert any(
        "Capture Derek unique summary hash after pipeline generation" in n
        for n in names
    )
    assert any(
        "Assert Derek unique summary was not changed by post-processing" in n
        for n in names
    )


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


# ── Derek unique summary post-processing guard regression guard ─────
#
# Regression context: Derek near-lineup smoke run 26164363728 (post PR #17
# merge) failed at the "Assert Derek unique summary was not changed" step
# because the previous guard compared the *pre-pipeline* hash to the
# *post-pipeline+post-processing* hash. The delivery pipeline is the
# authoritative writer of the current-slate
# `deliveries/<date>/derek_forward_feed/derek_unique_props_summary.csv`,
# so the previous shape effectively forbade any same-day refresh by
# Derek modes (derek_near_lineup, close_lock) once WoO morning had built
# the first version.
#
# Correct shape:
#   pre-pipeline hash    -> informational only, never used to fail
#   pipeline runs        -> may regenerate the current-date summary
#   after-pipeline hash  -> captured by `derek_unique_after_pipeline`
#   post-processing runs -> strip / previews / CSV size contract
#   after-postproc hash  -> compared to after-pipeline hash
#   FAIL only if post-processing changed the file
#
# Additionally, both the after-pipeline capture step and the post-process
# guard step re-assert the strict six-column public contract:
#   player_name, projected_minutes, stat, pmf_mean, market_line, p_over


def test_derek_unique_summary_guard_allows_pipeline_generation_but_blocks_postprocessing_mutation(
    workflow_text,
):
    """The Derek guard must allow same-day pipeline regeneration but block
    any post-processing mutation, with the strict 6-column contract enforced
    at both the after-pipeline capture step and the post-process guard step.
    """

    # Required new step names and pass markers.
    assert (
        "Capture Derek unique summary hash after pipeline generation"
        in workflow_text
    )
    assert (
        "Assert Derek unique summary was not changed by post-processing"
        in workflow_text
    )
    assert "DEREK_UNIQUE_SUMMARY_SCHEMA_PASS" in workflow_text
    assert "DEREK_UNIQUE_SUMMARY_POSTPROCESS_GUARD_PASS" in workflow_text
    assert "was changed by post-processing" in workflow_text

    # The post-processing guard must reference the after-pipeline hash, not
    # the informational pre-pipeline hash.
    assert (
        "steps.derek_unique_after_pipeline.outputs.hash" in workflow_text
    )

    # The old failure semantics must not return: the pre-pipeline hash must
    # never be used to fail the run.
    forbidden = (
        "derek_unique_props_summary.csv changed during this run. "
        "This is not allowed."
    )
    assert forbidden not in workflow_text, (
        "The pre-pipeline hash must NOT be used to fail current-date "
        "delivery regeneration; only post-processing mutation may fail."
    )


# ── Stale rebase-state cleanup regression guard ─────────────────────
#
# Regression context: run 26188323723 failed in
# ``model_chain_training_calibration → Commit training/calibration
# artifacts`` with
#   fatal: It seems that there is already a rebase-merge directory
# The retry loop ``git pull --rebase --autostash origin main && git push``
# did not clear stale ``.git/rebase-merge`` / ``.git/rebase-apply`` state,
# so once a rebase failed mid-way every subsequent retry tripped the same
# fatal. Every self-committing step in the workflow must now use the
# ``cleanup_rebase_state`` / ``sync_and_push`` helper pattern, which
# scrubs the partial-rebase directories before AND after every attempt.


def test_self_commit_blocks_clean_stale_rebase_state(workflow_text):
    """Every self-commit step uses the cleanup_rebase_state + sync_and_push helpers.

    The helpers MUST be defined inside the same shell block (each step
    runs in its own subshell), and the autostashed rebase pull MUST be
    inside the ``sync_and_push`` body — not a bare retry loop.
    """

    text = workflow_text

    # Helpers are defined at least once.
    assert "cleanup_rebase_state" in text
    assert "git rebase --abort" in text
    assert "rm -rf .git/rebase-merge .git/rebase-apply" in text
    assert "git pull --rebase --autostash origin main" in text

    # The pattern is used by every self-commit step we patched. The
    # step name appears verbatim in the YAML and the helpers + invocation
    # must live in the same step body (well within 4000 chars).
    expected_blocks = [
        "Commit refreshed player stats",
        "Commit training/calibration artifacts",
        "Commit Phase 8 artifacts",
        "Commit Phase 13 artifacts",
        "Commit prediction artifacts + automation health",
        "Build delivery index and commit delivery outputs",
        "Build delivery index and commit after-game outputs",
    ]
    for block_name in expected_blocks:
        idx = text.index(block_name)
        window = text[idx : idx + 4000]
        assert "cleanup_rebase_state" in window, (
            f"{block_name!r} missing cleanup_rebase_state"
        )
        assert "sync_and_push" in window, (
            f"{block_name!r} missing sync_and_push invocation"
        )
        assert "git pull --rebase --autostash origin main" in window, (
            f"{block_name!r} missing --autostash --rebase pull"
        )
        assert "rm -rf .git/rebase-merge .git/rebase-apply" in window, (
            f"{block_name!r} missing rebase-merge/rebase-apply cleanup"
        )

    # No bare un-cleaned rebase pulls remain inside any self-commit
    # retry loop. (The standalone post-checkout
    # ``- run: git pull --rebase origin main || true`` lines run against
    # a clean working tree right after checkout and intentionally keep
    # their original shape, so the forbidden substring is the exact
    # newline-terminated bare pull.)
    forbidden = [
        "git pull --rebase origin main\n",
    ]
    for s in forbidden:
        assert s not in text, f"forbidden pattern still present: {s!r}"

    # No force-push refspec anywhere in the workflow. We check for the
    # specific git-push force shapes rather than the bare substring
    # ``--force`` (which would also match unrelated flags like
    # ``--force-run`` / ``--force-run-predict`` that gate manual
    # delivery / predict invocations).
    assert "git push --force" not in text, (
        "force-push must not appear in this workflow"
    )
    assert "--force-with-lease" not in text, (
        "force-with-lease push must not appear in this workflow"
    )
    assert "push -f" not in text, "short-form force push must not appear"
    assert "HEAD:+main" not in text, (
        "force-overwrite push refspec (HEAD:+main) must not appear"
    )
    assert ":+main" not in text, (
        "force-overwrite push refspec (+main) must not appear"
    )


def test_self_commit_no_swallowed_push_failure(workflow_text):
    """``sync_and_push`` must be allowed to fail loudly.

    Wrapping the helper invocation in ``|| true`` would swallow a real
    push failure and silently green-light a step whose changes never
    landed on main. Forbid the obvious shapes.
    """

    text = workflow_text
    assert "sync_and_push 5 || true" not in text
    assert "sync_and_push 3 || true" not in text
    assert "sync_and_push || true" not in text


def _step_body_after(workflow_text: str, step_name: str) -> str:
    idx = workflow_text.index(step_name)
    return workflow_text[idx : idx + 5000]


def test_refresh_player_stats_commit_owns_freshness_automation_health(workflow_text):
    """``player_game_stats_freshness_*`` paths are owned only by the
    settled-stats refresh self-commit step.

    Regression: run 26226082429 hit add/add rebase conflicts when
    ``Commit training/calibration artifacts`` also staged the same
    per-date freshness files via a broad ``artifacts/automation_health``
    add.
    """

    body = _step_body_after(workflow_text, "Commit refreshed player stats")
    for pattern in (
        "player_game_stats_freshness_*.json",
        "player_game_stats_freshness_*.md",
        "player_game_stats_freshness_check_*.json",
    ):
        assert pattern in body, (
            f"Commit refreshed player stats must stage {pattern!r}"
        )


def test_training_commit_excludes_freshness_from_automation_health(workflow_text):
    """Training/calibration self-commit must not stage overlapping
    ``player_game_stats_freshness_*`` automation_health files."""

    body = _step_body_after(workflow_text, "Commit training/calibration artifacts")
    assert "player_game_stats_freshness_* paths are owned exclusively" in body
    assert "git reset HEAD --" in body
    for pattern in (
        "player_game_stats_freshness_*.json",
        "player_game_stats_freshness_*.md",
        "player_game_stats_freshness_check_*.json",
    ):
        assert pattern in body, (
            f"training commit must unstage {pattern!r} after broad add"
        )
    # Must not use the old broad-only add line without the reset guard.
    assert (
        "artifacts/automation_health \\\n" not in body
        and "\n            artifacts/automation_health \\" not in body
    ), (
        "training commit still uses bare artifacts/automation_health add"
    )


def test_phase8_commit_excludes_freshness_from_automation_health(workflow_text):
    """Phase 8 self-commit uses the same freshness ownership guard."""

    body = _step_body_after(workflow_text, "Commit Phase 8 artifacts")
    assert "git reset HEAD --" in body
    assert "player_game_stats_freshness_*.json" in body
    assert (
        "\n            artifacts/automation_health \\" not in body
    ), "phase8 commit still uses bare artifacts/automation_health add"

_PHASE8_DIAGNOSTICS_STEP = (
    "Run diagnostics and market-eval gates (no unexplained NaNs)"
)
_DAILY_PMF_DELIVERY_WORKFLOW = (
    REPO_ROOT / ".github" / "workflows" / "daily_pmf_delivery.yml"
)


@pytest.mark.parametrize(
    "required_fragment",
    [
        'D="${{ needs.resolve_context.outputs.delivery_date }}"',
        'python3 scripts/verify_role_bucket_contract.py --date "$D"',
        'python3 scripts/verify_combo_role_calibration_contract.py || true',
        'python3 scripts/run_diagnostics.py \\',
        '--run-date "$D"',
        "--allow-provisional-block",
        '--end-date "$D"',
    ],
)
def test_phase8_diagnostics_step_wires_delivery_date_and_verifiers(
    workflow_text, required_fragment
):
    """Phase 8 diagnostics must pass ``$D`` into role-bucket verifier and
    keep the existing run_diagnostics / combo-verifier contracts.
    """

    body = _step_body_after(workflow_text, _PHASE8_DIAGNOSTICS_STEP)
    assert required_fragment in body


def test_phase8_role_bucket_verifier_is_not_suppressed(workflow_text):
    """The role-bucket contract verifier must fail the step on violation."""

    body = _step_body_after(workflow_text, _PHASE8_DIAGNOSTICS_STEP)
    assert "verify_role_bucket_contract.py || true" not in body


def test_legacy_daily_pmf_delivery_workflow_unchanged_by_phase8_verifier_wiring():
    """The legacy manual workflow must not pick up Phase 8 verifier wiring."""

    text = _DAILY_PMF_DELIVERY_WORKFLOW.read_text(encoding="utf-8")
    assert "verify_role_bucket_contract.py" not in text


def test_only_canonical_nba_pmf_delivery_workflow_has_automatic_trigger():
    """At-most-one AUTOMATIC NBA-PMF delivery writer.

    "Automatic" = ``schedule:`` OR ``workflow_run:``. The canonical
    ``nba_pmf_delivery.yml`` is the only workflow under
    ``.github/workflows/`` whose ``name:`` starts with
    ``NBA PMF Delivery`` and whose triggers include either of those
    keys. This is the STRONGER cross-workflow regression-lock for
    the parent audit's TWO_SCHEDULED_WRITERS_DETECTED conclusion
    (2026-05-20): it prevents not only a reintroduced ``schedule:``
    but also any ``workflow_run:`` chain that would silently fire
    a duplicate delivery writer whenever an upstream workflow
    completes on main.
    """

    wf_dir = REPO_ROOT / ".github" / "workflows"
    automatic_keys = {"schedule", "workflow_run"}
    offenders: list[tuple[str, list[str]]] = []
    canonical_seen = False
    for wf_path in sorted(wf_dir.glob("*.yml")):
        text = wf_path.read_text(encoding="utf-8")
        # Same pre-screen rationale as the schedule-only sibling test:
        # only candidate workflows whose ``name:`` line starts with
        # the "NBA PMF Delivery" prefix participate.
        if not any(
            line.startswith('name: NBA PMF Delivery')
            or line.startswith('name: "NBA PMF Delivery')
            or line.startswith("name: 'NBA PMF Delivery")
            for line in text.splitlines()
        ):
            continue
        data = yaml.safe_load(text)
        assert isinstance(data, dict), (
            f"{wf_path.name} declares an NBA-PMF-Delivery `name:` but is "
            "not a parseable mapping"
        )
        triggers = data.get("on") if "on" in data else data.get(True)
        if isinstance(triggers, dict):
            keys = set(triggers.keys())
        elif isinstance(triggers, list):
            keys = set(triggers)
        else:
            keys = {triggers}
        present_automatic = sorted(keys & automatic_keys)
        if wf_path.name == "nba_pmf_delivery.yml":
            canonical_seen = True
            assert present_automatic, (
                "Canonical nba_pmf_delivery.yml must retain at least one "
                f"automatic trigger ({sorted(automatic_keys)})."
            )
        else:
            if present_automatic:
                offenders.append((wf_path.name, present_automatic))
    assert canonical_seen, (
        "Canonical nba_pmf_delivery.yml not found in .github/workflows/"
    )
    assert offenders == [], (
        "Multiple automatic NBA PMF delivery writers detected. Only "
        "nba_pmf_delivery.yml may trigger delivery work automatically "
        f"(schedule or workflow_run). Offenders: {offenders}"
    )


def test_only_canonical_nba_pmf_delivery_workflow_has_schedule_trigger():
    """At-most-one scheduled NBA-PMF delivery writer.

    The canonical ``nba_pmf_delivery.yml`` is the only workflow under
    ``.github/workflows/`` whose ``name:`` starts with
    ``NBA PMF Delivery`` and whose triggers include ``schedule:``.
    Regression-lock against the parent audit's
    TWO_SCHEDULED_WRITERS_DETECTED conclusion (2026-05-20). Prevents
    accidental reintroduction of dual scheduled writers under the
    ``NBA PMF Delivery`` display-name family.
    """

    wf_dir = REPO_ROOT / ".github" / "workflows"
    offenders: list[str] = []
    canonical_seen = False
    for wf_path in sorted(wf_dir.glob("*.yml")):
        text = wf_path.read_text(encoding="utf-8")
        # Pre-screen by file text: only candidate workflows whose
        # ``name:`` line starts with the "NBA PMF Delivery" prefix
        # participate in this cross-workflow check. This keeps the
        # test robust against unrelated workflows whose YAML bodies
        # embed inline Python heredocs that PyYAML's strict
        # ``safe_load`` rejects (see e.g.
        # ``derek_live_game_snapshots.yml``); GitHub Actions parses
        # them fine, but they are out of scope here.
        if not any(
            line.startswith('name: NBA PMF Delivery')
            or line.startswith('name: "NBA PMF Delivery')
            or line.startswith("name: 'NBA PMF Delivery")
            for line in text.splitlines()
        ):
            continue
        data = yaml.safe_load(text)
        assert isinstance(data, dict), (
            f"{wf_path.name} declares an NBA-PMF-Delivery `name:` but is "
            "not a parseable mapping"
        )
        # PyYAML 1.1 parses bare ``on:`` as the boolean True key.
        triggers = data.get("on") if "on" in data else data.get(True)
        if isinstance(triggers, dict):
            keys = set(triggers.keys())
        elif isinstance(triggers, list):
            keys = set(triggers)
        else:
            keys = {triggers}
        has_schedule = "schedule" in keys
        if wf_path.name == "nba_pmf_delivery.yml":
            canonical_seen = True
            assert has_schedule, (
                "Canonical nba_pmf_delivery.yml must retain its "
                "`schedule:` trigger as the sole scheduled NBA PMF "
                "delivery writer."
            )
        else:
            if has_schedule:
                offenders.append(wf_path.name)
    assert canonical_seen, (
        "Canonical nba_pmf_delivery.yml not found in .github/workflows/"
    )
    assert offenders == [], (
        "Multiple scheduled NBA PMF delivery writers detected. Only "
        "nba_pmf_delivery.yml may schedule delivery work. Offenders: "
        f"{offenders}"
    )


def test_cleanup_rebase_state_defined_in_every_patched_step(workflow_text):
    """The helper definitions must appear once per patched step body.

    Each step runs in its own subshell, so the helpers must be redefined
    inside each affected ``run:`` block. We expect exactly as many helper
    definitions as patched self-commit steps.
    """

    text = workflow_text
    expected_blocks = [
        "Commit refreshed player stats",
        "Commit training/calibration artifacts",
        "Commit Phase 8 artifacts",
        "Commit Phase 13 artifacts",
        "Commit prediction artifacts + automation health",
        "Build delivery index and commit delivery outputs",
        "Build delivery index and commit after-game outputs",
    ]
    n = len(expected_blocks)

    cleanup_defs = text.count("cleanup_rebase_state() {")
    sync_defs = text.count("sync_and_push() {")
    assert cleanup_defs == n, (
        f"expected {n} cleanup_rebase_state definitions (one per patched "
        f"step); found {cleanup_defs}"
    )
    assert sync_defs == n, (
        f"expected {n} sync_and_push definitions (one per patched step); "
        f"found {sync_defs}"
    )
