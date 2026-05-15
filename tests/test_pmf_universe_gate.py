"""Tests for the PMF universe gate.

The M8.9 root-cause rewire requires that ``build_prop_pmfs()`` is NEVER
called for player-games that fail the eligibility rule. These tests use
the same helper plumbing as ``scripts/build_stat_grid_pmfs.py`` —
``build_eligibility_map`` — and assert exactly which keys survive.

Cases:

    1. Deep bench player-game is excluded from the eligibility map
       (so the caller would never invoke build_prop_pmfs for them).
    2. Projected starter without a market line is included.
    3. Player with a market line is included even with low minutes.
    4. ``assert_no_ineligible_pmfs`` raises when any output row has
       ``player_game_eligible == False``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.pipelines.player_game_eligibility import (  # noqa: E402
    assert_no_ineligible_pmfs,
    build_current_market_player_signal,
    build_player_game_eligibility,
)


SLATE_DATE = "2026-05-15"


def _mrow(player_id, game_id, **kw):
    row = {
        "slate_date": SLATE_DATE,
        "game_id": game_id,
        "player_id": player_id,
        "minutes_mean": kw.get("minutes_mean", 8.0),
        "minutes_p10": kw.get("minutes_p10", 4.0),
        "minutes_p50": kw.get("minutes_p50", 8.0),
        "minutes_p90": kw.get("minutes_p90", 14.0),
        "minutes_std": kw.get("minutes_std", 3.0),
        "rotation_probability": kw.get("rotation_probability", 0.20),
        "starter_probability": kw.get("starter_probability", 0.05),
        "projected_role": kw.get("projected_role", "fringe"),
        "p_inactive_used": kw.get("p_inactive_used", 0.10),
        "minutes_source": "state_aware_minutes_model",
        "minutes_model_version": "state_aware_v1",
    }
    return row


def _build_map(candidates, minutes_rows, market_rows):
    base = pd.DataFrame([
        {"slate_date": SLATE_DATE, "game_id": gid, "player_id": pid}
        for pid, gid in candidates
    ])
    minutes = pd.DataFrame(minutes_rows)
    market = pd.DataFrame(market_rows)
    signal = build_current_market_player_signal(market, slate_date=SLATE_DATE)
    eligibility = build_player_game_eligibility(
        base, minutes, signal, slate_date=SLATE_DATE
    )
    eligible = eligibility[eligibility["player_game_eligible"]].copy()
    return {
        (int(r["player_id"]), int(r["game_id"])): r.to_dict()
        for _, r in eligible.iterrows()
    }


def test_universe_gate_excludes_deep_bench():
    candidates = [(101, 9001), (102, 9001)]
    minutes = [
        _mrow(101, 9001, minutes_mean=30.0, rotation_probability=0.95,
              starter_probability=0.90, projected_role="starter"),
        _mrow(102, 9001, minutes_mean=3.0, rotation_probability=0.05,
              starter_probability=0.01, p_inactive_used=0.40,
              projected_role="inactive_risk"),
    ]
    keep = _build_map(candidates, minutes, market_rows=[])
    assert (101, 9001) in keep
    assert (102, 9001) not in keep


def test_universe_gate_includes_projected_starter_without_market_line():
    candidates = [(201, 9002)]
    minutes = [
        _mrow(201, 9002, minutes_mean=8.0, rotation_probability=0.30,
              starter_probability=0.80, projected_role="starter"),
    ]
    keep = _build_map(candidates, minutes, market_rows=[])
    assert (201, 9002) in keep
    assert keep[(201, 9002)]["eligibility_reason"] == "starter_probability"


def test_universe_gate_includes_market_quoted_low_minutes_player():
    candidates = [(301, 9003)]
    minutes = [
        _mrow(301, 9003, minutes_mean=2.0, rotation_probability=0.05,
              starter_probability=0.01, p_inactive_used=0.35,
              projected_role="inactive_risk"),
    ]
    market = [{
        "slate_date": SLATE_DATE,
        "game_id": 9003,
        "player_id": 301,
        "stat": "points",
        "line": 4.5,
    }]
    keep = _build_map(candidates, minutes, market_rows=market)
    assert (301, 9003) in keep
    assert keep[(301, 9003)]["eligibility_reason"] == "current_market_line"


def test_assert_no_ineligible_pmfs_raises_on_false_rows():
    df = pd.DataFrame([
        {"slate_date": SLATE_DATE, "game_id": 9001, "player_id": 101,
         "player_name": "Star", "stat": "points",
         "player_game_eligible": True},
        {"slate_date": SLATE_DATE, "game_id": 9001, "player_id": 102,
         "player_name": "Bench", "stat": "points",
         "player_game_eligible": False},
    ])
    with pytest.raises(RuntimeError, match="contains ineligible PMF rows"):
        assert_no_ineligible_pmfs(df, label="test_grid")


def test_assert_no_ineligible_pmfs_passes_clean_df():
    df = pd.DataFrame([
        {"slate_date": SLATE_DATE, "game_id": 9001, "player_id": 101,
         "stat": "points", "player_game_eligible": True},
    ])
    # Should not raise.
    assert_no_ineligible_pmfs(df, label="test_grid")


def test_assert_no_ineligible_pmfs_raises_if_column_missing():
    df = pd.DataFrame([{"player_id": 101, "stat": "points"}])
    with pytest.raises(RuntimeError, match="missing player_game_eligible"):
        assert_no_ineligible_pmfs(df, label="test_grid")
