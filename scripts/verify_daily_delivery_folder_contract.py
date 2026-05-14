#!/usr/bin/env python3
"""Verify required daily delivery subfolders exist for a slate date."""
from __future__ import annotations

import argparse
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
