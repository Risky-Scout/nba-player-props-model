#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-dir", default="artifacts/model_diagnostics/sparse_stat_hurdle")
    args = ap.parse_args()
    inp = Path(args.input)
    out_dir = Path(args.out_dir)
    df = pd.read_parquet(inp)
    required = [
        "expected_steal_opportunities",
        "expected_block_opportunities",
        "sparse_p0_prior",
        "sparse_positive_tail_prior",
    ]
    miss = [c for c in required if c not in df.columns]
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {"n_rows": int(len(df)), "missing_columns": miss, "pass": len(miss) == 0}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("SPARSE_STAT_HURDLE_FEATURES_OOF_PASS" if summary["pass"] else "SPARSE_STAT_HURDLE_FEATURES_OOF_FAIL")
    return 0 if summary["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
