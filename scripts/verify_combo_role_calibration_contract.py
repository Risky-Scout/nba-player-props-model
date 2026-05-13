#!/usr/bin/env python3
"""M8.6 — mission combo stats must have role calibrator PKL or explicit gap."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "artifacts" / "models"
META = MODEL_DIR / "pmf_cal_meta.json"

COMBOS = ("stocks", "pa", "pr", "ra", "pra")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="Slate date (logging only).")
    args = ap.parse_args()

    gaps: dict = {}
    if META.exists():
        try:
            meta = json.loads(META.read_text(encoding="utf-8"))
            gaps = meta.get("combo_calibration_gaps") or {}
        except Exception as e:
            print(f"WARN: pmf_cal_meta parse: {e}", file=sys.stderr)

    bad: list[str] = []
    for stat in COMBOS:
        pkl = MODEL_DIR / f"pmf_cal_role_{stat}.pkl"
        if pkl.exists():
            continue
        g = gaps.get(stat) or {}
        if str(g.get("calibration_status", "")).lower() == "insufficient_oof":
            continue
        bad.append(stat)

    if bad:
        print(
            "COMBO_ROLE_CALIBRATION_CONTRACT_FAIL "
            f"missing_pkl_or_gap_for={bad!r} date={args.date!r}",
            file=sys.stderr,
        )
        return 1
    print(f"COMBO_ROLE_CALIBRATION_CONTRACT_PASS date={args.date!r} combos={COMBOS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
