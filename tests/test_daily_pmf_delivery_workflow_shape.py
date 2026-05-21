"""Lock-in: ``.github/workflows/daily_pmf_delivery.yml`` must preserve
the ``workflow_dispatch`` entry-point (so morning monetization can be
manually re-run) and must ship the core delivery bundle even when the
WoO dashboard step later fails. Run 25953498606 surfaced a real risk
that workflow edits would silently disable manual dispatch — that risk
is what this test guards against."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "daily_pmf_delivery.yml"
NEW_WORKFLOW = (
    Path(__file__).resolve().parent.parent
    / ".github"
    / "workflows"
    / "nba_pmf_delivery.yml"
)


@pytest.fixture(scope="module")
def workflow_text() -> str:
    assert WORKFLOW.is_file(), f"workflow missing: {WORKFLOW}"
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow() -> dict:
    text = WORKFLOW.read_text(encoding="utf-8")
    return yaml.safe_load(text)


@pytest.fixture(scope="module")
def new_workflow_text() -> str:
    assert NEW_WORKFLOW.is_file(), f"workflow missing: {NEW_WORKFLOW}"
    return NEW_WORKFLOW.read_text(encoding="utf-8")


def test_workflow_dispatch_block_is_present(workflow_text):
    assert "workflow_dispatch:" in workflow_text


def test_workflow_dispatch_inputs_present(workflow_text):
    for needle in ("mode:", "delivery_date:", "run_predict:", "force_run:"):
        assert needle in workflow_text, f"missing input: {needle}"


def test_woo_morning_modes_listed(workflow_text):
    assert "woo_morning_monetization" in workflow_text


def test_core_delivery_upload_step_runs_always(workflow_text):
    """Core upload must use ``always()`` + ``run_delivery == 'true'``
    so it survives a downstream WoO dashboard / render-contract
    failure."""
    assert "Upload core delivery bundle after pipeline attempt" in workflow_text
    # The step's ``if:`` predicate must enable always(); the marker line
    # below confirms the bundle is emitted on every run path the
    # delivery gate opened.
    assert "always() && steps.delivery_flags.outputs.run_delivery == 'true'" in workflow_text
    assert "CORE_DELIVERY_ARTIFACT_UPLOAD_PASS" in workflow_text


def test_core_delivery_upload_uses_correct_artifact_name(workflow_text):
    assert (
        "name: daily-pmf-core-delivery-${{ steps.d.outputs.date }}-${{ github.run_id }}"
        in workflow_text
    )


def test_core_delivery_upload_includes_required_paths(workflow_text):
    for path in (
        "deliveries/${{ steps.d.outputs.date }}/canonical_source/",
        "deliveries/${{ steps.d.outputs.date }}/wizard_of_odds/",
        "public_export/wizard_of_odds/",
        "predictions/stat_grid_${{ steps.d.outputs.date }}.parquet",
        "predictions/all_props_${{ steps.d.outputs.date }}.parquet",
        "predictions/pmf_research.json",
        "artifacts/minutes_predictions/${{ steps.d.outputs.date }}/",
        "artifacts/current_market_signal/${{ steps.d.outputs.date }}.json",
        "data/freshness_manifest/${{ steps.d.outputs.date }}.json",
    ):
        assert path in workflow_text, f"missing path in core upload: {path}"


def test_success_gated_delivery_bundle_still_present(workflow_text):
    """The pre-existing success-gated upload (full bundle) must stay —
    the core upload is additive, never a replacement."""
    assert "Upload daily PMF delivery bundle" in workflow_text
    assert "DELIVERY_ARTIFACT_UPLOAD_PASS" in workflow_text


def test_forced_manual_assertion_marker_unchanged(workflow_text):
    """The forced-manual outputs assertion path must keep emitting the
    pass marker the workflow Definition-of-Done gates on."""
    assert "FORCED_MANUAL_DELIVERY_RUN_ASSERTION_PASS" in workflow_text


def test_core_upload_is_ordered_before_woo_dashboard_step(workflow_text):
    """Core upload must run BEFORE the WoO dashboard step, so that a
    later WoO render-contract failure cannot prevent the core bundle
    from being uploaded."""
    core_idx = workflow_text.find("Upload core delivery bundle after pipeline attempt")
    woo_idx = workflow_text.find("Phase 13AM WoO new pipeline (publish/build/verify)")
    assert core_idx != -1
    assert woo_idx != -1
    assert core_idx < woo_idx, (
        "core upload must precede WoO dashboard step so it captures the bundle "
        "before any render-contract failure"
    )


# ── 4-decimal rounding regression guard ─────────────────────────────
#
# Regression context: FINAL_DELIVERY_AUDIT_FAIL on 2026-05-20 was traced to
# this legacy workflow overwriting the new ``nba_pmf_delivery.yml``
# workflow's already-rounded ``wizard_of_odds/publishable_edges.csv`` with
# long-decimal values. The new workflow's commit (48465d70) emitted the
# CSV with 4dp values; subsequent legacy-workflow commits ("daily delivery
# champion metadata 2026-05-20 (derek_near_lineup)") re-committed the file
# with full precision because the legacy workflow did not invoke
# ``scripts/round_delivery_csv_numeric_display.py`` before commit/push.
#
# Each "Stage and commit" step in this workflow runs (in order, inside
# one shell):
#   stamp_delivery_champion_metadata.py
#   verify_derek_woo_champion_dependency.py
#   strip_empty_delivery_columns.py --date <date> --write
#   round_delivery_csv_numeric_display.py --date <date> --places 4 --write
#       --preserve derek_forward_feed/derek_unique_props_summary.csv
#   git add deliveries/<date> ...
#   git commit ...
#   git pull --rebase ... && git push
# The rounding call MUST appear AFTER strip and BEFORE the deliveries/
# git-add line, byte-for-byte matching the new workflow's invocation.


# Step names that house the post-pipeline strip + commit shell block in
# the legacy workflow's per-mode jobs. Each step body has its own copy of
# the strip/round/git-add sequence (one per mode: morning,
# woo_morning_monetization, woo_afternoon_refresh, derek_near_lineup,
# close_lock, after_game).
_LEGACY_COMMIT_STEP_NAMES = {
    "Stage and commit approved files",
    "Stage and commit",
}


def _commit_step_run_bodies(workflow: dict) -> list[tuple[str, str, str]]:
    """Return (job_name, step_name, run_body) for each commit step."""

    bodies: list[tuple[str, str, str]] = []
    jobs = workflow.get("jobs", {}) or {}
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps", []) or []:
            if not isinstance(step, dict):
                continue
            name = step.get("name") or ""
            if name not in _LEGACY_COMMIT_STEP_NAMES:
                continue
            run_body = step.get("run") or ""
            if "git add deliveries/" not in run_body:
                continue
            bodies.append((job_name, name, run_body))
    return bodies


def test_legacy_workflow_has_six_post_pipeline_commit_steps(workflow):
    """Sanity: each per-mode job (morning, woo_morning_monetization,
    woo_afternoon_refresh, derek_near_lineup, close_lock, after_game)
    contributes exactly one commit step that we patch."""

    bodies = _commit_step_run_bodies(workflow)
    job_names = sorted(b[0] for b in bodies)
    assert job_names == [
        "after_game",
        "close_lock",
        "derek_near_lineup",
        "morning",
        "woo_afternoon_refresh",
        "woo_morning_monetization",
    ], f"unexpected commit-step job set: {job_names}"


def test_legacy_workflow_invokes_rounding_script_in_every_commit_step(
    workflow,
):
    """Every per-mode commit step must call the 4dp rounding script
    AFTER ``strip_empty_delivery_columns.py`` and BEFORE the
    ``git add deliveries/`` line in the same run body. This is the
    minimum-viable fix for FINAL_DELIVERY_AUDIT_FAIL on 2026-05-20:
    the legacy workflow was overwriting the new workflow's already-
    rounded ``wizard_of_odds/publishable_edges.csv`` with long-decimal
    values because no rounding step existed before commit/push.
    """

    bodies = _commit_step_run_bodies(workflow)
    assert bodies, "no commit steps found; locator broken"

    for job_name, step_name, run_body in bodies:
        strip_idx = run_body.find("scripts/strip_empty_delivery_columns.py")
        round_idx = run_body.find("scripts/round_delivery_csv_numeric_display.py")
        git_add_idx = run_body.find("git add deliveries/")
        assert strip_idx != -1, (
            f"{job_name}/{step_name}: strip step missing from commit body"
        )
        assert round_idx != -1, (
            f"{job_name}/{step_name}: round_delivery_csv_numeric_display.py "
            f"missing from commit body — see PR fixing FINAL_DELIVERY_AUDIT_FAIL"
        )
        assert git_add_idx != -1, (
            f"{job_name}/{step_name}: git add deliveries/ missing from commit body"
        )
        assert strip_idx < round_idx < git_add_idx, (
            f"{job_name}/{step_name}: rounding step out of order; "
            f"strip={strip_idx} round={round_idx} git_add={git_add_idx}"
        )


def test_legacy_workflow_rounding_invocation_matches_new_workflow_byte_for_byte(
    workflow,
):
    """Each rounding invocation must use ``--places 4 --write`` and the
    Derek unique-summary preserve flag — byte-for-byte aligned with the
    new ``nba_pmf_delivery.yml`` ``delivery_build`` invocation. This
    guards against accidental flag drift between the two workflows
    while both coexist."""

    bodies = _commit_step_run_bodies(workflow)
    assert bodies
    for job_name, step_name, run_body in bodies:
        for needle in (
            "scripts/round_delivery_csv_numeric_display.py",
            "--places 4",
            "--write",
            "--preserve derek_forward_feed/derek_unique_props_summary.csv",
        ):
            assert needle in run_body, (
                f"{job_name}/{step_name}: rounding invocation missing {needle!r}"
            )


def test_new_workflow_still_invokes_rounding_script_before_commit(
    new_workflow_text,
):
    """Companion regression-lock: the new ``nba_pmf_delivery.yml``
    ``delivery_build`` job must continue to invoke the 4dp rounding
    step. The strict in-step ordering is already covered by
    ``tests/test_nba_pmf_delivery_workflow_shape.py::
    test_delivery_csv_rounding_runs_in_correct_post_processing_order``;
    this test only ensures the call is not removed in passing."""

    assert "scripts/round_delivery_csv_numeric_display.py" in new_workflow_text
    assert "--places 4" in new_workflow_text
    assert (
        "--preserve derek_forward_feed/derek_unique_props_summary.csv"
        in new_workflow_text
    )
