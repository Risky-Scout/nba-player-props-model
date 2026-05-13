#!/usr/bin/env python3
"""Build missing stat_grid / canonical / daily delivery for dates that have odds + actuals.

Does not publish public_export. Respects --skip-existing unless --force.
Only runs local pipeline steps (no implicit network); odds processing is out of scope.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]


def _as_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "t", "yes")


def _run(py: str, cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--inventory",
        type=Path,
        default=REPO_ROOT / "artifacts" / "model_diagnostics" / "event_market_backtest_date_inventory.csv",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        print("FATAL: pass --dry-run or --apply", file=sys.stderr)
        return 2
    if args.dry_run and args.apply:
        print("FATAL: use only one of --dry-run or --apply", file=sys.stderr)
        return 2

    if not args.inventory.is_file():
        print(f"MISSING {args.inventory}", file=sys.stderr)
        return 2

    df = pd.read_csv(args.inventory)
    py = sys.executable
    plan: list[dict] = []
    for _, r in df.iterrows():
        row = r.to_dict()
        if _as_bool(row.get("eligible_for_event_market_backtest", False)):
            continue
        d = str(row.get("date", "")).strip()[:10]
        if not d:
            continue
        has_proc = _as_bool(row.get("has_processed_odds", False))
        has_act = _as_bool(row.get("has_player_game_stats", False))
        has_sg = _as_bool(row.get("has_stat_grid", False))
        has_can = _as_bool(row.get("has_canonical_delivery", False))
        if not (has_proc and has_act):
            continue
        if not args.force and has_sg and has_can:
            continue
        cmd = [
            py,
            str(REPO_ROOT / "scripts" / "build_backtest_delivery_range.py"),
            "--start-date",
            d,
            "--end-date",
            d,
            "--no-public-export",
        ]
        if not args.force:
            cmd.append("--skip-existing")
        if args.force:
            cmd.append("--force")
        plan.append({"date": d, "cmd": cmd})

    if args.dry_run:
        print(json.dumps({"planned_dates": [p["date"] for p in plan], "n": len(plan)}, indent=2))
        return 0

    failures: list[dict] = []
    for p in plan:
        rc, out = _run(py, p["cmd"])
        if rc != 0:
            failures.append({"date": p["date"], "rc": rc, "tail": out[-4000:]})
    rep = REPO_ROOT / "artifacts" / "model_diagnostics" / "build_missing_backtest_inputs_report.json"
    rep.write_text(json.dumps({"built": [p["date"] for p in plan], "failures": failures}, indent=2) + "\n")
    print(f"BUILD_MISSING_BACKTEST_INPUTS_APPLY_DONE n={len(plan)} failures={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
