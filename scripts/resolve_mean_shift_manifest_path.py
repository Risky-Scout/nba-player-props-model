#!/usr/bin/env python3
"""Print path of the most recently-dated PMF mean shift repair manifest.

Always exits 0. Prints empty string if nothing is found.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS = REPO_ROOT / "artifacts" / "models"


def main() -> int:
    candidates = list(MODELS.glob("pmf_mean_shift_repair_*.json"))
    if not candidates:
        print("", end="")
        return 0
    dated = sorted(
        [c for c in candidates if re.search(r"\d{4}-\d{2}-\d{2}", c.name)],
        key=lambda p: re.search(r"(\d{4}-\d{2}-\d{2})", p.name).group(1),
        reverse=True,
    )
    result = dated[0] if dated else sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
