"""Tests for verify_derek_forward_feed_contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def test_contract_script_exists():
    assert (REPO / "scripts" / "verify_derek_forward_feed_contract.py").is_file()


def test_verify_passes_on_minimal_unified(tmp_path: Path, monkeypatch):
    from nba_props_model.delivery.delivery_contract import DEREK_UNIFIED_REQUIRED_COLUMNS

    feed = tmp_path / "deliveries" / "2099-06-01" / "derek_forward_feed"
    feed.mkdir(parents=True)
    row = {c: None for c in DEREK_UNIFIED_REQUIRED_COLUMNS}
    row.update(
        {
            "game_date": "2099-06-01",
            "run_date": "2099-06-01",
            "run_id": "test",
            "run_mode": "morning_expected",
            "generated_at_utc": "2099-01-01T00:00:00Z",
            "pipeline_version": "test",
            "model_version": "test",
            "model_artifact_hash": "",
            "source_data_asof_utc": "2099-01-01T00:00:00Z",
            "player_id": 1,
            "player_name": "A",
            "team": "T",
            "opponent": "O",
            "game_id": "g",
            "event_id": None,
            "stat": "pts",
            "role_bucket": "starter",
            "inactive_risk": 0.0,
            "expected_lineup_status": "projected",
            "official_lineup_status": "not_available_yet",
            "injury_status": "ok",
            "injury_source": "x",
            "injury_last_updated_utc": None,
            "lineup_source": "y",
            "lineup_last_updated_utc": None,
            "stale_injury_flag": False,
            "stale_lineup_flag": False,
            "market_status": "no_offered_market",
            "delivery_status": "ready",
            "unavailable_reason": None,
            "calculation_source": "unit_test",
            "calculation_status": "ok",
            "model_prob_over_raw": 0.5,
            "model_prob_over_active": 0.5,
            "model_prob_under_active": 0.5,
            "fair_over_odds": 100,
            "fair_under_odds": -100,
            "pmf_mean": 10.0,
            "pmf_variance": 1.0,
            "pmf_p10": 5.0,
            "pmf_p50": 10.0,
            "pmf_p90": 15.0,
            "market_prob_over": None,
            "no_vig_market_prob_over": None,
            "edge": 0.0,
            "line": None,
            "projected_minutes": 25.0,
            "minutes_q10": None,
            "minutes_q50": 24.0,
            "minutes_q90": None,
        }
    )
    pd.DataFrame([row]).to_parquet(feed / "derek_forward_feed.parquet", index=False)
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            "2099-06-01",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "DEREK_FORWARD_FEED_CONTRACT_PASS" in res.stdout


def test_verify_fails_when_parquet_missing_and_no_skip_marker(tmp_path: Path):
    feed = tmp_path / "deliveries" / "2099-06-02" / "derek_forward_feed"
    feed.mkdir(parents=True)
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            "2099-06-02",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "DEREK_FORWARD_FEED_CONTRACT_FAIL" in res.stdout


def test_verify_valid_skip_on_no_games_after_game(tmp_path: Path):
    """After-game runs on a true no-game day must accept the producer's
    honest skip marker instead of red-failing the missing parquet."""
    date = "2099-06-03"
    delivery = tmp_path / "deliveries" / date
    feed = delivery / "derek_forward_feed"
    feed.mkdir(parents=True)
    (feed / "derek_forward_feed_unified_skip.json").write_text(
        '{"unified_feed_status": "skipped_no_rows"}'
    )
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            date,
            "--repo-root",
            str(tmp_path),
            "--run-mode",
            "final_after_game",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "DEREK_FORWARD_FEED_CONTRACT_VALID_SKIP" in res.stdout


def test_verify_valid_skip_honors_slate_sentinel(tmp_path: Path):
    date = "2099-06-04"
    delivery = tmp_path / "deliveries" / date
    feed = delivery / "derek_forward_feed"
    feed.mkdir(parents=True)
    (delivery / "no_games_today.json").write_text(
        '{"status": "after_game_skipped_no_games_prev_day"}'
    )
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            date,
            "--repo-root",
            str(tmp_path),
            "--run-mode",
            "final_after_game",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "DEREK_FORWARD_FEED_CONTRACT_VALID_SKIP" in res.stdout


def test_verify_does_not_skip_for_strict_run_modes(tmp_path: Path):
    """Producer skip markers do NOT satisfy the contract for t25/t5/
    morning_expected — those modes require a real parquet."""
    date = "2099-06-05"
    delivery = tmp_path / "deliveries" / date
    feed = delivery / "derek_forward_feed"
    feed.mkdir(parents=True)
    (feed / "derek_forward_feed_unified_skip.json").write_text("{}")
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            date,
            "--repo-root",
            str(tmp_path),
            "--run-mode",
            "t25",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "DEREK_FORWARD_FEED_CONTRACT_FAIL" in res.stdout


if __name__ == "__main__":
    import pytest  # noqa: F401

    pytest.main([__file__, "-q"])
