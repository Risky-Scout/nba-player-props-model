#!/usr/bin/env python3
"""Phase 13AH — score Wizard of Odds props after games using
``data/player_game_stats.parquet``.

For a delivery date <date>, joins ``predictions/all_props_<date>.parquet``
to the settled player game stats and computes per-prop binary scoring
(over/under) plus mean realized probability under the model PMF.

Outputs:
  artifacts/scoring/woo/<date>/woo_scoring_summary.json
  artifacts/scoring/woo/<date>/woo_scoring_summary.md
  artifacts/scoring/woo/<date>/woo_scored_props.csv

Pass / fail:
  WOO_AFTER_GAME_SCORING_PASS    — props_scored > 0
  WOO_AFTER_GAME_SCORING_PENDING — outcomes for the date not present yet
  WOO_AFTER_GAME_SCORING_FAILED  — predictions parquet missing OR scorer
                                    crashed

Hard rules:
  - Never fabricates outcomes.
  - Reads only model output (predictions parquet) and settled stats.
  - No model probabilities are mutated.
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
STATS_PATH = REPO_ROOT / "data" / "player_game_stats.parquet"
OUT_DIR = REPO_ROOT / "artifacts" / "scoring" / "woo"

STAT_TO_COL = {
    "pts": "pts", "reb": "reb", "ast": "ast",
    "fg3m": "fg3m", "stl": "stl", "blk": "blk", "tov": "turnover",
}


def _utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _logloss(p: float, y: float) -> float:
    p = max(min(p, 1 - 1e-9), 1e-9)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args(argv)
    date = args.date

    out_dir = OUT_DIR / date
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "woo_scoring_summary.json"
    md_path = out_dir / "woo_scoring_summary.md"
    csv_path = out_dir / "woo_scored_props.csv"

    pred_parquet = PRED_DIR / f"all_props_{date}.parquet"
    if not pred_parquet.exists():
        payload = {
            "schema_version": "1.0",
            "date": date,
            "generated_at_utc": _utc_iso(),
            "status": "failed",
            "reason": f"missing {pred_parquet.relative_to(REPO_ROOT)}",
            "props_scored": 0,
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        md_path.write_text(
            f"# WoO after-game scoring — {date}\n\n"
            f"- status: **FAILED** (missing predictions parquet)\n",
            encoding="utf-8",
        )
        print(f"WOO_AFTER_GAME_SCORING_FAILED  date={date}  "
              f"reason=missing_predictions_parquet", file=sys.stderr)
        return 1

    if not STATS_PATH.exists():
        print(f"WOO_AFTER_GAME_SCORING_FAILED  date={date}  "
              f"reason=missing_stats_parquet", file=sys.stderr)
        return 1
    stats = pd.read_parquet(STATS_PATH)
    if "game_date" not in stats.columns:
        print(f"WOO_AFTER_GAME_SCORING_FAILED  date={date}  "
              f"reason=stats_missing_game_date", file=sys.stderr)
        return 1
    settled = stats[stats["game_date"].astype(str).str[:10] == date]
    if settled.empty:
        payload = {
            "schema_version": "1.0",
            "date": date,
            "generated_at_utc": _utc_iso(),
            "status": "pending",
            "reason": (f"no rows in player_game_stats.parquet for "
                       f"game_date={date}; outcomes not yet settled"),
            "props_scored": 0,
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        md_path.write_text(
            f"# WoO after-game scoring — {date}\n\n"
            f"- status: **PENDING**\n- reason: outcomes not yet settled\n",
            encoding="utf-8",
        )
        print(f"WOO_AFTER_GAME_SCORING_PENDING  date={date}  "
              f"reason=outcomes_not_yet_settled")
        return 0

    preds = pd.read_parquet(pred_parquet)
    rows: list[dict] = []
    skipped: dict[str, int] = {"unknown_stat": 0, "no_outcome": 0,
                                "no_pmf": 0}
    for _, r in preds.iterrows():
        stat = str(r.get("stat") or "")
        col = STAT_TO_COL.get(stat)
        if not col or col not in settled.columns:
            skipped["unknown_stat"] += 1
            continue
        pid = r.get("player_id")
        if pid is None:
            skipped["no_outcome"] += 1
            continue
        oc = settled[settled["player_id"] == pid]
        if oc.empty:
            skipped["no_outcome"] += 1
            continue
        actual_series = oc[col].dropna()
        if actual_series.empty:
            skipped["no_outcome"] += 1
            continue
        try:
            actual_int = int(round(float(actual_series.iloc[0])))
        except Exception:
            skipped["no_outcome"] += 1
            continue

        # PMF probability of the realized outcome.
        pmf_payload = r.get("pmf")
        p_realized = None
        if isinstance(pmf_payload, str):
            try:
                d = json.loads(pmf_payload)
                p_realized = float(d.get(str(actual_int), 0.0))
            except Exception:
                p_realized = None
        elif isinstance(pmf_payload, dict):
            try:
                p_realized = float(pmf_payload.get(str(actual_int), 0.0))
            except Exception:
                p_realized = None
        if p_realized is None:
            skipped["no_pmf"] += 1
            continue

        # Over/under outcome relative to the line.
        line = r.get("line")
        side = str(r.get("side", "")).upper()
        side_correct = None
        try:
            line_f = float(line)
            over_realized = (1.0 if actual_int > line_f
                              else (0.5 if actual_int == line_f else 0.0))
        except Exception:
            line_f = None
            over_realized = None

        model_prob_cal = r.get("model_prob_cal")
        if model_prob_cal is None or pd.isna(model_prob_cal):
            model_prob_cal = r.get("model_prob")
        try:
            model_prob_cal = float(model_prob_cal)
        except Exception:
            model_prob_cal = None
        market_prob = r.get("market_prob")
        try:
            market_prob = float(market_prob)
        except Exception:
            market_prob = None

        side_indicator = (over_realized
                          if side == "OVER"
                          else (1.0 - over_realized if over_realized is not None
                                and side == "UNDER" else None))
        model_brier = ((side_indicator - model_prob_cal) ** 2
                       if side_indicator is not None and model_prob_cal is not None
                       else None)
        market_brier = ((side_indicator - market_prob) ** 2
                        if side_indicator is not None and market_prob is not None
                        else None)
        model_logloss = (_logloss(model_prob_cal, side_indicator)
                         if side_indicator is not None and model_prob_cal is not None
                         else None)
        market_logloss = (_logloss(market_prob, side_indicator)
                          if side_indicator is not None and market_prob is not None
                          else None)

        rows.append({
            "player_id": int(pid) if pd.notna(pid) else None,
            "player_name": r.get("player_name"),
            "game_id": int(r["game_id"]) if pd.notna(r.get("game_id")) else None,
            "stat": stat,
            "side": side,
            "line": line_f,
            "actual": actual_int,
            "p_realized": p_realized,
            "model_prob_side": model_prob_cal,
            "market_prob_side": market_prob,
            "model_brier": model_brier,
            "market_brier": market_brier,
            "model_logloss": model_logloss,
            "market_logloss": market_logloss,
        })

    if not rows:
        payload = {
            "schema_version": "1.0",
            "date": date,
            "generated_at_utc": _utc_iso(),
            "status": "failed",
            "reason": (f"predictions parquet had {len(preds)} rows but "
                       "0 joined to settled outcomes — investigate id "
                       "or schema mismatch"),
            "props_scored": 0,
            "skipped": skipped,
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        md_path.write_text(
            f"# WoO after-game scoring — {date}\n\n"
            f"- status: **FAILED** (zero joined props)\n"
            f"- skipped: {skipped}\n",
            encoding="utf-8",
        )
        print(f"WOO_AFTER_GAME_SCORING_FAILED  date={date}  "
              f"reason=zero_joined  skipped={skipped}", file=sys.stderr)
        return 1

    sdf = pd.DataFrame(rows)
    sdf.to_csv(csv_path, index=False)

    summary = {
        "schema_version": "1.0",
        "date": date,
        "generated_at_utc": _utc_iso(),
        "status": "scored",
        "props_scored": int(len(sdf)),
        "skipped": skipped,
        "mean_p_realized": float(sdf["p_realized"].mean()),
        "median_p_realized": float(sdf["p_realized"].median()),
        "mean_nll": float(
            sdf["p_realized"].clip(lower=1e-9).apply(lambda x: -math.log(x)).mean()
        ),
        "model_brier_mean": float(sdf["model_brier"].dropna().mean())
            if sdf["model_brier"].notna().any() else None,
        "market_brier_mean": float(sdf["market_brier"].dropna().mean())
            if sdf["market_brier"].notna().any() else None,
        "model_logloss_mean": float(sdf["model_logloss"].dropna().mean())
            if sdf["model_logloss"].notna().any() else None,
        "market_logloss_mean": float(sdf["market_logloss"].dropna().mean())
            if sdf["market_logloss"].notna().any() else None,
        "outputs": {
            "summary_json": str(json_path.relative_to(REPO_ROOT)),
            "summary_md": str(md_path.relative_to(REPO_ROOT)),
            "scored_props_csv": str(csv_path.relative_to(REPO_ROOT)),
        },
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_lines = [
        f"# WoO after-game scoring — {date}",
        "",
        f"- status: **scored**",
        f"- props_scored: **{summary['props_scored']}**",
        f"- mean P(realized): {summary['mean_p_realized']:.4f}",
        f"- median P(realized): {summary['median_p_realized']:.4f}",
        f"- mean NLL: {summary['mean_nll']:.4f}",
    ]
    if summary["model_brier_mean"] is not None:
        md_lines.append(
            f"- model Brier (over/under): {summary['model_brier_mean']:.4f} "
            f"vs market: {summary['market_brier_mean']:.4f}"
        )
    if summary["model_logloss_mean"] is not None:
        md_lines.append(
            f"- model logloss (over/under): {summary['model_logloss_mean']:.4f} "
            f"vs market: {summary['market_logloss_mean']:.4f}"
        )
    md_lines.append("")
    md_lines.append(f"- skipped: `{skipped}`")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"WOO_AFTER_GAME_SCORING_PASS  date={date}  "
          f"props_scored={summary['props_scored']}  "
          f"mean_nll={summary['mean_nll']:.4f}  "
          f"summary={json_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
