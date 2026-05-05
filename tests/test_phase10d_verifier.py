"""Phase 13AN regression tests for the Phase 10D / 10D.2 overlay scanner.

The scanner used to substring-match ``phase10d`` against any string in a
manifest, with weak negation handling that misfired on legitimate gate
status names like ``no_phase10d_overlays_referenced``. The fix replaces
that with a structural scan that only flags real overlay key names and
real overlay artifact paths.
"""

from __future__ import annotations

from nba_props_model.training_automation import (
    SAFE_OVERLAY_REFERENCE_STRINGS,
    scan_for_forbidden_overlay_tokens,
)


def test_safe_gate_status_strings_pass() -> None:
    """Manifests that announce overlay-absence MUST not trip the scanner."""
    safe_payload = {
        "as_of_date": "2026-05-04",
        "phase10d_overlays_in_use": False,
        "promotion_summary": {
            "from_version": "challenger-2026-04-30",
            "promoted": False,
            "reason": "halted_pending_upstream_data",
        },
        "checks": [
            {"name": "no_phase10d_overlays_referenced", "passed": True},
            {"name": "no_phase10d_overlays_in_manifests", "passed": True},
            {"name": "workflow_no_phase10d_overlays", "passed": True},
        ],
    }
    hits = scan_for_forbidden_overlay_tokens(safe_payload)
    assert hits == [], f"safe payload incorrectly flagged: {hits}"


def test_real_overlay_path_fails() -> None:
    bad_payload = {
        "minutes_overlay": "artifacts/phase10d/foo.parquet",
    }
    hits = scan_for_forbidden_overlay_tokens(bad_payload)
    assert hits, "real overlay path was missed"
    assert any("phase10d" in h.lower() for h in hits)


def test_real_overlay_key_fails() -> None:
    bad_payload = {
        "phase10d_overlay_path": "/some/path",
    }
    hits = scan_for_forbidden_overlay_tokens(bad_payload)
    assert hits, "real overlay key was missed"
    assert any("phase10d_overlay_path" in h for h in hits)


def test_phase10d2_path_fails() -> None:
    bad_payload = {
        "calibration_overlay": "phase10d2_overlays/foo.json",
    }
    hits = scan_for_forbidden_overlay_tokens(bad_payload)
    assert hits


def test_safe_string_in_value_does_not_match_path() -> None:
    """Values that contain a safe gate name must not trip overlay-path scan."""
    safe = {
        "status": "no_phase10d_overlays_referenced",
        "verifier_log": "workflow_no_phase10d_overlays passed",
    }
    hits = scan_for_forbidden_overlay_tokens(safe)
    assert hits == []


def test_allowlist_is_lowercase_and_complete() -> None:
    expected = {
        "no_phase10d_overlays_referenced",
        "no_phase10d_overlays_in_manifests",
        "phase10d_overlays_in_use",
        "workflow_no_phase10d_overlays",
        "no_phase10d_overlays",
    }
    assert SAFE_OVERLAY_REFERENCE_STRINGS == expected
