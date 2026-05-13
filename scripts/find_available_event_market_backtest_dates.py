#!/usr/bin/env python3
"""Inventory dates where model PMFs, odds, and box scores overlap for event-market backtest."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.markets.oddsapi_markets import stat_for_market_key  # noqa: E402


def _iter_dates(start_s: str, end_s: str) -> list[str]:
    s = date.fromisoformat(start_s)
    e = date.fromisoformat(end_s)
    out: list[str] = []
    while s <= e:
        out.append(s.isoformat())
        s += timedelta(days=1)
    return out


def _norm_stat(s) -> str | None:
    s = str(s or "").lower().strip()
    mapping = {
        "points": "pts", "rebounds": "reb", "assists": "ast",
        "threes_made": "fg3m", "threes": "fg3m", "three_pointers_made": "fg3m",
        "turnovers": "tov", "steals": "stl", "blocks": "blk",
        "steals_blocks": "stocks", "stl_blk": "stocks",
        "points_assists": "pa", "pts_ast": "pa",
        "points_rebounds": "pr", "pts_reb": "pr",
        "points_rebounds_assists": "pra", "pts_reb_ast": "pra",
        "rebounds_assists": "ra", "reb_ast": "ra",
    }
    if s in mapping:
        return mapping[s]
    return s if s else None


def _scan_raw(day: str) -> tuple[list[str], set[str], Counter]:
    raw_dir = REPO_ROOT / "data" / "odds_api" / "raw" / day
    paths: list[str] = []
    keys: Counter = Counter()
    if not raw_dir.exists():
        return paths, set(), keys
    for p in sorted(raw_dir.glob("*.json")):
        if p.name.startswith("live_events_") or p.name.startswith("smoke_"):
            continue
        paths.append(str(p.relative_to(REPO_ROOT)))
        try:
            blob = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for b in blob.get("bookmakers") or []:
            if not isinstance(b, dict):
                continue
            for m in b.get("markets") or []:
                k = str(m.get("key") or "").strip()
                if k:
                    keys[k] += 1
    return paths, set(keys.keys()), keys


def _find_odds_pairs(day: str, snapshot_substr: str) -> list[Path]:
    base = REPO_ROOT / "data" / "odds_api" / "processed" / day
    if not base.exists():
        return []
    cand = sorted(base.glob(f"odds_pairs_*{snapshot_substr}*.parquet"))
    if cand:
        return [cand[-1]]
    fallback = sorted(base.glob("odds_pairs_*.parquet"))
    return [fallback[-1]] if fallback else []


def _processed_summary(day: str, snapshot_substr: str) -> dict:
    paths = _find_odds_pairs(day, snapshot_substr)
    rel = [str(p.relative_to(REPO_ROOT)) for p in paths]
    if not paths:
        return {
            "processed_odds_paths": rel,
            "processed_stats_present": [],
            "processed_market_keys_seen": [],
            "two_way_market_rows": 0,
        }
    df = pd.read_parquet(paths[0])
    mk_seen: set[str] = set()
    if "market_key" in df.columns:
        mk_seen = set(df["market_key"].dropna().astype(str).unique())
    stats: set[str] = set()
    if "market_stat" in df.columns:
        stats |= set(df["market_stat"].apply(_norm_stat).dropna().astype(str).str.lower())
    elif "stat" in df.columns:
        stats |= set(df["stat"].apply(_norm_stat).dropna().astype(str).str.lower())
    for k in mk_seen:
        st = stat_for_market_key(k)
        if st:
            stats.add(str(st).lower())
    tw = 0
    if "no_vig_over_prob" in df.columns and "no_vig_under_prob" in df.columns:
        tw = int((df["no_vig_over_prob"].notna() & df["no_vig_under_prob"].notna()).sum())
    return {
        "processed_odds_paths": rel,
        "processed_stats_present": sorted(stats),
        "processed_market_keys_seen": sorted(mk_seen),
        "two_way_market_rows": tw,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", required=True)
    ap.add_argument("--end-date", required=True)
    ap.add_argument("--snapshot-substr", default="close_or_lock")
    args = ap.parse_args()

    pgs_path = REPO_ROOT / "data" / "player_game_stats.parquet"
    pgs_max = None
    today = datetime.now(timezone.utc).date().isoformat()
    if pgs_path.exists():
        bx = pd.read_parquet(pgs_path, columns=["game_date"])
        pgs_max = str(bx["game_date"].astype(str).str.slice(0, 10).max())

    rows_out: list[dict] = []
    for d in _iter_dates(args.start_date, args.end_date):
        stat_grid_path = REPO_ROOT / "predictions" / f"stat_grid_{d}.parquet"
        canonical_path = (
            REPO_ROOT
            / "deliveries"
            / d
            / "canonical_source"
            / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
        )
        daily_review = REPO_ROOT / "deliveries" / d / "pmf_model_review_package" / "README.md"
        woo_manifest = REPO_ROOT / "deliveries" / d / "wizard_of_odds" / "run_manifest.json"

        has_stat_grid = stat_grid_path.exists()
        has_canonical = canonical_path.exists()
        has_model_pmfs = has_stat_grid or has_canonical
        has_daily_pmf_delivery = daily_review.exists() or woo_manifest.exists()

        raw_paths, raw_keys, _ = _scan_raw(d)
        has_raw_odds = len(raw_paths) > 0

        proc = _processed_summary(d, args.snapshot_substr)
        has_processed_odds = len(proc["processed_odds_paths"]) > 0

        actual_rows = 0
        if pgs_path.exists():
            bx = pd.read_parquet(pgs_path, columns=["game_date"])
            actual_rows = int(bx["game_date"].astype(str).str.slice(0, 10).eq(d).sum())
        has_player_game_stats = actual_rows > 0

        model_stats_present: list[str] = []
        if has_stat_grid:
            sg = pd.read_parquet(stat_grid_path, columns=["stat"])
            model_stats_present = sorted(sg["stat"].astype(str).str.lower().unique().tolist())
        elif has_canonical:
            try:
                cg = pd.read_parquet(canonical_path, columns=["stat"])
                model_stats_present = sorted(cg["stat"].astype(str).str.lower().unique().tolist())
            except Exception:
                model_stats_present = []

        future_or_unscored = False
        if d > today:
            future_or_unscored = True
        if pgs_max and d > pgs_max:
            future_or_unscored = True

        tw = proc["two_way_market_rows"]
        joinable = min(tw, actual_rows) if tw and actual_rows else 0

        reasons: list[str] = []
        if not has_processed_odds:
            reasons.append("no_processed_odds")
        if not has_player_game_stats:
            reasons.append("no_box_score_actuals")
        if tw <= 0:
            reasons.append("no_two_way_market_rows")
        if not has_model_pmfs:
            reasons.append("no_model_pmfs")
        if future_or_unscored:
            reasons.append("future_or_unscored_game_date")

        eligible = not reasons
        missing_reason = "eligible" if eligible else ";".join(reasons)

        rows_out.append({
            "date": d,
            "has_stat_grid": has_stat_grid,
            "has_canonical_delivery": has_canonical,
            "has_model_pmfs": has_model_pmfs,
            "has_daily_pmf_delivery": has_daily_pmf_delivery,
            "has_processed_odds": has_processed_odds,
            "has_raw_odds": has_raw_odds,
            "has_player_game_stats": has_player_game_stats,
            "stat_grid_path": str(stat_grid_path.relative_to(REPO_ROOT)) if has_stat_grid else "",
            "canonical_path": str(canonical_path.relative_to(REPO_ROOT)) if has_canonical else "",
            "processed_odds_paths": json.dumps(proc["processed_odds_paths"]),
            "raw_odds_paths": json.dumps(raw_paths),
            "actual_rows": actual_rows,
            "model_stats_present": json.dumps(model_stats_present),
            "raw_market_keys_seen": json.dumps(sorted(raw_keys)),
            "processed_stats_present": json.dumps(proc["processed_stats_present"]),
            "processed_market_keys_seen": json.dumps(proc["processed_market_keys_seen"]),
            "two_way_market_rows": tw,
            "estimated_joinable_rows": joinable,
            "eligible_for_event_market_backtest": eligible,
            "missing_reason": missing_reason,
        })

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows_out)
    csv_path = out_dir / "event_market_backtest_date_inventory.csv"
    json_path = out_dir / "event_market_backtest_date_inventory.json"
    df.to_csv(csv_path, index=False)
    json_path.write_text(
        json.dumps(
            {
                "start_date": args.start_date,
                "end_date": args.end_date,
                "snapshot_substr": args.snapshot_substr,
                "n_dates": len(rows_out),
                "n_eligible": int(df["eligible_for_event_market_backtest"].sum()),
                "dates": rows_out,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"EVENT_MARKET_BACKTEST_DATE_INVENTORY_PASS wrote {csv_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
