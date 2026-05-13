#!/usr/bin/env python3
"""M8.6 — RA combo must have OOF coverage + role calibrator or explicit gap.

Pass markers:
  RA_ROLE_CALIBRATION_CONTRACT_PASS           — pmf_cal_role_ra.pkl present
  RA_ROLE_CALIBRATION_CONTRACT_PASS_EXPLICIT_GAP — documented non-promotable gap
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "artifacts" / "models"
PKL = MODEL_DIR / "pmf_cal_role_ra.pkl"
META = MODEL_DIR / "pmf_cal_meta.json"
OOF_COMBO = REPO_ROOT / "data" / "oof_combo_pmfs.parquet"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="Slate date (logging only).")
    args = ap.parse_args()

    if PKL.exists():
        print(f"RA_ROLE_CALIBRATION_CONTRACT_PASS pkl={PKL.relative_to(REPO_ROOT)}")
        return 0

    n_ra_oof = 0
    if OOF_COMBO.exists():
        try:
            df = pd.read_parquet(OOF_COMBO)
            if "stat" in df.columns:
                n_ra_oof = int((df["stat"].astype(str).str.lower() == "ra").sum())
        except Exception as e:
            print(f"WARN: could not read OOF combo parquet: {e}", file=sys.stderr)

    gap_ok = False
    if META.exists():
        try:
            meta = json.loads(META.read_text(encoding="utf-8"))
            gaps = meta.get("combo_calibration_gaps") or {}
            ra_gap = gaps.get("ra") or {}
            if str(ra_gap.get("calibration_status", "")).lower() == "insufficient_oof":
                gap_ok = True
        except Exception as e:
            print(f"WARN: could not parse pmf_cal_meta.json: {e}", file=sys.stderr)

    if gap_ok:
        print(
            "RA_ROLE_CALIBRATION_CONTRACT_PASS_EXPLICIT_GAP "
            f"date={args.date!r} n_ra_oof_rows={n_ra_oof} "
            "combo_calibration_gaps.ra.calibration_status=insufficient_oof"
        )
        return 0

    print(
        "RA_ROLE_CALIBRATION_CONTRACT_FAIL "
        f"missing={PKL.relative_to(REPO_ROOT)} "
        f"oof_ra_rows={n_ra_oof} "
        "and no combo_calibration_gaps.ra.calibration_status=insufficient_oof in pmf_cal_meta.json",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
