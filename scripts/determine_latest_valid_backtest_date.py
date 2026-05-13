#!/usr/bin/env python3
"""Pick the latest calendar date safe for historical backtest / event-market evaluation.

Rules (M8.6):
- Never propose a date after the latest finalized box-score ``game_date`` in
  ``data/player_game_stats.parquet``.
- Cap at ``as_of_date - 1 day`` so we never treat the operator reference day as a
  completed slate (avoids same-day incomplete games when as_of is "today").
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--as-of-date",
        required=True,
        help="Reference calendar date YYYY-MM-DD (e.g. operator mission date).",
    )
    args = ap.parse_args()
    as_of = date.fromisoformat(str(args.as_of_date).strip()[:10])
    cap = as_of - timedelta(days=1)

    pgs_path = REPO_ROOT / "data" / "player_game_stats.parquet"
    sources_checked: list[str] = []
    if not pgs_path.is_file():
        print(f"FATAL missing {pgs_path}", file=sys.stderr)
        return 2
    sources_checked.append(str(pgs_path.relative_to(REPO_ROOT)))

    gd = pd.read_parquet(pgs_path, columns=["game_date"])
    gd["game_date"] = gd["game_date"].astype(str).str.slice(0, 10)
    max_actuals = date.fromisoformat(str(gd["game_date"].max()))

    latest_valid = min(max_actuals, cap)

    excluded: list[str] = []
    d = latest_valid + timedelta(days=1)
    while d <= as_of:
        excluded.append(d.isoformat())
        d += timedelta(days=1)

    reason = (
        f"latest_valid_backtest_date=min(max_actuals_game_date={max_actuals.isoformat()}, "
        f"as_of_minus_1day={cap.isoformat()}) with as_of={as_of.isoformat()}."
    )

    out = {
        "current_date": as_of.isoformat(),
        "max_actuals_date": max_actuals.isoformat(),
        "latest_valid_backtest_date": latest_valid.isoformat(),
        "excluded_dates_after_latest": excluded,
        "reason": reason,
        "data_sources_checked": sources_checked,
    }
    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    outp = out_dir / "latest_valid_backtest_date.json"
    outp.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"LATEST_VALID_BACKTEST_DATE wrote {outp.relative_to(REPO_ROOT)}")
    print(f"  latest_valid_backtest_date={out['latest_valid_backtest_date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
