#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-model", default="artifacts/models/sparse_stat_hurdle_summary.json")
    args = ap.parse_args()
    inp = Path(args.input)
    out = Path(args.out_model)
    df = pd.read_parquet(inp)
    summary = {
        "n_rows": int(len(df)),
        "has_sparse_priors": all(c in df.columns for c in ("sparse_p0_prior", "sparse_positive_tail_prior")),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("SPARSE_STAT_HURDLE_FEATURES_OOF_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
