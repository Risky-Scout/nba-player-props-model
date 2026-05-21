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


def test_daily_pmf_delivery_workflow_is_manual_only(workflow_text):
    """Legacy daily pipeline must be manual-only.

    The canonical ``nba_pmf_delivery.yml`` is the only AUTOMATIC writer
    of ``deliveries/``, ``public_export/``, and related artifacts. The
    legacy ``daily_pmf_delivery.yml`` retains ``workflow_dispatch`` for
    manual backfills via the Actions UI, but neither ``schedule:`` nor
    ``workflow_run:`` may fire it automatically — both would silently
    recreate the duplicate-writer regression the parent audit
    (TWO_SCHEDULED_WRITERS_DETECTED, 2026-05-20) just fixed.
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
        "canonical nba_pmf_delivery.yml may be an automatic writer. "
        f"Found triggers: {sorted(map(str, trigger_keys))}"
    )
    assert "workflow_run" not in trigger_keys, (
        "daily_pmf_delivery.yml has a `workflow_run:` trigger; the "
        "workflow must be manual-only. workflow_run would silently "
        "recreate the duplicate-writer regression every time the "
        "upstream chain workflow completes on main. "
        f"Found triggers: {sorted(map(str, trigger_keys))}"
    )
    assert "workflow_dispatch" in trigger_keys, (
        "workflow_dispatch must remain available for manual backfills; "
        f"found triggers: {sorted(map(str, trigger_keys))}"
    )
    assert trigger_keys == {"workflow_dispatch"}, (
        "daily_pmf_delivery.yml `on:` must contain EXACTLY one key, "
        "`workflow_dispatch`. Any additional trigger key would either "
        "reintroduce automatic firing (schedule, workflow_run) or "
        "fire on push/PR/etc. and re-create the duplicate-writer "
        f"regression. Found: {sorted(map(str, trigger_keys))}"
    )


def test_daily_pmf_delivery_workflow_dispatch_inputs_preserved(workflow_text):
    """Manual-only workflow MUST retain its workflow_dispatch inputs.

    Operators rely on manual backfills via the GitHub Actions UI for
    all delivery modes (morning, woo_morning_monetization, ...,
    after_game). Removing or renaming any input would silently
    regress operator workflows. This test pins the exact input
    schema captured at the time of the manual-only migration.
    """

    wf = yaml.safe_load(workflow_text)
    triggers = wf.get("on") if "on" in wf else wf.get(True)
    assert isinstance(triggers, dict), (
        f"unexpected on: shape {type(triggers).__name__}"
    )
    dispatch = triggers.get("workflow_dispatch")
    assert isinstance(dispatch, dict), (
        f"workflow_dispatch missing or malformed: {dispatch!r}"
    )
    inputs = dispatch.get("inputs") or {}
    expected_input_names = {"mode", "delivery_date", "run_predict", "force_run"}
    assert set(inputs.keys()) == expected_input_names, (
        f"workflow_dispatch inputs changed; expected "
        f"{sorted(expected_input_names)}, got {sorted(inputs.keys())}"
    )
    # ``mode`` must remain a choice covering all delivery modes
    # operators dispatch by hand from the Actions UI.
    mode = inputs["mode"]
    assert mode.get("type") == "choice", (
        f"`mode` input must be type=choice; got {mode.get('type')!r}"
    )
    mode_options = set(mode.get("options") or [])
    required_mode_options = {
        "morning",
        "woo_morning_monetization",
        "woo_afternoon_refresh",
        "derek_near_lineup",
        "close_lock",
        "after_game",
        "full_day",
    }
    missing = required_mode_options - mode_options
    assert not missing, (
        f"`mode` input lost required choices: {sorted(missing)}; "
        f"current options: {sorted(mode_options)}"
    )
