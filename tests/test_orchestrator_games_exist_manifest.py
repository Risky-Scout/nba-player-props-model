"""Tests for _emit_games_exist_delivery_manifest.

On a games-exist slate the orchestrator must write a top-level
``deliveries/<date>/manifest.json`` that:

  * carries the inverse of the no-games 4-flag gate so no verifier
    can mistake it for a confirmed no-games soft-skip (no_games_slate
    must be false AND confirmed_no_games_slate must be false);
  * records eligible_player_game_rows from the canonical MODEL_ONLY
    rectangle when the parquet exists;
  * records market_superiority_evaluated=True when the WoO run
    manifest exists AND market_comparison has rows>0;
  * declares derek_forward_feed_expected=True (a games-exist slate
    is the only path on which a Derek feed should be produced);
  * is invariant in shape between modes that run delivery
    (woo_morning_monetization, woo_afternoon_refresh,
    derek_pre_tipoff_refresh, close_lock, morning).

The forced-manual workflow assertion checks for
``deliveries/<date>/manifest.json`` and previously broke on
games-exist runs because only the no-games short-circuit produced
this file. This test guards the games-exist writer so the regression
cannot return.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_orchestrator(monkeypatch, tmp_path: Path):
    spec = importlib.util.spec_from_file_location(
        "_orchestrator_games_exist_manifest_under_test",
        REPO_ROOT / "scripts" / "run_daily_delivery_pipeline.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path, raising=True)
    return mod


def _stage_canonical(tmp_path: Path, date: str, rows: int) -> None:
    cs = tmp_path / "deliveries" / date / "canonical_source"
    cs.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({
        "player_id": [f"p{i}" for i in range(rows)],
        "game_id":   [f"g{i // 6}" for i in range(rows)],
        "stat":      ["pts"] * rows,
        "model_prob": [0.5] * rows,
    })
    df.to_parquet(cs / "player_prop_pmfs_tonight_MODEL_ONLY.parquet", index=False)
    df.to_parquet(cs / "all_props_model_only.parquet", index=False)


def _stage_market(tmp_path: Path, date: str, rows: int, *, write_run_manifest: bool) -> None:
    woo = tmp_path / "deliveries" / date / "wizard_of_odds"
    woo.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({
        "player_id": [f"p{i}" for i in range(rows)],
        "line":      [10.0] * rows,
        "model_p_over": [0.55] * rows,
    })
    df.to_parquet(woo / "market_comparison.parquet", index=False)
    if write_run_manifest:
        (woo / "run_manifest.json").write_text(json.dumps({
            "delivery_date": date,
            "market_superiority_claim_allowed": True,
        }), encoding="utf-8")


def _stage_derek(tmp_path: Path, date: str, rows: int) -> None:
    dfd = tmp_path / "deliveries" / date / "derek_forward_feed"
    dfd.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({
        "player_id": [f"p{i}" for i in range(rows)],
        "stat":      ["pts"] * rows,
        "pmf_mean":  [12.3] * rows,
        "line":      [11.5] * rows,
    })
    df.to_parquet(dfd / "derek_forward_feed.parquet", index=False)
    df.to_csv(dfd / "derek_forward_feed.csv", index=False)
    (dfd / "feed_manifest.json").write_text(json.dumps({
        "delivery_date": date,
        "rows": rows,
    }), encoding="utf-8")


def test_writes_top_level_manifest_with_inverse_no_games_flags(tmp_path, monkeypatch):
    mod = _load_orchestrator(monkeypatch, tmp_path)
    date = "2026-05-17"
    _stage_canonical(tmp_path, date, rows=168)
    _stage_market(tmp_path, date, rows=42, write_run_manifest=True)
    _stage_derek(tmp_path, date, rows=42)

    mod._emit_games_exist_delivery_manifest(date)

    p = tmp_path / "deliveries" / date / "manifest.json"
    assert p.is_file()
    m = json.loads(p.read_text(encoding="utf-8"))
    assert m["delivery_date"] == date
    assert m["reason"] == "games_exist"
    assert m["no_games_slate"] is False
    assert m["confirmed_no_games_slate"] is False
    assert m["marker"] == "PIPELINE_GAMES_EXIST_DELIVERY"
    assert m["eligible_player_game_rows"] == 168
    assert m["market_superiority_evaluated"] is True
    assert m["derek_forward_feed_expected"] is True
    # Subdir lineage is present.
    assert m["canonical_source"]["rows"] == 168
    assert m["wizard_of_odds"]["rows"] == 42
    assert m["derek_forward_feed"]["rows"] == 42


def test_market_superiority_evaluated_false_when_no_run_manifest(tmp_path, monkeypatch):
    mod = _load_orchestrator(monkeypatch, tmp_path)
    date = "2026-05-17"
    _stage_canonical(tmp_path, date, rows=24)
    _stage_market(tmp_path, date, rows=12, write_run_manifest=False)
    mod._emit_games_exist_delivery_manifest(date)
    m = json.loads((tmp_path / "deliveries" / date / "manifest.json").read_text())
    assert m["market_superiority_evaluated"] is False
    # market rows are still recorded so consumers can see the size.
    assert m["wizard_of_odds"]["rows"] == 12


def test_market_superiority_evaluated_false_when_market_empty(tmp_path, monkeypatch):
    mod = _load_orchestrator(monkeypatch, tmp_path)
    date = "2026-05-17"
    _stage_canonical(tmp_path, date, rows=24)
    _stage_market(tmp_path, date, rows=0, write_run_manifest=True)
    mod._emit_games_exist_delivery_manifest(date)
    m = json.loads((tmp_path / "deliveries" / date / "manifest.json").read_text())
    assert m["market_superiority_evaluated"] is False


def test_manifest_cannot_trigger_no_games_soft_skip(tmp_path, monkeypatch):
    """Read the games-exist manifest through every verifier's strict
    4-flag helper and confirm none of them treat it as a no-games
    soft-skip target. This is the regression test that ensures the
    inverse-flag manifest does not accidentally enable the no-games
    soft-skip gate on a games-exist slate."""
    mod = _load_orchestrator(monkeypatch, tmp_path)
    date = "2026-05-17"
    _stage_canonical(tmp_path, date, rows=10)
    _stage_market(tmp_path, date, rows=5, write_run_manifest=True)
    mod._emit_games_exist_delivery_manifest(date)

    # All five verifier helpers (they each load their own copy) must
    # return False when reading this manifest.
    def _load(script_name: str):
        spec = importlib.util.spec_from_file_location(
            f"_no_games_helper_{script_name}_under_test",
            REPO_ROOT / "scripts" / script_name,
        )
        m = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = m
        spec.loader.exec_module(m)
        return m

    for script_name, attr in (
        ("verify_daily_delivery_folder_contract.py",
         "_delivery_manifest_confirmed_no_games_slate"),
        ("verify_availability_freshness.py",
         "_delivery_manifest_confirmed_no_games_slate"),
        ("verify_morning_delivery_completeness.py",
         "_delivery_manifest_confirmed_no_games_slate"),
        ("verify_woo_dashboard_render_contract.py",
         "_delivery_manifest_confirmed_no_games_slate"),
        ("verify_woo_public_export_contract.py",
         "_delivery_manifest_confirmed_no_games_slate"),
        ("stamp_delivery_champion_metadata.py",
         "_delivery_manifest_confirmed_no_games_slate"),
    ):
        helper_mod = _load(script_name)
        helper_mod.REPO_ROOT = tmp_path
        fn = getattr(helper_mod, attr)
        # verify_woo_dashboard_render_contract takes (repo, date)
        if script_name == "verify_woo_dashboard_render_contract.py":
            assert fn(tmp_path, date) is False, (
                f"{script_name}: games-exist manifest must not pass strict 4-flag gate"
            )
        else:
            assert fn(date) is False, (
                f"{script_name}: games-exist manifest must not pass strict 4-flag gate"
            )
