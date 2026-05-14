#!/usr/bin/env python3
"""Basic leakage checks for player_game_features parquet (M8.6 D)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_SUBSTR = (
    "actual_pts",
    "actual_reb",
    "actual_ast",
    "postgame",
    "market_implied_pmf",
    "no_vig",
    "closing_line",
)

FORBIDDEN_EXACT = {"line", "odds", "pmf"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--snapshot", default="close_lock")
    args = ap.parse_args()

    p = (
        REPO_ROOT
        / "data"
        / "features"
        / f"player_game_features_{args.date}_{args.snapshot}.parquet"
    )
    if not p.exists():
        print(f"FEATURE_LEAKAGE_CONTRACT_FAIL missing {p}", file=sys.stderr)
        return 2

    df = pd.read_parquet(p)
    cols = [str(c).lower() for c in df.columns]
    bad = []
    for c in df.columns:
        cl = str(c).lower()
        if cl in FORBIDDEN_EXACT:
            bad.append(c)
        for tok in FORBIDDEN_SUBSTR:
            if tok in cl:
                bad.append(c)
    # Target-game box stats as raw columns (simple heuristic)
    for c in df.columns:
        if re.match(r"^(pts|reb|ast|stl|blk|tov|fg3m)_actual$", str(c).lower()):
            bad.append(c)

    if bad:
        print(
            "FEATURE_LEAKAGE_CONTRACT_FAIL forbidden_columns="
            f"{sorted(set(bad))}",
            file=sys.stderr,
        )
        return 1

    print("FEATURE_LEAKAGE_CONTRACT_PASS")
    print(f"  path={p.relative_to(REPO_ROOT)} rows={len(df)} cols={len(df.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
