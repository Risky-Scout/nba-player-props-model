"""Refresh `data/player_game_stats.parquet` with finalized BDL box scores.

Why max(game_date) can lag the calendar:
  - This script was not run after games finished (default fetch window is
    latest parquet date + 1 through today US/Eastern; override with
    ``--start-date`` / ``--end-date``).
  - BDL has no **Final** rows yet for those games (in-progress / postponed);
    non-final games and players with ``min < 1`` are dropped.
  - ``BDL_API_KEY`` is unset (refresh exits immediately).
  - A wrong ``--season`` filter removed all rows.

This is the season-to-date player×game box-score table used by every
downstream feature builder (predict.py, build_availability_table.py,
build_daily_pmf_delivery.py …). It is the source of truth for the
real outcome columns (pts, reb, ast, fg3m, stl, blk, **turnover**, …).

The refresh:

  1. Loads the existing parquet (if any) and identifies the latest
     `game_date` already present.
  2. Fetches BDL `/nba/v1/stats` rows for `[latest_date+1 … end_date]`.
     `--start-date` overrides the auto-discovered window. `--end-date`
     defaults to today (US/Eastern).
  3. Maps each BDL record into the existing parquet schema.
  4. Merges on `(game_id, player_id)` keeping the **incoming** row
     (BDL outcomes are authoritative for already-final games).
  5. Writes the merged table atomically.

Hard rules:
  - Never logs the API key.
  - Never fabricates outcomes — if BDL returns no rows, the parquet is
    left untouched and we exit non-zero.
  - Records with `min < 1` or missing player/game IDs are dropped
    (matches `bdl_client.get_player_game_stats` discipline).

CLI:
    python scripts/refresh_bdl_player_game_stats.py
    python scripts/refresh_bdl_player_game_stats.py --start-date 2026-04-22 \
        --end-date 2026-04-29 --season 2025
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

# Reuse the canonical BDL client so retry/backoff behaviour stays identical.
from nba_props_model.data.bdl_client import (  # noqa: E402
    get_player_game_stats, get_games, parse_minutes,
)

PARQUET_PATH = REPO_ROOT / "data" / "player_game_stats.parquet"

# Mirror the existing parquet column order exactly.
TARGET_COLUMNS = [
    "player_id", "player_name", "game_id", "game_date", "season",
    "home_team_id", "visitor_team_id", "team_id", "team_abbr",
    "min", "pts", "reb", "ast", "fg3m", "stl", "blk",
    "fga", "fg3a", "fta", "ftm", "fg_pct", "fg3_pct", "ft_pct",
    "oreb", "dreb", "turnover", "pf", "plus_minus", "position",
]


def _now_utc_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _today_eastern() -> date:
    """Eastern-time today. We don't need wall-clock precision; the
    `pytz`-free path is fine since we only use this for date math."""
    # UTC-4 (EDT) covers most of the NBA postseason. UTC-5 (EST) is the
    # off-season default. Either resolves to the right calendar date a
    # few minutes after midnight ET.
    return (datetime.utcnow() - timedelta(hours=4)).date()


def _bdl_record_to_row(rec: dict) -> dict | None:
    """Map a BDL `/nba/v1/stats` record into the existing parquet schema.
    Returns None for malformed / un-played / non-final records.

    Strict rule: we only ingest games whose `game.status` is ``Final`` or
    ``Final/OT`` (case-insensitive). Mid-game rows (``3rd Qtr``,
    ``4th Qtr``, ``Halftime``…) are dropped — letting them into the
    season-to-date parquet would poison every downstream feature with
    partial outcomes.
    """
    player = rec.get("player") or {}
    team = rec.get("team") or {}
    game = rec.get("game") or {}
    pid = player.get("id")
    gid = game.get("id")
    if not pid or not gid:
        return None
    status = str(game.get("status") or "").strip().lower()
    if not (status == "final" or status.startswith("final")):
        return None
    minutes = parse_minutes(rec.get("min", "0") or "0")
    if minutes < 1:
        return None
    first = (player.get("first_name") or "").strip()
    last = (player.get("last_name") or "").strip()
    full = (first + " " + last).strip() or f"Player {pid}"
    return {
        "player_id": int(pid),
        "player_name": full,
        "game_id": int(gid),
        "game_date": str(game.get("date") or "")[:10],
        "season": int(game.get("season") or 0),
        "home_team_id": int(game.get("home_team_id") or 0),
        "visitor_team_id": int(game.get("visitor_team_id") or 0),
        "team_id": int(team.get("id") or 0),
        "team_abbr": team.get("abbreviation"),
        "min": float(minutes),
        "pts": float(rec.get("pts") or 0),
        "reb": float(rec.get("reb") or 0),
        "ast": float(rec.get("ast") or 0),
        "fg3m": float(rec.get("fg3m") or 0),
        "stl": float(rec.get("stl") or 0),
        "blk": float(rec.get("blk") or 0),
        "fga": float(rec.get("fga") or 0),
        "fg3a": float(rec.get("fg3a") or 0),
        "fta": float(rec.get("fta") or 0),
        "ftm": float(rec.get("ftm") or 0),
        "fg_pct": float(rec.get("fg_pct") or 0),
        "fg3_pct": float(rec.get("fg3_pct") or 0),
        "ft_pct": float(rec.get("ft_pct") or 0),
        "oreb": float(rec.get("oreb") or 0),
        "dreb": float(rec.get("dreb") or 0),
        "turnover": float(rec.get("turnover") or 0),
        "pf": float(rec.get("pf") or 0),
        "plus_minus": float(rec.get("plus_minus") or 0),
        "position": player.get("position"),
    }


def _fetch_window(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch BDL stats for the inclusive [start_date, end_date] window."""
    print(f"  fetching BDL /nba/v1/stats {start_date} → {end_date}")
    started = time.time()
    raw = get_player_game_stats(start_date=start_date, end_date=end_date)
    print(f"    got {len(raw)} raw records in {time.time()-started:.1f}s")
    rows = [r for r in (_bdl_record_to_row(rec) for rec in raw) if r is not None]
    print(f"    {len(rows)} rows after schema map / min>=1 filter")
    if not rows:
        return pd.DataFrame(columns=TARGET_COLUMNS)
    df = pd.DataFrame(rows)
    # Conform to target column order; missing columns become NaN.
    for c in TARGET_COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA
    return df[TARGET_COLUMNS]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--start-date", default=None,
                     help="YYYY-MM-DD; default: latest_in_parquet + 1 day")
    ap.add_argument("--end-date", default=None,
                     help="YYYY-MM-DD; default: today (US/Eastern)")
    ap.add_argument("--season", type=int, default=None,
                     help="optional season filter for incoming rows "
                           "(e.g. 2025); skipped when unset")
    ap.add_argument("--dry-run", action="store_true",
                     help="fetch and report; do not write parquet")
    ap.add_argument("--force-rewrite", action="store_true",
                     help="rewrite all matched (game_id, player_id) keys "
                           "even if existing rows match (default: True)")
    args = ap.parse_args()

    if not os.environ.get("BDL_API_KEY", "").strip():
        print("FATAL: BDL_API_KEY not set", file=sys.stderr)
        return 2

    end_dt = (date.fromisoformat(args.end_date)
              if args.end_date else _today_eastern())
    if PARQUET_PATH.exists():
        existing = pd.read_parquet(PARQUET_PATH)
        latest_in = pd.to_datetime(existing["game_date"]).max().date()
        print(f"  existing parquet: {len(existing)} rows, "
              f"latest game_date={latest_in.isoformat()}")
    else:
        existing = pd.DataFrame(columns=TARGET_COLUMNS)
        latest_in = None
        print("  existing parquet: <missing> — will be created from this fetch")

    if args.start_date:
        start_dt = date.fromisoformat(args.start_date)
    else:
        start_dt = (latest_in + timedelta(days=1)) if latest_in else date(2024, 10, 1)

    if start_dt > end_dt:
        print(f"  start ({start_dt}) > end ({end_dt}); nothing to do.")
        return 0

    print("=" * 64)
    print(f"refresh_bdl_player_game_stats — {start_dt} → {end_dt}")
    print(f"  parquet={PARQUET_PATH.relative_to(REPO_ROOT)}")
    print(f"  dry_run={args.dry_run}  season_filter={args.season}")
    print("=" * 64)

    incoming = _fetch_window(start_dt.isoformat(), end_dt.isoformat())
    if args.season is not None and not incoming.empty:
        before = len(incoming)
        incoming = incoming[incoming["season"] == int(args.season)].reset_index(drop=True)
        print(f"  season filter dropped {before - len(incoming)} rows "
              f"(kept {len(incoming)})")

    if incoming.empty:
        # Before flagging as a real gap, check whether BDL scheduled any
        # games in this window.  On genuine rest days / off-nights BDL
        # returns an empty games list; zero stat rows are then expected and
        # the parquet is left unchanged (exit 0, valid-skip).  Only exit 1
        # when BDL confirms games were played but returned no stat rows,
        # which indicates a real data lag or API issue.
        try:
            games_in_window = get_games(
                start_date=start_dt.isoformat(),
                end_date=end_dt.isoformat(),
            )
        except Exception as exc:
            print(f"  WARN: BDL /v1/games check failed ({exc}); treating as data gap.")
            games_in_window = None  # unknown — fall through to exit 1

        if games_in_window is not None and len(games_in_window) == 0:
            print(
                f"  NO_GAMES_VALID_SKIP: BDL reports 0 games for "
                f"{start_dt} → {end_dt}; no stat rows expected."
            )
            return 0

        print("  WARN: BDL returned 0 mapped rows for this window.")
        # Don't write — exit non-zero so cron flags the gap.
        return 1

    print(f"\n  incoming rows: {len(incoming)}")
    print(f"    distinct game_dates: "
          f"{sorted(incoming['game_date'].astype(str).unique().tolist())}")
    print(f"    distinct game_ids:   {incoming['game_id'].nunique()}")
    print(f"    distinct players:    {incoming['player_id'].nunique()}")

    # Merge: keep INCOMING row when keys collide (BDL is authoritative for
    # already-final games). Then keep all old rows whose key is not in
    # incoming.
    if not existing.empty:
        existing = existing.copy()
        # Coerce column dtypes/order to match incoming so concat is clean.
        for c in TARGET_COLUMNS:
            if c not in existing.columns:
                existing[c] = pd.NA
        existing = existing[TARGET_COLUMNS]
        in_keys = set(zip(incoming["game_id"].astype(int),
                          incoming["player_id"].astype(int)))
        ex_keys = list(zip(existing["game_id"].astype(int),
                            existing["player_id"].astype(int)))
        keep_mask = [k not in in_keys for k in ex_keys]
        kept = existing[keep_mask].reset_index(drop=True)
        merged = pd.concat([kept, incoming], ignore_index=True)
        replaced = len(existing) - len(kept)
    else:
        merged = incoming.copy()
        replaced = 0

    merged = merged.sort_values(
        ["game_date", "game_id", "team_id", "player_id"]
    ).reset_index(drop=True)

    print(f"\n  merge summary:")
    print(f"    rows kept (no key conflict):     {len(merged) - len(incoming)}")
    print(f"    rows replaced (key conflict):    {replaced}")
    print(f"    rows added (new keys):           {len(incoming) - replaced}")
    print(f"    final row count:                 {len(merged)}")

    if args.dry_run:
        print("\n  dry-run; not writing.")
        return 0

    # Atomic write
    tmp = PARQUET_PATH.with_suffix(".parquet.tmp")
    merged.to_parquet(tmp, index=False)
    os.replace(tmp, PARQUET_PATH)
    print(f"\nwrote {PARQUET_PATH.relative_to(REPO_ROOT)}  ({_now_utc_iso()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
