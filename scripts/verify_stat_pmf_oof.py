#!/usr/bin/env python3
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
P = REPO_ROOT / "data" / "oof_stat_pmf_predictions.parquet"


def main() -> int:
    if not P.exists():
        print("STAT_PMF_OOF_VERIFY_FAIL", file=sys.stderr)
        return 2
    df = pd.read_parquet(P, columns=["stat", "pmf", "outcome"])
    assert len(df) > 0
    print(f"STAT_PMF_OOF_VERIFY_PASS rows={len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
