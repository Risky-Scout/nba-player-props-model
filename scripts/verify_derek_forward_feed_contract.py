#!/usr/bin/env python3
"""M8.8 — verify ``derek_forward_feed`` unified export matches delivery contract."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.delivery.delivery_contract import (  # noqa: E402
    DEREK_UNIFIED_REQUIRED_COLUMNS,
    banned_placeholder_tokens,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument(
        "--repo-root",
        default=None,
        help="Override repository root (testing only).",
    )
    args = ap.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    feed_dir = root / "deliveries" / args.date / "derek_forward_feed"
    pq = feed_dir / "derek_forward_feed.parquet"
    if not pq.is_file():
        print("DEREK_FORWARD_FEED_CONTRACT_FAIL missing derek_forward_feed.parquet")
        return 2
    df = pd.read_parquet(pq)
    miss = [c for c in DEREK_UNIFIED_REQUIRED_COLUMNS if c not in df.columns]
    if miss:
        print(f"DEREK_FORWARD_FEED_CONTRACT_FAIL missing_columns={miss[:12]}")
        return 2
    banned = [b.lower() for b in banned_placeholder_tokens()]
    for col in df.select_dtypes(include=["object"]).columns:
        ser = df[col].dropna().astype(str).str.lower()
        for v in ser.unique()[:500]:
            for b in banned:
                if b in v:
                    print(f"DEREK_FORWARD_FEED_CONTRACT_FAIL banned_token col={col} token={b}")
                    return 2
    print("DEREK_FORWARD_FEED_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
