"""Upstream eligibility-gate plumbing for scripts/build_stat_grid_pmfs.py.

Kept in a separate module so the gate is unit-testable in isolation and
so the change diff for the M8.9 root-cause rewire is small and obvious.

Inputs are read from disk:
    artifacts/minutes_predictions/{date}/minutes_predictions.parquet
    data/odds_api/processed/{date}/odds_pairs_*.parquet (optional)

Returns a ``{(player_id, game_id): eligibility_row_dict}`` map for every
candidate player-game that passes the eligibility rule. Player-games not
in the map MUST NOT have PMFs generated.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from nba_props_model.pipelines.player_game_eligibility import (
    build_current_market_player_signal,
    build_player_game_eligibility,
)


def load_minutes_predictions(repo_root: Path, target_date: str) -> pd.DataFrame:
    p = repo_root / "artifacts" / "minutes_predictions" / target_date / "minutes_predictions.parquet"
    if not p.exists():
        raise SystemExit(
            "FATAL: missing artifacts/minutes_predictions/"
            + str(target_date) + "/minutes_predictions.parquet. "
            "Run scripts/build_minutes_predictions.py --slate-date "
            + str(target_date) + " first; PMF generation is no longer "
            "allowed without the upstream minutes / rotation artifact."
        )
    return pd.read_parquet(p)


def load_current_market_signal(repo_root: Path, target_date: str) -> pd.DataFrame:
    """Concatenate all odds_pairs parquets for this date, normalize keys,
    and return the per-(slate_date, game_id, player_id) market signal."""
    odds_dir = repo_root / "data" / "odds_api" / "processed" / target_date
    frames = []
    if odds_dir.exists():
        for op in sorted(odds_dir.glob("odds_pairs_*.parquet")):
            try:
                frames.append(pd.read_parquet(op))
            except Exception as exc:
                print("  warn: could not read " + op.name + ": " + str(exc))
    if frames:
        market_df = pd.concat(frames, ignore_index=True)
        if "market_stat" in market_df.columns and "stat" not in market_df.columns:
            market_df = market_df.rename(columns={"market_stat": "stat"})
        for col, alt in (("player_id", "bdl_player_id"), ("game_id", "event_id")):
            if col not in market_df.columns and alt in market_df.columns:
                market_df[col] = market_df[alt]
    else:
        market_df = pd.DataFrame()
    return build_current_market_player_signal(market_df, slate_date=target_date)


def build_eligibility_map(
    repo_root: Path,
    target_date: str,
    keys: Iterable[tuple[int, int]],
) -> dict[tuple[int, int], dict]:
    """Build the keep-set: (player_id, game_id) -> eligibility row dict.

    ``keys`` is the iterable of candidate (player_id, game_id) the
    caller has already discovered (recent rosters, all_props, etc.).
    The returned map contains ONLY player-games that pass the
    eligibility rule (market line OR projected starter/rotation OR
    minutes_mean >= 12).
    """
    minutes_predictions = load_minutes_predictions(repo_root, target_date)
    print("  minutes_predictions rows: " + str(len(minutes_predictions)))

    current_market_signal = load_current_market_signal(repo_root, target_date)
    print("  current_market_signal rows: " + str(len(current_market_signal)))

    keys_list = [(int(pid), int(gid)) for pid, gid in keys]
    player_games_df = pd.DataFrame(
        [{"slate_date": str(target_date), "game_id": gid, "player_id": pid}
         for pid, gid in keys_list]
    )
    eligibility = build_player_game_eligibility(
        player_games_df,
        minutes_predictions,
        current_market_signal,
        slate_date=target_date,
    )

    eligible = eligibility[eligibility["player_game_eligible"]].copy()
    dropped = eligibility[~eligibility["player_game_eligible"]].copy()
    print(
        "  eligibility gate: kept=" + str(len(eligible))
        + " dropped=" + str(len(dropped))
        + " (no_line / non_rotation / sub_12_minutes)"
    )

    out = {}
    for _, r in eligible.iterrows():
        out[(int(r["player_id"]), int(r["game_id"]))] = r.to_dict()
    return out
