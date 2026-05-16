#!/usr/bin/env python3
"""Build as-of-safe player-prop feature snapshot parquet."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.asof_feature_store import (  # noqa: E402
    MissingSourceInputsError,
    assert_availability_confidence_is_numeric,
    build_feature_snapshot,
)
from nba_props_model.features.player_prop_feature_contract import RunMode  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--run-mode", required=True, choices=[m.value for m in RunMode])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    run_mode = RunMode(args.run_mode)
    out_path = Path(args.out) if args.out else REPO_ROOT / "data" / "features" / f"player_prop_features_{args.date}_{run_mode.value}.parquet"
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = build_feature_snapshot(REPO_ROOT, args.date, run_mode)
    except MissingSourceInputsError as exc:
        print(str(exc))
        return 2

    try:
        assert_availability_confidence_is_numeric(result.snapshot)
    except RuntimeError as exc:
        print(str(exc))
        return 3

    result.snapshot.to_parquet(out_path, index=False)
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(result.metadata, indent=2) + "\n", encoding="utf-8")
    print("PLAYER_PROP_FEATURE_SNAPSHOT_PASS")
    print(f"  rows={result.metadata['n_rows']}")
    print(f"  out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
