#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.teammate_on_off_features import build_teammate_on_off_features  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    inp = Path(args.input)
    out = Path(args.out)
    if not inp.is_absolute():
        inp = REPO_ROOT / inp
    if not out.is_absolute():
        out = REPO_ROOT / out
    df = pd.read_parquet(inp)
    feat = build_teammate_on_off_features(df)
    out.parent.mkdir(parents=True, exist_ok=True)
    feat.to_parquet(out, index=False)
    print("TEAMMATE_ON_OFF_FEATURES_PASS")
    print(f"  out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
