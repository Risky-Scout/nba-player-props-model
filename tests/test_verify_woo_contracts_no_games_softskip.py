"""verify_woo_dashboard_render_contract / verify_woo_public_export_contract —
strict no-games soft-skip tests.

Both WoO post-publish verifiers must soft-skip cleanly on a confirmed
no-games slate (delivery manifest carries ``no_games_slate: true`` AND
``reason: no_games_slate``) so the strict orchestrator short-circuit
does not get re-broken by a downstream zero-rows check. Any other
manifest shape (missing flag, false flag, missing manifest, corrupt
manifest, mismatched reason) keeps the original hard-fail behavior
intact — a games-bearing slate with zero rows is still a regression.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def _load_module(monkeypatch, script_name: str, mod_name: str):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(mod_name, SCRIPTS / script_name)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
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
    """Seed the full strict 4-flag confirmed no-games manifest by
    default. Tests can override individual fields to assert
    partial-flag manifests do NOT trigger soft-skip."""
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


# ---- render contract ------------------------------------------------------


def test_render_contract_helper_true_when_full_4_flag_manifest(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test")
    _write_full_manifest(tmp_path, "2026-05-16")
    assert mod._delivery_manifest_confirmed_no_games_slate(tmp_path, "2026-05-16") is True


def test_render_contract_helper_false_without_manifest(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_2")
    assert mod._delivery_manifest_confirmed_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_helper_false_when_no_games_slate_false(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_3")
    _write_full_manifest(tmp_path, "2026-05-16", no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_helper_false_when_confirmed_flag_false(tmp_path, monkeypatch):
    """Strict 4-flag rule: missing confirmed_no_games_slate=true keeps
    the gate closed even if no_games_slate=true is set."""
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_3b")
    _write_full_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_helper_false_when_market_superiority_true(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_3c")
    _write_full_manifest(tmp_path, "2026-05-16", market_superiority_evaluated=True)
    assert mod._delivery_manifest_confirmed_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_helper_false_when_derek_feed_expected_true(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_3d")
    _write_full_manifest(tmp_path, "2026-05-16", derek_forward_feed_expected=True)
    assert mod._delivery_manifest_confirmed_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_helper_false_when_reason_differs(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_4")
    _write_full_manifest(tmp_path, "2026-05-16", reason="something_else")
    assert mod._delivery_manifest_confirmed_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_helper_false_when_manifest_corrupt(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_5")
    p = tmp_path / "deliveries" / "2026-05-16" / "manifest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not json {{", encoding="utf-8")
    assert mod._delivery_manifest_confirmed_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_main_soft_skips_on_confirmed_no_games(tmp_path, monkeypatch, capsys):
    """End-to-end: the script's main() must short-circuit BEFORE
    checking any HTML/JSON artifacts when the manifest declares the
    full strict 4-flag confirmed no-games slate."""
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_main_under_test")
    monkeypatch.setattr(mod, "_delivery_manifest_confirmed_no_games_slate",
                        lambda repo, date: True, raising=True)
    monkeypatch.setattr(sys, "argv",
                        ["verify_woo_dashboard_render_contract.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "WOO_DASHBOARD_RENDER_CONTRACT_SOFT_SKIP_NO_GAMES_SLATE" in out
    assert "gate=no_games_slate+confirmed_no_games_slate" in out


def test_render_contract_main_does_not_soft_skip_without_signal(tmp_path, monkeypatch):
    """No no-games signal → main() must run the normal validation
    flow."""
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_main_no_signal")
    monkeypatch.setattr(mod, "_delivery_manifest_confirmed_no_games_slate",
                        lambda repo, date: False, raising=True)
    monkeypatch.setattr(sys, "argv",
                        ["verify_woo_dashboard_render_contract.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    assert rc != 0


# ---- public export contract ----------------------------------------------


def _make_export_module(monkeypatch, repo_root: Path):
    mod = _load_module(monkeypatch, "verify_woo_public_export_contract.py",
                       "_public_export_under_test")
    monkeypatch.setattr(mod, "REPO_ROOT", repo_root, raising=True)
    return mod


def test_export_contract_helper_true_when_full_4_flag_manifest(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16")
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is True


def test_export_contract_helper_false_without_manifest(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_export_contract_helper_false_when_no_games_slate_false(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_export_contract_helper_false_when_confirmed_flag_false(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_export_contract_helper_false_when_market_superiority_true(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", market_superiority_evaluated=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_export_contract_helper_false_when_derek_feed_expected_true(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", derek_forward_feed_expected=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_export_contract_helper_false_when_reason_differs(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    _write_full_manifest(tmp_path, "2026-05-16", reason="something_else")
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_export_contract_main_soft_skips_on_confirmed_no_games(tmp_path, monkeypatch, capsys):
    mod = _make_export_module(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "_delivery_manifest_confirmed_no_games_slate",
                        lambda date: True, raising=True)
    rc = mod.main(["--date", "2026-05-16"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "WOO_PUBLIC_EXPORT_CONTRACT_SOFT_SKIP_NO_GAMES_SLATE" in out
    assert "gate=no_games_slate+confirmed_no_games_slate" in out


def test_export_contract_main_does_not_soft_skip_without_signal(tmp_path, monkeypatch):
    """When the helper returns False the script must run normally."""
    mod = _make_export_module(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "_delivery_manifest_confirmed_no_games_slate",
                        lambda date: False, raising=True)
    rc = mod.main(["--date", "2026-05-16"])
    assert rc != 0
