#!/usr/bin/env python3
"""Role bucket + availability contract for stat_grid.

Must fail if:
- role_bucket missing or has unexpected values
- availability table is stale AND role_bucket contains `inactive_risk`
- required role/minutes diagnostics artifacts are missing
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

ALLOWED = frozenset({
    "bench", "core", "fringe", "inactive_risk", "rotation", "starter", "unknown",
})

ROLE_DIAG_DIR = REPO_ROOT / "artifacts" / "model_diagnostics" / "role_minutes"
REQUIRED_ROLE_DIAG = [
    ROLE_DIAG_DIR / "role_bucket_confusion.csv",
    ROLE_DIAG_DIR / "minutes_bias_by_role.csv",
    ROLE_DIAG_DIR / "summary.json",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    p = REPO_ROOT / "predictions" / f"stat_grid_{args.date}.parquet"
    if not p.exists():
        # stat_grid is produced by predict_daily (14:00 UTC). Phase 8 runs at
        # 9:30/12:30 UTC — before predict_daily. Valid-skip so Phase 8 can
        # commit fresh OOF artifacts; final_contract_verifiers re-checks after
        # predict_daily has run.
        print(f"ROLE_BUCKET_CONTRACT_VALID_SKIP stat_grid not yet available date={args.date!r}")
        return 0

    cols = [
        "role_bucket",
        "availability_table_freshness",
        "availability_blocks_market_superiority",
    ]
    try:
        df = pd.read_parquet(p, columns=cols)
    except Exception:
        # Older parquet engines / schema mismatches: read full and slice.
        full = pd.read_parquet(p)
        missing_cols = [c for c in cols if c not in full.columns]
        if missing_cols:
            if "role_bucket" not in full.columns:
                print(f"ROLE_BUCKET_CONTRACT_FAIL missing_cols={missing_cols}", file=sys.stderr)
                return 2
        df = full[[c for c in cols if c in full.columns]].copy()
    if df["role_bucket"].isna().all():
        print("ROLE_BUCKET_CONTRACT_FAIL all null", file=sys.stderr)
        return 1
    bad = set(df["role_bucket"].dropna().astype(str).unique()) - ALLOWED
    if bad:
        print(f"ROLE_BUCKET_CONTRACT_FAIL unexpected={sorted(bad)}", file=sys.stderr)
        return 1

    # If availability is stale, never allow inactive_risk (it would be treating stale
    # injury inputs as definitive DNP risk).
    if "availability_table_freshness" in df.columns:
        freshness = set(df["availability_table_freshness"].dropna().astype(str).unique())
        is_stale = any(f not in ("fresh", "ok", "ready") for f in freshness) and bool(freshness)
        if is_stale and (df["role_bucket"].astype(str) == "inactive_risk").any():
            print(
                f"ROLE_BUCKET_CONTRACT_FAIL stale_availability_has_inactive_risk freshness={sorted(freshness)}",
                file=sys.stderr,
            )
            return 1

    # Role diagnostics must be present (produced by diagnose_role_and_minutes_bias.py).
    missing = [str(x.relative_to(REPO_ROOT)) for x in REQUIRED_ROLE_DIAG if not x.exists()]
    if missing:
        print(f"ROLE_BUCKET_CONTRACT_FAIL missing_role_diagnostics={missing}", file=sys.stderr)
        return 2

    print(f"ROLE_BUCKET_CONTRACT_PASS date={args.date!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
