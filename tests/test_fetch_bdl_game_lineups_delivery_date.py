"""Contract tests for ``scripts/fetch_bdl_game_lineups.py``.

These tests pin down the behavior added when the orchestrator
(``scripts/run_daily_delivery_pipeline.py``) started calling the script
with only ``--delivery-date`` (the original signature required one of
``--game-id`` / ``--game-ids``, so the orchestrator was tripping
argparse exit 2 in the morning preflight). The fix must:

  * keep explicit ``--game-id`` and ``--game-ids`` modes working;
  * auto-discover game IDs from the BDL schedule when only
    ``--delivery-date`` is provided;
  * soft-skip with a structured marker when BDL reports no games on
    that slate date and write a small audit artifact;
  * hard-fail with a structured marker when BDL returns games but
    none have a usable ``id`` field (schema regression);
  * hard-fail when the schedule call itself raises (API/network).

All tests run hermetically by stubbing ``get_games`` / ``fetch_one``;
no network access required.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
SCRIPTS = REPO_ROOT / "scripts"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_script_module(monkeypatch):
    """Reload the script module fresh and stub heavy submodules.

    Stub ``nba_props_model.data.bdl_client`` so import succeeds without
    network. Each test injects the ``get_games`` it wants via
    monkeypatch.setattr on the loaded module's stub.
    """
    bdl_stub = types.ModuleType("nba_props_model.data.bdl_client")

    def _default_unused(*_a, **_k):  # pragma: no cover
        raise AssertionError("get_games stub was not overridden in this test")

    bdl_stub.get_games = _default_unused
    bdl_stub.get_lineups = lambda *_a, **_k: []
    bdl_stub.get_lineups_status = lambda *_a, **_k: (200, [])
    monkeypatch.setitem(sys.modules, "nba_props_model.data.bdl_client", bdl_stub)

    spec = importlib.util.spec_from_file_location(
        "_fetch_bdl_game_lineups_under_test",
        SCRIPTS / "fetch_bdl_game_lineups.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_fetch_bdl_game_lineups_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod, bdl_stub


def _set_bdl_key(monkeypatch):
    monkeypatch.setenv("BDL_API_KEY", "dummy")


def test_explicit_game_id_still_works(monkeypatch, tmp_path):
    mod, _ = _load_script_module(monkeypatch)
    _set_bdl_key(monkeypatch)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "LIVE_LINEUPS_DIR", tmp_path / "artifacts" / "live_lineups")

    called: list[tuple[str, str]] = []

    def fake_fetch_one(delivery_date, gid):
        called.append((delivery_date, gid))
        return {
            "game_id": gid,
            "bdl_fetch_status": "lineups_available",
            "bdl_http_status": 200,
            "lineup_confirmed": True,
            "lineup_complete": True,
            "total_rows": 10,
            "lineup_blocker": None,
            "lineup_hash": "abc",
        }

    monkeypatch.setattr(mod, "fetch_one", fake_fetch_one)
    rc = mod.main(["--delivery-date", "2099-01-01", "--game-id", "12345"])
    assert rc == 0
    assert called == [("2099-01-01", "12345")]


def test_explicit_game_ids_still_works(monkeypatch, tmp_path):
    mod, _ = _load_script_module(monkeypatch)
    _set_bdl_key(monkeypatch)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "LIVE_LINEUPS_DIR", tmp_path / "artifacts" / "live_lineups")

    called: list[str] = []

    def fake_fetch_one(_date, gid):
        called.append(gid)
        return {
            "game_id": gid,
            "bdl_fetch_status": "lineups_available",
            "bdl_http_status": 200,
            "lineup_confirmed": True,
            "lineup_complete": True,
            "total_rows": 10,
            "lineup_blocker": None,
            "lineup_hash": "abc",
        }

    monkeypatch.setattr(mod, "fetch_one", fake_fetch_one)
    rc = mod.main(["--delivery-date", "2099-01-01", "--game-ids", "1,2, 3"])
    assert rc == 0
    assert called == ["1", "2", "3"]


def test_delivery_date_discovers_and_fetches(monkeypatch, tmp_path):
    mod, bdl_stub = _load_script_module(monkeypatch)
    _set_bdl_key(monkeypatch)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "LIVE_LINEUPS_DIR", tmp_path / "artifacts" / "live_lineups")

    bdl_stub.get_games = lambda **kw: [
        {"id": 21681995, "date": kw.get("start_date")},
        {"id": 21681996, "date": kw.get("start_date")},
    ]

    fetched: list[str] = []

    def fake_fetch_one(_date, gid):
        fetched.append(gid)
        return {
            "game_id": gid,
            "bdl_fetch_status": "lineups_available",
            "bdl_http_status": 200,
            "lineup_confirmed": True,
            "lineup_complete": True,
            "total_rows": 10,
            "lineup_blocker": None,
            "lineup_hash": "h",
        }

    monkeypatch.setattr(mod, "fetch_one", fake_fetch_one)
    rc = mod.main(["--delivery-date", "2099-01-01"])
    assert rc == 0
    assert fetched == ["21681995", "21681996"]


def test_delivery_date_no_games_soft_skips_with_audit(monkeypatch, tmp_path, capsys):
    mod, bdl_stub = _load_script_module(monkeypatch)
    _set_bdl_key(monkeypatch)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "LIVE_LINEUPS_DIR", tmp_path / "artifacts" / "live_lineups")
    monkeypatch.setattr(mod, "fetch_one", lambda *a, **k: pytest.fail("fetch_one must NOT be called on no-games soft-skip"))
    bdl_stub.get_games = lambda **kw: []

    rc = mod.main(["--delivery-date", "2099-01-01"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "BDL_GAME_LINEUPS_SOFT_SKIP_NO_GAMES" in out
    assert "date=2099-01-01" in out

    audit = tmp_path / "artifacts" / "live_lineups" / "2099-01-01" / "no_games_soft_skip.json"
    assert audit.is_file()
    payload = json.loads(audit.read_text(encoding="utf-8"))
    assert payload["delivery_date"] == "2099-01-01"
    assert payload["marker"] == "BDL_GAME_LINEUPS_SOFT_SKIP_NO_GAMES"


def test_delivery_date_games_without_id_hard_fails(monkeypatch, tmp_path, capsys):
    mod, bdl_stub = _load_script_module(monkeypatch)
    _set_bdl_key(monkeypatch)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "LIVE_LINEUPS_DIR", tmp_path / "artifacts" / "live_lineups")
    monkeypatch.setattr(mod, "fetch_one", lambda *a, **k: pytest.fail("fetch_one must NOT be called when ID resolution fails"))
    bdl_stub.get_games = lambda **kw: [
        {"game_uuid": "x", "date": "2099-01-01"},
        {"game_uuid": "y", "date": "2099-01-01"},
    ]

    rc = mod.main(["--delivery-date", "2099-01-01"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "BDL_GAME_LINEUPS_GAME_ID_RESOLUTION_FAILED" in err
    assert "date=2099-01-01" in err
    assert "present_columns=" in err


def test_delivery_date_schedule_lookup_raises_hard_fails(monkeypatch, tmp_path, capsys):
    mod, bdl_stub = _load_script_module(monkeypatch)
    _set_bdl_key(monkeypatch)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "LIVE_LINEUPS_DIR", tmp_path / "artifacts" / "live_lineups")

    def boom(**_kw):
        raise RuntimeError("simulated upstream 500")

    bdl_stub.get_games = boom

    rc = mod.main(["--delivery-date", "2099-01-01"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "BDL_LINEUPS_FETCH_FAILED" in err
    assert "BDL games schedule lookup raised" in err
    assert "simulated upstream 500" in err


def test_orchestrator_call_signature_no_longer_argparse_errors(monkeypatch, tmp_path):
    """The preflight call form ``--delivery-date <D>`` (no game ids) must
    parse cleanly and reach the discovery path — never argparse-exit 2."""
    mod, bdl_stub = _load_script_module(monkeypatch)
    _set_bdl_key(monkeypatch)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "LIVE_LINEUPS_DIR", tmp_path / "artifacts" / "live_lineups")
    bdl_stub.get_games = lambda **kw: []
    # If argparse rejects the orchestrator's invocation it would raise
    # SystemExit(2) before our soft-skip logic runs.
    rc = mod.main(["--delivery-date", "2099-01-01"])
    assert rc == 0
