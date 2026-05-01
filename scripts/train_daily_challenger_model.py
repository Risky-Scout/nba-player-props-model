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


def _train_full_candidate(as_of_date: str, out_dir: Path) -> dict:
    """Phase 13D: real challenger training via scripts/calibrate_pmf.py
    aggregate-mode.

    In this codebase, "daily training" = role-aware PMF calibration via
    ``pmf_calibration.fit_all`` against the rolling OOF universe at
    ``data/oof_pmfs.parquet``. The heavy per-fold partial-refit (minutes /
    rate / hurdle / fg3m per fold) belongs to the periodic full refresh
    (``phase8.yml`` workflow), not to the nightly path: a single fold's
    worth of fresh OOF (~28 days, ~4k rows/stat) is too narrow for
    ``fit_all``'s internal walk-forward (which requires the OOF span to
    exceed ``min_train_days`` = 365 days).

    Daily challenger pattern:
      1. Snapshot ``data/training_table.parquet`` and ``data/oof_pmfs.parquet``
         to the challenger dir (the production baselines are never modified).
      2. Apply the ``--as-of-date`` cutoff inside calibrate_pmf so any OOF
         rows newer than ``as_of_date`` are filtered out — leakage-safe.
      3. Run ``calibrate_pmf.py --aggregate-mode`` against the snapshot,
         with ``--output-dir`` pointing at the challenger dir. fit_all
         consumes the rolling OOF and produces fresh ``pmf_cal_role_*.pkl``
         + ``pmf_cal_meta.json`` in the challenger dir. Per-fold refit is
         skipped — runtime is ~30-60s.
      4. Hash all scoped artifacts and record paths in ``train_manifest.json``.

    The full per-fold refresh path remains available via the existing
    ``phase8.yml`` workflow and via ``calibrate_pmf.py`` without
    ``--aggregate-mode``; it is invoked manually on a periodic cadence.

    Returns a dict shaped for ``train_manifest.json`` consumption.
    """
    import shutil
    import subprocess
    import time

    started_at = utcnow_iso()
    pointer = load_champion_pointer()

    # 1a. Snapshot training_table.parquet (kept for traceability even though
    #     aggregate-mode does not re-read it). Phase 13F: this file is
    #     gitignored and may legitimately be absent on a fresh GitHub
    #     runner. Aggregate-mode does not consume it, so we treat missing
    #     as advisory and continue.
    src_table = REPO_ROOT / "data" / "training_table.parquet"
    train_subdir = out_dir / "training"
    train_subdir.mkdir(parents=True, exist_ok=True)
    scoped_table: Path | None = None
    scoped_table_hash: str | None = None
    if src_table.exists():
        scoped_table = train_subdir / "training_table.parquet"
        if not scoped_table.exists():
            shutil.copy2(src_table, scoped_table)
        scoped_table_hash = sha256_file(scoped_table)

    # 1b. Locate the scoped OOF aggregate parquet. Phase 13F: the
    #     orchestrator runs ``scripts/prepare_training_inputs.py`` first,
    #     which writes the leakage-safe filtered OOF to
    #     <ch_dir>/aggregate_input/fold_aggregate.parquet. If that file is
    #     already present we use it directly (no re-filter); otherwise we
    #     fall back to creating it inline for backwards compatibility with
    #     standalone trainer invocations.
    aggregate_dir = out_dir / "aggregate_input"
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    fold_aggregate_path = aggregate_dir / "fold_aggregate.parquet"
    pre_rows = 0
    future_rows_excluded = 0
    if not fold_aggregate_path.exists():
        src_oof = REPO_ROOT / "data" / "oof_pmfs.parquet"
        if not src_oof.exists():
            raise FileNotFoundError(
                f"data/oof_pmfs.parquet missing at {src_oof}. The rolling OOF "
                "universe is required for daily challenger calibration. The "
                "preflight step (scripts/check_training_inputs.py) should have "
                "caught this — re-run with prepare_training_inputs.py invoked "
                "first, or restore the file from a phase8.yml run."
            )
        try:
            import pandas as pd
            oof_df = pd.read_parquet(src_oof)
            cutoff = pd.Timestamp(as_of_date)
            pre_rows = len(oof_df)
            oof_df["game_date"] = pd.to_datetime(oof_df["game_date"])
            future_rows_excluded = int((oof_df["game_date"] > cutoff).sum())
            oof_filtered = oof_df[oof_df["game_date"] <= cutoff].reset_index(drop=True)
            oof_filtered.to_parquet(fold_aggregate_path, index=False)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to snapshot/filter data/oof_pmfs.parquet: {exc}"
            ) from exc
    else:
        # Pull pre/post counts from the prepared file for the manifest.
        try:
            import pandas as pd
            df_check = pd.read_parquet(fold_aggregate_path, columns=["game_date"])
            pre_rows = int(len(df_check))
            future_rows_excluded = 0  # prepare_training_inputs already filtered
        except Exception:
            pass
    fold_aggregate_hash = sha256_file(fold_aggregate_path)

    # 2-3. Invoke calibrate_pmf.py in aggregate-mode. Output redirects to
    #      out_dir; production paths are untouched.
    log_path = out_dir / "calibrate_pmf.log"
    cmd = [
        "python3",
        "scripts/calibrate_pmf.py",
        "--core-props-only",
        "--aggregate-mode",
        "--aggregate-oofs",
        str(aggregate_dir.resolve()),
        "--output-dir",
        str(out_dir.resolve()),
    ]
    t0 = time.perf_counter()
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"$ {' '.join(cmd)}\n\n")
        f.flush()
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            stdout=f,
            stderr=subprocess.STDOUT,
            check=False,
        )
    elapsed_s = time.perf_counter() - t0

    if proc.returncode != 0:
        raise RuntimeError(
            f"calibrate_pmf.py exited {proc.returncode} after {elapsed_s:.1f}s. "
            f"See log: {log_path.relative_to(REPO_ROOT)}"
        )

    # 4. Inventory the produced challenger artifacts and record hashes.
    pickles = sorted(out_dir.glob("*.pkl"))
    pickle_records = [
        {"path": str(p.relative_to(REPO_ROOT)), "sha256": sha256_file(p)}
        for p in pickles
    ]
    oof_path = out_dir / "oof_pmfs.parquet"
    cal_meta_path = out_dir / "pmf_cal_meta.json"

    summary = _summarize_training_window(parse_date(as_of_date))
    summary["model_version"] = f"challenger-{as_of_date}"
    summary["calibrate_pmf_elapsed_seconds"] = round(elapsed_s, 1)
    # Phase 13F: when prepare_training_inputs already filtered the OOF, we
    # report the filtered row count from the file itself; the source
    # pre-cutoff count and excluded-future count are recorded in the
    # nightly run dir's training_inputs_manifest.json.
    try:
        import pandas as _pd
        rows_after_cutoff = int(len(_pd.read_parquet(fold_aggregate_path, columns=["game_date"])))
    except Exception:
        rows_after_cutoff = 0
    summary["aggregate_oof_rows_after_cutoff"] = rows_after_cutoff
    summary["aggregate_oof_rows_pre_cutoff"] = int(pre_rows) if pre_rows else None
    summary["aggregate_oof_future_rows_excluded"] = (
        int(future_rows_excluded) if future_rows_excluded else None
    )

    artifacts = {
        "challenger_kind": "real-aggregate-mode-from-rolling-oof",
        "model_dir_reference": str(out_dir.relative_to(REPO_ROOT)),
        "training_table_snapshot": (
            str(scoped_table.relative_to(REPO_ROOT)) if scoped_table is not None else None
        ),
        "training_table_sha256": scoped_table_hash,
        "fold_aggregate_input": str(fold_aggregate_path.relative_to(REPO_ROOT)),
        "fold_aggregate_sha256": fold_aggregate_hash,
        "calibrate_pmf_cmd": cmd,
        "calibrate_pmf_log": str(log_path.relative_to(REPO_ROOT)),
        "calibrate_pmf_elapsed_seconds": round(elapsed_s, 1),
        "files": pickle_records,
        "oof_pmfs_parquet": (
            str(oof_path.relative_to(REPO_ROOT)) if oof_path.exists() else None
        ),
        "pmf_cal_meta_json": (
            str(cal_meta_path.relative_to(REPO_ROOT)) if cal_meta_path.exists() else None
        ),
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
