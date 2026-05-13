#!/usr/bin/env python3
"""Event-market coverage audit by canonical stat (M8.6).

Evidence-backed classification: `no_offered_market` only when registry-requested keys
are absent from raw Odds API JSON (raw files must exist).

Run:
  python3 scripts/audit_event_market_coverage_by_stat.py --date 2026-05-12
  python3 scripts/audit_event_market_coverage_by_stat.py --start-date 2026-05-07 --end-date 2026-05-12
  python3 scripts/audit_event_market_coverage_by_stat.py --dates-file artifacts/.../inventory.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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
REGISTRY_SOURCE = "nba_props_model.markets.oddsapi_markets.ODDSAPI_NBA_DEFAULT_MARKETS"
DEFAULT_MIN_SCORED = 100


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


def _scan_raw_detail(day: str) -> tuple[list[str], set[str], Counter]:
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
        bookmakers = blob.get("bookmakers") or []
        if not isinstance(bookmakers, list):
            continue
        for b in bookmakers:
            for m in b.get("markets") or []:
                k = str(m.get("key") or "").strip()
                if not k:
                    continue
                keys[k] += 1
    return paths, set(keys.keys()), keys


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


def _load_eml_for_label(dates: list[str], label: str) -> pd.DataFrame:
    p_dates = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    if p_dates.exists():
        return pd.read_parquet(p_dates)
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


def _final_classify(
    *,
    expected_keys: tuple[str, ...],
    registry: frozenset[str],
    raw_json_files_checked: int,
    raw_market_keys_seen_for_stat: set[str],
    proc_rows: int,
    proc_two_way: int,
    eml_rows: int,
    matched: int,
    scored: int,
    min_scored: int,
) -> tuple[str, str, str, str, str, str]:
    exp_set = set(expected_keys)
    missing_from_registry = sorted(exp_set - registry)
    requested = sorted(exp_set & registry)
    req_status = (
        "all_expected_keys_in_registry"
        if not missing_from_registry
        else "missing_expected_keys_from_registry"
    )
    if missing_from_registry:
        return (
            "not_requested_from_odds_api",
            req_status,
            "not_evaluated",
            "not_evaluated",
            "not_evaluated",
            json.dumps(requested),
        )

    raw_pres = (
        "no_raw_json_files"
        if raw_json_files_checked == 0
        else (
            "expected_keys_present_in_raw"
            if raw_market_keys_seen_for_stat
            else "expected_keys_absent_in_raw"
        )
    )

    if raw_json_files_checked == 0:
        return (
            "event_market_join_failed",
            req_status,
            raw_pres,
            "unknown_no_processed_context",
            "blocked_no_raw_odds_evidence",
            json.dumps(requested),
        )

    if not raw_market_keys_seen_for_stat:
        return (
            "no_offered_market",
            req_status,
            raw_pres,
            "no_processed_rows_for_stat",
            "no_event_rows_expected",
            json.dumps(requested),
        )

    proc_pres = (
        "processed_rows_for_stat_absent"
        if proc_rows == 0
        else ("two_way_absent" if proc_two_way == 0 else "two_way_present")
    )

    if proc_rows == 0:
        return (
            "processed_parser_dropped_market",
            req_status,
            raw_pres,
            proc_pres,
            "no_event_rows",
            json.dumps(requested),
        )

    if proc_two_way == 0:
        return (
            "event_market_join_failed",
            req_status,
            raw_pres,
            proc_pres,
            "blocked_missing_two_way_odds",
            json.dumps(requested),
        )

    join_pres = (
        "no_event_market_rows"
        if eml_rows == 0
        else ("no_matched_rows" if matched == 0 else "matched_rows_present")
    )

    if eml_rows == 0 or matched == 0:
        return (
            "event_market_join_failed",
            req_status,
            raw_pres,
            proc_pres,
            join_pres,
            json.dumps(requested),
        )

    if scored < min_scored:
        return (
            "insufficient_scored_rows",
            req_status,
            raw_pres,
            proc_pres,
            "matched_but_insufficient_scored_sample",
            json.dumps(requested),
        )

    return (
        "covered",
        req_status,
        raw_pres,
        proc_pres,
        "scored_sample_sufficient",
        json.dumps(requested),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--dates-file", default=None)
    ap.add_argument("--include-ineligible", action="store_true")
    ap.add_argument("--snapshot-substr", default="close_or_lock")
    ap.add_argument("--min-scored-rows", type=int, default=DEFAULT_MIN_SCORED)
    args = ap.parse_args()

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from event_market_date_selection import resolve_event_market_label  # noqa: WPS433

    dates, label, meta = resolve_event_market_label(
        date=args.date,
        start_date=args.start_date,
        end_date=args.end_date,
        dates_file=args.dates_file,
        include_ineligible=args.include_ineligible,
    )
    dates_fp = meta.get("dates_fingerprint")
    registry = frozenset(ODDSAPI_NBA_DEFAULT_MARKETS)

    all_raw_paths: list[str] = []
    all_raw_keys: set[str] = set()
    raw_key_counts: Counter = Counter()
    odds_snapshots_checked: list[str] = []
    proc_frames: list[pd.DataFrame] = []

    for d in dates:
        rp, rk, rc = _scan_raw_detail(d)
        all_raw_paths.extend(rp)
        all_raw_keys |= rk
        raw_key_counts += rc
        op = _find_odds_pairs_file(d, args.snapshot_substr)
        if op and op.exists():
            odds_snapshots_checked.append(str(op.relative_to(REPO_ROOT)))
        proc_frames.append(_load_processed_for_day(d, args.snapshot_substr))

    proc_all = pd.concat(proc_frames, ignore_index=True) if proc_frames else pd.DataFrame()
    seen_proc_keys: set[str] = set()
    if len(proc_all) and "market_key" in proc_all.columns:
        seen_proc_keys = set(proc_all["market_key"].dropna().astype(str).unique())

    sg_counts = _aggregate_stat_grid(dates)
    can_counts = _aggregate_canonical(dates)
    eml = _load_eml_for_label(dates, label)
    raw_json_n = len(all_raw_paths)

    rows_out: list[dict] = []
    for stat in REQUIRED_STATS:
        expected_keys = tuple(market_keys_for_stat(stat, include_alternates=True))
        keys_for_stat_set = set(expected_keys)
        raw_seen_stat = keys_for_stat_set & all_raw_keys
        proc_keys_stat = sorted(keys_for_stat_set & seen_proc_keys)

        sub_proc = (
            proc_all[proc_all["stat_canonical"].astype(str).str.lower() == stat]
            if len(proc_all)
            else pd.DataFrame()
        )
        pr = int(len(sub_proc))
        if pr and "no_vig_over_prob" in sub_proc.columns and "no_vig_under_prob" in sub_proc.columns:
            ptw = int((sub_proc["no_vig_over_prob"].notna() & sub_proc["no_vig_under_prob"].notna()).sum())
        else:
            ptw = 0

        sub_eml = (
            eml[eml["stat"].astype(str).str.lower() == stat]
            if len(eml) and "stat" in eml.columns
            else pd.DataFrame()
        )
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

        final, req_cov, raw_pres, proc_pres, join_pres, requested_json = _final_classify(
            expected_keys=expected_keys,
            registry=registry,
            raw_json_files_checked=raw_json_n,
            raw_market_keys_seen_for_stat=raw_seen_stat,
            proc_rows=pr,
            proc_two_way=ptw,
            eml_rows=er,
            matched=matched,
            scored=scored,
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
            "expected_market_keys_for_stat": list(expected_keys),
            "requested_market_keys": json.loads(requested_json),
            "raw_market_keys_seen_for_stat": sorted(raw_seen_stat),
            "processed_market_keys_seen_for_stat": proc_keys_stat,
            "odds_snapshot_files_checked": odds_snapshots_checked,
            "raw_json_files_checked": raw_json_n,
            "raw_json_paths_checked": all_raw_paths,
            "request_registry_source": REGISTRY_SOURCE,
            "request_coverage_status": req_cov,
            "raw_market_presence_status": raw_pres,
            "processed_market_presence_status": proc_pres,
            "event_join_presence_status": join_pres,
            "final_missing_reason": final,
            "missing_reason": final,
            "market_keys_requested": list(expected_keys),
            "market_keys_seen_raw": sorted(raw_seen_stat),
            "market_keys_seen_processed": proc_keys_stat,
        })

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_coverage_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows_out)
    df_csv = df.copy()
    for col in (
        "expected_market_keys_for_stat",
        "requested_market_keys",
        "raw_market_keys_seen_for_stat",
        "processed_market_keys_seen_for_stat",
        "odds_snapshot_files_checked",
        "raw_json_paths_checked",
        "market_keys_requested",
        "market_keys_seen_raw",
        "market_keys_seen_processed",
    ):
        if col in df_csv.columns:
            df_csv[col] = df_csv[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
    df_csv.to_csv(out_dir / "coverage_by_stat.csv", index=False)

    payload = {
        "label": label,
        "dates": dates,
        "dates_fingerprint": dates_fp,
        "dates_used": dates,
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
        "| stat | processed | two_way | eml | matched | scored | final_missing_reason | raw_presence |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in rows_out:
        md_lines.append(
            f"| {r['stat']} | {r['processed_odds_rows']} | {r['two_way_odds_rows']} | "
            f"{r['event_market_rows']} | {r['matched_rows']} | {r['scored_rows']} | "
            f"`{r['final_missing_reason']}` | `{r['raw_market_presence_status']}` |"
        )
    md_lines.extend([
        "",
        "## Rules",
        "",
        "- **`no_offered_market`** only when requested registry keys are **absent** from raw JSON "
        "and at least one raw JSON file was scanned.",
        "- **`not_requested_from_odds_api`** when expected keys are missing from the default registry.",
        "- **`event_market_join_failed`** includes missing raw files (cannot prove offer) or join gaps.",
        "",
    ])
    (out_dir / "missing_market_diagnosis.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"EVENT_MARKET_COVERAGE_AUDIT_PASS out={out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
