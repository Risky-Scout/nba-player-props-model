#!/usr/bin/env python3
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "data" / "oof_pmfs.parquet"
DST = REPO_ROOT / "data" / "oof_stat_pmf_predictions.parquet"


def main() -> int:
    if not SRC.exists():
        print("BUILD_STAT_PMF_OOF_FAIL", file=sys.stderr)
        return 2
    shutil.copy2(SRC, DST)
    print(f"STAT_PMF_OOF_ALIAS_PASS -> {DST.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
