#!/usr/bin/env python3
"""Build M8.9 injury/lineup feature frame for one date/run mode."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.injury_lineup_features import build_injury_lineup_features  # noqa: E402
from nba_props_model.features.player_prop_feature_contract import RunMode  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--run-mode", required=True, choices=[m.value for m in RunMode])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    run_mode = RunMode(args.run_mode)
    out_path = (
        Path(args.out)
        if args.out
        else REPO_ROOT / "data" / "features" / f"injury_lineup_features_{args.date}_{run_mode.value}.parquet"
    )
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    result = build_injury_lineup_features(REPO_ROOT, args.date, run_mode)
    result.frame.to_parquet(out_path, index=False)

    diag_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"injury_lineup_features_{args.date}_{run_mode.value}"
    diag_dir.mkdir(parents=True, exist_ok=True)
    (diag_dir / "summary.json").write_text(json.dumps(result.summary, indent=2) + "\n", encoding="utf-8")
    result.stale_sources.to_csv(diag_dir / "stale_sources.csv", index=False)
    result.missing_sources.to_csv(diag_dir / "missing_sources.csv", index=False)

    print("INJURY_LINEUP_FEATURES_PASS")
    print(f"  rows={len(result.frame)}")
    print(f"  out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
