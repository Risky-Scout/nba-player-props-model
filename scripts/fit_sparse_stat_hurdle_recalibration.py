#!/usr/bin/env python3
"""Fit empirical p0 offsets for sparse stats from OOF PMFs (no market)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

SPARSE = ("stl", "blk", "tov", "fg3m", "stocks")
OUT = REPO_ROOT / "artifacts" / "models" / "sparse_hurdle_offsets.json"


def _p0(arr) -> float:
    if arr is None:
        return 0.0
    if isinstance(arr, (list, tuple)):
        return float(arr[0]) if arr else 0.0
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return 0.0
    return float(a.flat[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oof", default=str(REPO_ROOT / "data" / "oof_pmfs.parquet"))
    args = ap.parse_args()

    p = Path(args.oof)
    if not p.exists():
        print("SPARSE_HURDLE_FIT_SKIP no oof_pmfs", file=sys.stderr)
        return 2

    df = pd.read_parquet(p)
    df = df[df["stat"].astype(str).isin(SPARSE)]
    if df.empty:
        print("SPARSE_HURDLE_FIT_SKIP no sparse stat rows", file=sys.stderr)
        return 3

    offsets: dict = {}
    for stat, g in df.groupby("stat"):
        pmfs = g["pmf"].values
        y0 = (g["outcome"].astype(float).values == 0).astype(float)
        p0_hat = np.array([_p0(x) for x in pmfs])
        delta = float(np.mean(y0) - np.mean(p0_hat))
        offsets[str(stat)] = {
            "delta_p0": delta,
            "n": int(len(g)),
            "mean_empirical_p0": float(np.mean(y0)),
            "mean_pred_p0": float(np.mean(p0_hat)),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"offsets": offsets, "version": "sparse_hurdle_v0"}, indent=2) + "\n")
    print(f"SPARSE_HURDLE_FIT_PASS wrote {OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
