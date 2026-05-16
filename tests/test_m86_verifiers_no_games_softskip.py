"""M8.6 post-delivery verifiers — strict no-games soft-skip tests.

Three M8.6 verifiers must soft-skip cleanly on a confirmed no-games
slate (delivery manifest carries the full strict 4-flag gate:
``no_games_slate: true`` + ``confirmed_no_games_slate: true`` +
``market_superiority_evaluated: false`` +
``derek_forward_feed_expected: false``):

  * verify_daily_delivery_folder_contract: pmf_model_review_package
    not produced on a no-games short-circuit.
  * verify_availability_freshness: refresh step skipped by design.
  * verify_morning_delivery_completeness: same missing-subdir set.

All three gates must keep hard-fail behavior on any other manifest
shape (missing flag, false flag, missing manifest, corrupt manifest,
mismatched reason, partial 4-flag).
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
    spec = importlib.util.spec_from_file_location(mod_name, SCRIPTS / script_name)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_manifest(
    repo: Path,
    date: str,
    *,
    no_games_slate: bool = True,
    confirmed_no_games_slate: bool = True,
    reason: str = "no_games_slate",
    market_superiority_evaluated: bool = False,
    derek_forward_feed_expected: bool = False,
) -> Path:
    """Seed a delivery manifest. Defaults produce the full strict
    4-flag confirmed no-games payload. Tests override individual
    fields to exercise partial-flag hard-fail behavior."""
    p = repo / "deliveries" / date / "manifest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "delivery_date": date,
        "no_games_slate": no_games_slate,
        "confirmed_no_games_slate": confirmed_no_games_slate,
        "reason": reason,
        "market_superiority_evaluated": market_superiority_evaluated,
        "derek_forward_feed_expected": derek_forward_feed_expected,
    }, indent=2), encoding="utf-8")
    return p


# ---- verify_daily_delivery_folder_contract.py ----------------------------


def _make_folder_module(monkeypatch, repo_root: Path):
    mod = _load_module(monkeypatch, "verify_daily_delivery_folder_contract.py",
                       "_folder_contract_under_test")
    monkeypatch.setattr(mod, "REPO_ROOT", repo_root, raising=True)
    return mod


def test_folder_contract_helper_true_when_full_4_flag_manifest(tmp_path, monkeypatch):
    mod = _make_folder_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16")
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is True


def test_folder_contract_helper_false_without_manifest(tmp_path, monkeypatch):
    mod = _make_folder_module(monkeypatch, tmp_path)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_folder_contract_helper_false_when_no_games_slate_false(tmp_path, monkeypatch):
    mod = _make_folder_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_folder_contract_helper_false_when_confirmed_flag_false(tmp_path, monkeypatch):
    """Strict 4-flag rule: even if no_games_slate=true, missing
    confirmed_no_games_slate=true must keep the gate closed."""
    mod = _make_folder_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_folder_contract_helper_false_when_market_superiority_true(tmp_path, monkeypatch):
    """A manifest claiming model superiority was evaluated cannot soft-skip
    even if other no-games flags are set — guards against logically
    impossible payloads."""
    mod = _make_folder_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", market_superiority_evaluated=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_folder_contract_helper_false_when_derek_feed_expected_true(tmp_path, monkeypatch):
    """A manifest claiming Derek forward-feed rows are expected cannot
    soft-skip — guards against logically impossible payloads."""
    mod = _make_folder_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", derek_forward_feed_expected=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_folder_contract_helper_false_when_reason_differs(tmp_path, monkeypatch):
    mod = _make_folder_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", reason="something_else")
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_folder_contract_main_soft_skips_with_required_marker(tmp_path, monkeypatch, capsys):
    """End-to-end: main() short-circuits BEFORE checking subdirs when
    the manifest declares the full 4-flag confirmed no-games slate.
    Emits the required marker
    VERIFY_DAILY_DELIVERY_FOLDER_CONTRACT_SOFT_SKIP_NO_GAMES."""
    mod = _make_folder_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16")
    monkeypatch.setattr(sys, "argv",
                        ["verify_daily_delivery_folder_contract.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "VERIFY_DAILY_DELIVERY_FOLDER_CONTRACT_SOFT_SKIP_NO_GAMES" in out
    assert "date=2026-05-16" in out
    assert "gate=no_games_slate+confirmed_no_games_slate" in out


def test_folder_contract_main_hard_fails_on_missing_subdirs_without_signal(
    tmp_path, monkeypatch, capsys
):
    """Games-bearing slate (no manifest no-games flag) with missing
    subdirs must still hard-fail."""
    mod = _make_folder_module(monkeypatch, tmp_path)
    (tmp_path / "deliveries" / "2026-05-16").mkdir(parents=True)
    monkeypatch.setattr(sys, "argv",
                        ["verify_daily_delivery_folder_contract.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "DAILY_DELIVERY_CONTRACT_FAIL" in err
    assert "missing_subdirs" in err


def test_folder_contract_main_hard_fails_when_only_partial_no_games_flags(
    tmp_path, monkeypatch, capsys
):
    """A manifest with only no_games_slate=true (missing
    confirmed_no_games_slate) on an otherwise empty delivery folder
    must still hard-fail rather than silently soft-skip."""
    mod = _make_folder_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    (tmp_path / "deliveries" / "2026-05-16").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sys, "argv",
                        ["verify_daily_delivery_folder_contract.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "DAILY_DELIVERY_CONTRACT_FAIL" in err


# ---- verify_availability_freshness.py ------------------------------------


def _make_avail_module(monkeypatch, repo_root: Path):
    mod = _load_module(monkeypatch, "verify_availability_freshness.py",
                       "_availability_under_test")
    monkeypatch.setattr(mod, "REPO_ROOT", repo_root, raising=True)
    monkeypatch.setattr(mod, "AV_PATH", repo_root / "data" / "player_availability_asof.parquet",
                        raising=True)
    return mod


def test_availability_helper_true_when_full_4_flag_manifest(tmp_path, monkeypatch):
    mod = _make_avail_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16")
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is True


def test_availability_helper_false_without_manifest(tmp_path, monkeypatch):
    mod = _make_avail_module(monkeypatch, tmp_path)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_availability_helper_false_when_no_games_slate_false(tmp_path, monkeypatch):
    mod = _make_avail_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_availability_helper_false_when_confirmed_flag_false(tmp_path, monkeypatch):
    mod = _make_avail_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_availability_helper_false_when_market_superiority_true(tmp_path, monkeypatch):
    mod = _make_avail_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", market_superiority_evaluated=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_availability_helper_false_when_derek_feed_expected_true(tmp_path, monkeypatch):
    mod = _make_avail_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", derek_forward_feed_expected=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_availability_main_soft_skips_with_required_marker(tmp_path, monkeypatch, capsys):
    """main() short-circuits before checking AV_PATH when the full
    4-flag confirmed no-games manifest is present. Emits required
    marker VERIFY_AVAILABILITY_FRESHNESS_SOFT_SKIP_NO_GAMES."""
    mod = _make_avail_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16")
    # AV file absent — this would normally cause AVAILABILITY_FRESHNESS_FAIL.
    monkeypatch.setattr(sys, "argv",
                        ["verify_availability_freshness.py",
                         "--date", "2026-05-16",
                         "--mode", "close_lock"], raising=True)
    rc = mod.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "VERIFY_AVAILABILITY_FRESHNESS_SOFT_SKIP_NO_GAMES" in out
    assert "date=2026-05-16" in out
    assert "gate=no_games_slate+confirmed_no_games_slate" in out


def test_availability_main_hard_fails_without_signal(tmp_path, monkeypatch, capsys):
    """Games-bearing slate (no no-games flag) with missing AV file
    must still hard-fail with AVAILABILITY_FRESHNESS_FAIL."""
    mod = _make_avail_module(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv",
                        ["verify_availability_freshness.py",
                         "--date", "2026-05-16",
                         "--mode", "close_lock"], raising=True)
    rc = mod.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "AVAILABILITY_FRESHNESS_FAIL" in err
    assert "missing_file" in err


def test_availability_main_hard_fails_when_market_superiority_true(
    tmp_path, monkeypatch, capsys
):
    """Even with all other no-games flags set, market_superiority_
    evaluated=true means soft-skip is forbidden — the slate claims a
    real market-superiority evaluation, which cannot be true on a
    legit no-games slate."""
    mod = _make_avail_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", market_superiority_evaluated=True)
    monkeypatch.setattr(sys, "argv",
                        ["verify_availability_freshness.py",
                         "--date", "2026-05-16",
                         "--mode", "close_lock"], raising=True)
    rc = mod.main()
    assert rc == 1


# ---- verify_morning_delivery_completeness.py -----------------------------


def _make_morning_completeness_module(monkeypatch, repo_root: Path):
    mod = _load_module(monkeypatch, "verify_morning_delivery_completeness.py",
                       "_morning_completeness_under_test")
    monkeypatch.setattr(mod, "REPO_ROOT", repo_root, raising=True)
    return mod


def test_morning_completeness_helper_true_when_full_4_flag_manifest(tmp_path, monkeypatch):
    mod = _make_morning_completeness_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16")
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is True


def test_morning_completeness_helper_false_without_manifest(tmp_path, monkeypatch):
    mod = _make_morning_completeness_module(monkeypatch, tmp_path)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_morning_completeness_helper_false_when_confirmed_flag_false(tmp_path, monkeypatch):
    mod = _make_morning_completeness_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_morning_completeness_helper_false_when_market_superiority_true(tmp_path, monkeypatch):
    mod = _make_morning_completeness_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", market_superiority_evaluated=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_morning_completeness_helper_false_when_derek_feed_expected_true(tmp_path, monkeypatch):
    mod = _make_morning_completeness_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", derek_forward_feed_expected=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_morning_completeness_main_soft_skips_with_required_marker(
    tmp_path, monkeypatch, capsys
):
    """End-to-end: main() short-circuits BEFORE checking required
    subdirs and prints the required marker
    VERIFY_MORNING_DELIVERY_COMPLETENESS_SOFT_SKIP_NO_GAMES."""
    mod = _make_morning_completeness_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16")
    monkeypatch.setattr(sys, "argv",
                        ["verify_morning_delivery_completeness.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "VERIFY_MORNING_DELIVERY_COMPLETENESS_SOFT_SKIP_NO_GAMES" in out
    assert "date=2026-05-16" in out
    assert "gate=no_games_slate+confirmed_no_games_slate" in out


def test_morning_completeness_main_hard_fails_on_missing_subdirs_without_signal(
    tmp_path, monkeypatch, capsys
):
    """Games-bearing slate (no manifest no-games flag) with missing
    required subdirs must still hard-fail with MORNING_DELIVERY_
    COMPLETENESS_FAIL."""
    mod = _make_morning_completeness_module(monkeypatch, tmp_path)
    (tmp_path / "deliveries" / "2026-05-16").mkdir(parents=True)
    monkeypatch.setattr(sys, "argv",
                        ["verify_morning_delivery_completeness.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    assert rc == 1
    out = capsys.readouterr().out
    assert "MORNING_DELIVERY_COMPLETENESS_FAIL" in out


def test_morning_completeness_main_hard_fails_on_partial_4_flag_manifest(
    tmp_path, monkeypatch
):
    """Partial 4-flag manifest must NOT trigger soft-skip."""
    mod = _make_morning_completeness_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    (tmp_path / "deliveries" / "2026-05-16").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sys, "argv",
                        ["verify_morning_delivery_completeness.py",
                         "--date", "2026-05-16"], raising=True)
    rc = mod.main()
    assert rc == 1


def test_availability_main_hard_fails_on_partial_4_flag_manifest(
    tmp_path, monkeypatch, capsys
):
    """A manifest with only partial no-games flags (e.g. missing
    confirmed_no_games_slate) must NOT trigger soft-skip. The
    freshness check runs normally and hard-fails on the missing
    parquet."""
    mod = _make_avail_module(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    monkeypatch.setattr(sys, "argv",
                        ["verify_availability_freshness.py",
                         "--date", "2026-05-16",
                         "--mode", "close_lock"], raising=True)
    rc = mod.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "AVAILABILITY_FRESHNESS_FAIL" in err
