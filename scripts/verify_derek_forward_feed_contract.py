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


# Modes for which derek_forward_feed.parquet is OPTIONAL per the M8.8
# delivery contract (DEREK_UNIFIED_REQUIRED_COLUMNS spec in
# nba_props_model.delivery.delivery_contract). The historical strict
# behaviour ignored run_mode entirely and red-flagged every after-game
# slate that the producer honestly skipped because there were no rows
# to write (no-game-day, empty pipeline). We now mirror the spec.
_OPTIONAL_PARQUET_RUN_MODES = frozenset({"final_after_game", "backtest"})


def _detect_honest_skip(feed_dir: Path, date: str) -> tuple[bool, str]:
    """Return (is_honest_skip, reason) when the producer documented why
    derek_forward_feed.parquet is absent. We look for any of the
    sentinel files the orchestrator / builder write on no-game slates.

    Order: builder skip JSON, after-game no-games status JSON, slate-
    level no_games_today.json. Each is sufficient on its own.
    """
    skip = feed_dir / "derek_forward_feed_unified_skip.json"
    if skip.is_file():
        return True, "builder_emitted_unified_skip"
    no_games_status = feed_dir / "after_game_no_games_status.json"
    if no_games_status.is_file():
        return True, "after_game_no_games_prev_day"
    slate_sentinel = feed_dir.parent / "no_games_today.json"
    if slate_sentinel.is_file():
        return True, "slate_no_games_today_sentinel"
    return False, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument(
        "--repo-root",
        default=None,
        help="Override repository root (testing only).",
    )
    ap.add_argument(
        "--run-mode",
        default=None,
        help=(
            "Active M8.8 run mode (morning_expected|t25|t5|final_after_game|"
            "backtest). When set to a mode where derek_forward_feed.parquet "
            "is OPTIONAL per the delivery contract and an honest no-game "
            "skip marker is on disk, the verifier emits a non-fatal "
            "CONTRACT_VALID_SKIP and returns 0 instead of failing."
        ),
    )
    args = ap.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    feed_dir = root / "deliveries" / args.date / "derek_forward_feed"
    pq = feed_dir / "derek_forward_feed.parquet"

    if not pq.is_file():
        is_skip, reason = _detect_honest_skip(feed_dir, args.date)
        run_mode = (args.run_mode or "").strip().lower()
        if is_skip and run_mode in _OPTIONAL_PARQUET_RUN_MODES:
            print(
                "DEREK_FORWARD_FEED_CONTRACT_VALID_SKIP "
                f"date={args.date} run_mode={run_mode} reason={reason}"
            )
            return 0
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
