#!/usr/bin/env python3
"""Verify player_availability_asof.parquet exists and is fresh enough for production."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AV_PATH = REPO_ROOT / "data" / "player_availability_asof.parquet"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="Slate date YYYY-MM-DD (for logging).")
    ap.add_argument(
        "--mode",
        default="close_lock",
        choices=(
            "close_lock",
            "final",
            "backtest",
            "development",
            "morning",
            "provisional_early_market",
        ),
        help=(
            "Strict age gate (>6h) applies to close_lock/final only. "
            "Relaxed modes skip the age gate (historical reruns, CI, or "
            "early-market snapshots where availability was just rebuilt)."
        ),
    )
    ap.add_argument(
        "--allow-historical",
        action="store_true",
        help="Skip strict age gate (historical reruns / CI without live refresh).",
    )
    args = ap.parse_args()

    if not AV_PATH.exists():
        print(f"AVAILABILITY_FRESHNESS_FAIL missing_file={AV_PATH}", file=sys.stderr)
        return 1

    age_h = (time.time() - AV_PATH.stat().st_mtime) / 3600.0
    print(f"availability_asof mtime_age_hours={age_h:.3f} path={AV_PATH}")

    relaxed_modes = frozenset({
        "backtest",
        "development",
        "morning",
        "provisional_early_market",
    })
    if args.allow_historical or args.mode in relaxed_modes:
        print(f"AVAILABILITY_FRESHNESS_PASS (relaxed mode={args.mode})")
        return 0

    if args.mode in ("close_lock", "final") and age_h > 6.0:
        print(
            f"AVAILABILITY_FRESHNESS_FAIL stale age_hours={age_h:.3f} max=6",
            file=sys.stderr,
        )
        return 1

    print("AVAILABILITY_FRESHNESS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
