#!/usr/bin/env python3
"""Verify MODEL_ONLY canonical has equal per-stat counts for all mission stats."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402

REQUIRED = {str(s).lower() for s in MISSION_REQUIRED_TARGETS_CANONICAL}


def _parse_pmf_minimal(s) -> bool:
    if s is None or (isinstance(s, float) and s != s):
        return False
    if isinstance(s, str):
        t = s.strip()
        if not t.startswith("{"):
            return False
        try:
            d = json.loads(t)
        except Exception:
            return False
        if not isinstance(d, dict) or not d:
            return False
        tot = sum(float(v) for v in d.values() if isinstance(v, (int, float)))
        return math.isfinite(tot) and tot > 0
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    d = str(args.date).strip()[:10]
    pq = REPO_ROOT / "deliveries" / d / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    if not pq.is_file():
        print(f"CANONICAL_RECTANGULARITY_FAIL missing {pq}", file=sys.stderr)
        return 2
    df = pd.read_parquet(pq)
    if "stat" not in df.columns:
        print("CANONICAL_RECTANGULARITY_FAIL missing stat column", file=sys.stderr)
        return 2
    stats = set(df["stat"].astype(str).str.lower())
    missing = sorted(REQUIRED - stats)
    extra = sorted(stats - REQUIRED)
    if missing or extra:
        print(
            f"CANONICAL_RECTANGULARITY_FAIL stat_set mismatch missing={missing} extra={extra}",
            file=sys.stderr,
        )
        return 1
    vc = df["stat"].astype(str).str.lower().value_counts()
    if vc.empty or vc.min() != vc.max():
        print(
            "CANONICAL_RECTANGULARITY_FAIL uneven counts "
            f"{vc.sort_index().to_dict()}",
            file=sys.stderr,
        )
        return 1
    pmf_col = "pmf_active" if "pmf_active" in df.columns else "pmf_json" if "pmf_json" in df.columns else None
    if pmf_col:
        bad = int((~df[pmf_col].map(_parse_pmf_minimal)).sum())
        if bad:
            print(f"CANONICAL_RECTANGULARITY_FAIL invalid_pmfs n={bad}", file=sys.stderr)
            return 1
    if "role_bucket" in df.columns:
        rb = df["role_bucket"].isna() | (
            df["role_bucket"].astype(str).str.lower().isin(["", "none", "nan", "unknown"])
        )
        if bool(rb.any()):
            print(
                f"CANONICAL_RECTANGULARITY_FAIL missing role_bucket n={int(rb.sum())}",
                file=sys.stderr,
            )
            return 1
    print("CANONICAL_MODEL_ONLY_RECTANGULARITY_PASS")
    print(f"  rows={len(df)} per_stat={int(vc.iloc[0])} stats={sorted(REQUIRED)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
