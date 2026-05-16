"""Run 25956457781 surfaced the daily delivery's `Stage and commit
approved files` step hard-failing on champion freshness when the
champion was 14.79 days old vs the historical default of `max=14`.

The verifier now uses a two-tier model:
    - age <= --max-stale-days  → silent pass (existing behavior)
    - age <= --fail-stale-days → STALE_CHAMPION_WARNING + pass
    - age >  --fail-stale-days → hard fail

This preserves the cadence signal without blocking a forced morning
delivery from being auto-committed. Required Fix 7 in the user's spec
covers the broader nightly retrain cadence audit; this is the narrow
gate adjustment so the morning workflow doesn't false-fail."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "verify_derek_woo_champion_dependency",
    REPO / "scripts" / "verify_derek_woo_champion_dependency.py",
)
mod = importlib.util.module_from_spec(SPEC)
# Register before exec so dataclasses on Python 3.9 can introspect.
sys.modules["verify_derek_woo_champion_dependency"] = mod
SPEC.loader.exec_module(mod)


def _build_report(max_stale=14, fail_stale=30):
    return mod.DependencyReport(
        generated_at_utc="2026-05-16T07:50:00Z",
        code_commit="deadbeef",
        max_stale_days=max_stale,
        fail_stale_days=fail_stale,
    )


def _check(report, pointer):
    mod.check_champion_freshness(report, pointer)
    return report


# ── three tiers ────────────────────────────────────────────────────


def test_fresh_champion_passes_silently(monkeypatch):
    """Within the soft threshold: pass, no warning."""
    monkeypatch.setattr(
        mod,
        "utcnow",
        lambda: mod.dt.datetime(2026, 5, 16, 12, 0, 0, tzinfo=mod.dt.timezone.utc),
    )
    report = _build_report(max_stale=14, fail_stale=30)
    pointer = {"promoted_at_utc": "2026-05-10T12:00:00Z"}  # 6 days old
    _check(report, pointer)
    [c] = report.checks
    assert c.name == "champion_freshness"
    assert c.passed is True
    assert report.warnings == []


def test_stale_champion_warns_but_passes(monkeypatch):
    """Run 25956457781 regression: 14.79 days old must NOT hard-fail."""
    monkeypatch.setattr(
        mod,
        "utcnow",
        lambda: mod.dt.datetime(2026, 5, 16, 7, 50, 0, tzinfo=mod.dt.timezone.utc),
    )
    report = _build_report(max_stale=14, fail_stale=30)
    pointer = {"promoted_at_utc": "2026-05-01T13:00:00Z"}  # ~14.79 days
    _check(report, pointer)
    [c] = report.checks
    assert c.name == "champion_freshness"
    assert c.passed is True, c.detail
    assert report.warnings, "expected STALE_CHAMPION_WARNING"
    [w] = report.warnings
    assert w.name == "champion_freshness_stale_warning"
    assert "age_days" in w.detail
    assert "non-blocking" in w.detail


def test_extremely_stale_champion_hard_fails(monkeypatch):
    monkeypatch.setattr(
        mod,
        "utcnow",
        lambda: mod.dt.datetime(2026, 5, 16, 12, 0, 0, tzinfo=mod.dt.timezone.utc),
    )
    report = _build_report(max_stale=14, fail_stale=30)
    pointer = {"promoted_at_utc": "2026-04-01T12:00:00Z"}  # 45 days
    _check(report, pointer)
    [c] = report.checks
    assert c.name == "champion_freshness"
    assert c.passed is False
    assert "hard-fail threshold exceeded" in c.detail
    assert not report.warnings


def test_unparseable_promoted_at_still_hard_fails(monkeypatch):
    report = _build_report()
    pointer = {"promoted_at_utc": "not-a-real-timestamp"}
    _check(report, pointer)
    [c] = report.checks
    assert c.passed is False
    assert "no parseable promoted_at_utc" in c.detail


def test_missing_promoted_at_still_hard_fails(monkeypatch):
    report = _build_report()
    _check(report, {})
    [c] = report.checks
    assert c.passed is False


# ── serialization includes the new thresholds and warnings ─────────


def test_report_serialization_carries_fail_stale_days(monkeypatch):
    monkeypatch.setattr(
        mod,
        "utcnow",
        lambda: mod.dt.datetime(2026, 5, 16, 7, 50, 0, tzinfo=mod.dt.timezone.utc),
    )
    report = _build_report(max_stale=14, fail_stale=30)
    _check(report, {"promoted_at_utc": "2026-05-01T13:00:00Z"})
    payload = report.to_dict()
    assert payload["max_stale_days"] == 14
    assert payload["fail_stale_days"] == 30
    assert payload["passed"] is True
    assert any(w["name"] == "champion_freshness_stale_warning" for w in payload["warnings"])


# ── misconfiguration guard ─────────────────────────────────────────


def test_fail_stale_below_max_stale_is_a_structural_error(tmp_path, monkeypatch, capsys):
    """If an operator passes --fail-stale-days < --max-stale-days,
    fail loudly with exit code 2 — silently swapping would mask the
    misconfiguration."""
    monkeypatch.setattr(mod.sys, "argv", ["verify", "--max-stale-days", "30", "--fail-stale-days", "10"])
    rc = mod.main([
        "--max-stale-days",
        "30",
        "--fail-stale-days",
        "10",
    ])
    assert rc == 2
