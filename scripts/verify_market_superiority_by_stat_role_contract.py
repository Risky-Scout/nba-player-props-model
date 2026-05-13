#!/usr/bin/env python3
"""M8.6 — hard gate: global superiority claim only if every eligible segment passes.

Prints MARKET_SUPERIORITY_BY_STAT_ROLE_CONTRACT_PASS only when
summary.json allows the global claim AND no failed eligible segments remain.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
META = REPO_ROOT / "artifacts" / "models" / "pmf_cal_meta.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument(
        "--allow-provisional-block",
        action="store_true",
        help="Exit 0 with MARKET_SUPERIORITY_CONTRACT_BLOCKED when claim disallowed "
        "(CI / historical replay without full market proof).",
    )
    args = ap.parse_args()
    if args.start_date or args.end_date:
        if not (args.start_date and args.end_date):
            print("FATAL: --start-date and --end-date together", file=sys.stderr)
            return 2
        label = f"{args.start_date}_{args.end_date}"
    elif args.date:
        label = args.date
    else:
        print("FATAL: pass --date or --start-date/--end-date", file=sys.stderr)
        return 2

    sup_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_superiority_{label}"
    summ_path = sup_dir / "summary.json"
    sr_path = sup_dir / "stat_role_market_superiority.csv"
    if not summ_path.exists() or not sr_path.exists():
        print(f"MISSING_SUPERIORITY_ARTIFACTS {summ_path} {sr_path}", file=sys.stderr)
        return 1

    summary = json.loads(summ_path.read_text(encoding="utf-8"))
    df = pd.read_csv(sr_path)

    # RA must not claim superiority while explicitly gapped in meta.
    ra_blocked = False
    if META.exists():
        meta = json.loads(META.read_text(encoding="utf-8"))
        gap = (meta.get("combo_calibration_gaps") or {}).get("ra") or {}
        if str(gap.get("calibration_status", "")).lower() == "insufficient_oof":
            ra_blocked = True

    eligible = df[df.get("market_superiority_eligible", False) == True]
    failed_eligible = eligible[eligible.get("market_superiority_pass", False) == False]

    global_ok = bool(summary.get("global_market_superiority_claim_allowed"))
    if ra_blocked and global_ok:
        print(
            "MARKET_SUPERIORITY_BY_STAT_ROLE_CONTRACT_FAIL "
            "RA is explicitly insufficient_oof but summary claims global superiority",
            file=sys.stderr,
        )
        return 1

    if len(failed_eligible) == 0 and global_ok and not summary.get("required_stats_missing_in_event_rows"):
        print("MARKET_SUPERIORITY_BY_STAT_ROLE_CONTRACT_PASS")
        return 0

    if args.allow_provisional_block:
        print(
            "MARKET_SUPERIORITY_CONTRACT_BLOCKED "
            f"failed_eligible={len(failed_eligible)} global_ok={global_ok} "
            f"summary={summary.get('n_segments_passed')}/{summary.get('n_segments_total')}"
        )
        return 0

    print(
        "MARKET_SUPERIORITY_BY_STAT_ROLE_CONTRACT_FAIL "
        f"failed_eligible_segments={len(failed_eligible)} global_claim={global_ok}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
