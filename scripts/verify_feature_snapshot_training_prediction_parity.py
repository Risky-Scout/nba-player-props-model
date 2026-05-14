#!/usr/bin/env python3
"""Verify feature parity between training, prediction, diagnostics, and delivery."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REQUIRED_DIAGNOSTIC_COLUMNS = [
    "injury_status_current",
    "official_lineup_status",
    "expected_lineup_status",
    "projected_minutes",
    "minutes_q10",
    "minutes_q50",
    "minutes_q90",
    "p_starter",
    "p_inactive",
    "usage_projection",
    "opponent_def_rating_recent",
    "expected_steal_opportunities",
    "cov_pts_reb_player",
]


def _cols(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return set(map(str, pd.read_parquet(path).columns))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--training-table", required=True)
    ap.add_argument("--prediction-features", required=True)
    ap.add_argument("--event-market-rows", required=False, default=None)
    ap.add_argument("--derek-feed", required=False, default=None)
    ap.add_argument("--out-dir", default="artifacts/model_diagnostics/feature_parity")
    args = ap.parse_args()

    tcols = _cols(Path(args.training_table))
    pcols = _cols(Path(args.prediction_features))
    ecols = _cols(Path(args.event_market_rows)) if args.event_market_rows else set()
    dcols = _cols(Path(args.derek_feed)) if args.derek_feed else set()

    common = sorted(tcols.intersection(pcols))
    missing_training = sorted(pcols - tcols)
    missing_prediction = sorted(tcols - pcols)
    diag_missing = sorted([c for c in REQUIRED_DIAGNOSTIC_COLUMNS if c not in ecols]) if ecols else []
    derek_missing = sorted([c for c in REQUIRED_DIAGNOSTIC_COLUMNS if c not in dcols]) if dcols else []
    no_leakage_cols = sorted([c for c in tcols if c.startswith("market_") or c in {"no_vig_market_prob_over", "market_prob_over"}])

    summary = {
        "training_columns": len(tcols),
        "prediction_columns": len(pcols),
        "common_columns": len(common),
        "missing_in_training": missing_training[:200],
        "missing_in_prediction": missing_prediction[:200],
        "event_market_missing_diagnostics": diag_missing,
        "derek_feed_missing_diagnostics": derek_missing,
        "market_like_columns_in_training": no_leakage_cols,
    }
    summary["pass"] = (
        len(missing_training) == 0
        and len(diag_missing) == 0
        and len(no_leakage_cols) == 0
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        "FEATURE_SNAPSHOT_TRAINING_PREDICTION_PARITY_PASS"
        if summary["pass"]
        else "FEATURE_SNAPSHOT_TRAINING_PREDICTION_PARITY_FAIL"
    )
    return 0 if summary["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
