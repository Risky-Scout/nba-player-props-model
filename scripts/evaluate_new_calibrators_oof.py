#!/usr/bin/env python3
"""Evaluate new role-aware calibrators against old ones on OOF test data.

Loads data/oof_stat_pmf_predictions.parquet, applies both the old and new
pmf_cal_role_*.pkl calibrators, and reports Brier score + calibration error
by stat and role_bucket. This validates the new calibrators before the next
CI pipeline run applies them to actual deliveries.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.calibration.pmf_calibration import load_calibrator  # noqa: E402

OOF_PATH = REPO_ROOT / "data" / "oof_stat_pmf_predictions.parquet"
OUT_DIR = REPO_ROOT / "reports"

# Use the last 20% of OOF dates as holdout (same as calibrator validation split)
HOLDOUT_FRAC = 0.20
STATS = ["pts", "reb", "ast", "fg3m", "stl", "blk"]


def _pad_pmf(arr: np.ndarray, max_len: int) -> np.ndarray:
    p = np.asarray(arr, dtype=float)
    p = np.clip(np.nan_to_num(p, nan=0.0), 0.0, None)
    s = float(p.sum())
    if s > 0:
        p = p / s
    if len(p) >= max_len:
        return p[:max_len]
    out = np.zeros(max_len, dtype=float)
    out[:len(p)] = p
    return out


def _brier(p_over: np.ndarray, actual_over: np.ndarray) -> float:
    return float(np.mean((p_over - actual_over) ** 2))


def _ece(p_over: np.ndarray, actual_over: np.ndarray, n_bins: int = 10) -> float:
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(p_over)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (p_over >= lo) & (p_over < hi)
        if not mask.any():
            continue
        bin_pred = float(p_over[mask].mean())
        bin_actual = float(actual_over[mask].mean())
        ece += (mask.sum() / n) * abs(bin_pred - bin_actual)
    return float(ece)


def _mean_nll(pmfs: np.ndarray, outcomes: np.ndarray) -> float:
    nlls = []
    for pmf, y in zip(pmfs, outcomes):
        idx = min(int(y), len(pmf) - 1)
        p = max(float(pmf[idx]), 1e-12)
        nlls.append(-np.log(p))
    return float(np.mean(nlls)) if nlls else float("nan")


def main() -> int:
    if not OOF_PATH.exists():
        print(f"FATAL: {OOF_PATH} not found", file=sys.stderr)
        return 1

    df = pd.read_parquet(OOF_PATH)
    df["stat"] = df["stat"].astype(str).str.lower()
    df["game_date"] = df["game_date"].astype(str).str[:10]
    df["outcome"] = pd.to_numeric(df["outcome"], errors="coerce").fillna(0).astype(int)
    df["role_bucket"] = df["role_bucket"].fillna("unknown").astype(str).str.lower()

    # Use last 20% of dates as holdout
    all_dates = sorted(df["game_date"].unique())
    cut = int(len(all_dates) * (1 - HOLDOUT_FRAC))
    holdout_dates = set(all_dates[cut:])
    holdout = df[df["game_date"].isin(holdout_dates)].copy().reset_index(drop=True)
    print(f"Holdout: {len(holdout)} rows, dates {min(holdout_dates)} → {max(holdout_dates)}")

    rows = []
    for stat in STATS:
        sub = holdout[holdout["stat"] == stat].copy().reset_index(drop=True)
        if sub.empty:
            print(f"  [{stat}] no holdout rows")
            continue

        cal = load_calibrator(stat)
        if cal is None:
            print(f"  [{stat}] no calibrator found — skipping")
            continue

        pmf_col = "pmf_active" if "pmf_active" in sub.columns else "pmf"
        pmf_list = sub[pmf_col].tolist()
        max_len = max(len(np.asarray(p, dtype=float)) for p in pmf_list)
        raw_pmfs = np.stack([_pad_pmf(np.asarray(p, dtype=float), max_len) for p in pmf_list])
        outcomes = sub["outcome"].to_numpy(dtype=int)
        role_buckets = sub["role_bucket"].to_numpy(dtype=str)

        for role in sorted(sub["role_bucket"].unique()):
            mask = role_buckets == role
            if mask.sum() < 30:
                continue
            raw_sub = raw_pmfs[mask]
            out_sub = outcomes[mask]
            rb_sub = role_buckets[mask]

            # Apply new calibrators
            cal_pmfs = np.stack([
                cal.apply(raw_sub[i], role_bucket=rb_sub[i])
                if hasattr(cal, "apply") and "role_bucket" in cal.apply.__code__.co_varnames
                else cal.apply(raw_sub[i])
                for i in range(len(raw_sub))
            ])

            # For a "fair" line at the PMF median, compute over probability
            def get_p_over(pmf: np.ndarray, median_line: float) -> float:
                return float(sum(pmf[k] for k in range(len(pmf)) if k > median_line))

            # Use a line at ~50th percentile of model distribution
            raw_medians = np.array([
                float(np.argmax(np.cumsum(raw_sub[i]) >= 0.5))
                for i in range(len(raw_sub))
            ])

            # For each row, p_over at the median line
            raw_p_over = np.array([get_p_over(raw_sub[i], raw_medians[i] - 0.5) for i in range(len(raw_sub))])
            cal_p_over = np.array([get_p_over(cal_pmfs[i], raw_medians[i] - 0.5) for i in range(len(cal_pmfs))])
            actual_over = (out_sub > (raw_medians - 0.5)).astype(float)

            brier_raw = _brier(raw_p_over, actual_over)
            brier_cal = _brier(cal_p_over, actual_over)
            ece_raw = _ece(raw_p_over, actual_over)
            ece_cal = _ece(cal_p_over, actual_over)
            nll_raw = _mean_nll(raw_sub, out_sub)
            nll_cal = _mean_nll(cal_pmfs, out_sub)
            mean_err_raw = float(np.mean(raw_p_over) - np.mean(actual_over))
            mean_err_cal = float(np.mean(cal_p_over) - np.mean(actual_over))

            rows.append({
                "stat": stat,
                "role_bucket": role,
                "n": int(mask.sum()),
                "brier_raw": round(brier_raw, 4),
                "brier_cal": round(brier_cal, 4),
                "brier_delta": round(brier_cal - brier_raw, 4),
                "ece_raw": round(ece_raw, 4),
                "ece_cal": round(ece_cal, 4),
                "ece_delta": round(ece_cal - ece_raw, 4),
                "nll_raw": round(nll_raw, 4),
                "nll_cal": round(nll_cal, 4),
                "nll_delta": round(nll_cal - nll_raw, 4),
                "mean_err_raw": round(mean_err_raw, 4),
                "mean_err_cal": round(mean_err_cal, 4),
                "mean_err_delta": round(mean_err_cal - mean_err_raw, 4),
            })
            print(f"  [{stat}|{role}] n={mask.sum()} brier_raw={brier_raw:.4f} brier_cal={brier_cal:.4f} "
                  f"Δ={brier_cal - brier_raw:+.4f} ece_cal={ece_cal:.4f} mean_err_cal={mean_err_cal:+.4f}")

    result_df = pd.DataFrame(rows)
    if result_df.empty:
        print("No results to write.")
        return 1

    OUT_DIR.mkdir(exist_ok=True)
    result_df.to_csv(OUT_DIR / "new_calibrator_oof_evaluation.csv", index=False)
    print(f"\nSaved to reports/new_calibrator_oof_evaluation.csv")

    # Print summary by stat
    print("\nSummary by stat (mean across roles):")
    by_stat = result_df.groupby("stat")[["brier_raw","brier_cal","brier_delta","ece_cal","mean_err_cal"]].mean()
    print(by_stat.round(4).to_string())

    print("\nNEW_CALIBRATOR_EVAL_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
