#!/usr/bin/env python3
"""Fit stratified SGP joint-probability calibrators from backtest data.

Loads data/sgp_backtest_rows.parquet.  If the file is missing or contains
fewer than ``--min-rows`` rows, writes an empty HierarchicalCalibratorRegistry
and exits 0 with a clear status message.

Otherwise fits stratified isotonic calibrators per (n_legs × relationship_type)
cell plus a global fallback, with Bayesian shrinkage toward the global mean.

Writes
------
  artifacts/models/sgp/calibrator/sgp_joint_calibrator_latest.pkl
  artifacts/models/sgp/calibrator/sgp_calibration_metrics.json
  artifacts/models/sgp/calibrator/sgp_reliability_table.csv

Usage
-----
  python3 scripts/fit_sgp_joint_calibrator.py --repo-root .
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_SRC = Path(__file__).resolve().parent.parent / "src"
if _REPO_SRC.is_dir():
    sys.path.insert(0, str(_REPO_SRC))


# ── Calibration imports (graceful fallback if sgp_engine not installed) ───────

try:
    from sgp_engine.calibration import (
        HierarchicalCalibratorRegistry,
        JointProbabilityCalibrator,
        expected_calibration_error,
        fit_stratified_calibrators,
        reliability_table,
    )
    _CALIB_AVAILABLE = True
except ImportError as _e:
    _CALIB_AVAILABLE = False
    print(f"  WARNING: sgp_engine.calibration import failed: {_e}", file=sys.stderr)
    # Stubs so the rest of the module is type-safe at parse time.
    HierarchicalCalibratorRegistry = None  # type: ignore[assignment,misc]
    JointProbabilityCalibrator = None      # type: ignore[assignment,misc]
    fit_stratified_calibrators = None      # type: ignore[assignment]
    reliability_table = None               # type: ignore[assignment]
    expected_calibration_error = None      # type: ignore[assignment]


# ── Metric helpers ────────────────────────────────────────────────────────────

def _brier(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((np.clip(p, 1e-9, 1 - 1e-9) - y) ** 2))


def _log_loss(y: np.ndarray, p: np.ndarray, eps: float = 1e-9) -> float:
    p = np.clip(p, eps, 1 - eps)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _metrics(df: pd.DataFrame, pred_col: str, y_col: str) -> dict:
    valid = df[[pred_col, y_col]].dropna()
    if len(valid) == 0:
        return {"n": 0, "ece": None, "brier": None, "log_loss": None}
    y = valid[y_col].to_numpy(dtype=float)
    p = valid[pred_col].clip(1e-6, 1 - 1e-6).to_numpy(dtype=float)
    ece: float | None = None
    if _CALIB_AVAILABLE and expected_calibration_error is not None:
        try:
            ece = float(expected_calibration_error(valid, pred_col=pred_col, y_col=y_col))
        except Exception:
            pass
    return {
        "n": int(len(valid)),
        "ece":      round(ece, 6) if ece is not None else None,
        "brier":    round(_brier(y, p), 6),
        "log_loss": round(_log_loss(y, p), 6),
    }


# ── Fallback calibration (sklearn directly) ───────────────────────────────────

def _fallback_registry(
    df: pd.DataFrame,
    pred_col: str,
    y_col: str,
    min_n: int = 200,
):
    """Fit a global-only isotonic calibrator directly via sklearn."""
    from sklearn.isotonic import IsotonicRegression
    # We need at minimum the dataclass shells from sgp_engine.
    # If sgp_engine is truly absent we return None.
    try:
        from sgp_engine.calibration import (
            HierarchicalCalibratorRegistry as _Reg,
            JointProbabilityCalibrator as _Cal,
        )
    except ImportError:
        return None

    valid = df[[pred_col, y_col]].dropna()
    if len(valid) < min_n:
        return _Reg()

    x = valid[pred_col].clip(1e-6, 1 - 1e-6).to_numpy(dtype=float)
    y = valid[y_col].to_numpy(dtype=float)
    model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    model.fit(x, y)
    global_cal = _Cal(
        calibrator_id=f"global_isotonic_fallback_n{len(valid)}",
        model=model,
        n_train=int(len(valid)),
        cell="global",
    )
    return _Reg(global_calibrator=global_cal)


# ── Empty-registry writer ─────────────────────────────────────────────────────

def _write_empty(out_pkl: Path, out_metrics: Path, out_rel: Path, reason: str) -> None:
    """Write stub outputs when there is no usable backtest data."""
    if _CALIB_AVAILABLE and HierarchicalCalibratorRegistry is not None:
        HierarchicalCalibratorRegistry().save(out_pkl)
    out_metrics.write_text(
        json.dumps(
            {
                "fitted_at_utc": datetime.now(timezone.utc).isoformat(),
                "n_rows":    0,
                "n_cells":   0,
                "ece":       None,
                "brier":     None,
                "log_loss":  None,
                "status":    "NO_DATA",
                "reason":    reason,
            },
            indent=2,
        )
    )
    pd.DataFrame(
        columns=["bucket", "n", "mean_pred", "actual_rate",
                 "abs_calibration_error", "weighted_abs_calibration_error"]
    ).to_csv(out_rel, index=False)
    print(f"[FIT CALIBRATOR] Done (no data — {reason}).", flush=True)


# ── Column detection helpers ─────────────────────────────────────────────────

_PRED_COL_CANDIDATES = [
    "raw_joint_prob",
    "raw_joint_probability",
    "raw_prob",
    "joint_prob",
]
_STRATUM_COLS = [
    "n_legs",
    "stat_mix",
    "relationship_type",
    "role_mix",
    "line_percentile_bucket",
]


def _find_pred_col(df: pd.DataFrame) -> str | None:
    for c in _PRED_COL_CANDIDATES:
        if c in df.columns:
            return c
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument(
        "--min-rows", type=int, default=200,
        help="Minimum backtest rows required to fit calibrators (default: 200)",
    )
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    cal_dir = repo_root / "artifacts" / "models" / "sgp" / "calibrator"
    cal_dir.mkdir(parents=True, exist_ok=True)

    out_pkl     = cal_dir / "sgp_joint_calibrator_latest.pkl"
    out_metrics = cal_dir / "sgp_calibration_metrics.json"
    out_rel     = cal_dir / "sgp_reliability_table.csv"

    print("[FIT CALIBRATOR] Starting …", flush=True)

    # ── 1. Load backtest rows ──────────────────────────────────────────────────
    bt_path = repo_root / "data" / "sgp_backtest_rows.parquet"

    if not bt_path.exists():
        _write_empty(out_pkl, out_metrics, out_rel,
                     reason="data/sgp_backtest_rows.parquet not found")
        return 0

    try:
        df = pd.read_parquet(bt_path)
    except Exception as exc:
        _write_empty(out_pkl, out_metrics, out_rel,
                     reason=f"could_not_read_parquet:{exc}")
        return 0

    print(f"  Loaded {len(df)} rows from {bt_path.name}", flush=True)

    if len(df) < args.min_rows:
        _write_empty(out_pkl, out_metrics, out_rel,
                     reason=f"too_few_rows:{len(df)}<{args.min_rows}")
        return 0

    # ── 2. Identify columns ────────────────────────────────────────────────────
    pred_col = _find_pred_col(df)
    if pred_col is None:
        print(f"  WARNING: No raw probability column found in {list(df.columns)}",
              file=sys.stderr)
        _write_empty(out_pkl, out_metrics, out_rel,
                     reason="no_raw_probability_column")
        return 0

    y_col = "hit_result"
    if y_col not in df.columns:
        print(f"  WARNING: Column 'hit_result' missing.", file=sys.stderr)
        _write_empty(out_pkl, out_metrics, out_rel,
                     reason="no_hit_result_column")
        return 0

    avail_stratum = [c for c in _STRATUM_COLS if c in df.columns]
    print(f"  pred_col={pred_col!r}  y_col={y_col!r}", flush=True)
    print(f"  Stratum cols available: {avail_stratum}", flush=True)

    # ── 3. Clip and cast ───────────────────────────────────────────────────────
    df = df.copy()
    df[pred_col] = df[pred_col].clip(0.001, 0.999)
    df[y_col]    = pd.to_numeric(df[y_col], errors="coerce")

    settled = df.dropna(subset=[pred_col, y_col])
    if len(settled) < args.min_rows:
        _write_empty(out_pkl, out_metrics, out_rel,
                     reason=f"too_few_settled_rows:{len(settled)}<{args.min_rows}")
        return 0

    print(f"  Settled rows (non-null pred+y): {len(settled)}", flush=True)

    # ── 4. Metrics before calibration ────────────────────────────────────────
    metrics_before = _metrics(settled, pred_col, y_col)

    # ── 5. Fit calibrators ─────────────────────────────────────────────────────
    registry = None

    if _CALIB_AVAILABLE and fit_stratified_calibrators is not None:
        try:
            registry = fit_stratified_calibrators(
                settled,
                pred_col=pred_col,
                y_col=y_col,
                min_n_exact=500,
                min_n_parent=300,
                min_n_global=200,
                shrinkage_k=400.0,
            )
            n_cells = registry.cell_count
            print(f"  Stratified fitting complete: {n_cells} cells + global", flush=True)
        except Exception as exc:
            print(f"  fit_stratified_calibrators failed ({exc}); trying fallback …",
                  file=sys.stderr)
            registry = _fallback_registry(settled, pred_col, y_col, min_n=200)
    else:
        registry = _fallback_registry(settled, pred_col, y_col, min_n=200)

    if registry is None:
        _write_empty(out_pkl, out_metrics, out_rel,
                     reason="calibrator_fit_failed")
        return 0

    # ── 6. Compute calibrated predictions for metrics ─────────────────────────
    cal_preds = np.array([
        registry.predict(float(p), {})[0]
        for p in settled[pred_col]
    ])
    settled = settled.copy()
    settled["_calibrated_prob"] = cal_preds
    metrics_after = _metrics(settled, "_calibrated_prob", y_col)

    # ── 7. Reliability table ──────────────────────────────────────────────────
    rel_df: pd.DataFrame | None = None
    if _CALIB_AVAILABLE and reliability_table is not None:
        try:
            rel_df = reliability_table(settled, pred_col="_calibrated_prob", y_col=y_col)
        except Exception as exc:
            print(f"  WARNING: reliability_table failed: {exc}", file=sys.stderr)

    if rel_df is None:
        rel_df = pd.DataFrame(
            columns=["bucket", "n", "mean_pred", "actual_rate",
                     "abs_calibration_error", "weighted_abs_calibration_error"]
        )

    # ── 8. Per-stratum ECE ────────────────────────────────────────────────────
    stratum_ece: dict[str, dict[str, float]] = {}
    if _CALIB_AVAILABLE and expected_calibration_error is not None:
        for col in avail_stratum:
            col_ece: dict[str, float] = {}
            for val, grp in settled.groupby(col):
                if len(grp) < 30:
                    continue
                try:
                    ece = float(expected_calibration_error(
                        grp, pred_col="_calibrated_prob", y_col=y_col
                    ))
                    col_ece[str(val)] = round(ece, 6)
                except Exception:
                    pass
            if col_ece:
                stratum_ece[col] = col_ece

    # ── 9. Write outputs ───────────────────────────────────────────────────────
    registry.save(out_pkl)

    n_cells = getattr(registry, "cell_count", 0)
    metrics_json = {
        "fitted_at_utc":    datetime.now(timezone.utc).isoformat(),
        "n_rows":           int(len(settled)),
        "n_cells":          int(n_cells),
        "before_calibration": metrics_before,
        "after_calibration":  metrics_after,
        "ece":              metrics_after.get("ece"),
        "brier":            metrics_after.get("brier"),
        "log_loss":         metrics_after.get("log_loss"),
        "stratum_ece":      stratum_ece,
        "status":           "FITTED",
    }
    out_metrics.write_text(json.dumps(metrics_json, indent=2))

    rel_out = rel_df.copy()
    if "bucket" in rel_out.columns:
        rel_out["bucket"] = rel_out["bucket"].astype(str)
    rel_out.to_csv(out_rel, index=False)

    # ── 10. Summary ───────────────────────────────────────────────────────────
    def _fmt(v: float | None) -> str:
        return f"{v:.4f}" if v is not None else "N/A"

    print(f"\n[FIT CALIBRATOR] Summary", flush=True)
    print(f"  Rows loaded:     {len(settled)}", flush=True)
    print(f"  Cells fitted:    {n_cells}", flush=True)
    print(
        f"  ECE    before={_fmt(metrics_before.get('ece'))}  "
        f"after={_fmt(metrics_after.get('ece'))}",
        flush=True,
    )
    print(
        f"  Brier  before={_fmt(metrics_before.get('brier'))}  "
        f"after={_fmt(metrics_after.get('brier'))}",
        flush=True,
    )
    print(
        f"  LogL   before={_fmt(metrics_before.get('log_loss'))}  "
        f"after={_fmt(metrics_after.get('log_loss'))}",
        flush=True,
    )
    print(f"  Outputs: {out_pkl.name}  {out_metrics.name}  {out_rel.name}", flush=True)
    print("[FIT CALIBRATOR] Done.", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
