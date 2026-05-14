#!/usr/bin/env python3
"""Verify public WoO artifacts only reference mission-allowed canonical stats (12 incl. RA)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL, canonical

    allowed_c = {str(s).lower() for s in MISSION_REQUIRED_TARGETS_CANONICAL}

    def ok(tok: str) -> bool:
        t = str(tok).strip().lower()
        if not t:
            return True
        if t == "reb_ast":
            t = "ra"
        try:
            c = str(canonical(t)).lower()
        except Exception:
            c = t
        return c in allowed_c

    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    date = args.date

    targets = [
        REPO_ROOT / "predictions" / "nba-props.html",
        REPO_ROOT / "predictions" / "nba-pmf-research.html",
        REPO_ROOT / "public_export" / "wizard_of_odds" / date / "affiliate_dashboard.json",
        REPO_ROOT / "public_export" / "wizard_of_odds" / date / "pmf_research.json",
    ]

    bad: list[str] = []
    scanned = False
    for p in targets:
        if not p.exists():
            print(f"  skip (absent): {p.relative_to(REPO_ROOT)}")
            continue
        scanned = True
        text = p.read_text(encoding="utf-8", errors="replace")
        found: set[str] = set()
        for m in re.finditer(r'"stat"\s*:\s*"([^"]+)"', text):
            found.add(m.group(1))
        for m in re.finditer(r'"stat_key"\s*:\s*"([^"]+)"', text):
            found.add(m.group(1))
        for tok in sorted(found):
            if not ok(tok):
                bad.append(f"{p.name}: disallowed stat {tok!r}")
        print(f"  scanned: {p.relative_to(REPO_ROOT)} stat-like={sorted(found)} bad={len([b for b in bad if p.name in b])}")

    if not scanned:
        print("WOO_PUBLIC_TARGET_ALLOWLIST_PASS (no artifacts)")
        return 0
    if bad:
        print("WOO_PUBLIC_TARGET_ALLOWLIST_FAILED", file=sys.stderr)
        for b in bad:
            print(f"  {b}", file=sys.stderr)
        return 1
    print("WOO_PUBLIC_TARGET_ALLOWLIST_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
