#!/usr/bin/env python3
"""Thin wrapper: full training table is built by scripts/train.py (BDL + odds fetch).

Date bounds are recorded for provenance; the upstream builder currently emits
the full universe (no row filter in train.py). Use --dry-run to validate keys
and show the command without executing.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FAIL_JSON = REPO_ROOT / "artifacts" / "model_diagnostics" / "training_table_build_failure.json"


def _write_fail(payload: dict) -> None:
    FAIL_JSON.parent.mkdir(parents=True, exist_ok=True)
    FAIL_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("TRAINING_TABLE_BUILD_FAIL", file=sys.stderr)
    print(f"Wrote {FAIL_JSON}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", required=True)
    ap.add_argument("--end-date", required=True)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "training_table.parquet")
    ap.add_argument(
        "--feature-snapshot",
        type=Path,
        default=None,
        help="Optional as-of feature snapshot parquet to validate parity metadata against.",
    )
    ap.add_argument("--force", action="store_true", help="Overwrite --out if it exists.")
    ap.add_argument("--dry-run", action="store_true", help="Print plan only.")
    args = ap.parse_args()

    if not os.environ.get("BDL_API_KEY"):
        _write_fail(
            {
                "code": "TRAINING_TABLE_BUILD_FAIL",
                "missing_inputs": ["BDL_API_KEY environment variable"],
                "searched_paths": [],
                "required_source_tables": [
                    "data/player_game_stats.parquet (fetched)",
                    "data/player_game_adv.parquet (fetched)",
                    "data/odds_api/odds.parquet or equivalent (fetched)",
                ],
                "suggested_recovery_commands": [
                    "export BDL_API_KEY=...",
                    "python scripts/train.py --build-table-only",
                ],
                "can_use_github_artifact": True,
                "workflow_artifact_name": "training-table",
                "note": "Full rebuild uses nba_props_model.pipelines.train.fetch_all_data + build_training_table.",
            }
        )
        return 2

    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "train.py"), "--build-table-only"]
    built_path = REPO_ROOT / "data" / "training_table.parquet"
    manifest = {
        "start_date": args.start_date,
        "end_date": args.end_date,
        "train_cli": cmd,
        "default_output": str(built_path),
        "requested_output": str(args.out),
        "note": "train.py always writes data/training_table.parquet; use cp if --out differs.",
        "feature_snapshot": str(args.feature_snapshot) if args.feature_snapshot else None,
    }
    if args.dry_run:
        print(json.dumps(manifest, indent=2))
        print("DRY_RUN: would run:", " ".join(cmd))
        return 0

    if args.out.exists() and not args.force:
        print(f"Refusing to overwrite {args.out} (pass --force)", file=sys.stderr)
        return 1

    rc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if rc.returncode != 0:
        _write_fail(
            {
                "code": "TRAINING_TABLE_BUILD_FAIL",
                "missing_inputs": ["train.py returned non-zero"],
                "searched_paths": [str(built_path)],
                "required_source_tables": manifest["required_source_tables"],
                "suggested_recovery_commands": ["python scripts/train.py --build-table-only"],
                "can_use_github_artifact": True,
                "workflow_artifact_name": "training-table",
                "subprocess_returncode": rc.returncode,
            }
        )
        return 2

    if not built_path.is_file():
        _write_fail(
            {
                "code": "TRAINING_TABLE_BUILD_FAIL",
                "missing_inputs": [str(built_path)],
                "searched_paths": [str(built_path)],
                "required_source_tables": manifest["required_source_tables"],
                "suggested_recovery_commands": ["Inspect train logs for fetch_all_data failure"],
                "can_use_github_artifact": True,
                "workflow_artifact_name": "training-table",
            }
        )
        return 2

    if args.out.resolve() != built_path.resolve():
        import shutil

        args.out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built_path, args.out)

    meta_side = REPO_ROOT / "artifacts" / "model_diagnostics" / "training_table_build_manifest.json"
    if args.feature_snapshot:
        fs = args.feature_snapshot if args.feature_snapshot.is_absolute() else REPO_ROOT / args.feature_snapshot
        manifest["feature_snapshot_exists"] = fs.is_file()
        if fs.is_file():
            try:
                import pandas as pd

                tdf = pd.read_parquet(args.out)
                sdf = pd.read_parquet(fs)
                manifest["feature_snapshot_training_overlap_columns"] = sorted(
                    set(map(str, tdf.columns)).intersection(set(map(str, sdf.columns)))
                )[:200]
            except Exception as exc:
                manifest["feature_snapshot_parity_read_error"] = str(exc)
    meta_side.parent.mkdir(parents=True, exist_ok=True)
    meta_side.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"TRAINING_TABLE_BUILD_OK -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
