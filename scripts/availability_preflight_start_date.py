#!/usr/bin/env python3
"""Compute the first availability date that needs refresh before a slate.

Prints:
- the requested slate date when the existing availability parquet is missing,
  empty, unreadable, lacks usable game_date values, or has no game_date column;
- an empty string when the existing table already covers the slate date;
- max(existing game_date) + 1 day when the table is stale.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


def compute_start_date(target_date: str, out_path: Path) -> str:
    target = date.fromisoformat(target_date)

    if not out_path.exists():
        return target.isoformat()

    try:
        df = pd.read_parquet(out_path, columns=["game_date"])
    except Exception:
        return target.isoformat()

    if df.empty or "game_date" not in df.columns:
        return target.isoformat()

    parsed = pd.to_datetime(df["game_date"], errors="coerce").dropna()
    if parsed.empty:
        return target.isoformat()

    max_date = parsed.max().date()
    if max_date >= target:
        return ""

    return (max_date + timedelta(days=1)).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Target slate/delivery date, YYYY-MM-DD.")
    parser.add_argument("--out", required=True, help="Availability parquet path.")
    args = parser.parse_args()

    print(compute_start_date(args.date, Path(args.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
