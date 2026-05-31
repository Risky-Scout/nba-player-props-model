#!/usr/bin/env python3
"""Fit SGP factor weights from historical PMF PIT residuals.

If historical data is unavailable, writes hardcoded defaults and exits 0.
If data is available, computes empirical correlations of PIT z-scores
across player-stat pairs and outputs fitted factor weights.

Usage
-----
  python3 scripts/fit_sgp_factor_weights.py --as-of-date 2026-05-29 --repo-root .
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


# ── Default weights ───────────────────────────────────────────────────────────

_DEFAULT_WEIGHTS = {
    "pts": {
        "pace": 0.20, "total": 0.20, "team_offense": 0.18, "team_shooting": 0.18,
        "minutes": 0.24, "usage": 0.28, "player_shooting": 0.18,
        "overtime": 0.08, "blowout": -0.05,
    },
    "reb": {
        "pace": 0.20, "team_rebound_pool": 0.20,
        "minutes": 0.28, "usage": 0.15, "overtime": 0.07, "blowout": 0.03,
    },
    "ast": {
        "pace": 0.22, "total": 0.18, "team_offense": 0.20, "team_shooting": 0.26,
        "minutes": 0.25, "usage": 0.22, "overtime": 0.07,
    },
    "fg3m": {
        "pace": 0.17, "total": 0.14, "team_shooting": 0.30,
        "minutes": 0.22, "usage": 0.22, "player_shooting": 0.26, "overtime": 0.06,
    },
    "tov": {
        "pace": 0.20, "team_turnover": 0.26, "minutes": 0.22, "usage": 0.28,
    },
    "stl": {
        "pace": 0.18, "minutes": 0.22, "defensive_activity": 0.32,
    },
    "blk": {
        "pace": 0.14, "minutes": 0.22, "defensive_activity": 0.30,
    },
}

_FACTOR_NAMES = [
    "pace", "total", "team_offense", "team_shooting", "team_rebound_pool",
    "team_turnover", "minutes", "usage", "player_shooting",
    "defensive_activity", "overtime", "blowout",
]


def _write_defaults(out_path: Path, as_of_date: str, reason: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "as_of_date": as_of_date,
        "method": "hardcoded_defaults_no_historical_data",
        "reason": reason,
        "trained_rows": 0,
        "factor_names": _FACTOR_NAMES,
        "weights": {
            "global": _DEFAULT_WEIGHTS,
        },
        "fit_diagnostics": {
            "rmse_corr": None,
            "max_abs_error": None,
            "n_cells": 0,
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"[FIT FACTORS] Wrote defaults to {out_path}  reason={reason}", flush=True)


# ── PIT z-score computation ───────────────────────────────────────────────────

def _compute_pit_z(pmf_json: str, actual: float, domain_max: float | None = None) -> float | None:
    """Compute the PIT (probability integral transform) z-score for an outcome."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
        from sgp_engine.pmf import parse_pmf
        from scipy.stats import norm

        pmf = parse_pmf(pmf_json, domain_max=domain_max)
        k = int(round(actual))
        k = max(0, min(k, len(pmf) - 1))
        cdf_lower = float(pmf[:k].sum())
        cdf_upper = float(pmf[:k + 1].sum())
        # PIT: sample uniform in [cdf(k-1), cdf(k)], then invert normal
        u = (cdf_lower + cdf_upper) / 2.0
        u = max(1e-6, min(u, 1 - 1e-6))
        return float(norm.ppf(u))
    except Exception:
        return None


def _fit_from_historical(
    stats_df: pd.DataFrame,
    repo_root: Path,
    as_of_date: str,
) -> dict:
    """Fit factor weights from historical data using PIT z-score correlations."""
    direct_stats = {"pts", "reb", "ast", "fg3m", "tov", "stl", "blk"}

    # Filter to only dates with PMF deliveries
    delivery_root = repo_root / "deliveries"
    if not delivery_root.exists():
        raise FileNotFoundError("No deliveries directory")

    # Collect PIT z-scores by joining stats to PMF deliveries
    z_records: list[dict] = []

    # Try to find stat columns
    stat_col_map = {
        "pts": ["pts", "points"],
        "reb": ["reb", "rebounds"],
        "ast": ["ast", "assists"],
        "fg3m": ["fg3m", "threes"],
        "tov": ["tov", "turnovers"],
        "stl": ["stl", "steals"],
        "blk": ["blk", "blocks"],
    }

    date_col = next((c for c in ["game_date", "slate_date", "date"] if c in stats_df.columns), None)
    if date_col is None:
        raise ValueError("No date column in player_game_stats")

    grouped_dates = stats_df.groupby(pd.to_datetime(stats_df[date_col]).dt.date.astype(str))
    n_dates = 0
    for game_date, day_df in grouped_dates:
        if str(game_date) > as_of_date:
            continue
        # Load PMF delivery for this date
        pmf_path_candidates = [
            delivery_root / game_date / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet",
            delivery_root / game_date / "canonical_source" / "all_props_model_only.parquet",
        ]
        pmf_df = None
        for pp in pmf_path_candidates:
            if pp.exists():
                try:
                    pmf_df = pd.read_parquet(pp)
                    break
                except Exception:
                    pass
        if pmf_df is None:
            continue

        # Build lookup: player_id + stat -> pmf_json
        pmf_lookup: dict[tuple, str] = {}
        if "pmf_json" in pmf_df.columns and "player_id" in pmf_df.columns and "stat" in pmf_df.columns:
            for _, pr in pmf_df.iterrows():
                pmf_lookup[(str(pr["player_id"]), str(pr["stat"]).lower())] = str(pr["pmf_json"])

        if not pmf_lookup:
            continue

        for _, row in day_df.iterrows():
            pid = str(row.get("player_id", ""))
            gid = str(row.get("game_id", ""))
            for stat, cols in stat_col_map.items():
                actual = None
                for col in cols:
                    if col in row and pd.notna(row[col]):
                        actual = float(row[col])
                        break
                if actual is None:
                    continue
                pmf_json = pmf_lookup.get((pid, stat))
                if pmf_json is None:
                    continue
                z = _compute_pit_z(pmf_json, actual)
                if z is None or not np.isfinite(z):
                    continue
                z_records.append({
                    "game_date": game_date,
                    "game_id": gid,
                    "player_id": pid,
                    "stat": stat,
                    "actual": actual,
                    "z_score": z,
                })
        n_dates += 1
        if n_dates >= 60:  # cap at 60 days for speed
            break

    if len(z_records) < 50:
        raise ValueError(f"Insufficient PIT z-score records: {len(z_records)}")

    z_df = pd.DataFrame(z_records)
    print(f"  {len(z_df)} PIT z-scores from {n_dates} dates", flush=True)

    # Compute empirical cross-stat correlations within same (game_id, player_id)
    pivoted = z_df.pivot_table(
        index=["game_id", "player_id"],
        columns="stat",
        values="z_score",
        aggfunc="first",
    )

    fit_corrs: dict[str, dict[str, float]] = {}
    avail_stats = [s for s in direct_stats if s in pivoted.columns]
    for stat in avail_stats:
        fit_corrs[stat] = {}
        for other in avail_stats:
            if other == stat:
                continue
            try:
                pair = pivoted[[stat, other]].dropna()
                if len(pair) >= 30:
                    corr = float(pair.corr().iloc[0, 1])
                    fit_corrs[stat][other] = corr
            except Exception:
                pass

    # Cross-player within-team correlations (simplified: use default scaling)
    # For now, scale default weights by empirical cross-stat corr where available
    fitted_weights = {}
    for stat, default_w in _DEFAULT_WEIGHTS.items():
        fitted_weights[stat] = dict(default_w)
        # Adjust shared factor weights based on cross-stat correlations observed
        if stat in fit_corrs:
            avg_corr = float(np.mean(list(fit_corrs[stat].values()))) if fit_corrs[stat] else 0.0
            # Scale shared factors (pace, total, team factors) proportionally
            shared_factors = ["pace", "total", "team_offense", "team_shooting", "team_rebound_pool",
                              "team_turnover", "overtime"]
            for f in shared_factors:
                if f in fitted_weights[stat]:
                    # Slight adjustment toward empirical average cross-stat correlation
                    scale = 1.0 + 0.5 * (avg_corr - 0.1)
                    scale = max(0.5, min(2.0, scale))
                    fitted_weights[stat][f] = round(fitted_weights[stat][f] * scale, 4)

    # Diagnostics
    n_cells = sum(len(v) for v in fit_corrs.values())
    all_corrs = [v for d in fit_corrs.values() for v in d.values()]
    rmse_corr = float(np.sqrt(np.mean(np.array(all_corrs) ** 2))) if all_corrs else None
    max_corr = float(max(abs(c) for c in all_corrs)) if all_corrs else None

    return {
        "as_of_date": as_of_date,
        "method": "pit_z_score_cross_stat_correlation",
        "trained_rows": len(z_df),
        "n_dates": n_dates,
        "factor_names": _FACTOR_NAMES,
        "weights": {"global": fitted_weights},
        "empirical_cross_stat_correlations": fit_corrs,
        "fit_diagnostics": {
            "rmse_corr": rmse_corr,
            "max_abs_error": max_corr,
            "n_cells": n_cells,
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--as-of-date", required=True, help="As-of date YYYY-MM-DD")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument("--min-rows", type=int, default=50,
                    help="Minimum PIT z-score rows required for fitting (default: 50)")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    as_of_date = args.as_of_date

    out_path = (
        repo_root / "artifacts" / "models" / "sgp" / "factor_weights" / "factor_weights_latest.json"
    )

    print(f"[FIT FACTORS] as_of_date={as_of_date}", flush=True)

    # ── Check for historical data ─────────────────────────────────────────────
    stats_path = repo_root / "data" / "player_game_stats.parquet"
    if not stats_path.exists():
        _write_defaults(out_path, as_of_date, reason="player_game_stats.parquet_not_found")
        return 0

    try:
        stats_df = pd.read_parquet(stats_path)
    except Exception as exc:
        _write_defaults(out_path, as_of_date, reason=f"could_not_read_stats: {exc}")
        return 0

    if stats_df.empty:
        _write_defaults(out_path, as_of_date, reason="player_game_stats_empty")
        return 0

    print(f"  Loaded {len(stats_df)} rows from player_game_stats.parquet", flush=True)

    # ── Try to fit from historical data ───────────────────────────────────────
    try:
        result = _fit_from_historical(stats_df, repo_root, as_of_date)
        if result["trained_rows"] < args.min_rows:
            _write_defaults(
                out_path, as_of_date,
                reason=f"insufficient_pit_records: {result['trained_rows']} < {args.min_rows}",
            )
            return 0

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True))
        print(f"  Fitted weights written to {out_path}", flush=True)
        print(f"  Trained rows: {result['trained_rows']}", flush=True)
        diag = result["fit_diagnostics"]
        print(f"  Diagnostics: rmse_corr={diag['rmse_corr']:.4f}  "
              f"max_abs_error={diag['max_abs_error']:.4f}  "
              f"n_cells={diag['n_cells']}", flush=True)

    except Exception as exc:
        print(f"  WARNING: Fitting failed ({exc}); writing defaults.", file=sys.stderr)
        _write_defaults(out_path, as_of_date, reason=f"fitting_exception: {exc}")

    print("[FIT FACTORS] Done.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
