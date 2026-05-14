#!/usr/bin/env python3
"""Remove Odds API artifact trees that use literal placeholder date/timestamp tokens.

Default is dry-run. Deletes only paths whose string form contains one of:
  YYYY-MM-DD
  YYYY-MM-DDTHHMMSSZ
  YYYY-MM-DDTHH:MM:SSZ
  THH:MM:SSZ

Real calendar paths (e.g. 2026-05-07) are never matched by the YYYY-MM-DD token
substring rule used here only when the segment is literally the template string.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Match only placeholder *path segments* / filenames, not real ISO dates.
PLACEHOLDER_SUBSTRINGS = (
    "YYYY-MM-DDTHH:MM:SSZ",
    "YYYY-MM-DDTHHMMSSZ",
    "THH:MM:SSZ",
)


def _is_placeholder_path(p: Path) -> bool:
    s = str(p)
    if any(tok in s for tok in PLACEHOLDER_SUBSTRINGS):
        return True
    parts = p.parts
    return "YYYY-MM-DD" in parts


def _iter_under_roots(roots: tuple[Path, ...]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if _is_placeholder_path(child):
                found.append(child)
    return sorted(set(found))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="List placeholder paths only (default if --apply not passed).",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete placeholder paths (default: dry-run only).",
    )
    args = ap.parse_args()
    do_apply = bool(args.apply)
    if args.dry_run and args.apply:
        print("FATAL: use only one of --dry-run or --apply", file=sys.stderr)
        return 2

    roots = (
        REPO_ROOT / "data" / "odds_api" / "raw",
        REPO_ROOT / "data" / "odds_api" / "processed",
    )
    targets = _iter_under_roots(roots)
    if not targets:
        print("CLEANUP_PLACEHOLDER_ODDS_ARTIFACTS_DRY_RUN n=0")
        return 0
    print(f"CLEANUP_PLACEHOLDER_ODDS_ARTIFACTS_{'APPLY' if args.apply else 'DRY_RUN'} n={len(targets)}")
    for t in targets:
        print(f"  {t.relative_to(REPO_ROOT)}")
    if not args.apply:
        return 0
    for t in targets:
        if t.is_dir():
            shutil.rmtree(t, ignore_errors=False)
        elif t.is_file():
            t.unlink(missing_ok=True)
    print("CLEANUP_PLACEHOLDER_ODDS_ARTIFACTS_APPLY_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
