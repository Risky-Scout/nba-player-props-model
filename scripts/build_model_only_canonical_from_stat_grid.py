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
