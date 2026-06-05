#!/usr/bin/env python3
"""Refit role-aware PMF calibrators directly from OOF predictions parquets.

Handles both single-stat OOF (data/oof_stat_pmf_predictions.parquet) and
combo-stat OOF (data/oof_combo_pmfs.parquet — pa, pr, ra, pra, stocks).

Writes: artifacts/models/pmf_cal_role_{stat}.pkl for each stat processed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.calibration.pmf_calibration import fit_all  # noqa: E402

STATS = ["pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "stocks"]
COMBO_STATS = {"pa", "pr", "ra", "pra"}
OOF_PATH = REPO_ROOT / "data" / "oof_stat_pmf_predictions.parquet"
OOF_COMBO_PATH = REPO_ROOT / "data" / "oof_combo_pmfs.parquet"


def _parse_pmf_cell(v) -> np.ndarray | None:
    """Parse a PMF cell that may be ndarray, list, or dict."""
    if v is None:
        return None
    if isinstance(v, np.ndarray):
        return v.astype(float)
    if isinstance(v, list):
        return np.asarray(v, dtype=float)
    if isinstance(v, dict):
        if not v:
            return None
        ks = sorted(int(k) for k in v.keys())
        max_k = max(ks) + 1
        arr = np.zeros(max_k, dtype=float)
        for k, p in v.items():
            ki = int(k)
            if 0 <= ki < max_k:
                arr[ki] = float(p)
        return arr
    if isinstance(v, str):
        import json
        try:
            return _parse_pmf_cell(json.loads(v))
        except Exception:
            return None
    return None


def _pad_pmfs(pmf_list: list, max_len: int) -> np.ndarray:
    """Pad list of PMF values (any format) to (N, max_len) matrix."""
    out = np.zeros((len(pmf_list), max_len), dtype=float)
    for i, p in enumerate(pmf_list):
        arr = _parse_pmf_cell(p)
        if arr is None:
            continue
        arr = np.clip(np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
        s = float(arr.sum())
        if s > 0:
            arr = arr / s
        n = min(len(arr), max_len)
        out[i, :n] = arr[:n]
    row_sums = out.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    return out / row_sums


def _load_and_prepare(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["stat"] = df["stat"].astype(str).str.lower()
    df["game_date"] = df["game_date"].astype(str).str[:10]
    df["outcome"] = pd.to_numeric(df["outcome"], errors="coerce").fillna(0).astype(int)
    df["role_bucket"] = df["role_bucket"].fillna("unknown").astype(str).str.lower()
    return df


def _build_inputs(df: pd.DataFrame, target_stats: list[str]) -> dict[str, tuple]:
    per_stat_inputs: dict[str, tuple] = {}
    for stat in target_stats:
        sub = df[df["stat"] == stat].copy().reset_index(drop=True)
        if sub.empty:
            print(f"  [{stat}] no rows — skipping")
            continue
        pmf_col = "pmf_active" if "pmf_active" in sub.columns else "pmf"
        pmf_list = sub[pmf_col].tolist()
        lengths = []
        for p in pmf_list:
            arr = _parse_pmf_cell(p)
            lengths.append(len(arr) if arr is not None else 0)
        max_len = max((l for l in lengths if l > 0), default=1)
        pmfs = _pad_pmfs(pmf_list, max_len)
        outcomes = sub["outcome"].to_numpy(dtype=int)
        dates = sub["game_date"].to_numpy()
        role_buckets = sub["role_bucket"].to_numpy(dtype=str)
        n_dates = len(np.unique(dates))
        print(f"  [{stat}] n={len(sub)}, n_dates={n_dates}, pmf_len={max_len}")
        per_stat_inputs[stat] = (pmfs, outcomes, dates, role_buckets)
    return per_stat_inputs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", default=",".join(STATS),
                    help="Comma-separated stats to refit (default: single-stat set)")
    ap.add_argument("--fold-days", type=int, default=28)
    ap.add_argument("--min-train-days", type=int, default=90)
    ap.add_argument("--oof", default=str(OOF_PATH),
                    help="Path to single-stat OOF parquet")
    ap.add_argument("--oof-combo", default=None,
                    help="Path to combo-stat OOF parquet (pa, pr, ra, pra, stocks)")
    args = ap.parse_args()

    target_stats = [s.strip().lower() for s in args.stats.split(",") if s.strip()]
    single_stats = [s for s in target_stats if s not in COMBO_STATS]
    combo_stats = [s for s in target_stats if s in COMBO_STATS]

    per_stat_inputs: dict[str, tuple] = {}

    # Load single-stat OOF
    if single_stats:
        oof_path = Path(args.oof)
        if not oof_path.exists():
            print(f"FATAL: OOF file not found: {oof_path}", file=sys.stderr)
            return 1
        df_single = _load_and_prepare(oof_path)
        inputs = _build_inputs(df_single, single_stats)
        per_stat_inputs.update(inputs)

    # Load combo-stat OOF
    if combo_stats:
        combo_path = Path(args.oof_combo) if args.oof_combo else OOF_COMBO_PATH
        if not combo_path.exists():
            print(f"FATAL: combo OOF file not found: {combo_path}", file=sys.stderr)
            return 1
        df_combo = _load_and_prepare(combo_path)
        inputs = _build_inputs(df_combo, combo_stats)
        per_stat_inputs.update(inputs)

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
