#!/usr/bin/env python3
"""Refresh ``predictions/nba_props_today.json`` from the day's dated
prediction artifacts.

The Wizard of Odds NBA props page (`predictions/nba-props.html`) renders
either from a deployed PHP endpoint (`./api/live_props.php`) or, in the
local fallback path, from `predictions/nba_props_today.json`. The daily
prediction pipeline writes dated files (`all_props_<date>.parquet`,
`pmf_display_<date>.json`, `singles_<date>.json`) but historically did
not refresh the static `nba_props_today.json`, leaving the local
fallback stale (months old in the worst case).

This helper reads the dated artifacts and writes a fresh
`nba_props_today.json` with:

  - date (target date)
  - generated_at (utc iso)
  - count = number of props
  - games = unique game_id count from the parquet
  - reason (only when count == 0; explains the no-data state)
  - upstream_statuses (paths + presence of each input file)
  - props[] = per-prop view matching the historical schema:
      player_id, player, game_id, game, stat, line, commence_time,
      over_odds, under_odds, model_prob_over, model_prob_under,
      ev_over, ev_under, projection, q_preds, book_key, market_prob_over

Hard rules:
  - NO model values are mutated.
  - NO PMFs are recomputed — values flow through from the parquet.
  - NO odds re-anchored to market.
  - When all inputs are missing, an honest no-data file is written so
    the WoO front-end can render a clear empty state.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = REPO_ROOT / "predictions"


def _utc_iso(now: dt.datetime | None = None) -> str:
    return (now or dt.datetime.now(dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%S")


def _coerce_float(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return f


def _row_to_prop(row: pd.Series) -> dict | None:
    """Project one parquet row into the historical nba_props_today shape.
    Returns ``None`` when essential fields are absent."""
    player_id = row.get("player_id")
    stat = row.get("stat")
    line = _coerce_float(row.get("line"))
    if player_id is None or stat is None or line is None:
        return None
    side = str(row.get("side", "")).upper()

    over_odds = row.get("over_odds")
    under_odds = row.get("under_odds")
    model_prob_cal = _coerce_float(row.get("model_prob_cal"))
    if model_prob_cal is None:
        model_prob_cal = _coerce_float(row.get("model_prob"))
    market_prob = _coerce_float(row.get("market_prob"))
    ev = _coerce_float(row.get("ev"))

    if side == "OVER":
        model_prob_over, model_prob_under = model_prob_cal, (
            None if model_prob_cal is None else 1.0 - model_prob_cal
        )
        market_prob_over = market_prob
        ev_over, ev_under = ev, None
    elif side == "UNDER":
        model_prob_under, model_prob_over = model_prob_cal, (
            None if model_prob_cal is None else 1.0 - model_prob_cal
        )
        market_prob_over = (
            None if market_prob is None else 1.0 - market_prob
        )
        ev_under, ev_over = ev, None
    else:
        model_prob_over = model_prob_cal
        model_prob_under = (
            None if model_prob_cal is None else 1.0 - model_prob_cal
        )
        market_prob_over = market_prob
        ev_over = ev
        ev_under = None

    q_preds_raw = row.get("q_preds")
    if isinstance(q_preds_raw, str):
        try:
            q_preds = json.loads(q_preds_raw)
        except Exception:
            try:
                q_preds = json.loads(q_preds_raw.replace("'", '"'))
            except Exception:
                q_preds = None
    elif isinstance(q_preds_raw, dict):
        q_preds = q_preds_raw
    else:
        q_preds = None

    return {
        "player_id": int(player_id) if pd.notna(player_id) else None,
        "player": row.get("player_name") or "",
        "game_id": int(row["game_id"]) if pd.notna(row.get("game_id")) else None,
        "game": row.get("game") or "",
        "stat": stat,
        "side": side or None,
        "line": line,
        "commence_time": row.get("game_start_time") or row.get("commence_time"),
        "over_odds": _coerce_float(over_odds),
        "under_odds": _coerce_float(under_odds),
        "model_prob_over": model_prob_over,
        "model_prob_under": model_prob_under,
        "ev_over": ev_over,
        "ev_under": ev_under,
        "projection": _coerce_float(row.get("pmf_mean")) or _coerce_float(row.get("q50")),
        "q_preds": q_preds,
        "book_key": row.get("bet_vendor") or row.get("book"),
        "market_prob_over": market_prob_over,
    }


def _write_nodata(date: str, reason: str, upstream: dict, out_path: Path) -> None:
    payload = {
        "date": date,
        "generated_at": _utc_iso(),
        "count": 0,
        "games": 0,
        "props": [],
        "reason": reason,
        "upstream_statuses": upstream,
    }
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--output", default=str(PRED_DIR / "nba_props_today.json"))
    args = ap.parse_args(argv)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    parquet = PRED_DIR / f"all_props_{args.date}.parquet"
    pmf_display = PRED_DIR / f"pmf_display_{args.date}.json"
    singles = PRED_DIR / f"singles_{args.date}.json"

    upstream = {
        "all_props_parquet": {"path": str(parquet.relative_to(REPO_ROOT)),
                                 "exists": parquet.exists()},
        "pmf_display_json": {"path": str(pmf_display.relative_to(REPO_ROOT)),
                                 "exists": pmf_display.exists()},
        "singles_json": {"path": str(singles.relative_to(REPO_ROOT)),
                                 "exists": singles.exists()},
    }

    if not parquet.exists():
        _write_nodata(
            args.date,
            f"all_props_{args.date}.parquet does not exist; daily prediction "
            "pipeline likely has not run for this date or upstream data is missing.",
            upstream, out_path,
        )
        print(f"NBA_PROPS_TODAY_NODATA  date={args.date}  reason=missing_parquet  out={out_path.relative_to(REPO_ROOT)}")
        return 0

    df = pd.read_parquet(parquet)
    if df.empty:
        _write_nodata(
            args.date,
            f"all_props_{args.date}.parquet is empty (zero prop rows). Slate "
            "may have no games or upstream odds were unavailable.",
            upstream, out_path,
        )
        print(f"NBA_PROPS_TODAY_NODATA  date={args.date}  reason=empty_parquet  "
              f"out={out_path.relative_to(REPO_ROOT)}")
        return 0

    props: list[dict] = []
    for _, r in df.iterrows():
        p = _row_to_prop(r)
        if p is not None:
            props.append(p)

    n_games = int(df["game_id"].nunique()) if "game_id" in df.columns else 0
    payload = {
        "date": args.date,
        "generated_at": _utc_iso(),
        "count": len(props),
        "games": n_games,
        "props": props,
        "upstream_statuses": upstream,
    }
    if not props:
        payload["reason"] = (
            "all_props parquet had rows but no prop projection passed the "
            "row→display projection (missing player_id/stat/line)."
        )

    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"NBA_PROPS_TODAY_PUBLISHED  date={args.date}  count={len(props)}  "
          f"games={n_games}  out={out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
