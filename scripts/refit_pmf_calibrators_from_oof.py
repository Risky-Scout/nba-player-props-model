#!/usr/bin/env python3
"""Refit role-aware PMF calibrators directly from OOF predictions parquet.

Uses data/oof_stat_pmf_predictions.parquet (Dec 2025 – May 2026, 153K rows)
with min_train_days=90 and fold_days=28 to produce stable isotonic calibrators
that are not biased by the small playoff-only sample in the current pkl files.

Writes: artifacts/models/pmf_cal_role_{stat}.pkl for each stat in OOF data.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.calibration.pmf_calibration import (  # noqa: E402
    fit_role_aware_calibrator,
    fit_all,
)

STATS = ["pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "stocks"]
OOF_PATH = REPO_ROOT / "data" / "oof_stat_pmf_predictions.parquet"


def _pad_pmfs(pmf_list: list[np.ndarray], max_len: int) -> np.ndarray:
    """Pad list of 1-D PMF arrays to (N, max_len) matrix."""
    out = np.zeros((len(pmf_list), max_len), dtype=float)
    for i, p in enumerate(pmf_list):
        arr = np.asarray(p, dtype=float)
        arr = np.clip(np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
        s = float(arr.sum())
        if s > 0:
            arr = arr / s
        n = min(len(arr), max_len)
        out[i, :n] = arr[:n]
    # Renormalize rows
    row_sums = out.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    return out / row_sums


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", default=",".join(STATS),
                    help="Comma-separated stats to refit (default: all)")
    ap.add_argument("--fold-days", type=int, default=28)
    ap.add_argument("--min-train-days", type=int, default=90)
    ap.add_argument("--oof", default=str(OOF_PATH))
    args = ap.parse_args()

    target_stats = [s.strip().lower() for s in args.stats.split(",") if s.strip()]
    oof_path = Path(args.oof)
    if not oof_path.exists():
        print(f"FATAL: OOF file not found: {oof_path}", file=sys.stderr)
        return 1

    df = pd.read_parquet(oof_path)
    df["stat"] = df["stat"].astype(str).str.lower()
    df["game_date"] = df["game_date"].astype(str).str[:10]
    df["outcome"] = pd.to_numeric(df["outcome"], errors="coerce").fillna(0).astype(int)
    df["role_bucket"] = df["role_bucket"].fillna("unknown").astype(str).str.lower()

    per_stat_inputs: dict[str, tuple] = {}

    for stat in target_stats:
        sub = df[df["stat"] == stat].copy().reset_index(drop=True)
        if sub.empty:
            print(f"  [{stat}] no rows — skipping")
            continue

        pmf_col = "pmf_active" if "pmf_active" in sub.columns else "pmf"
        pmf_list = sub[pmf_col].tolist()

        # Determine max PMF length
        lengths = [len(np.asarray(p, dtype=float)) for p in pmf_list]
        max_len = max(lengths)

        pmfs = _pad_pmfs(pmf_list, max_len)
        outcomes = sub["outcome"].to_numpy(dtype=int)
        dates = sub["game_date"].to_numpy()
        role_buckets = sub["role_bucket"].to_numpy(dtype=str)

        n_dates = len(np.unique(dates))
        print(f"  [{stat}] n={len(sub)}, n_dates={n_dates}, pmf_len={max_len}")
        per_stat_inputs[stat] = (pmfs, outcomes, dates, role_buckets)

    if not per_stat_inputs:
        print("FATAL: no stats with usable data", file=sys.stderr)
        return 1

    print(f"\nFitting {len(per_stat_inputs)} stats with "
          f"fold_days={args.fold_days}, min_train_days={args.min_train_days}...")

    meta = fit_all(
        per_stat_inputs,
        fold_days=args.fold_days,
        min_train_days=args.min_train_days,
    )

    print("\nResults:")
    for stat, info in meta.get("stats", {}).items():
        fitted = info.get("fitted", False)
        n = info.get("n_train", 0)
        spans = info.get("fold_spans", [])
        buckets = info.get("fitted_buckets", [])
        pit_raw = info.get("pit_mean_raw", float("nan"))
        pit_cal = info.get("pit_mean_cal", float("nan"))
        print(f"  {stat}: fitted={fitted} n_train={n} folds={len(spans)} "
              f"buckets={buckets} pit_raw={pit_raw:.3f} pit_cal={pit_cal:.3f}")

    print("\nREFIT_PMF_CALIBRATORS_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
