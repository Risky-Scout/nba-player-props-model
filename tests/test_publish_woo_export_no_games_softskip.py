"""publish_woo_public_export.py — strict no-games soft-skip tests.

The Phase 13AM WoO publish step hard-failed on a confirmed no-games
slate because its post-publish hook ran
``scripts/build_woo_pmf_research_from_canonical.py`` against an empty
canonical PMF surface. The strict rule: when the dated delivery
manifest carries ``no_games_slate: true`` (which the orchestrator
only writes after a dual predict + BDL schedule confirmation), the
PMF-research builder must skip cleanly.

These tests exercise the helpers directly so they stay hermetic.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def _load_publish_module(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "_publish_woo_public_export_under_test",
        SCRIPTS / "publish_woo_public_export.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_full_manifest(
    repo: Path,
    date: str,
    *,
    no_games_slate: bool = True,
    confirmed_no_games_slate: bool = True,
    reason: str = "no_games_slate",
    market_superiority_evaluated: bool = False,
    derek_forward_feed_expected: bool = False,
) -> Path:
    p = repo / "deliveries" / date / "manifest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "delivery_date": date,
        "no_games_slate": no_games_slate,
        "confirmed_no_games_slate": confirmed_no_games_slate,
        "reason": reason,
        "market_superiority_evaluated": market_superiority_evaluated,
        "derek_forward_feed_expected": derek_forward_feed_expected,
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


def test_no_games_helper_true_when_full_4_flag_manifest(tmp_path, monkeypatch):
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16")
    assert mod._m8_6o_delivery_manifest_confirmed_no_games_slate("2026-05-16") is True


def test_no_games_helper_false_when_manifest_missing(tmp_path, monkeypatch):
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    assert mod._m8_6o_delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_no_games_helper_false_when_no_games_slate_false(tmp_path, monkeypatch):
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", no_games_slate=False)
    assert mod._m8_6o_delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_no_games_helper_false_when_confirmed_flag_false(tmp_path, monkeypatch):
    """Strict 4-flag rule: missing confirmed_no_games_slate=true keeps
    the gate closed even if no_games_slate=true is set."""
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    assert mod._m8_6o_delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_no_games_helper_false_when_market_superiority_true(tmp_path, monkeypatch):
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", market_superiority_evaluated=True)
    assert mod._m8_6o_delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_no_games_helper_false_when_derek_feed_expected_true(tmp_path, monkeypatch):
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", derek_forward_feed_expected=True)
    assert mod._m8_6o_delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_no_games_helper_false_when_reason_differs(tmp_path, monkeypatch):
    """Even with the boolean flags set, reason must say no_games_slate.
    Defensive against partial / stale manifests."""
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", reason="something_else")
    assert mod._m8_6o_delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_no_games_helper_false_when_manifest_corrupt(tmp_path, monkeypatch):
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    p = tmp_path / "deliveries" / "2026-05-16" / "manifest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not json {{", encoding="utf-8")
    assert mod._m8_6o_delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_no_games_helper_false_when_date_none(tmp_path, monkeypatch):
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    assert mod._m8_6o_delivery_manifest_confirmed_no_games_slate(None) is False


def test_pmf_research_builder_hook_soft_skips_on_confirmed_no_games_slate(
    tmp_path, monkeypatch, capsys
):
    """The hook MUST NOT subprocess into the canonical PMF research
    builder when the delivery manifest is a confirmed no-games slate
    (all 4 strict flags set); that builder hard-fails on a row-empty
    PMF parquet."""
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16")
    (tmp_path / "scripts").mkdir(exist_ok=True)
    (tmp_path / "scripts" / "build_woo_pmf_research_from_canonical.py").write_text(
        "raise SystemExit('should not be invoked on no-games slate')\n",
        encoding="utf-8",
    )

    invoked: list[list[str]] = []
    import subprocess as _subprocess

    def fake_run(cmd, check=True, **kwargs):
        invoked.append(cmd)
        class _R: returncode = 0
        return _R()
    monkeypatch.setattr(_subprocess, "run", fake_run, raising=True)
    monkeypatch.setattr(sys, "argv", ["publish_woo_public_export.py", "--date", "2026-05-16"], raising=True)

    mod._m8_6o_run_canonical_pmf_research_builder()
    out = capsys.readouterr().out
    assert "M8_6O_CANONICAL_PMF_RESEARCH_BUILDER_SOFT_SKIP_NO_GAMES_SLATE" in out
    assert "date=2026-05-16" in out
    assert "gate=no_games_slate+confirmed_no_games_slate" in out
    assert invoked == [], "subprocess builder must NOT be invoked on no-games slate"


def test_pmf_research_builder_hook_runs_on_partial_4_flag_manifest(
    tmp_path, monkeypatch
):
    """A manifest missing any of the 4 strict flags must NOT trigger
    soft-skip — the subprocess hook runs normally so games-bearing
    slates still hard-fail on missing canonical PMF rows."""
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    (tmp_path / "scripts").mkdir(exist_ok=True)
    (tmp_path / "scripts" / "build_woo_pmf_research_from_canonical.py").write_text(
        "# stub\n", encoding="utf-8"
    )

    invoked: list[list[str]] = []
    import subprocess as _subprocess

    def fake_run(cmd, check=True, **kwargs):
        invoked.append(cmd)
        class _R: returncode = 0
        return _R()
    monkeypatch.setattr(_subprocess, "run", fake_run, raising=True)
    monkeypatch.setattr(sys, "argv",
                        ["publish_woo_public_export.py", "--date", "2026-05-16"],
                        raising=True)

    mod._m8_6o_run_canonical_pmf_research_builder()
    assert invoked, "partial 4-flag manifest must NOT trigger soft-skip"


def test_pmf_research_builder_hook_runs_normally_when_no_manifest(
    tmp_path, monkeypatch, capsys
):
    """Without any manifest, the hook must subprocess into the real
    builder (no silent skip on a games-bearing slate)."""
    mod = _load_publish_module(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "scripts").mkdir(exist_ok=True)
    builder = tmp_path / "scripts" / "build_woo_pmf_research_from_canonical.py"
    builder.write_text("# stub\n", encoding="utf-8")

    invoked: list[list[str]] = []
    import subprocess as _subprocess

    def fake_run(cmd, check=True, **kwargs):
        invoked.append(cmd)
        class _R: returncode = 0
        return _R()
    monkeypatch.setattr(_subprocess, "run", fake_run, raising=True)
    monkeypatch.setattr(sys, "argv", ["publish_woo_public_export.py", "--date", "2026-05-16"], raising=True)

    mod._m8_6o_run_canonical_pmf_research_builder()
    out = capsys.readouterr().out
    assert "M8_6O_CANONICAL_PMF_RESEARCH_BUILDER_HOOK_PASS" in out
    assert invoked, "builder subprocess must run on games-bearing slates"
