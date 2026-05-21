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


@pytest.fixture(scope="module")
def workflow_text() -> str:
    assert WORKFLOW.is_file(), f"workflow missing: {WORKFLOW}"
    return WORKFLOW.read_text(encoding="utf-8")


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


def test_daily_pmf_delivery_workflow_has_no_schedule_trigger(workflow_text):
    """Legacy daily pipeline must not be a scheduled writer.

    The canonical ``nba_pmf_delivery.yml`` is the only scheduled writer
    of ``deliveries/``, ``public_export/``, and related artifacts. The
    legacy ``daily_pmf_delivery.yml`` is retained for manual backfills
    (``workflow_dispatch``) and as a ``workflow_run`` consumer only.
    Regression-lock against the parent audit's
    TWO_SCHEDULED_WRITERS_DETECTED conclusion (2026-05-20).
    """

    wf = yaml.safe_load(workflow_text)
    # PyYAML 1.1 parses the bare YAML key ``on:`` as the Python boolean
    # ``True`` because YAML 1.1 treats ``on`` as a truthy alias. Reach
    # under either key so the test stays robust if pyyaml is later
    # bumped to a 1.2-compliant loader.
    triggers = wf.get("on") if "on" in wf else wf.get(True)
    if isinstance(triggers, list):
        trigger_keys = set(triggers)
    elif isinstance(triggers, dict):
        trigger_keys = set(triggers.keys())
    else:
        trigger_keys = {triggers}
    assert "schedule" not in trigger_keys, (
        "daily_pmf_delivery.yml has a `schedule:` trigger; only the "
        "canonical nba_pmf_delivery.yml may be a scheduled writer. "
        f"Found triggers: {sorted(map(str, trigger_keys))}"
    )
    assert "workflow_dispatch" in trigger_keys, (
        "workflow_dispatch must remain available for manual backfills; "
        f"found triggers: {sorted(map(str, trigger_keys))}"
    )
    assert "workflow_run" in trigger_keys, (
        "workflow_run chain must remain available; "
        f"found triggers: {sorted(map(str, trigger_keys))}"
    )
