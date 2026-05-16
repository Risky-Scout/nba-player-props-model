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


def _write_no_games_manifest(repo: Path, date: str, *, flag: bool = True,
                              reason: str = "no_games_slate") -> Path:
    p = repo / "deliveries" / date / "manifest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "delivery_date": date,
        "no_games_slate": flag,
        "reason": reason,
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


# ---- render contract ------------------------------------------------------


def test_render_contract_helper_true_when_manifest_says_so(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test")
    _write_no_games_manifest(tmp_path, "2026-05-16")
    assert mod._delivery_manifest_no_games_slate(tmp_path, "2026-05-16") is True


def test_render_contract_helper_false_without_manifest(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_2")
    assert mod._delivery_manifest_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_helper_false_when_flag_false(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_3")
    _write_no_games_manifest(tmp_path, "2026-05-16", flag=False)
    assert mod._delivery_manifest_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_helper_false_when_reason_differs(tmp_path, monkeypatch):
    """no_games_slate=true alone is not enough; reason must also say
    no_games_slate. Defensive against partial / stale manifests."""
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_4")
    _write_no_games_manifest(tmp_path, "2026-05-16", flag=True, reason="something_else")
    assert mod._delivery_manifest_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_helper_false_when_manifest_corrupt(tmp_path, monkeypatch):
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_under_test_5")
    p = tmp_path / "deliveries" / "2026-05-16" / "manifest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not json {{", encoding="utf-8")
    assert mod._delivery_manifest_no_games_slate(tmp_path, "2026-05-16") is False


def test_render_contract_main_soft_skips_on_no_games(tmp_path, monkeypatch, capsys):
    """End-to-end: the script's main() must short-circuit BEFORE
    checking any HTML/JSON artifacts when the manifest declares a
    confirmed no-games slate."""
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_main_under_test")
    # Re-point the script's hard-coded ``Path(__file__).resolve().parent.parent``
    # by chdir + symlink-style fakery is unnecessary: the function
    # builds ``repo`` from __file__, which still resolves to the real
    # repo. So we instead seed the REAL repo's deliveries/<test-date>/
    # manifest — but we cannot pollute the real tree. Use monkeypatch on
    # the function itself instead.
    # Simulate via direct call: stub the helper to return True for our
    # date, then call main() with --date through argv.
    monkeypatch.setattr(mod, "_delivery_manifest_no_games_slate",
                        lambda repo, date: True, raising=True)
    monkeypatch.setattr(sys, "argv",
                        ["verify_woo_dashboard_render_contract.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "WOO_DASHBOARD_RENDER_CONTRACT_SOFT_SKIP_NO_GAMES_SLATE" in out
    assert "date=2026-05-16" in out


def test_render_contract_main_does_not_soft_skip_without_signal(tmp_path, monkeypatch):
    """No no-games signal → main() must run the normal validation
    flow. Verify by stubbing the helper to False; main() should then
    proceed past the soft-skip gate and start checking artifacts (which
    are missing in tmp_path, so it returns a non-zero failure)."""
    mod = _load_module(monkeypatch, "verify_woo_dashboard_render_contract.py",
                       "_render_contract_main_no_signal")
    monkeypatch.setattr(mod, "_delivery_manifest_no_games_slate",
                        lambda repo, date: False, raising=True)
    monkeypatch.setattr(sys, "argv",
                        ["verify_woo_dashboard_render_contract.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    # We expect a non-zero exit because props_html / aff_json / pmf_json
    # do not exist in the real repo for this fake date.
    assert rc != 0


# ---- public export contract ----------------------------------------------


def _make_export_module(monkeypatch, repo_root: Path):
    mod = _load_module(monkeypatch, "verify_woo_public_export_contract.py",
                       "_public_export_under_test")
    monkeypatch.setattr(mod, "REPO_ROOT", repo_root, raising=True)
    return mod


def test_export_contract_helper_true_when_manifest_says_so(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    _write_no_games_manifest(tmp_path, "2026-05-16")
    assert mod._delivery_manifest_no_games_slate("2026-05-16") is True


def test_export_contract_helper_false_without_manifest(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    assert mod._delivery_manifest_no_games_slate("2026-05-16") is False


def test_export_contract_helper_false_when_flag_false(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    _write_no_games_manifest(tmp_path, "2026-05-16", flag=False)
    assert mod._delivery_manifest_no_games_slate("2026-05-16") is False


def test_export_contract_helper_false_when_reason_differs(tmp_path, monkeypatch):
    mod = _make_export_module(monkeypatch, tmp_path)
    _write_no_games_manifest(tmp_path, "2026-05-16", flag=True, reason="something_else")
    assert mod._delivery_manifest_no_games_slate("2026-05-16") is False


def test_export_contract_main_soft_skips_on_no_games(tmp_path, monkeypatch, capsys):
    mod = _make_export_module(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "_delivery_manifest_no_games_slate",
                        lambda date: True, raising=True)
    rc = mod.main(["--date", "2026-05-16"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "WOO_PUBLIC_EXPORT_CONTRACT_SOFT_SKIP_NO_GAMES_SLATE" in out
    assert "date=2026-05-16" in out


def test_export_contract_main_does_not_soft_skip_without_signal(tmp_path, monkeypatch):
    """When the helper returns False the script must run normally.
    Returns non-zero because the real export artifacts are missing in
    the test tree."""
    mod = _make_export_module(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "_delivery_manifest_no_games_slate",
                        lambda date: False, raising=True)
    rc = mod.main(["--date", "2026-05-16"])
    assert rc != 0
