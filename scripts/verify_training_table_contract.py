#!/usr/bin/env python3
"""Validate training_table.parquet for diagnostics / calibration consumers."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Columns required by scripts/run_diagnostics._build_legacy_pmfs_for_rows lookup
REQUIRED_BASE = (
    "stat",
    "player_id",
    "game_id",
    "game_date",
    "actual",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", type=Path, default=Path("data/training_table.parquet"))
    args = ap.parse_args()
    fails: list[str] = []

    if not args.path.is_file():
        fails.append(f"missing_file:{args.path}")
        print("TRAINING_TABLE_CONTRACT_FAIL")
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1

    df = pd.read_parquet(args.path)
    n = len(df)
    if n <= 0:
        fails.append("row_count_zero")

    for c in REQUIRED_BASE:
        if c not in df.columns:
            fails.append(f"missing_column:{c}")

    if not fails:
        for c in REQUIRED_BASE:
            if c in df.columns and df[c].isna().all():
                fails.append(f"all_null:{c}")

    for c in REQUIRED_BASE:
        if c not in df.columns or fails:
            continue
        if c in ("stat", "game_date"):
            continue
        if not np.issubdtype(df[c].dtype, np.number):
            s = pd.to_numeric(df[c], errors="coerce")
        else:
            s = pd.to_numeric(df[c], errors="coerce")
        arr = s.to_numpy(dtype=float, na_value=np.nan)
        finite = arr[np.isfinite(arr)]
        if len(finite) == 0:
            continue
        if not np.all(np.isfinite(arr)):
            fails.append(f"non_finite:{c}")

    if fails:
        print("TRAINING_TABLE_CONTRACT_FAIL")
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1

    print("TRAINING_TABLE_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
