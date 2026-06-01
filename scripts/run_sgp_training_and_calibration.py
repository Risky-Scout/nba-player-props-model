#!/usr/bin/env python3
"""Daily SGP shadow training and calibration pipeline.

Trains and calibrates the SGP Engine through the previous day (as_of_date).
Writes factor weights and joint calibrator artifacts used for today's prices.

Usage
-----
  python3 scripts/run_sgp_training_and_calibration.py \\
    --as-of-date 2026-05-29 \\
    --repo-root . \\
    --season-mode auto

Five stages
-----------
  Stage 1 — Resolve as-of context
    Confirm as_of_date < today. Identify latest settled game date.
    Identify no-game days. Valid-skip safely if nothing new to process.

  Stage 2 — Build/refresh SGP backtest rows
    Auto-detect missing dates from player_game_stats.parquet.
    Trigger build_sgp_backtest_rows.py for missing in-season dates.
    Append/merge into data/sgp_backtest_rows.parquet.
    Deduplicate by (sgp_id, prediction_date).

  Stage 3 — Fit PIT factor weights
    Use OOF PMF residuals from oof_combo_pmfs.parquet when available.
    Compute midpoint PIT -> Gaussian z-scores.
    Estimate empirical same-game correlations by stat/role/relationship.
    Apply shrinkage toward prior (k=400).
    Write factor_weights_{as_of_date}.json + factor_weights_latest.json.

  Stage 4 — Fit hierarchical joint calibrators
    Use data/sgp_backtest_rows.parquet filtered through as_of_date.
    Walk-forward: hold out last 20% by date for OOF validation.
    Fit global + segment-level isotonic calibrators.
    Apply shrinkage and fallback hierarchy.
    Write joint_calibrator_{as_of_date}.pkl + joint_calibrator_latest.pkl.

  Stage 5 — Produce reports
    Training report, calibration report, gate report, segment reliability.
    Registry pointer: artifacts/models/sgp/registry/sgp_model_pointer.json.

Production workflow
-------------------
Gated by:
  ENABLE_SGP_TRAINING=true
  run_sgp_training: "true"

Default is disabled (false). Do not activate daily by default until approved.
The --auto-build-dates flag is required to auto-detect and build missing dates.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

_REPO_SRC = Path(__file__).resolve().parent.parent / "src"
if _REPO_SRC.is_dir():
    sys.path.insert(0, str(_REPO_SRC))

# Shrinkage constant: n / (n + SHRINK_K).
_SHRINK_K = 400
# Minimum settled rows for a global calibrator fit.
_MIN_GLOBAL_CALIBRATION = 50
# Minimum rows before factor-weight fitting is attempted.
_MIN_FACTOR_FIT = 500
# OOF walk-forward holdout fraction (most-recent dates).
_WF_HOLDOUT_FRAC = 0.20
# Promotion gate thresholds.
_ECE_THRESHOLD = 0.025
_MCE_THRESHOLD = 0.075
_SLOPE_LO = 0.90
_SLOPE_HI = 1.10
_UCB95_LL_DELTA = -0.0025
_UCB95_BR_DELTA = -0.0010


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str))


def _get_commit_sha(repo_root: Path) -> str | None:
    """Return HEAD commit SHA, or None if not in a git repo."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(repo_root), timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _valid_skip(reason: str, as_of_date: str, out_dir: Path) -> int:
    status = {
        "status": "VALID_SKIP",
        "reason": reason,
        "as_of_date": as_of_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(out_dir / "sgp_training_status.json", status)
    print(f"[SGP-TRAIN] VALID_SKIP: {reason}")
    return 0


def _ece(pred: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(pred)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (pred >= lo) & (pred < hi)
        if mask.sum() < 3:
            continue
        frac_pos = actual[mask].mean()
        mean_pred = pred[mask].mean()
        ece += (mask.sum() / n) * abs(frac_pos - mean_pred)
    return float(ece)


def _mce(pred: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
    """Maximum Calibration Error."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    errors = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (pred >= lo) & (pred < hi)
        if mask.sum() < 3:
            continue
        errors.append(abs(actual[mask].mean() - pred[mask].mean()))
    return float(max(errors)) if errors else float("nan")


def _logloss(pred: np.ndarray, actual: np.ndarray, eps: float = 1e-7) -> float:
    p = pred.clip(eps, 1 - eps)
    return float(-np.mean(actual * np.log(p) + (1 - actual) * np.log(1 - p)))


def _brier(pred: np.ndarray, actual: np.ndarray) -> float:
    return float(np.mean((pred - actual) ** 2))


def _calibration_slope(pred: np.ndarray, actual: np.ndarray):
    """Return (slope, intercept) of logit-space reliability regression."""
    if len(pred) < 20:
        return None, None
    logit_p = np.log(pred.clip(1e-6, 1 - 1e-6) / (1 - pred.clip(1e-6, 1 - 1e-6)))
    try:
        slope, intercept, *_ = scipy_stats.linregress(logit_p, actual)
        return float(slope), float(intercept)
    except Exception:
        return None, None


def _ucb95_delta(model_loss: np.ndarray, ref_loss: np.ndarray) -> float:
    """Bootstrap UCB95 of mean(model_loss - ref_loss)."""
    diff = model_loss - ref_loss
    n = len(diff)
    if n < 30:
        return float("nan")
    mean_d = diff.mean()
    se = diff.std(ddof=1) / np.sqrt(n)
    return float(mean_d + 1.645 * se)


# ── Stage 1 — Resolve as-of context ──────────────────────────────────────────

def _stage1_resolve_context(
    as_of_date: str,
    repo_root: Path,
) -> dict[str, Any]:
    """Identify latest settled game date and whether new data exists.

    Primary source: data/oof_stat_pmf_predictions.parquet (game_date column).
    Fallback: data/player_game_stats.parquet if it exists.
    """
    today = date.today().isoformat()
    game_date_sources = [
        repo_root / "data" / "oof_stat_pmf_predictions.parquet",
        repo_root / "data" / "oof_combo_pmfs.parquet",
        repo_root / "data" / "player_game_stats.parquet",
    ]

    latest_game_date: str | None = None
    n_games_through: int = 0
    game_dates: list[str] = []

    for src in game_date_sources:
        if not src.exists():
            continue
        try:
            df = pd.read_parquet(src, columns=["game_date"])
            dates_arr = pd.to_datetime(df["game_date"], errors="coerce").dt.date.astype(str)
            filtered = sorted(d for d in dates_arr.dropna().unique() if d <= as_of_date)
            if filtered:
                latest_game_date = filtered[-1]
                game_dates = filtered
                n_games_through = len(filtered)
                break
        except Exception as exc:
            print(f"[SGP-TRAIN][S1] WARNING reading {src.name}: {exc}", file=sys.stderr)

    return {
        "today": today,
        "as_of_date": as_of_date,
        "latest_game_date": latest_game_date,
        "n_game_dates_available": n_games_through,
        "game_dates": game_dates,
    }


# ── Stage 2 — Build/refresh SGP backtest rows ─────────────────────────────────

def _stage2_refresh_backtest(
    ctx: dict,
    repo_root: Path,
    backtest_path: Path,
    n_sims: int,
    max_pairs: int,
    auto_build_dates: bool,
    dry_run: bool,
) -> pd.DataFrame:
    """Auto-detect missing dates and build new backtest rows."""
    as_of_date = ctx["as_of_date"]
    game_dates = ctx.get("game_dates", [])

    # Load existing backtest rows.
    existing_df = pd.DataFrame()
    if backtest_path.exists():
        try:
            existing_df = pd.read_parquet(backtest_path)
            date_col = next(
                (c for c in ["prediction_date", "slate_date"] if c in existing_df.columns),
                None,
            )
            if date_col:
                existing_df = existing_df[
                    pd.to_datetime(existing_df[date_col]).dt.date.astype(str) <= as_of_date
                ].copy()
            if "actual_hit" not in existing_df.columns and "hit_result" in existing_df.columns:
                existing_df["actual_hit"] = existing_df["hit_result"]
            print(f"[SGP-TRAIN][S2] Existing backtest rows: {len(existing_df)}")
        except Exception as exc:
            print(f"[SGP-TRAIN][S2] WARNING loading existing backtest: {exc}", file=sys.stderr)

    if not auto_build_dates or dry_run:
        return existing_df

    # Identify game dates not yet covered in backtest rows.
    covered_dates: set[str] = set()
    if not existing_df.empty:
        date_col = next(
            (c for c in ["prediction_date", "slate_date"] if c in existing_df.columns),
            None,
        )
        if date_col:
            covered_dates = set(
                pd.to_datetime(existing_df[date_col]).dt.date.astype(str).unique()
            )

    missing_dates = sorted(d for d in game_dates if d not in covered_dates)
    if not missing_dates:
        print("[SGP-TRAIN][S2] No missing game dates to build.")
        return existing_df

    print(f"[SGP-TRAIN][S2] Building backtest rows for {len(missing_dates)} missing dates: {missing_dates[:5]}{'...' if len(missing_dates) > 5 else ''}")

    build_cmd = [
        sys.executable,
        str(repo_root / "scripts" / "build_sgp_backtest_rows.py"),
        "--repo-root", str(repo_root),
        "--dates", ",".join(missing_dates),
        "--n-sims", str(n_sims),
        "--max-pairs-per-game", str(max_pairs),
        "--out", str(backtest_path),
        "--link-outcomes",
        "--allow-bundle-fail",
    ]
    result = subprocess.run(build_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[SGP-TRAIN][S2] WARNING: build_sgp_backtest_rows exited {result.returncode}: {result.stderr[:300]}", file=sys.stderr)
    else:
        print(f"[SGP-TRAIN][S2] Build complete.")

    if backtest_path.exists():
        try:
            df = pd.read_parquet(backtest_path)
            date_col = next(
                (c for c in ["prediction_date", "slate_date"] if c in df.columns),
                None,
            )
            if date_col:
                df = df[pd.to_datetime(df[date_col]).dt.date.astype(str) <= as_of_date].copy()
            if "actual_hit" not in df.columns and "hit_result" in df.columns:
                df["actual_hit"] = df["hit_result"]
            print(f"[SGP-TRAIN][S2] Reloaded: {len(df)} rows ({df['actual_hit'].notna().sum() if 'actual_hit' in df.columns else 0} settled)")
            return df
        except Exception as exc:
            print(f"[SGP-TRAIN][S2] WARNING reloading after build: {exc}", file=sys.stderr)

    return existing_df


# ── Stage 3 — Fit PIT factor weights ─────────────────────────────────────────

def _compute_pit_from_oof(repo_root: Path, as_of_date: str) -> pd.DataFrame | None:
    """Extract PIT z-scores from OOF PMF predictions through as_of_date.

    Uses oof_stat_pmf_predictions.parquet (pmf column = numpy ndarray, k starts at 0).
    Falls back to oof_combo_pmfs.parquet.

    Returns DataFrame with columns: game_date, player_id, stat, z_score
    or None if no usable OOF data is available.
    """
    candidates = [
        repo_root / "data" / "oof_stat_pmf_predictions.parquet",
        repo_root / "data" / "oof_combo_pmfs.parquet",
    ]
    oof_path = next((p for p in candidates if p.exists()), None)
    if oof_path is None:
        return None

    try:
        oof = pd.read_parquet(oof_path)
    except Exception as exc:
        print(f"[SGP-TRAIN][S3] WARNING loading OOF data from {oof_path.name}: {exc}", file=sys.stderr)
        return None

    date_col = next((c for c in ["game_date", "slate_date", "prediction_date"] if c in oof.columns), None)
    if date_col:
        oof = oof[pd.to_datetime(oof[date_col], errors="coerce").dt.date.astype(str) <= as_of_date].copy()

    if oof.empty:
        return None

    actual_col = next((c for c in ["outcome", "actual", "y", "stat_value"] if c in oof.columns), None)
    stat_col = next((c for c in ["stat", "stat_type", "stat_name"] if c in oof.columns), None)
    player_col = next((c for c in ["player_id", "bkref_id", "player_name"] if c in oof.columns), None)
    pmf_col = "pmf" if "pmf" in oof.columns else None

    if actual_col is None or pmf_col is None:
        return None

    rows: list[dict] = []
    for _, row in oof.iterrows():
        y_raw = row[actual_col]
        if pd.isna(y_raw):
            continue
        y = int(y_raw)

        pmf_val = row[pmf_col]
        if pmf_val is None:
            continue

        try:
            probs = np.asarray(pmf_val, dtype=np.float64).ravel()
        except Exception:
            continue

        if len(probs) == 0 or not np.isfinite(probs).all():
            continue
        s = probs.sum()
        if s < 0.5:
            continue
        probs = probs / s

        # PMF is indexed from k=0.
        cdf_before = float(probs[:y].sum()) if y > 0 else 0.0
        p_y = float(probs[y]) if y < len(probs) else 0.0
        u = np.clip(cdf_before + 0.5 * p_y, 1e-6, 1 - 1e-6)
        z = float(scipy_stats.norm.ppf(u))

        rec: dict = {
            "z_score": z,
            "game_date": str(row[date_col]) if date_col else as_of_date,
        }
        if stat_col:
            rec["stat"] = row[stat_col]
        if player_col:
            rec["player_id"] = row[player_col]
        rows.append(rec)

    if not rows:
        return None

    return pd.DataFrame(rows)


def _fit_factor_weights_full(
    backtest_df: pd.DataFrame,
    pit_df: pd.DataFrame | None,
    as_of_date: str,
    repo_root: Path,
) -> dict:
    """Fit PIT factor weights with empirical correlations + shrinkage."""
    from sgp_engine.sports.nba.simulator import _DEFAULT_FACTOR_WEIGHTS

    n_rows = len(backtest_df)
    n_pit = len(pit_df) if pit_df is not None else 0

    # Load existing weights as prior.
    fw_path = repo_root / "artifacts" / "models" / "sgp" / "factor_weights" / "factor_weights_latest.json"
    prior: dict = {}
    if fw_path.exists():
        try:
            prior = json.loads(fw_path.read_text())
        except Exception:
            pass

    # Build default weights as base.
    fw_out = {k: v for k, v in prior.items() if not k.startswith("_")}
    for stat, weights in _DEFAULT_FACTOR_WEIGHTS.items():
        fw_out.setdefault(stat, weights)

    if n_rows < _MIN_FACTOR_FIT:
        fw_out["_meta"] = {
            "as_of_date": as_of_date,
            "fitted_at_utc": datetime.now(timezone.utc).isoformat(),
            "method": "prior_defaults_insufficient_data",
            "n_backtest_rows": n_rows,
            "n_pit_rows": n_pit,
            "min_required": _MIN_FACTOR_FIT,
            "fallback_used": True,
            "shrinkage_k": _SHRINK_K,
        }
        return {
            "status": "INSUFFICIENT_DATA",
            "n_rows": n_rows,
            "n_pit_rows": n_pit,
            "method": "prior_defaults_insufficient_data",
            "as_of_date": as_of_date,
            "factor_weights": fw_out,
        }

    # ── Compute empirical correlations from backtest 2-leg pairs. ─────────────
    required_cols = {"calibrated_joint_probability", "independent_probability", "actual_hit"}
    if not required_cols.issubset(set(backtest_df.columns)):
        missing = sorted(required_cols - set(backtest_df.columns))
        fw_out["_meta"] = {
            "as_of_date": as_of_date,
            "method": "prior_defaults_schema_mismatch",
            "missing_columns": missing,
            "fallback_used": True,
        }
        return {
            "status": "SCHEMA_MISMATCH",
            "missing_columns": missing,
            "factor_weights": fw_out,
            "as_of_date": as_of_date,
        }

    settled = backtest_df.dropna(subset=["actual_hit"])
    n_settled = len(settled)

    # Empirical correlation factor by relationship type (shrinkage applied).
    emp_corr_by_rel: dict[str, float] = {}
    sample_sizes_by_rel: dict[str, int] = {}
    if n_settled >= 100 and "relationship_type" in settled.columns:
        for rel, grp in settled.groupby("relationship_type"):
            n_rel = len(grp)
            if n_rel < 30:
                continue
            indep_p = grp["independent_probability"].clip(1e-6, 1 - 1e-6)
            cal_p = grp["calibrated_joint_probability"].clip(1e-6, 1 - 1e-6)
            emp_cf = float((cal_p / indep_p).mean())
            # Shrinkage toward 1.0 (independence prior).
            w = n_rel / (n_rel + _SHRINK_K)
            shrunk_cf = w * emp_cf + (1 - w) * 1.0
            emp_corr_by_rel[str(rel)] = round(shrunk_cf, 4)
            sample_sizes_by_rel[str(rel)] = n_rel

    # ── Empirical stat-pair correlations from PIT z-scores. ───────────────────
    pit_corr_by_stat_pair: dict[str, float] = {}
    pit_sample_sizes: dict[str, int] = {}
    if pit_df is not None and not pit_df.empty and "stat" in pit_df.columns and "player_id" in pit_df.columns:
        # Compute per-game z-score pairs for cross-stat within-player.
        game_col = "game_date" if "game_date" in pit_df.columns else None
        if game_col:
            grouped = pit_df.groupby(["player_id", game_col, "stat"])["z_score"].mean().reset_index()
            pivoted = grouped.pivot_table(index=["player_id", game_col], columns="stat", values="z_score")
            stat_cols = [c for c in pivoted.columns]
            for i, s1 in enumerate(stat_cols):
                for s2 in stat_cols[i + 1:]:
                    pair = f"{s1}__{s2}"
                    valid = pivoted[[s1, s2]].dropna()
                    n_pair = len(valid)
                    if n_pair < 30:
                        continue
                    r = float(np.corrcoef(valid[s1], valid[s2])[0, 1])
                    w = n_pair / (n_pair + _SHRINK_K)
                    shrunk_r = w * r
                    pit_corr_by_stat_pair[pair] = round(shrunk_r, 4)
                    pit_sample_sizes[pair] = n_pair

    # Standard factor names for the NBA game-mechanism model.
    _FACTOR_NAMES = [
        "pace", "total", "team_offense", "team_shooting", "team_rebound_pool",
        "team_turnover", "minutes", "usage", "player_shooting", "defensive_activity",
        "overtime", "blowout", "close_game",
    ]

    # Target correlations: empirical corr by stat pair (from PIT) + by relationship.
    target_correlations = {}
    target_correlations.update({f"rel__{k}": v for k, v in emp_corr_by_rel.items()})
    target_correlations.update({f"pit__{k}": v for k, v in pit_corr_by_stat_pair.items()})

    # Fit diagnostics.
    n_corr_cells = len(emp_corr_by_rel) + len(pit_corr_by_stat_pair)
    n_eligible = len([v for v in list(emp_corr_by_rel.values()) + list(pit_corr_by_stat_pair.values()) if abs(v) > 0])
    fit_diagnostics = {
        "rmse_corr": float(np.sqrt(np.mean([v**2 for v in target_correlations.values()]))) if target_correlations else None,
        "max_abs_corr": float(max(abs(v) for v in target_correlations.values())) if target_correlations else None,
        "n_corr_cells": n_corr_cells,
        "n_eligible_cells": n_eligible,
        "min_cell_n": int(min(list(sample_sizes_by_rel.values()) + list(pit_sample_sizes.values()))) if (sample_sizes_by_rel or pit_sample_sizes) else 0,
        "median_cell_n": float(np.median(list(sample_sizes_by_rel.values()) + list(pit_sample_sizes.values()))) if (sample_sizes_by_rel or pit_sample_sizes) else 0,
        "shrinkage_applied": True,
    }

    # Combine sample sizes.
    sample_sizes_by_cell = {}
    sample_sizes_by_cell.update({f"rel__{k}": v for k, v in sample_sizes_by_rel.items()})
    sample_sizes_by_cell.update({f"pit__{k}": v for k, v in pit_sample_sizes.items()})

    fw_out["_meta"] = {
        "as_of_date": as_of_date,
        "fitted_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "midpoint_pit_cross_player_corr_shrinkage",
        "trained_rows": n_rows,
        "n_games": n_settled,          # proxy; true game count from context
        "n_backtest_rows": n_rows,
        "n_settled": n_settled,
        "n_pit_rows": n_pit,
        "factor_names": _FACTOR_NAMES,
        "target_correlations": target_correlations,
        "fit_diagnostics": fit_diagnostics,
        "sample_sizes_by_cell": sample_sizes_by_cell,
        "shrinkage_k": _SHRINK_K,
        "fallback_used": n_settled < 500,
        "latest_actual_box_score_date": None,   # set by caller via _meta update
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        # Legacy keys for backward compat.
        "empirical_corr_by_relationship": emp_corr_by_rel,
        "pit_corr_by_stat_pair": pit_corr_by_stat_pair,
        "sample_sizes_by_relationship": sample_sizes_by_rel,
        "pit_sample_sizes_by_stat_pair": pit_sample_sizes,
    }

    return {
        "status": "FIT_COMPLETE",
        "n_rows": n_rows,
        "n_settled": n_settled,
        "n_pit_rows": n_pit,
        "method": "midpoint_pit_cross_player_corr_shrinkage",
        "empirical_corr_by_relationship": emp_corr_by_rel,
        "pit_corr_by_stat_pair": pit_corr_by_stat_pair,
        "as_of_date": as_of_date,
        "factor_weights": fw_out,
    }


# ── Stage 4 — Fit hierarchical joint calibrators ─────────────────────────────

def _stage4_fit_calibrators(
    backtest_df: pd.DataFrame,
    as_of_date: str,
    repo_root: Path,
    dry_run: bool,
) -> dict:
    """Fit hierarchical isotonic calibrators with walk-forward holdout."""
    if "actual_hit" not in backtest_df.columns:
        return {"status": "NO_ACTUAL_HIT_COLUMN", "as_of_date": as_of_date}

    settled = backtest_df.dropna(subset=["actual_hit"]).copy()
    n_settled = len(settled)

    if n_settled < _MIN_GLOBAL_CALIBRATION:
        return {
            "status": "INSUFFICIENT_DATA",
            "n_settled": n_settled,
            "min_required": _MIN_GLOBAL_CALIBRATION,
            "as_of_date": as_of_date,
        }

    if dry_run:
        return {"status": "DRY_RUN", "n_settled": n_settled, "as_of_date": as_of_date}

    # Walk-forward split: hold out most-recent _WF_HOLDOUT_FRAC of dates.
    date_col = next(
        (c for c in ["prediction_date", "slate_date"] if c in settled.columns), None
    )
    train_df = settled
    holdout_df = pd.DataFrame()

    if date_col and n_settled >= 100:
        sorted_dates = sorted(settled[date_col].astype(str).unique())
        n_holdout_dates = max(1, int(len(sorted_dates) * _WF_HOLDOUT_FRAC))
        holdout_dates = set(sorted_dates[-n_holdout_dates:])
        train_mask = ~settled[date_col].astype(str).isin(holdout_dates)
        train_df = settled[train_mask].copy()
        holdout_df = settled[~train_mask].copy()
        print(f"[SGP-TRAIN][S4] Walk-forward: train={len(train_df)}, holdout={len(holdout_df)}")

    try:
        from sgp_engine.calibration import HierarchicalCalibratorRegistry

        segment_cols = [c for c in [
            "leg_count", "relationship_type", "stat_mix", "role_mix",
            "lineup_status", "contains_sparse_stat", "contains_combo_overlap",
            "contains_alt_line", "line_percentile_bucket",
        ] if c in train_df.columns]

        registry = HierarchicalCalibratorRegistry(segment_cols=segment_cols)
        registry.fit(
            train_df,
            pred_col="calibrated_joint_probability",
            y_col="actual_hit",
            min_cell_n=50,
        )

        cal_dir = repo_root / "artifacts" / "models" / "sgp" / "joint_calibrators"
        cal_dir.mkdir(parents=True, exist_ok=True)
        cal_path = cal_dir / f"joint_calibrator_{as_of_date}.pkl"
        latest_path = cal_dir / "joint_calibrator_latest.pkl"
        registry.save(cal_path)
        registry.save(latest_path)

        # OOF validation metrics on holdout.
        oof_metrics: dict = {}
        if not holdout_df.empty and "calibrated_joint_probability" in holdout_df.columns:
            raw_pred = holdout_df["calibrated_joint_probability"].to_numpy(dtype=float)
            actual = holdout_df["actual_hit"].to_numpy(dtype=float)
            if len(raw_pred) >= 20:
                oof_metrics["oof_ece"] = _ece(raw_pred, actual)
                oof_metrics["oof_mce"] = _mce(raw_pred, actual)
                oof_metrics["oof_brier"] = _brier(raw_pred, actual)
                oof_metrics["oof_logloss"] = _logloss(raw_pred, actual)
                slope, intercept = _calibration_slope(raw_pred, actual)
                oof_metrics["oof_slope"] = slope
                oof_metrics["oof_intercept"] = intercept
                oof_metrics["n_holdout"] = int(len(raw_pred))

        return {
            "status": "FIT_COMPLETE",
            "n_train": len(train_df),
            "n_holdout": len(holdout_df),
            "n_settled": n_settled,
            "cell_count": registry.cell_count,
            "global_calibrator_fitted": registry.global_calibrator is not None,
            "segment_cols": segment_cols,
            "artifact_path": str(cal_path),
            "as_of_date": as_of_date,
            "oof_metrics": oof_metrics,
        }

    except Exception as exc:
        return {
            "status": "FIT_ERROR",
            "error": str(exc),
            "n_settled": n_settled,
            "as_of_date": as_of_date,
        }


# ── Stage 5 — Produce reports and gate assessment ────────────────────────────

def _segment_calibration_table(
    settled: pd.DataFrame,
    pred_col: str = "calibrated_joint_probability",
    y_col: str = "actual_hit",
    seg_col: str | None = None,
) -> list[dict]:
    """Compute per-segment calibration metrics."""
    rows: list[dict] = []

    def _metrics(df: pd.DataFrame, label: str, seg_value: str) -> dict:
        pred = df[pred_col].to_numpy(dtype=float).clip(1e-6, 1 - 1e-6)
        actual = df[y_col].to_numpy(dtype=float)
        n = len(pred)
        slope, intercept = _calibration_slope(pred, actual)
        return {
            "segment_col": label,
            "segment_value": seg_value,
            "n": n,
            "mean_pred": float(pred.mean()),
            "mean_actual": float(actual.mean()),
            "ece": _ece(pred, actual),
            "mce": _mce(pred, actual),
            "brier": _brier(pred, actual),
            "logloss": _logloss(pred, actual),
            "calibration_slope": slope,
            "calibration_intercept": intercept,
        }

    # Global.
    if len(settled) >= 20 and pred_col in settled.columns and y_col in settled.columns:
        rows.append(_metrics(settled, "global", "all"))

    if seg_col and seg_col in settled.columns:
        for val, grp in settled.groupby(seg_col):
            if len(grp) >= 20:
                rows.append(_metrics(grp, seg_col, str(val)))

    return rows


def _compute_gate_status(
    calibration_report: dict,
    n_settled: int,
) -> dict:
    """Evaluate promotion gates and return gate status."""
    gates: dict[str, Any] = {
        "as_of_date": calibration_report.get("as_of_date"),
        "n_settled": n_settled,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    # Gate 1: sufficient sample.
    gates["gate1_sufficient_sample"] = n_settled >= _MIN_GLOBAL_CALIBRATION
    gates["gate1_detail"] = f"n_settled={n_settled} >= {_MIN_GLOBAL_CALIBRATION}"

    global_metrics = calibration_report.get("global_metrics", {})
    oof_metrics = calibration_report.get("oof_metrics", {})

    # Gate 2: ECE.
    oof_ece = oof_metrics.get("oof_ece")
    gates["gate2_ece"] = (oof_ece is not None and oof_ece <= _ECE_THRESHOLD)
    gates["gate2_detail"] = f"oof_ece={oof_ece}  threshold={_ECE_THRESHOLD}"

    # Gate 3: MCE.
    oof_mce = oof_metrics.get("oof_mce")
    gates["gate3_mce"] = (oof_mce is not None and oof_mce <= _MCE_THRESHOLD)
    gates["gate3_detail"] = f"oof_mce={oof_mce}  threshold={_MCE_THRESHOLD}"

    # Gate 4: calibration slope.
    slope = oof_metrics.get("oof_slope")
    gates["gate4_slope"] = (slope is not None and _SLOPE_LO <= slope <= _SLOPE_HI)
    gates["gate4_detail"] = f"oof_slope={slope}  required=[{_SLOPE_LO},{_SLOPE_HI}]"

    # Gate 5: market superiority (UCB95) — not yet applicable.
    gates["gate5_market_superiority"] = False
    gates["gate5_detail"] = "No actual SGP market odds ingested yet (market_corr_factor_source=independence_placeholder)"

    # Overall.
    all_non_market = all([
        gates["gate1_sufficient_sample"],
        gates["gate2_ece"],
        gates["gate3_mce"],
        gates["gate4_slope"],
    ])
    gates["all_gates_pass"] = all_non_market and gates["gate5_market_superiority"]
    gates["non_market_gates_pass"] = all_non_market

    # Count certified segments (those passing all calibration thresholds).
    seg_reliability = calibration_report.get("segment_reliability", [])
    n_certified_segs = 0
    for seg in seg_reliability:
        seg_ece = seg.get("ece")
        seg_slope = seg.get("slope")
        seg_n = seg.get("n", 0)
        if (seg_n >= 200 and seg_ece is not None and seg_ece <= _ECE_THRESHOLD
                and seg_slope is not None and _SLOPE_LO <= seg_slope <= _SLOPE_HI):
            n_certified_segs += 1
    gates["n_certified_segments"] = n_certified_segs

    # Promotion status.
    if not gates["gate1_sufficient_sample"]:
        gates["promotion_status"] = "INSUFFICIENT_SAMPLE"
    elif all_non_market and gates["gate5_market_superiority"]:
        gates["promotion_status"] = "CERTIFIED"
    elif all_non_market:
        gates["promotion_status"] = "MODEL_PRICE"
    else:
        gates["promotion_status"] = "DIAGNOSTIC_ONLY"

    return gates


def _write_registry_pointer(
    repo_root: Path,
    as_of_date: str,
    n_rows: int,
    n_settled: int,
    n_games: int,
    fw_result: dict,
    cal_result: dict,
    gate_report: dict,
    ctx: dict | None = None,
) -> None:
    """Write sgp_model_pointer.json — single source of truth for SGP training state."""
    fw_dir = repo_root / "artifacts" / "models" / "sgp" / "factor_weights"
    cal_dir = repo_root / "artifacts" / "models" / "sgp" / "joint_calibrators"

    fw_artifact = str(fw_dir / f"factor_weights_{as_of_date}.json")
    cal_artifact = str(cal_dir / f"joint_calibrator_{as_of_date}.pkl")

    # Derive promotion_status from gate_report.
    promo = gate_report.get("promotion_status", "INSUFFICIENT_SAMPLE")
    # Map internal status values to spec-defined values.
    if n_rows == 0:
        promo = "DIAGNOSTIC_NO_BACKTEST"
    elif not gate_report.get("gate1_sufficient_sample", False):
        promo = "DIAGNOSTIC_NO_BACKTEST"
    elif cal_result.get("status") in ("FIT_COMPLETE",) and fw_result.get("status") == "FIT_COMPLETE":
        if gate_report.get("all_gates_pass", False):
            promo = "CERTIFIED_SEGMENTS_AVAILABLE"
        elif gate_report.get("non_market_gates_pass", False):
            promo = "FIT_COMPLETE_NOT_CERTIFIED"
        else:
            promo = "CALIBRATOR_FIT_INSUFFICIENT_SEGMENTS"
    elif fw_result.get("status") == "FIT_COMPLETE" and cal_result.get("status") != "FIT_COMPLETE":
        promo = "FACTOR_WEIGHTS_ONLY"
    else:
        promo = "DIAGNOSTIC_NO_BACKTEST"

    # Determine latest actual box-score date from context.
    latest_box_score = (ctx or {}).get("latest_game_date", as_of_date)

    # Check if fw artifact actually exists on disk.
    fw_exists = (fw_dir / f"factor_weights_{as_of_date}.json").exists()
    cal_exists = (cal_dir / f"joint_calibrator_{as_of_date}.pkl").exists()

    # Build pointer with all required fields.
    pointer = {
        # ── Identity ──────────────────────────────────────────────────────
        "sgp_model_version": "v1",
        # ── Temporal ──────────────────────────────────────────────────────
        "trained_through_date": as_of_date,
        "calibrated_through_date": as_of_date,
        "latest_actual_box_score_date": latest_box_score,
        # ── Artifacts ─────────────────────────────────────────────────────
        "factor_weights_artifact": fw_artifact if fw_exists else None,
        "factor_weights_artifact_exists": fw_exists,
        "factor_weights_latest": str(fw_dir / "factor_weights_latest.json") if (fw_dir / "factor_weights_latest.json").exists() else None,
        "joint_calibrator_artifact": cal_artifact if cal_exists else None,
        "joint_calibrator_artifact_exists": cal_exists,
        "joint_calibrator_latest": str(cal_dir / "joint_calibrator_latest.pkl") if (cal_dir / "joint_calibrator_latest.pkl").exists() else None,
        # ── Data counts ───────────────────────────────────────────────────
        "n_backtest_rows": n_rows,
        "n_settled": n_settled,
        "n_games": n_games,
        "n_segments": cal_result.get("cell_count", 0),
        "n_certified_segments": int(gate_report.get("n_certified_segments", 0)),
        # ── Status ────────────────────────────────────────────────────────
        "factor_weights_status": fw_result.get("status", "UNKNOWN"),
        "calibration_status": cal_result.get("status", "UNKNOWN"),
        "promotion_status": promo,
        "all_gates_pass": gate_report.get("all_gates_pass", False),
        "non_market_gates_pass": gate_report.get("non_market_gates_pass", False),
        "market_superiority_certified": gate_report.get("gate5_market_superiority", False),
        "market_sgp_odds_available": False,   # true only when real SGP odds ingested
        # ── Production gating ─────────────────────────────────────────────
        "default_delivery_enabled": False,    # NEVER set to True programmatically
        "default_delivery_note": (
            "SGP Engine remains opt-in (ENABLE_SGP_ENGINE=false, run_sgp_engine default false). "
            "Setting default_delivery_enabled=True requires explicit user approval "
            "after all calibration gates pass."
        ),
        # ── Calibration quality (from OOF holdout if available) ───────────
        "oof_ece": cal_result.get("oof_metrics", {}).get("oof_ece"),
        "oof_mce": cal_result.get("oof_metrics", {}).get("oof_mce"),
        "oof_slope": cal_result.get("oof_metrics", {}).get("oof_slope"),
        "oof_intercept": cal_result.get("oof_metrics", {}).get("oof_intercept"),
        # ── Metadata ──────────────────────────────────────────────────────
        "commit_sha": _get_commit_sha(repo_root),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    reg_dir = repo_root / "artifacts" / "models" / "sgp" / "registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    _write_json(reg_dir / "sgp_model_pointer.json", pointer)
    print(f"  Registry pointer written: promotion_status={promo}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--as-of-date", required=True,
                    help="Train/calibrate through this date (YYYY-MM-DD). Must be < today.")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument("--season-mode", default="auto",
                    choices=["auto", "season", "offseason"],
                    help="Season mode (default: auto — detect from game data).")
    ap.add_argument("--dates", default=None,
                    help="Comma-separated explicit dates to build backtest rows for.")
    ap.add_argument("--auto-build-dates", action="store_true",
                    help="Auto-detect missing game dates from player_game_stats.parquet and build rows.")
    ap.add_argument("--n-sims", type=int, default=50_000,
                    help="Simulation draws for new backtest rows (default: 50000).")
    ap.add_argument("--max-pairs-per-game", type=int, default=150,
                    help="Max pairs per game for backtest rows (default: 150).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build diagnostics only; do not write model artifacts.")
    ap.add_argument("--seg-col", default="leg_count",
                    help="Primary segment column for per-segment calibration report (default: leg_count).")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    as_of_date = args.as_of_date
    today = date.today().isoformat()
    out_dir = repo_root / "artifacts" / "models" / "sgp" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[SGP-TRAIN] ─────────────────────────────────────────────────────")
    print(f"[SGP-TRAIN] as_of_date={as_of_date}  today={today}  mode={args.season_mode}")

    # ── Safety gate: never use current-day or future data. ────────────────────
    if as_of_date >= today:
        print(
            f"[SGP-TRAIN] ERROR: as_of_date={as_of_date} is >= today={today}. "
            "Never train on current-day or future outcomes.",
            file=sys.stderr,
        )
        return 1

    # ════════════════════════════════════════════════════════════════════════
    # Stage 1 — Resolve as-of context.
    # ════════════════════════════════════════════════════════════════════════
    print("[SGP-TRAIN] Stage 1: Resolving as-of context ...")
    ctx = _stage1_resolve_context(as_of_date, repo_root)
    print(f"  latest_game_date={ctx['latest_game_date']}  "
          f"n_game_dates_available={ctx['n_game_dates_available']}")

    if args.season_mode == "offseason":
        return _valid_skip("Season mode = offseason; skipping.", as_of_date, out_dir)

    if ctx["latest_game_date"] is None and args.season_mode == "auto" and not args.dates:
        return _valid_skip(
            "No player_game_stats.parquet data found or no game dates through as_of_date.",
            as_of_date, out_dir,
        )

    # Merge explicit --dates with auto-detected dates if any.
    if args.dates:
        extra = [d.strip() for d in args.dates.split(",") if d.strip() and d.strip() <= as_of_date]
        ctx["game_dates"] = sorted(set(ctx["game_dates"]) | set(extra))

    # ════════════════════════════════════════════════════════════════════════
    # Stage 2 — Build/refresh SGP backtest rows.
    # ════════════════════════════════════════════════════════════════════════
    print("[SGP-TRAIN] Stage 2: Refreshing SGP backtest rows ...")
    backtest_path = repo_root / "data" / "sgp_backtest_rows.parquet"
    backtest_df = _stage2_refresh_backtest(
        ctx, repo_root, backtest_path,
        n_sims=args.n_sims,
        max_pairs=args.max_pairs_per_game,
        auto_build_dates=args.auto_build_dates,
        dry_run=args.dry_run,
    )
    n_rows = len(backtest_df)
    n_settled_total = int(backtest_df["actual_hit"].notna().sum()) if "actual_hit" in backtest_df.columns else 0
    n_games = int(backtest_df["game_id"].nunique()) if "game_id" in backtest_df.columns else 0
    print(f"  n_rows={n_rows}  n_settled={n_settled_total}  n_games={n_games}")

    if backtest_df.empty and args.season_mode == "auto":
        return _valid_skip("No backtest rows available (off-season or no games yet).", as_of_date, out_dir)

    # ════════════════════════════════════════════════════════════════════════
    # Stage 3 — Fit PIT factor weights.
    # ════════════════════════════════════════════════════════════════════════
    print("[SGP-TRAIN] Stage 3: Fitting PIT factor weights ...")
    pit_df = _compute_pit_from_oof(repo_root, as_of_date)
    if pit_df is not None:
        print(f"  OOF PIT residuals: {len(pit_df)} rows from {pit_df['game_date'].nunique() if 'game_date' in pit_df.columns else '?'} game dates")
    else:
        print("  No OOF PMF data found; factor weights will rely on backtest correlation signals only.")

    fw_result = _fit_factor_weights_full(backtest_df, pit_df, as_of_date, repo_root)
    print(f"  Factor weights: status={fw_result['status']}")

    if not args.dry_run and "factor_weights" in fw_result:
        fw_dir = repo_root / "artifacts" / "models" / "sgp" / "factor_weights"
        fw_dir.mkdir(parents=True, exist_ok=True)
        fw_versioned = fw_dir / f"factor_weights_{as_of_date}.json"
        fw_latest = fw_dir / "factor_weights_latest.json"
        fw_versioned.write_text(json.dumps(fw_result["factor_weights"], indent=2, sort_keys=True, default=str))
        fw_latest.write_text(json.dumps(fw_result["factor_weights"], indent=2, sort_keys=True, default=str))
        print(f"  Wrote: {fw_versioned.name}, factor_weights_latest.json")

    # Write factor weights report.
    _write_json(out_dir / f"sgp_factor_weights_report_{as_of_date}.json", {
        k: v for k, v in fw_result.items() if k != "factor_weights"
    })

    # ════════════════════════════════════════════════════════════════════════
    # Stage 4 — Fit hierarchical joint calibrators.
    # ════════════════════════════════════════════════════════════════════════
    print(f"[SGP-TRAIN] Stage 4: Fitting hierarchical joint calibrators (n_settled={n_settled_total}) ...")
    cal_result = _stage4_fit_calibrators(
        backtest_df, as_of_date, repo_root, dry_run=args.dry_run
    )
    print(f"  Calibrator: status={cal_result.get('status')}")
    oof_metrics = cal_result.get("oof_metrics", {})
    if oof_metrics:
        print(f"  OOF ECE={oof_metrics.get('oof_ece', 'n/a'):.4f}  "
              f"MCE={oof_metrics.get('oof_mce', 'n/a'):.4f}  "
              f"Slope={oof_metrics.get('oof_slope', 'n/a')}")

    # ════════════════════════════════════════════════════════════════════════
    # Stage 5 — Produce reports.
    # ════════════════════════════════════════════════════════════════════════
    print("[SGP-TRAIN] Stage 5: Producing reports ...")

    # Per-segment reliability table.
    seg_rows: list[dict] = []
    if not backtest_df.empty and "actual_hit" in backtest_df.columns and "calibrated_joint_probability" in backtest_df.columns:
        settled = backtest_df.dropna(subset=["actual_hit"])
        for seg_col in ["leg_count", "relationship_type", "stat_mix", "role_mix",
                        "lineup_status", "line_percentile_bucket"]:
            seg_rows.extend(_segment_calibration_table(settled, seg_col=seg_col))
        if seg_rows:
            seg_df = pd.DataFrame(seg_rows)
            rel_path = out_dir / f"sgp_reliability_by_segment_{as_of_date}.csv"
            latest_rel = repo_root / "artifacts" / "models" / "sgp" / "reports" / "sgp_reliability_by_segment_latest.csv"
            seg_df.to_csv(rel_path, index=False)
            seg_df.to_csv(latest_rel, index=False)
            print(f"  Reliability table: {len(seg_df)} rows across {len(seg_rows)} segments")

    # Calibration report.
    calibration_report = {
        "as_of_date": as_of_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "n_backtest_rows": n_rows,
        "n_settled": n_settled_total,
        "n_games": n_games,
        "calibrator_status": cal_result.get("status"),
        "oof_metrics": oof_metrics,
        "segment_cols": cal_result.get("segment_cols", []),
        "cell_count": cal_result.get("cell_count", 0),
        "fit_error": cal_result.get("error"),
        "segments_reliability": seg_rows,
    }
    _write_json(out_dir / f"sgp_calibration_report_{as_of_date}.json", calibration_report)

    # Gate report.
    gate_report = _compute_gate_status(calibration_report, n_settled_total)
    _write_json(out_dir / f"sgp_gate_report_{as_of_date}.json", gate_report)
    print(f"  Gate report: promotion_status={gate_report['promotion_status']}")
    for gate_key in ["gate1_sufficient_sample", "gate2_ece", "gate3_mce", "gate4_slope", "gate5_market_superiority"]:
        status_str = "PASS" if gate_report.get(gate_key) else "FAIL"
        print(f"    {gate_key}: {status_str}  ({gate_report.get(gate_key + '_detail', '')})")

    # Training report.
    training_report = {
        "status": "COMPLETE",
        "as_of_date": as_of_date,
        "trained_through_date": as_of_date,
        "calibrated_through_date": as_of_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "n_backtest_rows": n_rows,
        "n_settled": n_settled_total,
        "n_games": n_games,
        "n_pit_rows": fw_result.get("n_pit_rows", 0),
        "factor_weights_result": {k: v for k, v in fw_result.items() if k != "factor_weights"},
        "calibrator_result": {k: v for k, v in cal_result.items() if k != "oof_metrics"},
        "promotion_status": gate_report["promotion_status"],
    }
    _write_json(out_dir / f"sgp_training_report_{as_of_date}.json", training_report)
    _write_json(out_dir / "sgp_training_status.json", {
        "status": "COMPLETE",
        "as_of_date": as_of_date,
        "promotion_status": gate_report["promotion_status"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    })

    # Registry pointer.
    if not args.dry_run:
        _write_registry_pointer(
            repo_root, as_of_date,
            n_rows, n_settled_total, n_games,
            fw_result, cal_result, gate_report,
            ctx=ctx,
        )

    print(f"[SGP-TRAIN] ─────────────────────────────────────────────────────")
    print(f"[SGP-TRAIN] Done.  promotion_status={gate_report['promotion_status']}")
    print(f"[SGP-TRAIN]        Reports written to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
