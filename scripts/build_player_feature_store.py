#!/usr/bin/env python3
"""Build a minimal leakage-safe player-game feature slice from stat_grid (M8.6 D).

Excludes market odds/lines and PMF outputs from the feature matrix.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.feature_registry import (  # noqa: E402
    FEATURE_REGISTRY_VERSION,
    FEATURE_STORE_CLOSE_LOCK_COLUMNS,
)


DROP_LEAKAGE = (
    "line",
    "odds",
    "pmf",
    "pmf_summary_mean",
    "pmf_summary_median",
    "pmf_summary_mode",
    "support_max",
    "pmf_sum_error",
    "model_version",
    "calibrated",
    "source_recalibration_applied",
    "source_recalibration_version",
    "source_recalibration_stage",
    "source_recalibration_role_bucket",
    "side",
    "line_is_real",
    "scored_at_utc",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--snapshot", default="close_lock")
    args = ap.parse_args()

    sg = REPO_ROOT / "predictions" / f"stat_grid_{args.date}.parquet"
    if not sg.exists():
        print(f"FATAL: missing {sg}", file=sys.stderr)
        return 2

    df = pd.read_parquet(sg)
    for c in DROP_LEAKAGE:
        if c in df.columns:
            df = df.drop(columns=[c])

    df["feature_store_version"] = FEATURE_REGISTRY_VERSION
    df["snapshot"] = args.snapshot
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    df["game_context_as_of_utc"] = now

    out_dir = REPO_ROOT / "data" / "features"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"player_game_features_{args.date}_{args.snapshot}.parquet"
    out_path = out_dir / stem
    df.to_parquet(out_path, index=False)

    manifest = {
        "date": args.date,
        "snapshot": args.snapshot,
        "source_stat_grid": str(sg.relative_to(REPO_ROOT)),
        "output": str(out_path.relative_to(REPO_ROOT)),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "feature_registry_version": FEATURE_REGISTRY_VERSION,
        "excluded_columns": list(DROP_LEAKAGE),
        "contract_note": (
            "PMF columns and market line/odds intentionally excluded from feature store."
        ),
        "generated_at_utc": now,
    }
    man_path = out_dir / f"player_game_features_{args.date}_{args.snapshot}.manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"FEATURE_STORE_BUILD_PASS wrote {out_path} rows={len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
