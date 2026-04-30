"""Phase 13A — daily challenger PMF calibration.

Calibrates the daily challenger PMFs using walk-forward / rolling validation
only. Writes calibration artifacts under
``artifacts/models/challengers/<as_of_date>/``. Never alters the champion;
never updates ``champion_pointer.json``.

Default ``--dry-run`` mode (Phase 13A bootstrap):
    The challenger inherits the champion's calibrators by reference. We record
    the calibration window we *would have used* (rolling, no future leakage),
    the per-stat sample counts, and a manifest. Validation then sees identical
    calibrators on both sides and naturally declines to promote.

Full mode (future): plug a real calibration driver into ``_calibrate_full``.

Usage:
    python3 scripts/calibrate_daily_challenger_pmfs.py --as-of-date YYYY-MM-DD
    python3 scripts/calibrate_daily_challenger_pmfs.py --as-of-date YYYY-MM-DD \
        --challenger-dir artifacts/models/challengers/YYYY-MM-DD

Hard rules:
- Walk-forward / rolling validation only — no future leakage.
- Never market-anchor model-only PMFs.
- Never use Phase 10D / 10D.2 overlays.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_MODELS_DIR,
    SUPPORTED_STATS,
    challenger_dir,
    git_commit,
    parse_date,
    read_json,
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)

# Walk-forward defaults aligned with existing pmf_cal_meta.json (fold_days=28,
# min_train_days=365). These are reported in the manifest, not used to perform
# any actual recompute in dry-run.
DEFAULT_FOLD_DAYS = 28
DEFAULT_MIN_TRAIN_DAYS = 365
SHRINKAGE_FLOOR = 50  # samples; below this we shrink toward the role-bucket prior


def _calibration_window(as_of: dt.date) -> dict:
    train_end = as_of - dt.timedelta(days=DEFAULT_FOLD_DAYS)
    train_start = train_end - dt.timedelta(days=DEFAULT_MIN_TRAIN_DAYS)
    holdout_start = as_of - dt.timedelta(days=DEFAULT_FOLD_DAYS - 1)
    return {
        "fold_days": DEFAULT_FOLD_DAYS,
        "min_train_days": DEFAULT_MIN_TRAIN_DAYS,
        "training_window_start": train_start.isoformat(),
        "training_window_end": train_end.isoformat(),
        "validation_window_start": holdout_start.isoformat(),
        "validation_window_end": as_of.isoformat(),
        "scheme": "rolling-walk-forward",
    }


def _samples_by_stat_and_role(as_of: dt.date) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    """Count rows in the calibration window, by stat and by role bucket."""
    samples_by_stat: dict[str, int] = {s: 0 for s in SUPPORTED_STATS}
    role_breakdown: dict[str, dict[str, int]] = {s: {} for s in SUPPORTED_STATS}
    parquet = REPO_ROOT / "data" / "player_game_stats.parquet"
    try:
        import pandas as pd
    except ImportError:
        return samples_by_stat, role_breakdown
    if not parquet.exists():
        return samples_by_stat, role_breakdown
    df = pd.read_parquet(parquet)
    date_col = next((c for c in ("game_date", "date", "GAME_DATE", "Date") if c in df.columns), None)
    if date_col is None:
        return samples_by_stat, role_breakdown
    ds = pd.to_datetime(df[date_col]).dt.date
    cal_window = _calibration_window(as_of)
    a = dt.date.fromisoformat(cal_window["training_window_start"])
    b = dt.date.fromisoformat(cal_window["validation_window_end"])
    mask = (ds >= a) & (ds <= b)
    sub = df[mask]
    cols_lower = {c.lower(): c for c in df.columns}
    for s in SUPPORTED_STATS:
        col = s if s in df.columns else cols_lower.get(s.lower())
        if not col:
            continue
        finite = sub[col].notna()
        samples_by_stat[s] = int(finite.sum())
        role_col = (
            "role_bucket"
            if "role_bucket" in df.columns
            else cols_lower.get("role_bucket")
        )
        if role_col and role_col in sub.columns:
            grp = sub.loc[finite].groupby(role_col).size()
            role_breakdown[s] = {str(k): int(v) for k, v in grp.items()}
    return samples_by_stat, role_breakdown


def _calibrate_dry_run(as_of: dt.date, ch_dir: Path) -> dict:
    """Reference the champion's calibrators; no recompute."""
    cal_meta_path = CHAMPION_MODELS_DIR / "pmf_cal_meta.json"
    cal_manifest_path = CHAMPION_MODELS_DIR / "calibration_manifest.json"
    cal_meta_hash = sha256_file(cal_meta_path) if cal_meta_path.exists() else None
    cal_manifest_hash = sha256_file(cal_manifest_path) if cal_manifest_path.exists() else None

    samples_by_stat, role_breakdown = _samples_by_stat_and_role(as_of)
    window = _calibration_window(as_of)

    # Per-stat shrinkage: where samples < SHRINKAGE_FLOOR we'd shrink to prior.
    shrinkage_applied = {
        s: bool(samples_by_stat.get(s, 0) < SHRINKAGE_FLOOR) for s in SUPPORTED_STATS
    }

    # TOV-specific diagnostics scaffold (filled with NaN-equivalents in dry-run;
    # real values come from the validator that reads outcomes).
    tov_diagnostics = {
        "p0_error": None,
        "mean_bias": None,
        "nll": None,
        "rps": None,
        "role_bucket_calibration": None,
        "notes": "Diagnostics computed by validate_champion_vs_challenger.py.",
    }

    return {
        "calibrator_kind": "dry-run-champion-reference",
        "champion_pmf_cal_meta_sha256": cal_meta_hash,
        "champion_calibration_manifest_sha256": cal_manifest_hash,
        "calibration_window": window,
        "samples_by_stat": samples_by_stat,
        "samples_by_role_bucket": role_breakdown,
        "shrinkage_floor_samples": SHRINKAGE_FLOOR,
        "shrinkage_applied": shrinkage_applied,
        "tov_diagnostics": tov_diagnostics,
    }


def _calibrate_full(as_of: dt.date, ch_dir: Path) -> dict:  # pragma: no cover
    raise NotImplementedError(
        "Full PMF calibration is not yet wired. Use --dry-run; the full path "
        "will be enabled once a rolling/walk-forward calibration driver is "
        "available end-to-end."
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Calibrate daily challenger PMFs.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    p.add_argument(
        "--challenger-dir",
        help="Override challenger output dir (default artifacts/models/challengers/<date>)",
    )
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    args = p.parse_args(argv)

    as_of = parse_date(args.as_of_date)
    ch_dir = (
        Path(args.challenger_dir).resolve() if args.challenger_dir else challenger_dir(args.as_of_date)
    )
    ch_dir.mkdir(parents=True, exist_ok=True)

    started_at = utcnow_iso()
    warnings: list[str] = []
    status = "ok"
    try:
        if args.dry_run:
            result = _calibrate_dry_run(as_of, ch_dir)
        else:
            result = _calibrate_full(as_of, ch_dir)
    except NotImplementedError as exc:
        status = "not_implemented"
        warnings.append(str(exc))
        result = {}
    except Exception as exc:  # pragma: no cover
        status = "error"
        warnings.append(f"calibration failed: {exc}")
        result = {}

    finished_at = utcnow_iso()

    cal_manifest = {
        "schema_version": "1.0",
        "as_of_date": args.as_of_date,
        "dry_run": bool(args.dry_run),
        "status": status,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "code_commit": git_commit(),
        "calibrator_type": "phase8-role-bucket",
        "details": result,
        "warnings": warnings,
        "phase10d_overlays_in_use": False,
        "notes": (
            "Phase 13A dry-run inherits champion calibrators by reference. The "
            "rolling validation window is reported but no recompute is performed. "
            "Walk-forward only — no future leakage."
        ),
    }
    write_json_atomic(ch_dir / "calibration_manifest.json", cal_manifest)

    print(
        json.dumps(
            {
                "as_of_date": args.as_of_date,
                "dry_run": bool(args.dry_run),
                "status": status,
                "challenger_dir": str(ch_dir.relative_to(REPO_ROOT)),
            },
            indent=2,
        )
    )
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
