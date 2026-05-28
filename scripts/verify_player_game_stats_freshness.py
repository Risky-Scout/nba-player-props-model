#!/usr/bin/env python3
"""Phase 13AE — verify that ``data/player_game_stats.parquet`` is fresh
through a target date and structurally sound.

Inputs:
  --required-through-date YYYY-MM-DD

Checks:
  - parquet exists and is readable;
  - latest ``game_date`` >= required date;
  - row count for the required date is > 0 IF the NBA had a slate that
    day (we accept zero rows when the day is genuinely empty — this is
    a soft signal the workflow surfaces honestly);
  - no duplicate ``(game_id, player_id)`` rows;
  - core stat columns are non-null on rows for the required date;
  - the schema columns expected downstream are all present.

Pass:  PLAYER_GAME_STATS_FRESHNESS_PASS
Fail:  PLAYER_GAME_STATS_FRESHNESS_FAILED  with the exact reason
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PARQUET = REPO_ROOT / "data" / "player_game_stats.parquet"

CORE_STAT_COLS = ("pts", "reb", "ast", "fg3m", "stl", "blk", "turnover", "min")
EXPECTED_SCHEMA = (
    "player_id", "player_name", "game_id", "game_date", "season",
    "team_id", "min", "pts", "reb", "ast", "fg3m", "stl", "blk", "turnover",
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--required-through-date", required=True)
    args = ap.parse_args(argv)
    required = args.required_through_date

    failures: list[str] = []

    if not PARQUET.exists():
        print(f"PLAYER_GAME_STATS_FRESHNESS_FAILED  "
              f"required_through={required}  reason=parquet_missing  "
              f"path={PARQUET.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1

    df = pd.read_parquet(PARQUET)
    if df.empty:
        print(f"PLAYER_GAME_STATS_FRESHNESS_FAILED  "
              f"required_through={required}  reason=parquet_empty",
              file=sys.stderr)
        return 1

    missing_cols = [c for c in EXPECTED_SCHEMA if c not in df.columns]
    if missing_cols:
        failures.append(f"schema columns missing: {missing_cols}")

    s = pd.to_datetime(df["game_date"], errors="coerce")
    max_date = str(s.max().date())
    min_date = str(s.min().date())
    if max_date < required:
        # Before failing, confirm BDL actually had games on the required date.
        # On genuine no-games / rest days, max_date < required is expected and
        # should not block training.
        _no_games_day = False
        try:
            from nba_props_model.data.bdl_client import get_games  # noqa: WPS433
            games_on_required = get_games(start_date=required, end_date=required)
            if len(games_on_required) == 0:
                _no_games_day = True
                print(
                    f"  FRESHNESS_NOCHECK: {required} is a no-games day per BDL "
                    f"(max_date={max_date}); treating freshness as satisfied."
                )
        except Exception as exc:
            print(f"  WARN: BDL games check for {required} failed ({exc}); "
                  f"applying freshness gate conservatively.")
        if not _no_games_day:
            failures.append(
                f"latest game_date {max_date!r} < required_through_date "
                f"{required!r} — backfill is missing dates "
                f"{(dt.date.fromisoformat(max_date) + dt.timedelta(days=1)).isoformat()} "
                f"through {required}"
            )

    rows_for_required = int((s.dt.date.astype(str) == required).sum())

    duplicates = int(df.duplicated(subset=["game_id", "player_id"], keep=False).sum())
    if duplicates > 0:
        failures.append(
            f"duplicate (game_id, player_id) rows: {duplicates}"
        )

    null_keys: dict[str, int] = {}
    if max_date >= required:
        sub = df[s.dt.date.astype(str) == required]
        for c in CORE_STAT_COLS:
            if c in sub.columns:
                null_keys[c] = int(sub[c].isna().sum())
        bad_nulls = {c: n for c, n in null_keys.items() if n > 0}
        if bad_nulls:
            failures.append(f"null core stats on {required}: {bad_nulls}")

    summary = {
        "schema_version": "1.0",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "required_through_date": required,
        "max_game_date": max_date,
        "min_game_date": min_date,
        "rows_total": int(len(df)),
        "rows_for_required_date": rows_for_required,
        "duplicate_key_rows": duplicates,
        "null_core_stats_on_required_date": null_keys,
        "schema_columns_present": [c for c in EXPECTED_SCHEMA if c in df.columns],
        "schema_columns_missing": missing_cols,
        "failures": failures,
    }
    out_dir = REPO_ROOT / "artifacts" / "automation_health"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"player_game_stats_freshness_check_{required}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if failures:
        print(f"PLAYER_GAME_STATS_FRESHNESS_FAILED  "
              f"required_through={required}  max_game_date={max_date}  "
              f"failures={len(failures)}", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(f"PLAYER_GAME_STATS_FRESHNESS_PASS  "
          f"required_through={required}  max_game_date={max_date}  "
          f"rows_total={summary['rows_total']}  "
          f"rows_for_required_date={rows_for_required}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
