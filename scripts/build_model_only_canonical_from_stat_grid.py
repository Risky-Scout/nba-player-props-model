#!/usr/bin/env python3
"""Build canonical MODEL_ONLY PMF parquet from predictions/stat_grid_DATE.parquet.

This is the PMF-only bridge for Derek/WoO delivery automation:
  build_stat_grid_pmfs.py
  -> build_model_only_canonical_from_stat_grid.py
  -> build_daily_pmf_delivery.py --model-only ...

It does not rename or remove fields. It reuses the canonical stat-grid row
mapping already defined in build_daily_pmf_delivery.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_daily_pmf_delivery import _stat_grid_rows



REQUIRED_TARGET_STATS = ["ast", "fg3m", "pts", "reb", "tov"]


def _enforce_complete_stat_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Drop incomplete player-game pairs so MODEL_ONLY has even stat counts."""
    stat_col = "stat" if "stat" in df.columns else "target_stat" if "target_stat" in df.columns else None
    if stat_col is None:
        raise SystemExit("FATAL: STAT_GRID_RECTANGULARIZE_FAILED missing stat/target_stat column")

    key_options = [
        ["game_id", "player_id"],
        ["event_id", "player_id"],
        ["game_id", "player_name"],
        ["event_id", "player_name"],
        ["player_id", "team", "opponent"],
        ["player_name", "team", "opponent"],
        ["player_name", "team_abbr", "opponent_abbr"],
    ]
    key_cols = next((cols for cols in key_options if all(c in df.columns for c in cols)), None)
    if key_cols is None:
        raise SystemExit(
            "FATAL: STAT_GRID_RECTANGULARIZE_FAILED missing player-game key columns "
            f"columns={list(df.columns)}"
        )

    work = df.copy()
    work[stat_col] = work[stat_col].astype(str)
    work = work.drop_duplicates(key_cols + [stat_col], keep="first")

    before_rows = len(work)
    before_pairs = work[key_cols].drop_duplicates().shape[0]
    before_counts = work[stat_col].value_counts().sort_index().to_dict()

    present = set(work[stat_col].dropna().astype(str))
    missing = sorted(set(REQUIRED_TARGET_STATS) - present)
    if missing:
        raise SystemExit(
            "FATAL: STAT_GRID_RECTANGULARIZE_FAILED missing required target stats "
            f"missing={missing} present={sorted(present)}"
        )

    complete = (
        work.groupby(key_cols, dropna=False)[stat_col]
        .agg(lambda x: set(x))
        .reset_index(name="_stats")
    )
    complete = complete[
        complete["_stats"].apply(lambda stats: set(REQUIRED_TARGET_STATS).issubset(stats))
    ].drop(columns=["_stats"])

    if len(complete) == before_pairs:
        print(
            "STAT_GRID_RECTANGULARIZE_PASS "
            f"rows={before_rows} pairs={before_pairs} counts={before_counts}"
        )
        return work

    filtered = work.merge(complete, on=key_cols, how="inner")
    after_counts = filtered[stat_col].value_counts().sort_index().to_dict()
    after_pairs = filtered[key_cols].drop_duplicates().shape[0]

    print(
        "STAT_GRID_RECTANGULARIZE_WARN "
        f"key_cols={key_cols} before_rows={before_rows} after_rows={len(filtered)} "
        f"before_pairs={before_pairs} after_pairs={after_pairs} "
        f"dropped_incomplete_pairs={before_pairs - after_pairs} "
        f"before_counts={before_counts} after_counts={after_counts}"
    )

    if set(after_counts) != set(REQUIRED_TARGET_STATS) or len(set(after_counts.values())) != 1:
        raise SystemExit(
            "FATAL: STAT_GRID_RECTANGULARIZE_FAILED uneven counts remain "
            f"after_counts={after_counts}"
        )

    return filtered


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument(
        "--canonical-dir",
        default=None,
        help="default: deliveries/{date}/canonical_source",
    )
    args = ap.parse_args(argv)

    date = args.date
    stat_grid_path = REPO_ROOT / "predictions" / f"stat_grid_{date}.parquet"
    if not stat_grid_path.exists():
        print(f"FATAL: missing {stat_grid_path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1

    rows = _stat_grid_rows(date)
    if not rows:
        print(f"FATAL: no canonical rows produced from {stat_grid_path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1

    out_dir = Path(args.canonical_dir or REPO_ROOT / "deliveries" / date / "canonical_source")
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    df = _enforce_complete_stat_grid(df)

    pq_path = out_dir / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    jsonl_path = out_dir / "player_prop_pmfs_tonight_MODEL_ONLY.jsonl"
    csv_path = out_dir / "player_prop_pmfs_tonight_MODEL_ONLY.csv"

    df.to_parquet(pq_path, index=False)
    df.to_json(jsonl_path, orient="records", lines=True)
    df.to_csv(csv_path, index=False)

    print("=" * 72)
    print(f"build_model_only_canonical_from_stat_grid — date={date}")
    print(f"source: {stat_grid_path.relative_to(REPO_ROOT)}")
    print(f"rows: {len(df)}")
    if "stat" in df.columns:
        print("stat_counts:")
        print(df["stat"].astype(str).value_counts().sort_index().to_string())
    if "player_id" in df.columns:
        print(f"players: {df['player_id'].nunique()}")
    print(f"wrote: {pq_path.relative_to(REPO_ROOT)}")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
