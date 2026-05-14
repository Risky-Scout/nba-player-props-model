#!/usr/bin/env python3
"""Role + minutes diagnostics from OOF minutes predictions.

Writes (required by Phase 3/4 verifiers):
- artifacts/model_diagnostics/role_minutes/role_bucket_confusion.csv
- artifacts/model_diagnostics/role_minutes/minutes_bias_by_role.csv
- artifacts/model_diagnostics/role_minutes/summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OOF = REPO_ROOT / "data" / "oof_minutes_predictions.parquet"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="artifacts/model_diagnostics/role_minutes")
    args = ap.parse_args()

    if not OOF.exists():
        print("SKIP: no oof_minutes_predictions.parquet", file=sys.stderr)
        return 0

    df = pd.read_parquet(OOF)
    required = [
        "minutes_actual",
        "minutes_pred",
        "minutes_baseline_roll10",
        "dnp_actual",
        "dnp_prob_pred",
        "active_prob_pred",
        "role_bucket_pred",
        "role_bucket_actual",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"ROLE_MINUTES_DIAG_FAIL missing_cols={missing}", file=sys.stderr)
        return 2

    df = df.copy()
    df["err_model"] = df["minutes_actual"] - df["minutes_pred"]
    df["abs_err_model"] = np.abs(df["err_model"])
    df["err_base"] = df["minutes_actual"] - df["minutes_baseline_roll10"]
    df["abs_err_base"] = np.abs(df["err_base"])

    out_dir = REPO_ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Confusion matrix: predicted vs actual role buckets.
    cm = pd.crosstab(
        df["role_bucket_actual"].astype(str),
        df["role_bucket_pred"].astype(str),
        dropna=False,
    )
    cm_path = out_dir / "role_bucket_confusion.csv"
    cm.to_csv(cm_path)

    # Minutes bias by role bucket (using predicted role for stratification).
    by_role = []
    for role, g in df.groupby(df["role_bucket_pred"].astype(str)):
        by_role.append(
            {
                "role_bucket_pred": role,
                "n": int(len(g)),
                "dnp_rate_actual": float(np.mean(g["dnp_actual"].astype(int))),
                "dnp_prob_pred_mean": float(np.mean(g["dnp_prob_pred"].astype(float))),
                "active_logloss": float(
                    -np.mean(
                        (1 - g["dnp_actual"].astype(int)).to_numpy() * np.log(np.clip(g["active_prob_pred"].astype(float).to_numpy(), 1e-6, 1 - 1e-6))
                        + g["dnp_actual"].astype(int).to_numpy() * np.log(np.clip(1 - g["active_prob_pred"].astype(float).to_numpy(), 1e-6, 1 - 1e-6))
                    )
                ),
                "mae_model": float(np.mean(g["abs_err_model"])),
                "mae_baseline": float(np.mean(g["abs_err_base"])),
                "bias_model": float(np.mean(g["err_model"])),
                "bias_baseline": float(np.mean(g["err_base"])),
            }
        )
    bias_df = pd.DataFrame(by_role).sort_values(["role_bucket_pred"])
    bias_path = out_dir / "minutes_bias_by_role.csv"
    bias_df.to_csv(bias_path, index=False)

    summary = {
        "oof_path": str(OOF.relative_to(REPO_ROOT)),
        "rows": int(len(df)),
        "minutes_mae_model": float(np.mean(df["abs_err_model"])),
        "minutes_mae_baseline": float(np.mean(df["abs_err_base"])),
        "dnp_brier": float(np.mean((df["dnp_actual"].astype(int) - df["dnp_prob_pred"].astype(float)) ** 2)),
        "role_bucket_confusion_csv": str(cm_path.relative_to(REPO_ROOT)),
        "minutes_bias_by_role_csv": str(bias_path.relative_to(REPO_ROOT)),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(
        "ROLE_MINUTES_DIAG_PASS "
        f"wrote={out_dir.relative_to(REPO_ROOT)} rows={len(df)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
