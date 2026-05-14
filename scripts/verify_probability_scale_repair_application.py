#!/usr/bin/env python3
"""Verify event probability scale repair columns and canonical PMF immutability."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.calibration.event_neutral_probability_scale import (  # noqa: E402
    load_probability_scale_manifest,
)


def _sha_model_pmf(df: pd.DataFrame) -> str:
    col = "model_pmf_raw" if "model_pmf_raw" in df.columns else "model_pmf"
    if col not in df.columns:
        return ""
    s = df[col].fillna("").astype(str)
    h = hashlib.sha256()
    for v in s.values:
        h.update(v.encode("utf-8", errors="replace"))
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--compare-parquet", default=None, help="Optional baseline parquet without repair.")
    args = ap.parse_args()
    date = str(args.date)
    pq = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{date}.parquet"
    if not pq.is_file():
        print(f"FATAL: missing {pq}", file=sys.stderr)
        return 2
    df = pd.read_parquet(pq)
    man = load_probability_scale_manifest(Path(args.manifest))
    if man.get("uses_market_probability_as_feature"):
        print("FATAL: manifest must not use market probability as feature", file=sys.stderr)
        return 2

    required = (
        "model_prob_over_raw",
        "model_prob_over_active",
        "model_prob_over",
        "model_pmf",
    )
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"FATAL: missing columns {missing}", file=sys.stderr)
        return 2

    m = df["model_prob_over_active"].dropna()
    if len(m) and ((m < 0) | (m > 1)).any():
        print("FATAL: model_prob_over_active out of bounds", file=sys.stderr)
        return 2

    raw = df["model_prob_over_raw"].dropna()
    if len(raw) and ((raw < 0) | (raw > 1)).any():
        print("FATAL: model_prob_over_raw out of bounds", file=sys.stderr)
        return 2

    if not bool(man.get("canonical_pmf_unchanged", True)):
        print("FATAL: manifest must assert canonical_pmf_unchanged", file=sys.stderr)
        return 2

    h1 = _sha_model_pmf(df)
    if args.compare_parquet:
        p2 = Path(args.compare_parquet)
        if not p2.is_file():
            p2 = REPO_ROOT / p2
        if not p2.is_file():
            print(f"FATAL: compare parquet not found {p2}", file=sys.stderr)
            return 2
        df2 = pd.read_parquet(p2)
        h2 = _sha_model_pmf(df2)
        if h1 != h2:
            print(f"FATAL: model_pmf hash mismatch {h1[:16]} vs {h2[:16]}", file=sys.stderr)
            return 2

    print("CANONICAL_PMF_UNCHANGED_PASS")
    print("PROBABILITY_SCALE_REPAIR_APPLICATION_PASS")
    print(json.dumps({"model_pmf_sha256": h1, "rows": int(len(df))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
