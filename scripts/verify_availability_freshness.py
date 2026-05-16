#!/usr/bin/env python3
"""Verify player_availability_asof.parquet exists and is fresh enough for production."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AV_PATH = REPO_ROOT / "data" / "player_availability_asof.parquet"


def _delivery_manifest_confirmed_no_games_slate(date: str) -> bool:
    """Strict 4-flag no-games gate for the availability-freshness check.

    Returns True if and only if the dated delivery manifest declares
    ALL of:

      * ``no_games_slate == True``
      * ``confirmed_no_games_slate == True``
      * ``reason == "no_games_slate"``
      * ``market_superiority_evaluated == False``
      * ``derek_forward_feed_expected == False``

    On a confirmed no-games slate the refresh step (which keeps
    ``player_availability_asof.parquet`` fresh) is skipped by design,
    so the close_lock 6h age gate cannot be met — that is not a
    regression. Any other manifest shape (missing flag, false flag,
    missing manifest, corrupt manifest, mismatched reason, missing
    confirmation fields) returns False so a games-bearing slate with
    a stale or missing availability parquet still hard-fails. These
    four fields are stamped together only by the orchestrator's
    ``_emit_no_games_delivery_package`` after BOTH the predict
    no-games signal AND an independent BDL ``/games`` schedule lookup
    have confirmed zero games for the date.
    """
    manifest_path = REPO_ROOT / "deliveries" / date / "manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    return (
        payload.get("no_games_slate") is True
        and payload.get("confirmed_no_games_slate") is True
        and payload.get("reason") == "no_games_slate"
        and payload.get("market_superiority_evaluated") is False
        and payload.get("derek_forward_feed_expected") is False
    )


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

    if _delivery_manifest_confirmed_no_games_slate(args.date):
        print(
            f"VERIFY_AVAILABILITY_FRESHNESS_SOFT_SKIP_NO_GAMES "
            f"date={args.date} "
            f"manifest=deliveries/{args.date}/manifest.json "
            f"gate=no_games_slate+confirmed_no_games_slate+"
            f"market_superiority_evaluated=false+derek_forward_feed_expected=false "
            f"reason=refresh_step_skipped_by_design_on_confirmed_no_games_slate"
        )
        return 0

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
