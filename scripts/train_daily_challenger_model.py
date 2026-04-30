"""Phase 13A — daily challenger PMF model training.

Produces a candidate ("challenger") model under
``artifacts/models/challengers/<as_of_date>/``. Never alters the champion;
never updates ``champion_pointer.json``.

Default ``--dry-run`` mode (Phase 13A bootstrap):
    The challenger is registered as a *snapshot reference* of the current
    champion. Manifests record dry_run=true and refer to the champion's
    pickles by relative path. Validation will then naturally see "no change"
    and decline to promote — which is the safe behavior we want until full
    candidate training is enabled.

Full mode (future): plug a real trainer into ``_train_full_candidate``.

Usage:
    python3 scripts/train_daily_challenger_model.py --as-of-date YYYY-MM-DD
    python3 scripts/train_daily_challenger_model.py --as-of-date YYYY-MM-DD --dry-run

Hard rules:
- Excludes any data with date > as_of_date (no future leakage).
- Never market-anchors model-only PMFs.
- Never references Phase 10D / 10D.2 overlays.
- Writes only under artifacts/models/challengers/<date>/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_MODELS_DIR,
    SUPPORTED_STATS,
    challenger_dir,
    git_commit,
    load_champion_pointer,
    parse_date,
    read_json,
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)

DATA_DIR = REPO_ROOT / "data"
PLAYER_GAME_STATS_PARQUET = DATA_DIR / "player_game_stats.parquet"


def _detect_date_column(df) -> str | None:
    for c in ("game_date", "date", "GAME_DATE", "Date"):
        if c in df.columns:
            return c
    return None


def _summarize_training_window(as_of: dt.date) -> dict:
    """Return summary stats of training rows through ``as_of`` without leakage."""
    summary: dict = {
        "min_date": None,
        "max_date": None,
        "training_row_count": 0,
        "future_rows_excluded": 0,
        "stats_with_columns": [],
    }
    try:
        import pandas as pd
    except ImportError:
        summary["error"] = "pandas not installed"
        return summary
    if not PLAYER_GAME_STATS_PARQUET.exists():
        summary["error"] = "player_game_stats.parquet missing"
        return summary
    df = pd.read_parquet(PLAYER_GAME_STATS_PARQUET)
    date_col = _detect_date_column(df)
    if date_col is None:
        summary["error"] = "no date column"
        return summary
    ds = pd.to_datetime(df[date_col]).dt.date
    train_mask = ds <= as_of
    train = df[train_mask]
    cols_lower = {c.lower(): c for c in df.columns}
    stats_present: list[str] = []
    for s in SUPPORTED_STATS:
        if s in df.columns or s.lower() in cols_lower:
            stats_present.append(s)
    summary["training_row_count"] = int(train_mask.sum())
    summary["future_rows_excluded"] = int((~train_mask).sum())
    if not train.empty:
        summary["min_date"] = str(ds[train_mask].min())
        summary["max_date"] = str(ds[train_mask].max())
    summary["stats_with_columns"] = stats_present
    return summary


def _hash_champion_artifacts(model_dir: Path) -> dict[str, str]:
    """Hash the small/critical metadata files so we can prove what we trained against."""
    files = [
        "training_meta.json",
        "calibration_meta.json",
        "pmf_cal_meta.json",
        "calibration_manifest.json",
    ]
    hashes: dict[str, str] = {}
    for name in files:
        p = model_dir / name
        if p.exists():
            hashes[name] = sha256_file(p)
    return hashes


def _train_dry_run(as_of_date: str, out_dir: Path) -> dict:
    """Snapshot the current champion as the dry-run challenger."""
    pointer = load_champion_pointer()
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = _summarize_training_window(parse_date(as_of_date))
    artifacts = {
        "challenger_kind": "dry-run-champion-snapshot",
        "model_dir_reference": pointer.get("model_dir", "artifacts/models"),
        "files": [],
        "hashes": _hash_champion_artifacts(CHAMPION_MODELS_DIR),
    }
    return {
        "summary": summary,
        "artifacts": artifacts,
        "pointer_seen": {
            "model_version": pointer.get("model_version"),
            "calibrator_version": pointer.get("calibrator_version"),
            "code_commit": pointer.get("code_commit"),
        },
    }


def _train_full_candidate(as_of_date: str, out_dir: Path) -> dict:  # pragma: no cover
    """Placeholder for the eventual real training run.

    Wiring point: call into the existing rate-model / hurdle / minutes training
    code via ``src/nba_props_model/...`` once a leakage-safe training driver
    exists. Until then, we explicitly raise to prevent silent fake-training.
    """
    raise NotImplementedError(
        "Full candidate training is not yet wired. Use --dry-run; the full path "
        "will be enabled once a leakage-safe training driver is in place."
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Train a daily PMF challenger model.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="(default) snapshot current champion as the challenger; no retraining.",
    )
    p.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Run real training. NotImplementedError until full driver is wired.",
    )
    args = p.parse_args(argv)

    as_of = parse_date(args.as_of_date)
    out_dir = challenger_dir(args.as_of_date)
    out_dir.mkdir(parents=True, exist_ok=True)

    started_at = utcnow_iso()
    warnings: list[str] = []
    status = "ok"

    try:
        if args.dry_run:
            result = _train_dry_run(args.as_of_date, out_dir)
        else:
            result = _train_full_candidate(args.as_of_date, out_dir)
    except NotImplementedError as exc:
        status = "not_implemented"
        warnings.append(str(exc))
        result = {"summary": {}, "artifacts": {}, "pointer_seen": {}}
    except Exception as exc:  # pragma: no cover
        status = "error"
        warnings.append(f"training failed: {exc}")
        result = {"summary": {}, "artifacts": {}, "pointer_seen": {}}

    finished_at = utcnow_iso()

    # train_manifest.json
    train_manifest = {
        "schema_version": "1.0",
        "as_of_date": args.as_of_date,
        "dry_run": bool(args.dry_run),
        "status": status,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "code_commit": git_commit(),
        "stats_trained": list(SUPPORTED_STATS),
        "training_summary": result.get("summary", {}),
        "challenger_artifacts": result.get("artifacts", {}),
        "pointer_seen": result.get("pointer_seen", {}),
        "warnings": warnings,
        "notes": (
            "Phase 13A: dry-run challenger snapshots the current champion so the "
            "automation pipeline (readiness → train → calibrate → validate → "
            "promote) can be exercised end-to-end without retraining. Full "
            "training will be enabled via --no-dry-run once the leakage-safe "
            "training driver is wired."
        ),
        "phase10d_overlays_in_use": False,
    }
    write_json_atomic(out_dir / "train_manifest.json", train_manifest)

    # model_manifest.json — names the artifacts the challenger consists of.
    model_manifest = {
        "schema_version": "1.0",
        "as_of_date": args.as_of_date,
        "dry_run": bool(args.dry_run),
        "code_commit": git_commit(),
        "model_version": (
            f"challenger-{args.as_of_date}-dryrun"
            if args.dry_run
            else f"challenger-{args.as_of_date}"
        ),
        "calibrator_version": "to-be-fitted",
        "model_dir_reference": result.get("artifacts", {}).get(
            "model_dir_reference", "artifacts/models"
        ),
        "stats": list(SUPPORTED_STATS),
        "warnings": warnings,
    }
    write_json_atomic(out_dir / "model_manifest.json", model_manifest)

    print(
        json.dumps(
            {
                "as_of_date": args.as_of_date,
                "dry_run": bool(args.dry_run),
                "status": status,
                "challenger_dir": str(out_dir.relative_to(REPO_ROOT)),
            },
            indent=2,
        )
    )
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
