#!/usr/bin/env python3
"""Verifier for minutes OOF quality + required diagnostics.

This must fail if required diagnostic fields are missing:
- DNP Brier + active logloss (requires `dnp_actual`, `dnp_prob_pred`, `active_prob_pred`)
- Role bucket confusion matrix inputs (`role_bucket_pred`, `role_bucket_actual`)
- Quantile coverage diagnostics (`minutes_q10`, `minutes_q50`, `minutes_q90`)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OOF = REPO_ROOT / "data" / "oof_minutes_predictions.parquet"

REQUIRED_COLS = [
    "game_date",
    "player_id",
    "minutes_actual",
    "minutes_pred",
    "minutes_baseline_roll10",
    "dnp_actual",
    "dnp_prob_pred",
    "active_prob_pred",
    "minutes_q10",
    "minutes_q50",
    "minutes_q90",
    "role_bucket_pred",
    "role_bucket_actual",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-improvement-vs-baseline", action="store_true")
    ap.add_argument("--mae-tolerance", type=float, default=1.08,
                    help="Fail if mae_model > baseline * tolerance (default 1.08)")
    args = ap.parse_args()

    if not OOF.exists():
        print("MINUTES_MODEL_OOF_FAIL missing data/oof_minutes_predictions.parquet", file=sys.stderr)
        return 2

    df = pd.read_parquet(OOF)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        print(f"MINUTES_MODEL_OOF_FAIL missing_required_cols={missing}", file=sys.stderr)
        return 2

    # Basic sanity
    for c in ["minutes_q10", "minutes_q50", "minutes_q90", "dnp_prob_pred", "active_prob_pred"]:
        if not np.isfinite(pd.to_numeric(df[c], errors="coerce")).all():
            print(f"MINUTES_MODEL_OOF_FAIL non_finite_in={c}", file=sys.stderr)
            return 2
    if (df["minutes_q10"] > df["minutes_q50"]).any() or (df["minutes_q50"] > df["minutes_q90"]).any():
        print("MINUTES_MODEL_OOF_FAIL quantiles_not_monotone", file=sys.stderr)
        return 1
    if ((df["dnp_prob_pred"] < -1e-9) | (df["dnp_prob_pred"] > 1 + 1e-9)).any():
        print("MINUTES_MODEL_OOF_FAIL dnp_prob_pred_out_of_range", file=sys.stderr)
        return 1
    if ((df["active_prob_pred"] < -1e-9) | (df["active_prob_pred"] > 1 + 1e-9)).any():
        print("MINUTES_MODEL_OOF_FAIL active_prob_pred_out_of_range", file=sys.stderr)
        return 1
    if np.max(np.abs((df["active_prob_pred"] + df["dnp_prob_pred"]) - 1.0)) > 1e-3:
        print("MINUTES_MODEL_OOF_FAIL active_plus_dnp_prob_not_one", file=sys.stderr)
        return 1

    mae_m = float(np.mean(np.abs(df["minutes_actual"] - df["minutes_pred"])))
    mae_b = float(np.mean(np.abs(df["minutes_actual"] - df["minutes_baseline_roll10"])))

    y_dnp = df["dnp_actual"].astype(int).to_numpy()
    p_dnp = df["dnp_prob_pred"].astype(float).to_numpy()
    dnp_brier = float(np.mean((y_dnp - p_dnp) ** 2))
    # Active logloss (label=1 means active).
    y_active = 1 - y_dnp
    p_active = np.clip(df["active_prob_pred"].astype(float).to_numpy(), 1e-6, 1 - 1e-6)
    active_logloss = float(-np.mean(y_active * np.log(p_active) + (1 - y_active) * np.log(1 - p_active)))

    y = df["minutes_actual"].astype(float).to_numpy()
    q10 = df["minutes_q10"].astype(float).to_numpy()
    q50 = df["minutes_q50"].astype(float).to_numpy()
    q90 = df["minutes_q90"].astype(float).to_numpy()
    cov10 = float(np.mean(y <= q10))
    cov50 = float(np.mean(y <= q50))
    cov90 = float(np.mean(y <= q90))

    # Role confusion matrix existence (content checked by diagnose script).
    if df["role_bucket_pred"].isna().all() or df["role_bucket_actual"].isna().all():
        print("MINUTES_MODEL_OOF_FAIL role_bucket_missing", file=sys.stderr)
        return 1

    if args.require_improvement_vs_baseline and mae_m > mae_b * args.mae_tolerance:
        print(
            f"MINUTES_MODEL_OOF_FAIL mae_model={mae_m:.4f} mae_baseline={mae_b:.4f} "
            f"tolerance={args.mae_tolerance}",
            file=sys.stderr,
        )
        return 1

    print(
        "MINUTES_MODEL_OOF_PASS "
        f"rows={len(df)} mae_model={mae_m:.4f} mae_baseline={mae_b:.4f} "
        f"dnp_brier={dnp_brier:.4f} active_logloss={active_logloss:.4f} "
        f"cov10={cov10:.3f} cov50={cov50:.3f} cov90={cov90:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
