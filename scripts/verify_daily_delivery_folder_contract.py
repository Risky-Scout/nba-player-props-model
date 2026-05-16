#!/usr/bin/env python3
"""Verify required daily delivery subfolders exist for a slate date."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SUBDIRS = (
    "canonical_source",
    "derek_forward_feed",
    "wizard_of_odds",
    "after_game_scoring",
    "pmf_model_review_package",
)


def _delivery_manifest_confirmed_no_games_slate(date: str) -> bool:
    """Strict 4-flag no-games gate for the M8.6 folder-contract verifier.

    Returns True if and only if the dated delivery manifest declares
    ALL of:

      * ``no_games_slate == True``
      * ``confirmed_no_games_slate == True``
      * ``reason == "no_games_slate"``
      * ``market_superiority_evaluated == False``
      * ``derek_forward_feed_expected == False``

    Any partial / missing / corrupt manifest returns False so a
    games-bearing slate with a missing ``pmf_model_review_package``
    subdir (or any other required subdir) still hard-fails. These four
    fields are stamped together only by the orchestrator's
    ``_emit_no_games_delivery_package`` after BOTH the predict
    no-games signal AND an independent BDL ``/games`` schedule lookup
    have confirmed zero games for the date — so a False return here
    cannot be produced by API failures, schedule lookup failures, or
    missing inventory on a games-bearing slate.
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
    ap.add_argument("--date", required=True)
    ap.add_argument("--list-sample", type=int, default=10, help="max files to list per folder")
    ap.add_argument(
        "--allow-missing",
        nargs="*",
        default=(),
        help="Subdir names under deliveries/{date}/ that may be absent "
        "(e.g. after_game_scoring before the after_game scorer runs).",
    )
    args = ap.parse_args()
    if _delivery_manifest_confirmed_no_games_slate(args.date):
        print(
            f"VERIFY_DAILY_DELIVERY_FOLDER_CONTRACT_SOFT_SKIP_NO_GAMES "
            f"date={args.date} "
            f"manifest=deliveries/{args.date}/manifest.json "
            f"gate=no_games_slate+confirmed_no_games_slate+"
            f"market_superiority_evaluated=false+derek_forward_feed_expected=false "
            f"reason=no_eligible_player_game_rows_expected"
        )
        return 0
    root = REPO_ROOT / "deliveries" / args.date
    if not root.is_dir():
        print(f"DAILY_DELIVERY_CONTRACT_FAIL missing {root}", file=sys.stderr)
        return 1
    skip = set(args.allow_missing)
    unknown = skip - set(REQUIRED_SUBDIRS)
    if unknown:
        print(f"DAILY_DELIVERY_CONTRACT_FAIL unknown_allow_missing={sorted(unknown)}", file=sys.stderr)
        return 1
    required = tuple(d for d in REQUIRED_SUBDIRS if d not in skip)
    missing = [d for d in required if not (root / d).is_dir()]
    if missing:
        print(f"DAILY_DELIVERY_CONTRACT_FAIL missing_subdirs={missing}", file=sys.stderr)
        return 1
    for d in required:
        p = root / d
        files = sorted(p.rglob("*"))[: max(0, args.list_sample)]
        print(f"  {d}/ sample_files={len(files)}")
    print("DAILY_DELIVERY_FOLDER_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
