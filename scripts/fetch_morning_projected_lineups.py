#!/usr/bin/env python3
"""Fetch BDL lineup snapshots for every game on the morning slate.

This is a daily pre-lineup capture step: it records whatever BDL exposes
for each game (projected and/or confirmed rows) so the pipeline has an
explicit baseline before the t_minus_25 and close_lock reruns.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_game_ids(delivery_date: str) -> list[str]:
    p = REPO_ROOT / "predictions" / f"all_props_{delivery_date}.parquet"
    if not p.exists():
        return []
    df = pd.read_parquet(p)
    if "game_id" not in df.columns:
        return []
    ids = (
        df["game_id"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    return [x for x in ids if x.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--delivery-date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args(argv)

    if not os.environ.get("BDL_API_KEY", "").strip():
        print("MORNING_PROJECTED_LINEUPS_FETCH_FAILED", file=sys.stderr)
        print("  reason: BDL_API_KEY env var is not set", file=sys.stderr)
        return 1

    game_ids = _load_game_ids(args.delivery_date)
    if not game_ids:
        print(
            "MORNING_PROJECTED_LINEUPS_FETCH_PASS "
            f"date={args.delivery_date} games=0 reason=no_games_slate"
        )
        return 0

    # Local import keeps script startup cheap for non-run paths.
    from fetch_bdl_game_lineups import fetch_one

    ok = 0
    confirmed = 0
    partial = 0
    unavailable = 0
    failed_ids: list[str] = []

    for gid in game_ids:
        try:
            status = fetch_one(args.delivery_date, gid)
            ok += 1
            if bool(status.get("lineup_confirmed")):
                confirmed += 1
            else:
                comp = str(status.get("lineup_complete") or "").strip().lower()
                if comp == "partial":
                    partial += 1
                else:
                    unavailable += 1
        except Exception:
            failed_ids.append(gid)

    if failed_ids:
        print("MORNING_PROJECTED_LINEUPS_FETCH_FAILED", file=sys.stderr)
        print(
            f"  date={args.delivery_date} failed_games={len(failed_ids)} "
            f"game_ids={','.join(failed_ids[:10])}",
            file=sys.stderr,
        )
        return 1

    print(
        "MORNING_PROJECTED_LINEUPS_FETCH_PASS "
        f"date={args.delivery_date} games={len(game_ids)} "
        f"ok={ok} confirmed={confirmed} partial={partial} unavailable={unavailable}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
