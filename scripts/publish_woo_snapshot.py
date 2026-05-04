#!/usr/bin/env python3
"""Phase 13AH — publish a Wizard of Odds snapshot file for one (date,
game_id, snapshot_type) tuple.

Outputs:
  predictions/woo_snapshots/<date>/<snapshot_type>/<scope>/nba_props_today.json

Where ``<scope>`` is ``slate`` for the morning snapshot (covers the
whole day's slate) and ``<game_id>`` for per-game near-tip snapshots
(t_minus_25, close_lock).

Source data:
  predictions/all_props_<date>.parquet — the canonical model output
  for the date. The publisher does NOT recompute model probabilities
  or PMFs; it only projects the parquet rows into a JSON-shaped
  snapshot the WoO front-end and downstream verifiers can read.

Hard rules:
  - PMF / model_prob / market_prob values flow through unchanged.
  - When the parquet does not exist OR has no rows for the requested
    game_id, the script writes an honest no-data file with reason +
    upstream_statuses, never an empty/blank artifact.
  - The published snapshot embeds ``snapshot_type`` and
    ``snapshot_scope`` so downstream consumers can distinguish the
    morning slate from per-game near-tip snapshots.
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
WOO_SNAP_ROOT = PRED_DIR / "woo_snapshots"

VALID_SNAPSHOT_TYPES = ("morning", "t_minus_25", "close_lock")


def _utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _coerce_float(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return f


def _row_to_prop(row: pd.Series) -> dict | None:
    pid = row.get("player_id")
    stat = row.get("stat")
    line = _coerce_float(row.get("line"))
    if pid is None or stat is None or line is None:
        return None
    side = str(row.get("side", "")).upper()
    model_prob_cal = _coerce_float(row.get("model_prob_cal"))
    if model_prob_cal is None:
        model_prob_cal = _coerce_float(row.get("model_prob"))
    market_prob = _coerce_float(row.get("market_prob"))
    ev = _coerce_float(row.get("ev"))

    if side == "OVER":
        model_prob_over = model_prob_cal
        model_prob_under = None if model_prob_cal is None else 1.0 - model_prob_cal
        market_prob_over = market_prob
        ev_over, ev_under = ev, None
    elif side == "UNDER":
        model_prob_under = model_prob_cal
        model_prob_over = None if model_prob_cal is None else 1.0 - model_prob_cal
        market_prob_over = None if market_prob is None else 1.0 - market_prob
        ev_over, ev_under = None, ev
    else:
        model_prob_over = model_prob_cal
        model_prob_under = None if model_prob_cal is None else 1.0 - model_prob_cal
        market_prob_over = market_prob
        ev_over, ev_under = ev, None

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
        "player_id": int(pid) if pd.notna(pid) else None,
        "player": row.get("player_name") or "",
        "game_id": int(row["game_id"]) if pd.notna(row.get("game_id")) else None,
        "game": row.get("game") or "",
        "stat": stat,
        "side": side or None,
        "line": line,
        "commence_time": row.get("game_start_time") or row.get("commence_time"),
        "over_odds": _coerce_float(row.get("over_odds")),
        "under_odds": _coerce_float(row.get("under_odds")),
        "model_prob_over": model_prob_over,
        "model_prob_under": model_prob_under,
        "ev_over": ev_over,
        "ev_under": ev_under,
        "projection": _coerce_float(row.get("pmf_mean")) or _coerce_float(row.get("q50")),
        "q_preds": q_preds,
        "book_key": row.get("bet_vendor") or row.get("book"),
        "market_prob_over": market_prob_over,
        "raw_edge": _coerce_float(row.get("raw_edge")),
        "lineup_confirmed": bool(row.get("lineup_confirmed")) if "lineup_confirmed" in row.index else None,
        "feature_set_id": row.get("contextual_feature_set_id"),
        "edge_publish_status": row.get("edge_publish_status"),
        "calibration_support_status": row.get("calibration_support_status"),
    }


def _write_snapshot(out_path: Path, payload: dict) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--snapshot-type", required=True, choices=VALID_SNAPSHOT_TYPES)
    ap.add_argument("--game-id",
                    help="Per-game scope. Required for t_minus_25 and close_lock; "
                         "ignored for morning (which always covers the slate).")
    args = ap.parse_args(argv)

    if args.snapshot_type in ("t_minus_25", "close_lock") and not args.game_id:
        print(f"WOO_SNAPSHOT_PUBLISH_FAILED  date={args.date}  "
              f"snapshot_type={args.snapshot_type}  reason=game_id_required",
              file=sys.stderr)
        return 1

    parquet = PRED_DIR / f"all_props_{args.date}.parquet"
    upstream = {
        "all_props_parquet": {
            "path": str(parquet.relative_to(REPO_ROOT)),
            "exists": parquet.exists(),
        }
    }

    scope = "slate" if args.snapshot_type == "morning" else str(args.game_id)
    out_path = WOO_SNAP_ROOT / args.date / args.snapshot_type / scope / "nba_props_today.json"

    if not parquet.exists():
        payload = {
            "schema_version": "1.0",
            "date": args.date,
            "snapshot_type": args.snapshot_type,
            "snapshot_scope": scope,
            "game_id": int(args.game_id) if args.game_id else None,
            "generated_at": _utc_iso(),
            "count": 0,
            "games": 0,
            "props": [],
            "reason": (
                f"all_props_{args.date}.parquet does not exist; daily prediction "
                "pipeline has not produced today's slate."
            ),
            "upstream_statuses": upstream,
            "status": "no_data",
        }
        _write_snapshot(out_path, payload)
        print(f"WOO_SNAPSHOT_PUBLISH_NODATA  date={args.date}  "
              f"snapshot_type={args.snapshot_type}  scope={scope}  "
              f"out={out_path.relative_to(REPO_ROOT)}")
        return 0

    df = pd.read_parquet(parquet)
    if args.game_id:
        sub = df[df["game_id"].astype(str) == str(args.game_id)].copy()
    else:
        sub = df.copy()

    props: list[dict] = []
    for _, r in sub.iterrows():
        p = _row_to_prop(r)
        if p is not None:
            props.append(p)

    n_games = int(sub["game_id"].nunique()) if "game_id" in sub.columns else 0
    matchup = (sub["game"].iloc[0]
               if "game" in sub.columns and len(sub) > 0
               else None)
    payload = {
        "schema_version": "1.0",
        "date": args.date,
        "snapshot_type": args.snapshot_type,
        "snapshot_scope": scope,
        "game_id": int(args.game_id) if args.game_id else None,
        "matchup": matchup,
        "generated_at": _utc_iso(),
        "count": len(props),
        "games": n_games,
        "props": props,
        "upstream_statuses": upstream,
        "status": "ok" if props else "no_props_for_scope",
    }
    if not props:
        payload["reason"] = (
            f"all_props parquet had {len(sub)} rows for scope={scope!r} but no "
            "rows projected to a valid prop (missing player_id/stat/line)."
        )
    _write_snapshot(out_path, payload)
    print(f"WOO_SNAPSHOT_PUBLISH_PASS  date={args.date}  "
          f"snapshot_type={args.snapshot_type}  scope={scope}  "
          f"count={len(props)}  games={n_games}  "
          f"out={out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
