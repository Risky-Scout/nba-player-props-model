"""Phase 13F — prepare scoped, leakage-safe training inputs for nightly runs.

Snapshots the rolling OOF parquet (and, when present, the training table)
into the challenger directory, applies the as-of-date cutoff, and clears any
stale per-challenger state from a previous run so the orchestrator starts
from a known-clean baseline.

Usage:
    python3 scripts/prepare_training_inputs.py --as-of-date YYYY-MM-DD

Outputs:
    artifacts/models/challengers/<date>/training/training_table.parquet  (if available)
    artifacts/models/challengers/<date>/aggregate_input/fold_aggregate.parquet
    artifacts/nightly_training/<date>/training_inputs_manifest.json

Hard rules:
- Filters every loaded dataframe to ``game_date <= as_of_date`` — no future
  leakage.
- Never overwrites the production-side ``data/oof_pmfs.parquet`` or
  ``data/training_table.parquet``.
- Never commits its outputs (they live under gitignored
  ``artifacts/models/challengers/**/*.parquet`` patterns).
- Cleans stale ``calibration_manifest.json`` / ``train_manifest.json`` /
  ``model_manifest.json`` / ``validation_report.json`` /
  ``promotion_decision.json`` from any previous (potentially mixed-mode)
  run on the same date so the verifier sees a coherent state.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    challenger_dir,
    git_commit,
    nightly_run_dir,
    parse_date,
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)


# Filenames considered stale per-challenger state. These get deleted at the
# start of a run so the orchestrator/verifier never see a mix of fresh and
# stale manifests on the same date.
STALE_FILES = (
    "train_manifest.json",
    "model_manifest.json",
    "calibration_manifest.json",
    "validation_report.json",
    "validation_summary.md",
    "promotion_decision.json",
    "promotion_manifest.json",
    "pmf_cal_meta.json",
    "pmf_calibration_run.md",
    "calibrate_pmf.log",
    "oof_pmfs.parquet",
)


def _clean_stale_state(ch_dir: Path) -> list[str]:
    cleaned: list[str] = []
    if not ch_dir.exists():
        return cleaned
    for name in STALE_FILES:
        p = ch_dir / name
        if p.exists():
            try:
                p.unlink()
                cleaned.append(name)
            except Exception:
                pass
    # Remove any old pmf_cal_role_*.pkl from a prior run.
    for p in ch_dir.glob("pmf_cal_role_*.pkl"):
        try:
            p.unlink()
            cleaned.append(p.name)
        except Exception:
            pass
    # Aggregate input subdir is regenerated from scratch.
    agg_dir = ch_dir / "aggregate_input"
    if agg_dir.exists():
        shutil.rmtree(agg_dir, ignore_errors=True)
        cleaned.append("aggregate_input/")
    return cleaned


def prepare(as_of: dt.date) -> dict:
    ch_dir = challenger_dir(as_of.isoformat())
    ch_dir.mkdir(parents=True, exist_ok=True)
    train_subdir = ch_dir / "training"
    train_subdir.mkdir(parents=True, exist_ok=True)
    aggregate_dir = ch_dir / "aggregate_input"
    aggregate_dir.mkdir(parents=True, exist_ok=True)

    cleaned = _clean_stale_state(ch_dir)
    # _clean_stale_state removed aggregate_input — recreate it.
    aggregate_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "schema_version": "1.0",
        "as_of_date": as_of.isoformat(),
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "stale_state_cleaned": cleaned,
        "inputs": {},
        "errors": [],
    }

    try:
        import pandas as pd
    except ImportError:
        manifest["errors"].append("pandas not installed")
        return manifest
    cutoff = pd.Timestamp(as_of)

    # Required: rolling OOF parquet.
    src_oof = REPO_ROOT / "data" / "oof_pmfs.parquet"
    if not src_oof.exists():
        manifest["errors"].append(
            f"data/oof_pmfs.parquet missing — required for daily challenger calibration. "
            "The rolling OOF universe is produced by phase8.yml; restore it before re-running."
        )
    else:
        try:
            oof_df = pd.read_parquet(src_oof)
            pre_rows = len(oof_df)
            oof_df["game_date"] = pd.to_datetime(oof_df["game_date"])
            future_rows = int((oof_df["game_date"] > cutoff).sum())
            oof_filtered = oof_df[oof_df["game_date"] <= cutoff].reset_index(drop=True)
            scoped_oof = aggregate_dir / "fold_aggregate.parquet"
            oof_filtered.to_parquet(scoped_oof, index=False)
            manifest["inputs"]["fold_aggregate.parquet"] = {
                "source": str(src_oof.relative_to(REPO_ROOT)),
                "scoped_path": str(scoped_oof.relative_to(REPO_ROOT)),
                "source_sha256_prefix": (
                    sha256_file(src_oof)[:16] if src_oof.stat().st_size < 200 * 1024 * 1024 else None
                ),
                "scoped_sha256_prefix": sha256_file(scoped_oof)[:16],
                "rows_pre_cutoff": int(pre_rows),
                "rows_after_cutoff": int(len(oof_filtered)),
                "future_rows_excluded": future_rows,
            }
        except Exception as exc:
            manifest["errors"].append(f"failed snapshotting OOF: {exc}")

    # Advisory: training_table.parquet (gitignored locally, never available
    # on a fresh GitHub runner). The aggregate-mode path does NOT consume it,
    # so absence is fine — we just record the state.
    src_table = REPO_ROOT / "data" / "training_table.parquet"
    if src_table.exists():
        try:
            scoped_table = train_subdir / "training_table.parquet"
            shutil.copy2(src_table, scoped_table)
            manifest["inputs"]["training_table.parquet"] = {
                "source": str(src_table.relative_to(REPO_ROOT)),
                "scoped_path": str(scoped_table.relative_to(REPO_ROOT)),
                "source_sha256_prefix": (
                    sha256_file(src_table)[:16] if src_table.stat().st_size < 600 * 1024 * 1024 else None
                ),
                "size_bytes": scoped_table.stat().st_size,
                "advisory_only": True,
                "consumed_by_aggregate_mode": False,
            }
        except Exception as exc:
            manifest["errors"].append(f"failed copying training_table: {exc}")
    else:
        manifest["inputs"]["training_table.parquet"] = {
            "source": "data/training_table.parquet",
            "present": False,
            "advisory_only": True,
            "consumed_by_aggregate_mode": False,
            "note": (
                "Not required for the daily aggregate-mode challenger path; "
                "is required for the periodic per-fold refresh in phase8.yml."
            ),
        }

    # Required: champion calibrators. We do NOT copy them — the validator
    # reads them straight from artifacts/models/. Just record presence.
    champion_dir = REPO_ROOT / "artifacts" / "models"
    champion_calibrators: dict[str, dict] = {}
    for stat in ("pts", "reb", "ast", "fg3m", "tov"):
        p = champion_dir / f"pmf_cal_role_{stat}.pkl"
        if p.exists():
            champion_calibrators[stat] = {
                "path": str(p.relative_to(REPO_ROOT)),
                "size_bytes": p.stat().st_size,
                "sha256_prefix": sha256_file(p)[:16],
            }
        else:
            champion_calibrators[stat] = {"path": str(p.relative_to(REPO_ROOT)), "present": False}
            manifest["errors"].append(f"champion calibrator missing: {p.relative_to(REPO_ROOT)}")
    manifest["champion_calibrators"] = champion_calibrators

    return manifest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Prepare scoped training inputs.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    args = p.parse_args(argv)

    as_of = parse_date(args.as_of_date)
    out_dir = nightly_run_dir(as_of.isoformat())
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = prepare(as_of)
    write_json_atomic(out_dir / "training_inputs_manifest.json", manifest)

    if manifest["errors"]:
        print(
            json.dumps(
                {
                    "as_of_date": args.as_of_date,
                    "errors": manifest["errors"],
                }
            ),
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "as_of_date": args.as_of_date,
                "stale_state_cleaned": manifest["stale_state_cleaned"],
                "inputs_present": list(manifest["inputs"].keys()),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
