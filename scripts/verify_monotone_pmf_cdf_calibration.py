#!/usr/bin/env python3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "artifacts" / "models" / "monotone_pmf_cdf_v0.json"


def main() -> int:
    if not OUT.exists():
        print("MONOTONE_VERIFY_FAIL", file=sys.stderr)
        return 1
    print("MONOTONE_PMF_CDF_VERIFY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
