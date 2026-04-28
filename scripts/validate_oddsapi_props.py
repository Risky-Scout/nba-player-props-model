"""Validate Odds API processed-quote and paired-no-vig parquet files.

Usage:
  python3 scripts/validate_oddsapi_props.py --input data/odds_api/processed --latest
  python3 scripts/validate_oddsapi_props.py --quotes path/to/odds_quotes_*.parquet \
                                            --pairs  path/to/odds_pairs_*.parquet
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "data" / "odds_api" / "processed"

REQUIRED_QUOTE_COLS = [
    "snapshot_id", "snapshot_time_utc", "snapshot_type", "api_mode",
    "sport_key", "event_id", "commence_time_utc", "home_team", "away_team",
    "bookmaker_key", "bookmaker_title", "bookmaker_last_update",
    "market_key", "market_stat", "is_alternate", "market_last_update",
    "player_name", "side", "line", "odds_american", "outcome_sid",
    "raw_description", "raw_name", "source_file", "fetched_at_utc",
]
REQUIRED_PAIR_COLS = [
    "snapshot_id", "snapshot_time_utc", "snapshot_type", "api_mode",
    "event_id", "commence_time_utc", "home_team", "away_team",
    "bookmaker_key", "bookmaker_title",
    "market_key", "market_stat", "is_alternate",
    "player_name", "line",
    "over_odds_american", "under_odds_american",
    "over_odds_decimal", "under_odds_decimal",
    "over_implied_prob", "under_implied_prob",
    "no_vig_over_prob", "no_vig_under_prob",
    "bookmaker_last_update", "market_last_update",
    "over_sid", "under_sid", "pair_key", "fetched_at_utc",
]
TARGET_STATS = {"pts", "reb", "ast", "tov", "fg3m"}
TARGET_MARKETS = {
    "player_points", "player_rebounds", "player_assists",
    "player_turnovers", "player_threes",
    "player_points_alternate", "player_rebounds_alternate",
    "player_assists_alternate", "player_turnovers_alternate",
    "player_threes_alternate",
}


def _find_latest_pair(input_dir: Path) -> tuple[Path | None, Path | None]:
    """Find newest (quotes, pairs) parquet pair under input_dir.

    Prefer matched pairs that share the same suffix; if no exact suffix
    match, return newest of each.
    """
    quotes = sorted(input_dir.rglob("odds_quotes_*.parquet"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    pairs = sorted(input_dir.rglob("odds_pairs_*.parquet"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not quotes or not pairs:
        return (quotes[0] if quotes else None,
                pairs[0] if pairs else None)
    # Try to match newest quotes' suffix to a pairs file with same suffix.
    q0 = quotes[0]
    suffix = q0.name[len("odds_quotes_"):]
    candidate = q0.parent / f"odds_pairs_{suffix}"
    if candidate.exists():
        return q0, candidate
    return q0, pairs[0]


def _empty_str_or_null(s: pd.Series) -> pd.Series:
    """Boolean mask: NaN or empty/whitespace-only string."""
    return s.isna() | s.astype(str).str.strip().eq("")


def _validate_quotes(q: pd.DataFrame) -> dict:
    rep: dict = {}
    rep["row_count"] = len(q)
    rep["missing_cols"] = sorted(set(REQUIRED_QUOTE_COLS) - set(q.columns))
    if q.empty:
        return rep
    rep["null_event_id"] = int(_empty_str_or_null(q["event_id"]).sum()) if "event_id" in q else None
    rep["null_commence_time"] = (int(_empty_str_or_null(q["commence_time_utc"]).sum())
                                 if "commence_time_utc" in q else None)
    rep["null_player_name"] = (int(_empty_str_or_null(q["player_name"]).sum())
                               if "player_name" in q else None)
    rep["null_market_stat"] = (int(_empty_str_or_null(q["market_stat"]).sum())
                               if "market_stat" in q else None)
    rep["bad_market_stat"] = (int((~q["market_stat"].isin(list(TARGET_STATS))).sum())
                              if "market_stat" in q else None)
    rep["bad_line"] = (int((~np.isfinite(pd.to_numeric(q["line"], errors="coerce"))).sum())
                       if "line" in q else None)
    rep["bad_odds"] = (int((~np.isfinite(pd.to_numeric(q["odds_american"], errors="coerce"))).sum())
                       if "odds_american" in q else None)
    rep["alt_count"] = int(q["is_alternate"].sum()) if "is_alternate" in q else 0
    rep["main_count"] = int((~q["is_alternate"].astype(bool)).sum()) if "is_alternate" in q else 0
    if "market_key" in q:
        rep["seen_markets"] = sorted(q["market_key"].dropna().unique().tolist())
        rep["missing_target_markets"] = sorted(TARGET_MARKETS - set(rep["seen_markets"]))
        rep["rows_by_market"] = q["market_key"].value_counts().to_dict()
    if "market_stat" in q:
        rep["rows_by_stat"] = q["market_stat"].value_counts().to_dict()
    if "bookmaker_key" in q:
        rep["rows_by_book"] = q["bookmaker_key"].value_counts().to_dict()
    if "event_id" in q:
        rep["rows_by_event"] = q["event_id"].value_counts().to_dict()
    if "side" in q:
        rep["rows_by_side"] = q["side"].value_counts().to_dict()
    return rep


def _validate_pairs(p: pd.DataFrame, q: pd.DataFrame) -> dict:
    rep: dict = {}
    rep["row_count"] = len(p)
    rep["missing_cols"] = sorted(set(REQUIRED_PAIR_COLS) - set(p.columns))
    if p.empty:
        return rep
    nv_o = pd.to_numeric(p["no_vig_over_prob"], errors="coerce")
    nv_u = pd.to_numeric(p["no_vig_under_prob"], errors="coerce")
    rep["nv_over_min"] = float(nv_o.min())
    rep["nv_over_max"] = float(nv_o.max())
    rep["nv_under_min"] = float(nv_u.min())
    rep["nv_under_max"] = float(nv_u.max())
    rep["nv_over_out_of_range"] = int(((nv_o < 0) | (nv_o > 1)).sum())
    rep["nv_under_out_of_range"] = int(((nv_u < 0) | (nv_u > 1)).sum())
    rep["nv_sum_off_one"] = int(((nv_o + nv_u - 1.0).abs() > 1e-6).sum())
    if "pair_key" in p.columns:
        rep["duplicate_pair_count"] = int(p["pair_key"].duplicated().sum())
    if "is_alternate" in p.columns:
        rep["pairs_alt"] = int(p["is_alternate"].astype(bool).sum())
        rep["pairs_main"] = int((~p["is_alternate"].astype(bool)).sum())
    if "market_key" in p.columns:
        rep["pairs_by_market_key"] = p["market_key"].value_counts().to_dict()
    if "market_stat" in p.columns:
        rep["pairs_by_stat"] = p["market_stat"].value_counts().to_dict()
    if "bookmaker_key" in p.columns:
        rep["pairs_by_book"] = p["bookmaker_key"].value_counts().to_dict()
    if "event_id" in p.columns:
        rep["pairs_by_event"] = p["event_id"].value_counts().to_dict()
    if not q.empty:
        approx_unpaired = max(len(q) - 2 * len(p), 0)
        rep["approx_unpaired"] = int(approx_unpaired)
        if "market_key" in q.columns and "market_key" in p.columns:
            per_market_q = q["market_key"].value_counts()
            per_market_p = p["market_key"].value_counts()
            unpaired_by_market = {}
            for k in set(per_market_q.index) | set(per_market_p.index):
                unpaired_by_market[k] = int(per_market_q.get(k, 0) - 2 * per_market_p.get(k, 0))
            rep["unpaired_by_market"] = unpaired_by_market
    return rep


def _format_dict_block(d: dict, indent: int = 4, sort_by: str = "value_desc") -> list[str]:
    if not d:
        return [" " * indent + "(empty)"]
    items = list(d.items())
    if sort_by == "value_desc":
        items.sort(key=lambda kv: (-(kv[1] if isinstance(kv[1], (int, float)) else 0),
                                   str(kv[0])))
    else:
        items.sort(key=lambda kv: str(kv[0]))
    return [" " * indent + f"{k}: {v}" for k, v in items]


def _print_report(label: str, q_path: Path, p_path: Path,
                  q_rep: dict, p_rep: dict) -> None:
    print()
    print("=" * 72)
    print(f"VALIDATION — {label}")
    print(f"  quotes: {q_path}")
    print(f"  pairs:  {p_path}")
    print("=" * 72)
    print("\n[QUOTES]")
    for k, v in q_rep.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for line in _format_dict_block(v):
                print(line)
        elif isinstance(v, list):
            if not v:
                print(f"  {k}: []")
            elif all(isinstance(x, str) for x in v):
                print(f"  {k}: {v}")
            else:
                print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")
    print("\n[PAIRS]")
    for k, v in p_rep.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for line in _format_dict_block(v):
                print(line)
        elif isinstance(v, list):
            if not v:
                print(f"  {k}: []")
            else:
                print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DEFAULT_INPUT))
    ap.add_argument("--latest", action="store_true",
                    help="auto-pick newest odds_quotes_*.parquet + matching odds_pairs_*.parquet")
    ap.add_argument("--quotes", default=None, help="path to a quotes parquet")
    ap.add_argument("--pairs", default=None, help="path to a pairs parquet")
    ap.add_argument("--allow-empty", action="store_true",
                    help="treat empty quotes as WARN, not FAIL "
                         "(use only for fixture / quota-blocked smoke runs)")
    args = ap.parse_args()

    if args.latest:
        q_path, p_path = _find_latest_pair(Path(args.input))
    else:
        q_path = Path(args.quotes) if args.quotes else None
        p_path = Path(args.pairs) if args.pairs else None

    if not q_path or not p_path or not q_path.exists() or not p_path.exists():
        print(f"FATAL: could not resolve quotes/pairs files. quotes={q_path} pairs={p_path}",
              file=sys.stderr)
        return 1

    q = pd.read_parquet(q_path)
    p = pd.read_parquet(p_path)
    q_rep = _validate_quotes(q)
    p_rep = _validate_pairs(p, q)
    _print_report(f"latest under {args.input}", q_path, p_path, q_rep, p_rep)

    fail = False
    warn = False

    # Empty-frame handling
    if q.empty:
        if args.allow_empty:
            print("\nWARN: quotes file is empty (allowed by --allow-empty).")
            warn = True
        else:
            print("\nFAIL: quotes file is empty.")
            fail = True
    else:
        # Schema completeness
        if q_rep.get("missing_cols"):
            print(f"\nFAIL: quotes missing required columns: {q_rep['missing_cols']}")
            fail = True
        # Null/empty key fields
        for fld in ("null_event_id", "null_commence_time", "null_player_name",
                    "null_market_stat"):
            if (q_rep.get(fld) or 0) > 0:
                print(f"\nWARN: quotes has {q_rep[fld]} rows with empty/null {fld[5:]}")
                warn = True
        if (q_rep.get("bad_market_stat") or 0) > 0:
            print(f"\nFAIL: quotes has {q_rep['bad_market_stat']} rows with "
                  f"market_stat outside the target set {sorted(TARGET_STATS)}")
            fail = True
        if (q_rep.get("bad_line") or 0) > 0:
            print(f"\nFAIL: quotes has {q_rep['bad_line']} rows with non-finite line")
            fail = True
        if (q_rep.get("bad_odds") or 0) > 0:
            print(f"\nFAIL: quotes has {q_rep['bad_odds']} rows with non-finite odds_american")
            fail = True
        # Missing target markets → WARN, not FAIL
        missing = q_rep.get("missing_target_markets") or []
        if missing:
            print(f"\nWARN: target markets not present in this capture: {missing}")
            warn = True

    if p.empty:
        print("\nWARN: pairs file is empty (no Over/Under pairing produced)")
        warn = True
    else:
        if p_rep.get("missing_cols"):
            print(f"\nFAIL: pairs missing required columns: {p_rep['missing_cols']}")
            fail = True
        if p_rep.get("nv_over_out_of_range", 0) > 0:
            print(f"\nFAIL: {p_rep['nv_over_out_of_range']} pairs have "
                  f"no_vig_over_prob outside [0,1]")
            fail = True
        if p_rep.get("nv_under_out_of_range", 0) > 0:
            print(f"\nFAIL: {p_rep['nv_under_out_of_range']} pairs have "
                  f"no_vig_under_prob outside [0,1]")
            fail = True
        if p_rep.get("nv_sum_off_one", 0) > 0:
            print(f"\nFAIL: {p_rep['nv_sum_off_one']} pairs have "
                  f"no_vig_over + no_vig_under not equal 1 (within 1e-6)")
            fail = True
        if p_rep.get("duplicate_pair_count", 0) > 0:
            print(f"\nWARN: {p_rep['duplicate_pair_count']} duplicate pair_key rows")
            warn = True

    print()
    if fail:
        print("VALIDATION FAILED.")
        return 1
    if warn:
        print("VALIDATION OK (with WARNs above).")
        return 0
    print("VALIDATION OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
