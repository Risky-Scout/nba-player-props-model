#!/usr/bin/env python3
"""Minutes bias summary by coarse usage bucket from OOF predictions."""
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
    ap.add_argument("--out", default="artifacts/model_diagnostics/minutes_role_bias.json")
    args = ap.parse_args()

    if not OOF.exists():
        print("SKIP: no oof_minutes_predictions.parquet", file=sys.stderr)
        return 0

    df = pd.read_parquet(OOF)
    df["err_m"] = df["minutes_actual"] - df["minutes_pred"]
    df["err_b"] = df["minutes_actual"] - df["minutes_baseline_roll10"]
    df["bucket"] = pd.qcut(
        df["minutes_baseline_roll10"].rank(method="first"),
        q=min(6, max(2, len(df) // 200)),
        duplicates="drop",
    ).astype(str)

    rows = []
    for b, g in df.groupby("bucket"):
        rows.append({
            "bucket": b,
            "n": int(len(g)),
            "mae_model": float(np.mean(np.abs(g["err_m"]))),
            "mae_baseline": float(np.mean(np.abs(g["err_b"]))),
            "bias_model": float(np.mean(g["err_m"])),
            "bias_baseline": float(np.mean(g["err_b"])),
        })

    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"by_baseline_minutes_bucket": rows}, indent=2) + "\n")
    print(f"MINUTES_ROLE_BIAS_DIAG_PASS wrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
