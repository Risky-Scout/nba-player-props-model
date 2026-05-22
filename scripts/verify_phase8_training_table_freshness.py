#!/usr/bin/env python3
"""Phase 8 gate for persisted training_table freshness and availability coverage."""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import pandas as pd


def _parse_date(value: str, *, field: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except Exception as exc:
        raise ValueError(f"invalid_{field}:{value!r}") from exc


def verify_training_table(
    *,
    training_table: Path,
    as_of_date: dt.date,
    min_prob_active_coverage: float,
) -> tuple[bool, list[str]]:
    failures: list[str] = []

    if not training_table.is_file():
        return False, [f"missing_file:{training_table}"]

    df = pd.read_parquet(training_table)
    if df.empty:
        return False, ["row_count_zero"]

    if "game_date" not in df.columns:
        return False, ["missing_column:game_date"]
    if "prob_active" not in df.columns:
        return False, ["missing_column:prob_active"]

    game_dates = pd.to_datetime(df["game_date"], errors="coerce").dt.date
    if game_dates.isna().all():
        return False, ["invalid_game_date_values"]

    max_game_date = game_dates.max()
    if max_game_date < as_of_date:
        failures.append(
            f"stale_max_game_date:max={max_game_date.isoformat()}<as_of={as_of_date.isoformat()}"
        )

    as_of_mask = game_dates == as_of_date
    as_of_rows = int(as_of_mask.sum())
    if as_of_rows == 0:
        failures.append(f"missing_as_of_rows:as_of={as_of_date.isoformat()}")
        return False, failures

    prob_active = pd.to_numeric(df.loc[as_of_mask, "prob_active"], errors="coerce")
    coverage = float(prob_active.notna().mean())
    if coverage < min_prob_active_coverage:
        failures.append(
            "low_prob_active_coverage:"
            f"coverage={coverage:.4f}<min={min_prob_active_coverage:.4f}"
        )

    return not failures, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify persisted phase8 training_table recency and availability coverage."
    )
    parser.add_argument(
        "--training-table",
        type=Path,
        default=Path("data/training_table.parquet"),
        help="Path to training_table parquet.",
    )
    parser.add_argument(
        "--as-of-date",
        required=True,
        help="Required training cutoff date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--min-prob-active-coverage",
        type=float,
        default=0.80,
        help="Minimum non-null prob_active coverage on as-of-date rows.",
    )
    args = parser.parse_args(argv)

    try:
        as_of = _parse_date(args.as_of_date, field="as_of_date")
    except ValueError as exc:
        print("PHASE8_TRAINING_TABLE_FRESHNESS_FAIL", file=sys.stderr)
        print(f"  {exc}", file=sys.stderr)
        return 2

    ok, failures = verify_training_table(
        training_table=args.training_table,
        as_of_date=as_of,
        min_prob_active_coverage=float(args.min_prob_active_coverage),
    )
    if not ok:
        print("PHASE8_TRAINING_TABLE_FRESHNESS_FAIL")
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print("PHASE8_TRAINING_TABLE_FRESHNESS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

