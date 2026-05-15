"""Tests for the after-game no-games-day short-circuit.

Covers:
  * ``_detect_no_games_day`` correctly identifies the honest no-game
    fingerprint (predictions parquet + canonical parquet both present
    with zero rows).
  * It refuses to short-circuit when files are missing or non-empty —
    that would mask real data outages.
  * ``_emit_after_game_no_games_skip`` writes the Derek-folder status
    JSON, the slate-level sentinel, and the after_game_scoring marker.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest


REPO = Path(__file__).resolve().parents[1]


def _load_orchestrator():
    """Load run_daily_delivery_pipeline.py as a module without executing
    its argparse-driven main()."""
    spec = importlib.util.spec_from_file_location(
        "run_daily_delivery_pipeline",
        REPO / "scripts" / "run_daily_delivery_pipeline.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _write_empty_parquet(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"player_id": pd.Series(dtype="int64")}).to_parquet(
        path, index=False
    )


def _write_nonempty_parquet(path: Path, rows: int = 3) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"player_id": list(range(rows))}).to_parquet(path, index=False)


@pytest.fixture()
def orchestrator(tmp_path, monkeypatch):
    mod = _load_orchestrator()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path, raising=True)
    return mod


def test_detect_returns_true_when_both_parquets_have_zero_rows(orchestrator, tmp_path):
    date = "2099-07-01"
    _write_empty_parquet(tmp_path / "predictions" / f"all_props_{date}.parquet")
    _write_empty_parquet(
        tmp_path
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    is_no_games, evidence = orchestrator._detect_no_games_day(date)
    assert is_no_games is True
    assert evidence["predictions_parquet"]["rows"] == 0
    assert evidence["canonical_model_only_parquet"]["rows"] == 0


def test_detect_refuses_when_predictions_parquet_is_missing(orchestrator, tmp_path):
    date = "2099-07-02"
    _write_empty_parquet(
        tmp_path
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    is_no_games, evidence = orchestrator._detect_no_games_day(date)
    assert is_no_games is False
    assert evidence["predictions_parquet"]["exists"] is False


def test_detect_refuses_when_canonical_parquet_is_missing(orchestrator, tmp_path):
    date = "2099-07-03"
    _write_empty_parquet(tmp_path / "predictions" / f"all_props_{date}.parquet")
    is_no_games, evidence = orchestrator._detect_no_games_day(date)
    assert is_no_games is False
    assert evidence["canonical_model_only_parquet"]["exists"] is False


def test_detect_refuses_when_predictions_parquet_has_rows(orchestrator, tmp_path):
    date = "2099-07-04"
    _write_nonempty_parquet(
        tmp_path / "predictions" / f"all_props_{date}.parquet", rows=5
    )
    _write_empty_parquet(
        tmp_path
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    is_no_games, _ = orchestrator._detect_no_games_day(date)
    assert is_no_games is False


def test_emit_writes_all_three_sentinels(orchestrator, tmp_path):
    date = "2099-07-05"
    evidence = {"delivery_date": date, "checked_at_utc": "2099-07-05T00:00:00Z"}
    orchestrator._emit_after_game_no_games_skip(date, evidence)

    base = tmp_path / "deliveries" / date
    derek_status = base / "derek_forward_feed" / "after_game_no_games_status.json"
    after_status = base / "after_game_scoring" / "no_games_status.json"
    slate_sentinel = base / "no_games_today.json"

    assert derek_status.is_file()
    assert after_status.is_file()
    assert slate_sentinel.is_file()

    payload = json.loads(derek_status.read_text())
    assert payload["status"] == "after_game_skipped_no_games_prev_day"
    assert payload["delivery_date"] == date
    assert payload["evidence"] == evidence


def test_emit_is_idempotent(orchestrator, tmp_path):
    date = "2099-07-06"
    evidence = {"delivery_date": date}
    orchestrator._emit_after_game_no_games_skip(date, evidence)
    orchestrator._emit_after_game_no_games_skip(date, evidence)
    payload = json.loads(
        (tmp_path / "deliveries" / date / "no_games_today.json").read_text()
    )
    assert payload["delivery_date"] == date


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
