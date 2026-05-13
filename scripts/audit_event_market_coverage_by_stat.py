#!/usr/bin/env python3
"""Event-market coverage audit by canonical stat (M8.6).

Traces model → canonical → raw Odds API → processed odds → event_market_loss_rows
for each mission stat. Does not count model-only rows as market coverage.

Run:
  python3 scripts/audit_event_market_coverage_by_stat.py --date 2026-05-12
  python3 scripts/audit_event_market_coverage_by_stat.py --start-date 2026-05-07 --end-date 2026-05-12
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.markets.oddsapi_markets import (  # noqa: E402
    ODDSAPI_NBA_DEFAULT_MARKETS,
    market_keys_for_stat,
    stat_for_market_key,
)
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402

REQUIRED_STATS = [str(s).lower() for s in MISSION_REQUIRED_TARGETS_CANONICAL]

MISSING_REASONS = frozenset({
    "covered",
    "no_offered_market",
    "not_requested_from_odds_api",
    "raw_parser_dropped_market",
    "processed_parser_dropped_market",
    "missing_two_way_odds",
    "player_join_failed",
    "line_join_failed",
    "book_join_failed",
    "no_actuals",
    "insufficient_scored_rows",
})

DEFAULT_MIN_SCORED = 100


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
    if s in tuple(MISSION_REQUIRED_TARGETS_CANONICAL):
        return s
    return s if s else None


def _find_odds_pairs_file(d: str, snapshot_substr: str) -> Path | None:
    base = REPO_ROOT / "data" / "odds_api" / "processed" / d
    if not base.exists():
        return None
    cand = sorted(base.glob(f"odds_pairs_*{snapshot_substr}*.parquet"))
    if cand:
        return cand[-1]
    fallback = sorted(base.glob("odds_pairs_*.parquet"))
    return fallback[-1] if fallback else None


def _scan_raw_market_keys(day: str) -> tuple[int, set[str], Counter]:
    """Return (approx_row_count, unique_market_keys, key_counts) from raw JSON."""
    raw_dir = REPO_ROOT / "data" / "odds_api" / "raw" / day
    if not raw_dir.exists():
        return 0, set(), Counter()
    keys: Counter = Counter()
    rows = 0
    for p in sorted(raw_dir.glob("*.json")):
        if p.name.startswith("live_events_") or p.name.startswith("smoke_"):
            continue
        try:
            blob = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        bookmakers = blob.get("bookmakers") or []
        if not isinstance(bookmakers, list):
            continue
        for b in bookmakers:
            for m in b.get("markets") or []:
                k = str(m.get("key") or "").strip()
                if not k:
                    continue
                keys[k] += 1
                rows += 1
                for o in m.get("outcomes") or []:
                    rows += 1
    return rows, set(keys.keys()), keys


def _load_processed_for_day(day: str, snapshot_substr: str) -> pd.DataFrame:
    p = _find_odds_pairs_file(day, snapshot_substr)
    if p is None or not p.exists():
        return pd.DataFrame()
    df = pd.read_parquet(p)
    if "market_stat" in df.columns:
        df = df.copy()
        df["stat_canonical"] = df["market_stat"].apply(_norm_stat)
    elif "stat" in df.columns:
        df = df.copy()
        df["stat_canonical"] = df["stat"].apply(_norm_stat)
    else:
        df = df.copy()
        df["stat_canonical"] = None
    if "market_key" in df.columns:
        mk = df["market_key"].astype(str)
        st = mk.map(lambda x: stat_for_market_key(x))
        df["stat_canonical"] = df["stat_canonical"].fillna(st)
    return df


def _aggregate_stat_grid(dates: list[str]) -> dict[str, int]:
    counts: Counter = Counter()
    for d in dates:
        p = REPO_ROOT / "predictions" / f"stat_grid_{d}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p, columns=["stat"])
        df["stat"] = df["stat"].astype(str).str.lower()
        for s, n in df["stat"].value_counts().items():
            counts[str(s).lower()] += int(n)
    return dict(counts)


def _aggregate_canonical(dates: list[str]) -> dict[str, int]:
    counts: Counter = Counter()
    for d in dates:
        p = (
            REPO_ROOT
            / "deliveries"
            / d
            / "canonical_source"
            / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
        )
        if not p.exists():
            continue
        df = pd.read_parquet(p, columns=["stat"])
        df["stat"] = df["stat"].apply(_norm_stat).astype(str).str.lower()
        for s, n in df["stat"].value_counts().items():
            counts[str(s).lower()] += int(n)
    return dict(counts)


def _load_eml_for_dates(dates: list[str]) -> pd.DataFrame:
    if len(dates) > 1:
        r = (
            REPO_ROOT
            / "artifacts"
            / "model_diagnostics"
            / f"event_market_loss_rows_{dates[0]}_{dates[-1]}.parquet"
        )
        if r.exists():
            return pd.read_parquet(r)
    frames: list[pd.DataFrame] = []
    for d in dates:
        p = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{d}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _box_rows_for_dates(dates: list[str]) -> int:
    pgs = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not pgs.exists():
        return 0
    bx = pd.read_parquet(pgs, columns=["game_date"])
    bx["game_date"] = bx["game_date"].astype(str)
    m = bx["game_date"].str.slice(0, 10).isin(dates)
    return int(m.sum())


def _classify_stat(
    stat: str,
    *,
    keys_for_stat: tuple[str, ...],
    requested_global: frozenset[str],
    seen_raw_keys: set[str],
    seen_proc_keys: set[str],
    proc_rows: int,
    proc_two_way: int,
    eml_rows: int,
    matched: int,
    scored: int,
    box_rows: int,
    min_scored: int,
) -> str:
    keys_for_stat_set = set(keys_for_stat)
    if any(k not in requested_global for k in keys_for_stat):
        return "not_requested_from_odds_api"

    raw_hits = keys_for_stat_set & seen_raw_keys

    if not raw_hits:
        return "no_offered_market"

    # Raw contained at least one registered key for this stat, but processed
    # odds_pairs has no rows for this canonical stat (parser/filter/stat mapping).
    if raw_hits and proc_rows == 0:
        return "processed_parser_dropped_market"

    if proc_rows > 0 and proc_two_way == 0:
        return "missing_two_way_odds"

    if proc_rows > 0 and eml_rows == 0:
        return "player_join_failed"

    if eml_rows > 0 and matched == 0:
        return "player_join_failed"

    if matched > 0 and scored == 0:
        if box_rows <= 0:
            return "no_actuals"
        return "missing_two_way_odds"

    if scored > 0 and scored < min_scored:
        return "insufficient_scored_rows"

    if scored >= min_scored:
        return "covered"

    return "insufficient_scored_rows"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--snapshot-substr", default="close_or_lock")
    ap.add_argument("--min-scored-rows", type=int, default=DEFAULT_MIN_SCORED)
    args = ap.parse_args()

    if args.date:
        dates = [args.date]
        label = args.date
    elif args.start_date and args.end_date:
        dates = _iter_dates(args.start_date, args.end_date)
        label = f"{args.start_date}_{args.end_date}"
    else:
        print("FATAL: pass --date YYYY-MM-DD or --start-date and --end-date", file=sys.stderr)
        return 2

    requested_global = frozenset(ODDSAPI_NBA_DEFAULT_MARKETS)

    raw_rows_total = 0
    all_raw_keys: set[str] = set()
    raw_key_counts: Counter = Counter()

    proc_frames: list[pd.DataFrame] = []
    proc_rows_total = 0
    for d in dates:
        raw_r, raw_k, raw_c = _scan_raw_market_keys(d)
        raw_rows_total += raw_r
        all_raw_keys |= raw_k
        raw_key_counts += raw_c
        proc_frames.append(_load_processed_for_day(d, args.snapshot_substr))

    proc_all = pd.concat(proc_frames, ignore_index=True) if proc_frames else pd.DataFrame()
    proc_rows_total = len(proc_all)
    seen_proc_keys: set[str] = set()
    if proc_rows_total and "market_key" in proc_all.columns:
        seen_proc_keys = set(proc_all["market_key"].dropna().astype(str).unique())

    sg_counts = _aggregate_stat_grid(dates)
    can_counts = _aggregate_canonical(dates)
    eml = _load_eml_for_dates(dates)
    box_rows = _box_rows_for_dates(dates)

    rows_out: list[dict] = []
    for stat in REQUIRED_STATS:
        keys_for_stat = tuple(market_keys_for_stat(stat, include_alternates=True))
        market_keys_requested = list(keys_for_stat)
        keys_for_stat_set = set(keys_for_stat)
        seen_proc_for_stat = sorted(keys_for_stat_set & seen_proc_keys)

        sub_proc = proc_all[proc_all["stat_canonical"].astype(str).str.lower() == stat] if len(proc_all) else pd.DataFrame()
        pr = int(len(sub_proc))
        if pr and "no_vig_over_prob" in sub_proc.columns and "no_vig_under_prob" in sub_proc.columns:
            tw = sub_proc[
                sub_proc["no_vig_over_prob"].notna()
                & sub_proc["no_vig_under_prob"].notna()
            ]
            ptw = int(len(tw))
        else:
            ptw = 0

        sub_eml = eml[eml["stat"].astype(str).str.lower() == stat] if len(eml) and "stat" in eml.columns else pd.DataFrame()
        er = int(len(sub_eml))
        matched = int((sub_eml["join_status"] == "matched").sum()) if er and "join_status" in sub_eml.columns else 0
        scored = 0
        if er:
            sm = (
                sub_eml["model_prob_over"].notna()
                & sub_eml.get("market_prob_over_no_vig", pd.Series(np.nan)).notna()
                & sub_eml["hit_result"].notna()
                & sub_eml.get("model_event_logloss", pd.Series(np.nan)).notna()
                & sub_eml.get("market_event_logloss", pd.Series(np.nan)).notna()
            )
            scored = int(sm.sum()) if "model_prob_over" in sub_eml.columns else 0

        books = int(sub_eml["bookmaker_key"].nunique()) if er and "bookmaker_key" in sub_eml.columns else 0
        players = int(sub_eml["player_id"].nunique()) if er and "player_id" in sub_eml.columns else 0
        games = int(sub_eml["game_id"].nunique()) if er and "game_id" in sub_eml.columns else 0

        reason = _classify_stat(
            stat,
            keys_for_stat=keys_for_stat,
            requested_global=requested_global,
            seen_raw_keys=all_raw_keys,
            seen_proc_keys=seen_proc_keys,
            proc_rows=pr,
            proc_two_way=ptw,
            eml_rows=er,
            matched=matched,
            scored=scored,
            box_rows=box_rows,
            min_scored=args.min_scored_rows,
        )

        raw_stat = int(sum(raw_key_counts[k] for k in keys_for_stat_set & all_raw_keys))

        rows_out.append({
            "stat": stat,
            "model_stat_grid_rows": int(sg_counts.get(stat, 0)),
            "canonical_rows": int(can_counts.get(stat, 0)),
            "raw_odds_rows": raw_stat,
            "processed_odds_rows": int(pr),
            "two_way_odds_rows": int(ptw),
            "event_market_rows": er,
            "matched_rows": matched,
            "scored_rows": scored,
            "books_count": books,
            "players_count": players,
            "games_count": games,
            "market_keys_requested": market_keys_requested,
            "market_keys_seen_raw": sorted(keys_for_stat_set & all_raw_keys),
            "market_keys_seen_processed": seen_proc_for_stat,
            "missing_reason": reason,
        })

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_coverage_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows_out)
    # Expand list columns for CSV — use JSON strings
    df_csv = df.copy()
    df_csv["market_keys_requested"] = df_csv["market_keys_requested"].apply(json.dumps)
    df_csv["market_keys_seen_raw"] = df_csv["market_keys_seen_raw"].apply(json.dumps)
    df_csv["market_keys_seen_processed"] = df_csv["market_keys_seen_processed"].apply(json.dumps)
    df_csv.to_csv(out_dir / "coverage_by_stat.csv", index=False)

    payload = {
        "label": label,
        "dates": dates,
        "snapshot_substr": args.snapshot_substr,
        "min_scored_rows": args.min_scored_rows,
        "oddsapi_default_market_count": len(ODDSAPI_NBA_DEFAULT_MARKETS),
        "stats": rows_out,
    }
    (out_dir / "coverage_by_stat.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md_lines = [
        f"# Event-market coverage audit — `{label}`",
        "",
        f"- Dates: {', '.join(dates)}",
        f"- Snapshot filter: `*{args.snapshot_substr}*`",
        f"- `min_scored_rows` threshold for `covered`: {args.min_scored_rows}",
        "",
        "## Summary",
        "",
        "| stat | processed_rows | two_way | eml_rows | matched | scored | missing_reason |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows_out:
        md_lines.append(
            f"| {r['stat']} | {r['processed_odds_rows']} | {r['two_way_odds_rows']} | "
            f"{r['event_market_rows']} | {r['matched_rows']} | {r['scored_rows']} | `{r['missing_reason']}` |"
        )
    md_lines.extend([
        "",
        "## Interpretation",
        "",
        "- **no_offered_market**: Odds API responses for this slate did not include any "
        "registered market key for the stat (books did not offer / API omitted).",
        "- **processed_parser_dropped_market**: Raw JSON contained the market key but "
        "processed `odds_pairs` did not — investigate `oddsapi_nba_props.py` pairing/filtering.",
        "- **not_requested_from_odds_api**: A registered market key for this stat is missing "
        "from `ODDSAPI_NBA_DEFAULT_MARKETS` (fetch/registry bug).",
        "- **insufficient_scored_rows**: End-to-end rows exist but scored count is below "
        f"the audit threshold ({args.min_scored_rows}); use multi-date aggregation for superiority.",
        "",
    ])
    (out_dir / "missing_market_diagnosis.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"EVENT_MARKET_COVERAGE_AUDIT_PASS out={out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
