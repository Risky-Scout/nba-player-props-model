#!/usr/bin/env python3
"""Fail if minutes OOF is missing or model is much worse than rolling-10 baseline."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OOF = REPO_ROOT / "data" / "oof_minutes_predictions.parquet"


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
    mae_m = float(np.mean(np.abs(df["minutes_actual"] - df["minutes_pred"])))
    mae_b = float(np.mean(np.abs(df["minutes_actual"] - df["minutes_baseline_roll10"])))

    if args.require_improvement_vs_baseline and mae_m > mae_b * args.mae_tolerance:
        print(
            f"MINUTES_MODEL_OOF_FAIL mae_model={mae_m:.4f} mae_baseline={mae_b:.4f} "
            f"tolerance={args.mae_tolerance}",
            file=sys.stderr,
        )
        return 1

    print(f"MINUTES_MODEL_OOF_PASS rows={len(df)} mae_model={mae_m:.4f} mae_baseline={mae_b:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
