#!/usr/bin/env python3
"""Expand inventory rows with eligibility diagnostics and suggested fix commands."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]


def _as_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "t", "yes")


def _commands(row: dict) -> tuple[bool, bool, bool, str]:
    has_raw = _as_bool(row.get("has_raw_odds", False))
    has_proc = _as_bool(row.get("has_processed_odds", False))
    has_sg = _as_bool(row.get("has_stat_grid", False))
    has_can = _as_bool(row.get("has_canonical_delivery", False))
    has_daily = _as_bool(row.get("has_daily_pmf_delivery", False))
    has_act = _as_bool(row.get("has_player_game_stats", False))
    d = str(row.get("date", "")).strip()[:10]

    can_proc = has_raw and not has_proc
    can_build = has_proc and has_act and (not has_sg or not has_can or not has_daily)
    can_refresh = not has_act

    parts: list[str] = []
    if can_proc:
        parts.append(
            f"# {d}: process odds (needs Odds API / historical replay): "
            f"see scripts/oddsapi_nba_props.py live-snapshot --snapshot-type close_or_lock --target-date {d}"
        )
    if can_build:
        parts.append(
            f"python3 scripts/build_backtest_delivery_range.py --start-date {d} --end-date {d} "
            f"--no-public-export --skip-existing"
        )
    if can_refresh:
        parts.append(
            f"python3 scripts/refresh_bdl_player_game_stats.py --start-date {d} --end-date {d}"
        )
    if not parts:
        parts.append("# no automated local fix inferred (missing raw odds and/or box scores)")
    return can_proc, can_build, can_refresh, "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--inventory",
        type=Path,
        default=REPO_ROOT / "artifacts" / "model_diagnostics" / "event_market_backtest_date_inventory.csv",
    )
    args = ap.parse_args()
    inv = args.inventory
    if not inv.is_file():
        print(f"MISSING {inv}", file=sys.stderr)
        return 2

    df = pd.read_csv(inv)
    if "date" not in df.columns:
        print("FATAL: inventory missing date", file=sys.stderr)
        return 2

    rows_out: list[dict] = []
    for _, r in df.iterrows():
        row = r.to_dict()
        elig = _as_bool(row.get("eligible_for_event_market_backtest", False))
        if elig:
            continue
        can_proc, can_build, can_refresh, cmd = _commands(row)
        rows_out.append(
            {
                "date": str(row.get("date", ""))[:10],
                "missing_reason": row.get("missing_reason", ""),
                "has_raw_odds": _as_bool(row.get("has_raw_odds", False)),
                "has_processed_odds": _as_bool(row.get("has_processed_odds", False)),
                "has_stat_grid": _as_bool(row.get("has_stat_grid", False)),
                "has_canonical_delivery": _as_bool(row.get("has_canonical_delivery", False)),
                "has_daily_pmf_delivery": _as_bool(row.get("has_daily_pmf_delivery", False)),
                "has_actuals": _as_bool(row.get("has_player_game_stats", False)),
                "two_way_market_rows": int(row.get("two_way_market_rows", 0) or 0),
                "estimated_joinable_rows": int(row.get("estimated_joinable_rows", 0) or 0),
                "can_be_made_eligible_by_building_pmfs": can_build,
                "can_be_made_eligible_by_processing_odds": can_proc,
                "can_be_made_eligible_by_refreshing_actuals": can_refresh,
                "required_command_to_make_eligible": cmd,
            }
        )

    out_csv = REPO_ROOT / "artifacts" / "model_diagnostics" / "backtest_date_ineligibility_summary.csv"
    out_md = REPO_ROOT / "artifacts" / "model_diagnostics" / "backtest_date_ineligibility_summary.md"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(rows_out)
    out.to_csv(out_csv, index=False)

    lines = [
        "# Backtest date ineligibility summary",
        "",
        f"- Source inventory: `{inv}`",
        f"- Ineligible dates listed: **{len(out)}**",
        "",
        "See `backtest_date_ineligibility_summary.csv` for full commands per date.",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"BACKTEST_DATE_INELIGIBILITY_DIAG_PASS wrote {out_csv.relative_to(REPO_ROOT)}")
    print(json.dumps({"n_ineligible_rows": len(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
