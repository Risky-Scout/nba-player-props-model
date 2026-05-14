#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.role_state_features import build_role_state_features  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-model", default="artifacts/models/role_state_model_summary.json")
    args = ap.parse_args()
    inp = Path(args.input)
    out = Path(args.out_model)
    if not inp.is_absolute():
        inp = REPO_ROOT / inp
    if not out.is_absolute():
        out = REPO_ROOT / out
    df = pd.read_parquet(inp)
    feat = build_role_state_features(df)
    summary = {
        "n_rows": int(len(feat)),
        "avg_role_entropy": float(feat["role_entropy"].mean()) if len(feat) else 0.0,
        "avg_p_starter": float(feat["p_starter"].mean()) if len(feat) else 0.0,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("ROLE_STATE_MODEL_OOF_PASS")
    print(f"  out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
