#!/usr/bin/env python3
"""Summarize no-market model-only PMF calibration gate failures by stat-role."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent


def _dominant(row: pd.Series) -> str:
    pit = row.get("pit_ks_pvalue")
    try:
        pitf = float(pit)
    except Exception:
        pitf = np.nan
    if pitf == pitf and pitf < 0.01:
        return "PIT_shape"
    me = row.get("mean_error")
    try:
        if me == me and abs(float(me)) > 0.25:
            return "mean_bias"
    except Exception:
        pass
    p0e = row.get("p0_error")
    try:
        if p0e == p0e and abs(float(p0e)) > 0.08:
            return "p0_bias"
    except Exception:
        pass
    ve = row.get("variance_error")
    try:
        if ve == ve and abs(float(ve)) > 1.0:
            return "variance_bias"
    except Exception:
        pass
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    label = str(args.label).strip()
    base = REPO_ROOT / "artifacts" / "model_diagnostics" / f"model_only_no_market_calibration_{label}"
    sr_path = base / "stat_role.csv"
    if not sr_path.is_file():
        print(f"FATAL missing {sr_path}", file=sys.stderr)
        return 2
    df = pd.read_csv(sr_path)
    df["dominant_failure"] = df.apply(_dominant, axis=1)
    df.to_csv(base / "failure_modes.csv", index=False)

    counts = df["dominant_failure"].value_counts().to_dict()
    md = [
        f"# No-market PMF calibration failure modes — {label}",
        "",
        "## Dominant failure counts",
        "",
        "```",
        json.dumps(counts, indent=2),
        "```",
        "",
        "## Repairs",
        "",
        "- **PIT_shape:** monotone / isotonic PIT calibration with shrinkage to parent stat.",
        "- **mean_bias:** mean-shift or tail tilt on OOF PMFs with rollback on NLL.",
        "- **p0_bias:** sparse p0 hurdle recalibration for blk/stl/stocks.",
        "- **variance_bias:** variance inflation/deflation in joint sampler or post-hoc scale.",
        "",
    ]
    (base / "repair_recommendations.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"MODEL_ONLY_NO_MARKET_FAILURE_DIAG wrote {base.relative_to(REPO_ROOT)}/failure_modes.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
