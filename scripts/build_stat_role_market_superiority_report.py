#!/usr/bin/env python3
"""M8.6 — aggregate event-market loss rows to stat × role segments.

Writes:
  artifacts/model_diagnostics/event_market_superiority_<date>/
    stat_role_market_superiority.csv
    stat_market_superiority.csv
    role_market_superiority.csv
    book_market_superiority.csv
    snapshot_market_superiority.csv
    summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402

REQUIRED_STATS = list(MISSION_REQUIRED_TARGETS_CANONICAL)
DEFAULT_MIN_SCORED = 100
DEFAULT_MIN_JOINED = 100


def _finite_mean(s: pd.Series) -> float | None:
    x = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if x.empty:
        return None
    return float(x.mean())


def _agg_segment(sub: pd.DataFrame, *, min_scored: int, min_joined: int) -> dict:
    n_rows = int(len(sub))
    joined = sub[sub.get("join_status", pd.Series(["unknown"] * len(sub))) == "matched"]
    n_market_joined = int(len(joined))
    settled = sub[sub.get("settled", False) == True] if "settled" in sub.columns else sub.iloc[0:0]
    n_scored = int(len(settled))
    mask = pd.Series(True, index=sub.index)
    for c in (
        "model_event_logloss", "market_event_logloss", "model_brier", "market_brier",
    ):
        if c in sub.columns:
            mask &= sub[c].notna()
    n_scored_core = int(mask.sum())

    def _m(col):
        return _finite_mean(sub[col]) if col in sub.columns else None

    out = {
        "n_rows": n_rows,
        "n_scored": n_scored_core,
        "n_market_joined": n_market_joined,
        "n_books": int(sub["bookmaker_key"].nunique()) if "bookmaker_key" in sub.columns else 0,
        "n_players": int(sub["player_id"].nunique()) if "player_id" in sub.columns else 0,
        "n_games": int(sub["game_id"].nunique()) if "game_id" in sub.columns else 0,
        "model_brier_avg": _m("model_brier"),
        "market_brier_avg": _m("market_brier"),
        "model_logloss_avg": _m("model_event_logloss"),
        "market_logloss_avg": _m("market_event_logloss"),
        "model_rps_avg": _m("model_rps"),
        "market_rps_avg": _m("market_rps") if "market_rps" in sub.columns else None,
        "market_coverage_status": "covered" if n_market_joined else "none",
        "availability_freshness_status": "unknown",
        "failure_reason": "",
        "market_superiority_pass": False,
    }
    if n_scored_core < min_scored:
        out["failure_reason"] = "insufficient_scored_rows"
    elif n_market_joined < min_joined:
        out["failure_reason"] = "insufficient_market_overlap"
    else:
        out["failure_reason"] = "model_metrics_missing_or_join_incomplete"

    mb, mm = out["model_brier_avg"], out["market_brier_avg"]
    ml, mk = out["model_logloss_avg"], out["market_logloss_avg"]
    out["brier_delta_model_minus_market"] = (mb - mm) if (mb is not None and mm is not None) else None
    out["logloss_delta_model_minus_market"] = (ml - mk) if (ml is not None and mk is not None) else None
    mr, mkr = out["model_rps_avg"], out["market_rps_avg"]
    out["rps_delta_model_minus_market"] = (mr - mkr) if (mr is not None and mkr is not None) else None
    out["rps_status"] = "unavailable_market_distribution" if mkr is None else "available"

    # Strict pass only when deltas strictly negative (model better) and samples sufficient.
    if (
        out["failure_reason"] == ""
        and mb is not None
        and mm is not None
        and ml is not None
        and mk is not None
        and mb < mm
        and ml < mk
    ):
        if mkr is None or (mr is not None and mr < mkr):
            out["market_superiority_pass"] = True
            out["failure_reason"] = ""
    if out["failure_reason"] == "" and not out["market_superiority_pass"]:
        out["failure_reason"] = "model_probabilities_worse_than_market"

    out["model_beats_market_brier"] = bool(mb is not None and mm is not None and mb < mm)
    out["model_beats_market_logloss"] = bool(ml is not None and mk is not None and ml < mk)
    out["model_beats_market_rps"] = bool(mkr is None or (mr is not None and mr < mkr))
    out["calibration_pass"] = False
    out["model_ece"] = None
    out["market_ece"] = None
    out["model_calibration_slope"] = None
    out["model_calibration_intercept"] = None
    out["market_calibration_slope"] = None
    out["market_calibration_intercept"] = None
    out["pit_ks"] = None
    out["mean_error"] = None
    out["variance_error"] = None
    out["p0_error"] = None
    out["model_better_calibrated"] = False
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--min-scored-rows", type=int, default=DEFAULT_MIN_SCORED)
    ap.add_argument("--min-market-joined-rows", type=int, default=DEFAULT_MIN_JOINED)
    args = ap.parse_args()
    date = args.date

    eml_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{date}.parquet"
    if not eml_path.exists():
        print(f"FATAL missing {eml_path}", file=sys.stderr)
        return 1
    eml = pd.read_parquet(eml_path)
    if "role_bucket" not in eml.columns:
        eml = eml.copy()
        eml["role_bucket"] = "unknown"

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_superiority_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows_sr = []
    for stat in sorted(eml["stat"].astype(str).str.lower().unique()):
        for role in sorted(eml["role_bucket"].astype(str).unique()):
            sub = eml[(eml["stat"].astype(str).str.lower() == stat) & (eml["role_bucket"].astype(str) == role)]
            agg = _agg_segment(
                sub,
                min_scored=args.min_scored_rows,
                min_joined=args.min_market_joined_rows,
            )
            rows_sr.append({
                "date": date,
                "stat": stat,
                "role_bucket": role,
                **agg,
                "market_superiority_eligible": agg["n_scored"] >= args.min_scored_rows
                and agg["n_market_joined"] >= args.min_market_joined_rows,
                "market_superiority_claim_allowed": False,
                "promotion_status": "no_market_superiority_claim",
            })

    df_sr = pd.DataFrame(rows_sr)
    df_sr.to_csv(out_dir / "stat_role_market_superiority.csv", index=False)

    # Rollups
    def _rollup(key):
        g = eml.groupby(eml[key].astype(str).str.lower(), dropna=False)
        out_rows = []
        for k, sub in g:
            agg = _agg_segment(
                sub,
                min_scored=args.min_scored_rows,
                min_joined=args.min_market_joined_rows,
            )
            out_rows.append({key: k, **agg})
        return pd.DataFrame(out_rows)

    _rollup("stat").to_csv(out_dir / "stat_market_superiority.csv", index=False)
    _rollup("role_bucket").to_csv(out_dir / "role_market_superiority.csv", index=False)
    if "bookmaker_key" in eml.columns:
        g = eml.groupby(eml["bookmaker_key"].astype(str), dropna=False)
        br = []
        for k, sub in g:
            br.append({"book": k, **_agg_segment(sub, min_scored=args.min_scored_rows, min_joined=args.min_market_joined_rows)})
        pd.DataFrame(br).to_csv(out_dir / "book_market_superiority.csv", index=False)
    else:
        pd.DataFrame(columns=["book"]).to_csv(out_dir / "book_market_superiority.csv", index=False)
    if "snapshot_type" in eml.columns:
        g = eml.groupby(eml["snapshot_type"].astype(str), dropna=False)
        sr = []
        for k, sub in g:
            sr.append({"snapshot_type": k, **_agg_segment(sub, min_scored=args.min_scored_rows, min_joined=args.min_market_joined_rows)})
        pd.DataFrame(sr).to_csv(out_dir / "snapshot_market_superiority.csv", index=False)
    else:
        pd.DataFrame(columns=["snapshot_type"]).to_csv(out_dir / "snapshot_market_superiority.csv", index=False)

    present_stats = set(eml["stat"].astype(str).str.lower().unique())
    missing_required = sorted(set(REQUIRED_STATS) - present_stats)
    n_pass = int(df_sr["market_superiority_pass"].sum()) if len(df_sr) else 0
    n_fail = int((~df_sr["market_superiority_pass"]).sum()) if len(df_sr) else 0
    elig = df_sr[df_sr["market_superiority_eligible"] == True]
    global_ok = (
        len(elig) > 0
        and bool(elig["market_superiority_pass"].all())
        and not missing_required
    )
    summary = {
        "date": date,
        "global_market_superiority_claim_allowed": global_ok,
        "n_segments_total": int(len(df_sr)),
        "n_segments_passed": n_pass,
        "n_segments_failed": n_fail,
        "required_stats_missing_in_event_rows": missing_required,
        "min_scored_rows": args.min_scored_rows,
        "min_market_joined_rows": args.min_market_joined_rows,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"STAT_ROLE_MARKET_SUPERIORITY_REPORT_PASS out={out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
