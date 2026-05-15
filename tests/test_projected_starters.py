"""Unit tests for the projected-starter prior.

These lock in the contract that the prior is:

(a) strictly walk-forward (game_date < slate_date is the cutoff),
(b) per-team renormalized to exactly 5 expected starters,
(c) does NOT collapse a high-prob_active player to 0.0 when recent starts are 0,
(d) leakage-safe (rows with game_date >= slate_date are ignored even if the
    parquet has rows for the slate day or later).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nba_props_model.features.projected_starters import (
    DEFAULT_WINDOW_N,
    ProjectedStarterConfig,
    compute_projected_starter_prior,
)


def _make_history(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _team_history(team_id: int, n_games: int, *, starter_pids: list[int], bench_pids: list[int], start_game_id: int = 1000) -> list[dict]:
    """Build n_games of synthetic box-score rows for a team.

    The first 5 players (starter_pids) get high minutes; bench_pids get low
    minutes. This makes our top-5-by-minutes starter proxy deterministic.
    """
    rows: list[dict] = []
    base_date = pd.Timestamp("2025-12-01")
    for g in range(n_games):
        gid = start_game_id + g
        date = (base_date + pd.Timedelta(days=g)).strftime("%Y-%m-%d")
        for i, pid in enumerate(starter_pids):
            rows.append(
                {
                    "player_id": pid,
                    "game_id": gid,
                    "game_date": date,
                    "team_id": team_id,
                    "min": 32.0 - i,
                    "plus_minus": 5.0,
                }
            )
        for i, pid in enumerate(bench_pids):
            rows.append(
                {
                    "player_id": pid,
                    "game_id": gid,
                    "game_date": date,
                    "team_id": team_id,
                    "min": 10.0 - i * 0.5,
                    "plus_minus": -1.0,
                }
            )
    return rows


def test_strict_walk_forward_filter():
    starters = [10, 11, 12, 13, 14]
    bench = [20, 21, 22, 23, 24, 25, 26]
    pids = starters + bench
    history = _make_history(_team_history(1, 12, starter_pids=starters, bench_pids=bench, start_game_id=2000))

    leakage_row = {
        "player_id": 999,
        "game_id": 99999,
        "game_date": "2026-01-15",
        "team_id": 1,
        "min": 35.0,
        "plus_minus": 10.0,
    }
    history = pd.concat([history, _make_history([leakage_row])], ignore_index=True)

    eligible = pd.DataFrame({"player_id": pids + [999], "team_id": [1] * (len(pids) + 1)})
    out = compute_projected_starter_prior(eligible, "2026-01-15", history)

    row_leak = out[out["player_id"] == 999].iloc[0]
    assert row_leak["n_games"] == 0, (
        "Slate-day row must be filtered: passing slate_date with game_date>=slate must yield n_games=0."
    )


def test_strict_less_than_window():
    """Slate-day rows must be ignored: filter is strict less-than."""
    starters = [10, 11, 12, 13, 14]
    bench = [20, 21, 22, 23, 24]
    pids = starters + bench
    rows = _team_history(7, 5, starter_pids=starters, bench_pids=bench, start_game_id=3000)
    pre_dates_only = pd.DataFrame(rows)

    same_day_rows = []
    for pid in starters + bench:
        same_day_rows.append(
            {
                "player_id": pid,
                "game_id": 999999,
                "game_date": "2026-02-10",
                "team_id": 7,
                "min": 30.0,
                "plus_minus": 0.0,
            }
        )
    history = pd.concat([pre_dates_only, pd.DataFrame(same_day_rows)], ignore_index=True)

    eligible = pd.DataFrame({"player_id": pids, "team_id": [7] * len(pids)})
    out_with_leak = compute_projected_starter_prior(eligible, "2026-02-10", history)
    out_clean = compute_projected_starter_prior(eligible, "2026-02-10", pre_dates_only)

    for pid in pids:
        a = out_with_leak[out_with_leak["player_id"] == pid].iloc[0]
        b = out_clean[out_clean["player_id"] == pid].iloc[0]
        assert int(a["n_games"]) == int(b["n_games"]), (
            f"leakage check failed for pid={pid}: with-leak n_games={a['n_games']} clean n_games={b['n_games']}"
        )
        assert float(a["expected_starter_prob"]) == pytest.approx(float(b["expected_starter_prob"]), abs=1e-9)


def test_team_top5_sums_to_exactly_5():
    starters = [10, 11, 12, 13, 14]
    bench = [20, 21, 22, 23, 24, 25, 26, 27]
    pids = starters + bench
    history = _make_history(_team_history(1, 12, starter_pids=starters, bench_pids=bench))
    eligible = pd.DataFrame({"player_id": pids, "team_id": [1] * len(pids)})
    out = compute_projected_starter_prior(eligible, "2026-03-01", history)
    n_starters = int(out["expected_starter"].sum())
    assert n_starters == 5, f"expected exactly 5 starters per team, got {n_starters}: {out[['player_id','expected_starter_prob','expected_starter']]}"

    for pid in starters:
        row = out[out["player_id"] == pid].iloc[0]
        assert bool(row["expected_starter"]) is True
        assert float(row["expected_starter_prob"]) >= 0.5
    for pid in bench:
        row = out[out["player_id"] == pid].iloc[0]
        assert bool(row["expected_starter"]) is False
        assert float(row["expected_starter_prob"]) < 0.5


def test_returning_star_with_zero_recent_starts_not_collapsed_to_zero():
    """A player with prob_active high but zero recent starts (e.g. coming off
    injury) must NOT get expected_starter_prob == 0.

    The Beta-Binomial smoother with alpha=beta=1 yields p = 1/(n+2) for n
    zero-start games, which is strictly positive. And the floor (1e-3) also
    prevents 0.0.
    """
    other = [101, 102, 103, 104, 105, 106, 107, 108, 109]
    history_rows = _team_history(5, 12, starter_pids=other[:5], bench_pids=other[5:], start_game_id=5000)
    history = _make_history(history_rows)
    star_pid = 999
    pids = other + [star_pid]
    eligible = pd.DataFrame(
        {
            "player_id": pids,
            "team_id": [5] * len(pids),
            "prob_active": [0.9] * len(other) + [0.95],
        }
    )
    out = compute_projected_starter_prior(eligible, "2026-04-01", history)
    star_row = out[out["player_id"] == star_pid].iloc[0]
    assert float(star_row["expected_starter_prob"]) > 0.0
    assert int(star_row["n_games"]) == 0


def test_feature_freshness_column_present():
    pids = [1, 2, 3, 4, 5, 6, 7]
    history = _make_history(_team_history(9, 5, starter_pids=pids[:5], bench_pids=pids[5:], start_game_id=7000))
    eligible = pd.DataFrame({"player_id": pids, "team_id": [9] * len(pids)})
    out = compute_projected_starter_prior(eligible, "2026-04-15", history)
    assert "feature_freshness" in out.columns
    assert (out["feature_freshness"].astype(str) == f"projected_starter_rolling_N{DEFAULT_WINDOW_N}").all()


def test_two_teams_both_get_five_starters():
    pids_a = list(range(100, 113))
    pids_b = list(range(200, 213))
    history = _make_history(
        _team_history(1, 10, starter_pids=pids_a[:5], bench_pids=pids_a[5:])
        + _team_history(2, 10, starter_pids=pids_b[:5], bench_pids=pids_b[5:], start_game_id=8000)
    )
    eligible = pd.DataFrame(
        {
            "player_id": pids_a + pids_b,
            "team_id": [1] * len(pids_a) + [2] * len(pids_b),
        }
    )
    out = compute_projected_starter_prior(eligible, "2026-04-20", history)
    per_team = out.groupby("team_id")["expected_starter"].sum().to_dict()
    assert per_team.get(1) == 5
    assert per_team.get(2) == 5


def test_rotation_rank_and_slot_consistency():
    pids = list(range(1, 14))
    history = _make_history(_team_history(3, 10, starter_pids=pids[:5], bench_pids=pids[5:]))
    eligible = pd.DataFrame({"player_id": pids, "team_id": [3] * len(pids)})
    out = compute_projected_starter_prior(eligible, "2026-04-25", history)
    ranks = dict(zip(out["player_id"], out["expected_rotation_rank"]))
    slots = dict(zip(out["player_id"], out["projected_rotation_slot"]))
    for pid, r in ranks.items():
        if r <= 5:
            assert slots[pid] == "starter"
        elif r <= 9:
            assert slots[pid] == "rotation"
        else:
            assert slots[pid] == "deep_bench"


def test_low_prob_active_can_be_outranked_but_not_collapsed_to_zero():
    """A historic starter with prob_active = 0.2 (game-time decision out) should
    still have nonzero expected_starter_prob. Tie-break-by-prob_active in the
    renormalization step is allowed to push them out of the top-5; that is
    expected behavior.
    """
    historic_starters = [1, 2, 3, 4, 5]
    bench_pool = [6, 7, 8, 9, 10, 11, 12]
    history = _make_history(_team_history(4, 10, starter_pids=historic_starters, bench_pids=bench_pool))
    eligible = pd.DataFrame(
        {
            "player_id": historic_starters + bench_pool,
            "team_id": [4] * (len(historic_starters) + len(bench_pool)),
            "prob_active": [0.2, 0.95, 0.95, 0.95, 0.95] + [0.9] * len(bench_pool),
        }
    )
    out = compute_projected_starter_prior(eligible, "2026-04-26", history)
    row1 = out[out["player_id"] == 1].iloc[0]
    assert float(row1["expected_starter_prob"]) > 0.0
    assert (out["expected_starter"].sum()) == 5


def test_empty_history_returns_uniform_prior():
    eligible = pd.DataFrame({"player_id": list(range(1, 8)), "team_id": [1] * 7})
    out = compute_projected_starter_prior(eligible, "2026-03-01", pd.DataFrame(columns=["player_id", "game_id", "game_date", "team_id", "min", "plus_minus"]))
    assert len(out) == 7
    assert int(out["expected_starter"].sum()) == 5
    assert (out["expected_starter_prob"] > 0).all()
    assert (out["expected_starter_prob"] < 1).all()
