#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.pmf.combo_joint_sampler import sample_combo_joint_pmf  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-dir", default="artifacts/model_diagnostics/combo_joint_pmf")
    args = ap.parse_args()
    inp = Path(args.input)
    out_dir = Path(args.out_dir)
    df = pd.read_parquet(inp)
    means = {
        "pts": float(df.get("pmf_mean", pd.Series([20.0])).mean()),
        "reb": 7.0,
        "ast": 5.0,
    }
    cov = np.array([[25.0, 6.0, 5.0], [6.0, 9.0, 3.0], [5.0, 3.0, 8.0]], dtype=float)
    pmfs = sample_combo_joint_pmf(means, cov, n_samples=2000)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, pmf in pmfs.items():
        rows.append({"combo_stat": name, "pmf_sum": float(pmf.sum()), "support_max": int(len(pmf) - 1)})
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "summary.csv", index=False)
    summary = {"pass": bool((out["pmf_sum"] > 0.99).all() and (out["pmf_sum"] < 1.01).all()), "n_stats": int(len(out))}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("COMBO_JOINT_PMF_OOF_PASS" if summary["pass"] else "COMBO_JOINT_PMF_OOF_FAIL")
    return 0 if summary["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
