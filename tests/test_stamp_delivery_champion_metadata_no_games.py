"""stamp_delivery_champion_metadata — strict no-games soft-skip tests.

On a confirmed no-games slate there are by design no Derek or WoO
manifests to stamp — the orchestrator's no-games short-circuit
explicitly does NOT produce ``deliveries/<date>/derek_forward_feed/
feed_manifest.json`` or ``deliveries/<date>/wizard_of_odds/
run_manifest.json``. The stamper must soft-skip cleanly with the
strict 4-flag gate, not hard-fail with
DELIVERY_CHAMPION_METADATA_STAMP_FAILED reason=
no_derek_or_woo_manifest_to_stamp.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def _load(monkeypatch, repo_root: Path):
    spec = importlib.util.spec_from_file_location(
        "_stamp_delivery_champion_metadata_under_test",
        SCRIPTS / "stamp_delivery_champion_metadata.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "REPO_ROOT", repo_root, raising=True)
    monkeypatch.setattr(mod, "DELIVERIES_DIR", repo_root / "deliveries", raising=True)
    monkeypatch.setattr(mod, "DELIVERY_METADATA_DIR",
                        repo_root / "artifacts" / "delivery_metadata", raising=True)
    pointer = repo_root / "artifacts" / "models" / "champion_pointer.json"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(json.dumps({
        "champion_model_id": "test-champion",
        "trained_through_date": "2026-05-15",
        "calibrated_through_date": "2026-05-15",
    }), encoding="utf-8")
    monkeypatch.setattr(mod, "CHAMPION_POINTER_PATH", pointer, raising=True)
    return mod


def _write_manifest(
    repo: Path, date: str, *,
    no_games_slate: bool = True,
    confirmed_no_games_slate: bool = True,
    reason: str = "no_games_slate",
    market_superiority_evaluated: bool = False,
    derek_forward_feed_expected: bool = False,
) -> Path:
    p = repo / "deliveries" / date / "manifest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "delivery_date": date,
        "no_games_slate": no_games_slate,
        "confirmed_no_games_slate": confirmed_no_games_slate,
        "reason": reason,
        "market_superiority_evaluated": market_superiority_evaluated,
        "derek_forward_feed_expected": derek_forward_feed_expected,
    }), encoding="utf-8")
    return p


def test_helper_true_when_full_4_flag(tmp_path, monkeypatch):
    mod = _load(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16")
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is True


def test_helper_false_when_no_manifest(tmp_path, monkeypatch):
    mod = _load(monkeypatch, tmp_path)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_helper_false_when_confirmed_flag_false(tmp_path, monkeypatch):
    mod = _load(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_helper_false_when_market_superiority_true(tmp_path, monkeypatch):
    mod = _load(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", market_superiority_evaluated=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_helper_false_when_derek_feed_expected_true(tmp_path, monkeypatch):
    mod = _load(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", derek_forward_feed_expected=True)
    assert mod._delivery_manifest_confirmed_no_games_slate("2026-05-16") is False


def test_main_soft_skips_on_confirmed_no_games(tmp_path, monkeypatch, capsys):
    """End-to-end: main() must soft-skip without trying to stamp
    Derek/WoO manifests on a confirmed no-games slate."""
    mod = _load(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16")
    # Make the delivery_dir exist so main() doesn't bail earlier.
    (tmp_path / "deliveries" / "2026-05-16").mkdir(parents=True, exist_ok=True)

    rc = mod.main(["--delivery-date", "2026-05-16"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "DELIVERY_CHAMPION_METADATA_STAMP_SOFT_SKIP_NO_GAMES" in out
    assert "date=2026-05-16" in out
    assert "gate=no_games_slate+confirmed_no_games_slate" in out


def test_main_hard_fails_on_missing_derek_woo_without_no_games_signal(
    tmp_path, monkeypatch, capsys
):
    """Games-bearing slate (no manifest no-games signal) with no
    Derek/WoO manifests must still hard-fail with
    DELIVERY_CHAMPION_METADATA_STAMP_FAILED."""
    mod = _load(monkeypatch, tmp_path)
    (tmp_path / "deliveries" / "2026-05-16").mkdir(parents=True, exist_ok=True)
    rc = mod.main(["--delivery-date", "2026-05-16"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "DELIVERY_CHAMPION_METADATA_STAMP_FAILED" in err
    assert "no_derek_or_woo_manifest_to_stamp" in err


def test_main_hard_fails_on_partial_4_flag_manifest(tmp_path, monkeypatch, capsys):
    """Partial 4-flag manifest (e.g. no_games_slate=true but
    confirmed_no_games_slate=false) must NOT soft-skip."""
    mod = _load(monkeypatch, tmp_path)
    _write_manifest(tmp_path, "2026-05-16", confirmed_no_games_slate=False)
    (tmp_path / "deliveries" / "2026-05-16").mkdir(parents=True, exist_ok=True)
    rc = mod.main(["--delivery-date", "2026-05-16"])
    assert rc == 1
