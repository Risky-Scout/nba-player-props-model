#!/usr/bin/env python3
"""Fail if production workflows reference legacy prediction artifact paths."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

PRODUCTION_WORKFLOWS = ("daily_pmf_delivery.yml", "derek_live_game_snapshots.yml")

FORBIDDEN = re.compile(
    r"singles_\*\.json|sgps_\*\.json|paper_trade_log\.csv|nba_props_today",
    re.IGNORECASE,
)


def main() -> int:
    bad: list[str] = []
    for name in PRODUCTION_WORKFLOWS:
        path = WORKFLOWS / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("#"):
                continue
            if FORBIDDEN.search(line):
                bad.append(f"{name}:{i}:{line.strip()[:120]}")
    if bad:
        print("LEGACY_PREDICTION_ARTIFACT_REFERENCE_FAIL", file=sys.stderr)
        for b in bad[:50]:
            print(f"  {b}", file=sys.stderr)
        return 1
    print("NO_LEGACY_PREDICTION_ARTIFACTS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
