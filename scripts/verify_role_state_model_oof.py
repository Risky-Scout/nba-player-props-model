#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Parquet with role probabilities")
    ap.add_argument("--out-dir", default="artifacts/model_diagnostics/role_state")
    args = ap.parse_args()
    inp = Path(args.input)
    out_dir = Path(args.out_dir)
    df = pd.read_parquet(inp)
    required = ["p_inactive", "p_fringe", "p_bench", "p_rotation", "p_core", "p_starter"]
    miss = [c for c in required if c not in df.columns]
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {"n_rows": int(len(df)), "missing_columns": miss, "pass": len(miss) == 0}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("ROLE_STATE_MODEL_OOF_PASS" if summary["pass"] else "ROLE_STATE_MODEL_OOF_FAIL")
    return 0 if summary["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
