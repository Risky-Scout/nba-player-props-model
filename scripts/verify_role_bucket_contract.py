#!/usr/bin/env python3
"""stat_grid role_bucket must be present and in known set."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

ALLOWED = frozenset({
    "bench", "core", "fringe", "inactive_risk", "rotation", "starter", "unknown",
})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    p = REPO_ROOT / "predictions" / f"stat_grid_{args.date}.parquet"
    if not p.exists():
        print(f"ROLE_BUCKET_CONTRACT_FAIL missing {p}", file=sys.stderr)
        return 2

    df = pd.read_parquet(p, columns=["role_bucket"])
    if df["role_bucket"].isna().all():
        print("ROLE_BUCKET_CONTRACT_FAIL all null", file=sys.stderr)
        return 1
    bad = set(df["role_bucket"].dropna().astype(str).unique()) - ALLOWED
    if bad:
        print(f"ROLE_BUCKET_CONTRACT_FAIL unexpected={sorted(bad)}", file=sys.stderr)
        return 1

    print(f"ROLE_BUCKET_CONTRACT_PASS date={args.date!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
