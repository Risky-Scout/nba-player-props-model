#!/usr/bin/env python3
"""Phase 13AQ — measure and report playoff vs regular-season calibration drift.

Compares model PMF output against actual outcomes for:
  - Regular season games
  - Playoff games (is_playoff=True)

Outputs:
  reports/playoff_calibration_summary.json
  reports/playoff_calibration_by_stat.csv
  reports/playoff_calibration_by_role.csv

Usage:
    python3 scripts/evaluate_playoff_calibration.py
    python3 scripts/evaluate_playoff_calibration.py --output-dir reports/
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

_PLAYOFF_START = "2026-04-19"  # first playoff game date this season


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", default=str(REPO_ROOT / "reports"))
    ap.add_argument("--min-samples", type=int, default=30,
                    help="Minimum samples required to report a cell")
    args = ap.parse_args(argv)

    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        print("EVALUATE_PLAYOFF_CALIBRATION_SKIP  reason=pandas_not_available")
        return 0

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pgs_path = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not pgs_path.exists():
        print("EVALUATE_PLAYOFF_CALIBRATION_SKIP  reason=player_game_stats_missing")
        return 0

    # Load actuals
    pgs = pd.read_parquet(pgs_path)
    pgs["game_date"] = pd.to_datetime(pgs["game_date"]).dt.date.astype(str)
    pgs["is_playoff"] = pgs["game_date"] >= _PLAYOFF_START

    # Collect PMF predictions from deliveries
    delivery_root = REPO_ROOT / "deliveries"
    rows = []
    for date_dir in sorted(delivery_root.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]")):
        mc_path = date_dir / "wizard_of_odds" / "market_comparison.parquet"
        if not mc_path.exists():
            continue
        try:
            mc = pd.read_parquet(mc_path)
            mc["delivery_date"] = date_dir.name
            mc["is_playoff"] = date_dir.name >= _PLAYOFF_START
            rows.append(mc)
        except Exception:
            continue

    if not rows:
        print("EVALUATE_PLAYOFF_CALIBRATION_SKIP  reason=no_delivery_data")
        return 0

    pred = pd.concat(rows, ignore_index=True)

    # Join actuals: one row per (player_id, game_date, stat)
    stat_col_map = {
        "pts": "pts", "reb": "reb", "ast": "ast",
        "fg3m": "fg3m", "stl": "stl", "blk": "blk",
        "tov": "turnover",
    }

    results = []
    for stat, actual_col in stat_col_map.items():
        if actual_col not in pgs.columns:
            continue
        sub = pred[pred["stat"] == stat].copy()
        if sub.empty:
            continue
        sub = sub.merge(
            pgs[["player_id", "game_date", actual_col, "is_playoff"]].rename(
                columns={actual_col: "actual", "game_date": "delivery_date", "is_playoff": "is_playoff_actual"}
            ),
            on=["player_id", "delivery_date"],
            how="inner",
        )
        sub["hit_over"] = (sub["actual"] > sub["line"]).astype(float)
        sub["model_p_over"] = sub["p_over"]
        sub["brier"] = (sub["model_p_over"] - sub["hit_over"]) ** 2
        sub["stat"] = stat
        results.append(sub[["stat", "role_bucket", "is_playoff_actual",
                              "model_p_over", "hit_over", "brier",
                              "mean", "actual", "line"]].copy())

    if not results:
        print("EVALUATE_PLAYOFF_CALIBRATION_SKIP  reason=no_joined_data")
        return 0

    df = pd.concat(results, ignore_index=True)

    def _metrics(group: "pd.DataFrame") -> dict:
        n = len(group)
        if n < args.min_samples:
            return {"n": n, "status": "insufficient_sample"}
        mean_pred = float(group["model_p_over"].mean())
        observed_rate = float(group["hit_over"].mean())
        brier = float(group["brier"].mean())
        mean_error = float((group["mean"] - group["actual"]).mean())
        return {
            "n": n,
            "mean_predicted_prob": round(mean_pred, 4),
            "observed_hit_rate": round(observed_rate, 4),
            "calibration_error": round(abs(mean_pred - observed_rate), 4),
            "mean_absolute_error_stat": round(abs(mean_error), 3),
            "mean_signed_error_stat": round(mean_error, 3),
            "brier_score": round(brier, 4),
            "bias_direction": "model_too_high" if mean_error > 0.5 else (
                "model_too_low" if mean_error < -0.5 else "within_tolerance"),
            "status": "ok",
        }

    # By stat × playoff/regular
    by_stat_rows = []
    for stat in df["stat"].unique():
        for is_po in [False, True]:
            grp = df[(df["stat"] == stat) & (df["is_playoff_actual"] == is_po)]
            m = _metrics(grp)
            m["stat"] = stat
            m["context"] = "playoff" if is_po else "regular_season"
            by_stat_rows.append(m)

    by_stat_df = pd.DataFrame(by_stat_rows)
    stat_csv = out_dir / "playoff_calibration_by_stat.csv"
    by_stat_df.to_csv(stat_csv, index=False)
    print(f"  wrote {stat_csv.relative_to(REPO_ROOT)}")

    # By role × playoff/regular
    by_role_rows = []
    for role in df["role_bucket"].dropna().unique():
        for is_po in [False, True]:
            grp = df[(df["role_bucket"] == role) & (df["is_playoff_actual"] == is_po)]
            m = _metrics(grp)
            m["role_bucket"] = role
            m["context"] = "playoff" if is_po else "regular_season"
            by_role_rows.append(m)

    by_role_df = pd.DataFrame(by_role_rows)
    role_csv = out_dir / "playoff_calibration_by_role.csv"
    by_role_df.to_csv(role_csv, index=False)
    print(f"  wrote {role_csv.relative_to(REPO_ROOT)}")

    # Summary
    rs_all = df[~df["is_playoff_actual"]]
    po_all = df[df["is_playoff_actual"]]
    summary = {
        "schema_version": "1.0",
        "generated_at_utc": _utc_iso(),
        "playoff_start_date": _PLAYOFF_START,
        "regular_season": _metrics(rs_all),
        "playoff": _metrics(po_all),
        "by_stat": {
            s: {
                "regular_season": _metrics(df[(df["stat"] == s) & (~df["is_playoff_actual"])]),
                "playoff": _metrics(df[(df["stat"] == s) & (df["is_playoff_actual"])]),
            }
            for s in sorted(df["stat"].unique())
        },
        "artifacts": {
            "by_stat_csv": str(stat_csv.relative_to(REPO_ROOT)),
            "by_role_csv": str(role_csv.relative_to(REPO_ROOT)),
        },
    }
    summary_path = out_dir / "playoff_calibration_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"  wrote {summary_path.relative_to(REPO_ROOT)}")

    # Print key findings
    rs_m = summary["regular_season"]
    po_m = summary["playoff"]
    print()
    print("EVALUATE_PLAYOFF_CALIBRATION_PASS")
    print(f"  Regular season: n={rs_m.get('n')}  brier={rs_m.get('brier_score')}  "
          f"mean_err={rs_m.get('mean_signed_error_stat')}")
    print(f"  Playoff:        n={po_m.get('n')}  brier={po_m.get('brier_score')}  "
          f"mean_err={po_m.get('mean_signed_error_stat')}")
    if rs_m.get("mean_signed_error_stat") and po_m.get("mean_signed_error_stat"):
        drift = po_m["mean_signed_error_stat"] - rs_m["mean_signed_error_stat"]
        print(f"  Calibration drift (playoff - regular): {drift:+.3f} "
              f"({'model HIGHER in playoffs' if drift > 0.3 else 'acceptable' if abs(drift) < 0.5 else 'model LOWER in playoffs'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
