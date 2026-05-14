#!/usr/bin/env python3
"""Verify MODEL_ONLY parquet autodiscovery prefers canonical_source."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from delivery_model_only_paths import find_model_only_parquet_for_date  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD delivery date")
    args = ap.parse_args()
    d = str(args.date).strip()[:10]
    preferred = (
        REPO_ROOT / "deliveries" / d / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    chosen, cands, warn = find_model_only_parquet_for_date(REPO_ROOT, d)
    if warn:
        print(warn)
    if chosen is None:
        print("MODEL_ONLY_PARQUET_SELECTION_FAIL no MODEL_ONLY parquet under deliveries/", d)
        return 1
    if preferred.is_file():
        if chosen.resolve() != preferred.resolve():
            print(
                "MODEL_ONLY_PARQUET_SELECTION_FAIL",
                f"canonical_source exists but autodiscovery chose {chosen}",
            )
            return 1
    print(
        "MODEL_ONLY_PARQUET_SELECTION_PASS",
        f"chosen={chosen.relative_to(REPO_ROOT)} n_candidates={len(cands)}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
