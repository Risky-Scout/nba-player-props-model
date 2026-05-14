#!/usr/bin/env python3
"""Stat PMF models are produced by the aggregate calibration pipeline; this script is a noop hook."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    oof = REPO_ROOT / "data" / "oof_pmfs.parquet"
    if not oof.exists():
        print("STAT_PMF_TRAIN_SKIP no oof_pmfs", file=sys.stderr)
        return 2
    print("STAT_PMF_TRAIN_HOOK_PASS (use calibrate_pmf / stat_grid for production PMFs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
