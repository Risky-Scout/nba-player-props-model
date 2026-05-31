#!/usr/bin/env python3
"""Fit SGP factor weights from historical PMF PIT residuals.

Algorithm
---------
1. Load data/player_game_stats.parquet.  If missing, fall back to defaults.
2. Discover all delivery dates with canonical PMF parquet.
3. Join stats to PMFs on (date, player_id, stat); compute PIT z-scores with
   mid-point continuity correction, clipped to (0.01, 0.99).
4. Build cross-player pairs per game: same_team vs cross_team.
5. Compute empirical Pearson correlations by relationship type.
6. Fit factor weights via constrained least squares:
     w_game    = sqrt(max(rho_cross_team, 0))
     w_minutes = clip(corr(z_stat, player_mean_z), 0.10, 0.40)
     w_team    = sqrt(max(rho_same_team − w_game² + w_minutes² × 0.3, 0.01²))
7. Scale default factor-weight groups to match fitted targets; normalize to
   sum(w²) ≤ 0.95.
8. Write artifacts/models/sgp/factor_weights/factor_weights_latest.json.

Usage
-----
  python3 scripts/fit_sgp_factor_weights.py --repo-root .
  python3 scripts/fit_sgp_factor_weights.py --as-of-date 2026-05-29 --repo-root .
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date as _date
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

_REPO_SRC = Path(__file__).resolve().parent.parent / "src"
if _REPO_SRC.is_dir():
    sys.path.insert(0, str(_REPO_SRC))


# ── Factor structure (mirrors simulator's _DEFAULT_FACTOR_WEIGHTS) ────────────

_DEFAULT_FACTOR_WEIGHTS: dict[str, list[tuple[str, float]]] = {
    "pts": [
        ("pace_z", 0.20), ("total_z", 0.20), ("team_offense_z", 0.18),
        ("team_shooting_z", 0.18), ("player_usage_z", 0.28),
        ("player_minutes_z", 0.24), ("player_shooting_z", 0.18),
        ("ot_flag", 0.08), ("blowout_z", -0.05),
    ],
    "fg3m": [
        ("pace_z", 0.17), ("total_z", 0.14), ("team_three_z", 0.30),
        ("team_shooting_z", 0.16), ("player_usage_z", 0.22),
        ("player_minutes_z", 0.22), ("player_shooting_z", 0.26),
        ("ot_flag", 0.06),
    ],
    "ast": [
        ("pace_z", 0.22), ("total_z", 0.18), ("team_assist_env_z", 0.30),
        ("team_shooting_z", 0.26), ("player_usage_z", 0.22),
        ("player_minutes_z", 0.25), ("ot_flag", 0.07),
    ],
    "reb": [
        ("pace_z", 0.20), ("opp_shooting_z", -0.15), ("team_rebound_pool_z", 0.20),
        ("opp_rebound_pool_z", 0.22), ("player_minutes_z", 0.28),
        ("player_energy_z", 0.22), ("ot_flag", 0.07), ("blowout_z", 0.03),
    ],
    "tov": [
        ("pace_z", 0.20), ("team_turnover_z", 0.26), ("opp_def_activity_z", 0.20),
        ("player_usage_z", 0.28), ("player_minutes_z", 0.22),
        ("foul_env_z", 0.08),
    ],
    "stl": [
        ("pace_z", 0.18), ("opp_turnover_z", 0.24), ("team_def_activity_z", 0.26),
        ("player_minutes_z", 0.22), ("player_defense_z", 0.24),
        ("player_energy_z", 0.14),
    ],
    "blk": [
        ("pace_z", 0.14), ("opp_offense_z", 0.14), ("team_def_activity_z", 0.20),
        ("player_minutes_z", 0.22), ("player_defense_z", 0.30),
        ("player_energy_z", 0.16), ("player_foul_z", -0.08),
    ],
}

# Game-level factors: shared across ALL players in the same game.
_GAME_FACTORS: frozenset[str] = frozenset({"pace_z", "total_z"})

# Team-level factors: shared within the same team only.
_TEAM_FACTORS: frozenset[str] = frozenset({
    "team_offense_z", "team_shooting_z", "team_three_z", "team_assist_env_z",
    "team_rebound_pool_z", "team_turnover_z", "team_def_activity_z",
    "opp_offense_z", "opp_shooting_z", "opp_rebound_pool_z",
    "opp_def_activity_z", "opp_turnover_z", "foul_env_z",
})

_MINUTES_FACTOR = "player_minutes_z"

# Dirichlet negative minutes correlation constant (5-player team, roughly 1/5 + adjustments).
_C_DIRICHLET = 0.30

_STAT_COL_MAP: dict[str, list[str]] = {
    "pts":  ["pts", "points", "PTS"],
    "reb":  ["reb", "rebounds", "REB", "total_reb"],
    "ast":  ["ast", "assists", "AST"],
    "fg3m": ["fg3m", "fg3", "FG3M", "threes", "three_pointers_made"],
    "tov":  ["tov", "turnovers", "TOV"],
    "stl":  ["stl", "steals", "STL"],
    "blk":  ["blk", "blocks", "BLK"],
}


# ── Defaults helper ───────────────────────────────────────────────────────────

def _defaults_payload(as_of_date: str, reason: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {
        s: [[f, w] for f, w in pairs]
        for s, pairs in _DEFAULT_FACTOR_WEIGHTS.items()
    }
    payload["_meta"] = {
        "fitted_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_games": 0,
        "n_player_stat_obs": 0,
        "fit_method": "hardcoded_defaults",
        "min_obs_used": 0,
        "as_of_date": as_of_date,
        "reason": reason,
    }
    return payload


def _write_defaults(out_path: Path, as_of_date: str, reason: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(_defaults_payload(as_of_date, reason), indent=2))
    print(f"[FIT FACTORS] Wrote defaults → {out_path}  reason={reason}", flush=True)


# ── PMF parsing ───────────────────────────────────────────────────────────────

def _parse_pmf_value(val: Any) -> np.ndarray | None:
    """Convert a PMF column value (str, list, ndarray, dict) to ndarray."""
    try:
        if val is None:
            return None
        if isinstance(val, float) and np.isnan(val):
            return None
        if isinstance(val, np.ndarray):
            return val.astype(float)
        if isinstance(val, list):
            return np.array(val, dtype=float)
        if isinstance(val, str):
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return np.array(parsed, dtype=float)
            if isinstance(parsed, dict):
                max_k = max(int(k) for k in parsed)
                arr = np.zeros(max_k + 1, dtype=float)
                for k, v in parsed.items():
                    arr[int(k)] = float(v)
                return arr
        return None
    except Exception:
        return None


def _pit_z(pmf: np.ndarray, actual: float) -> float | None:
    """PIT z-score with mid-point continuity correction, clipped to (0.01, 0.99).

    u = CDF(y) − pmf(y)/2   (mid-point rule)
    z = Φ⁻¹(u)
    """
    try:
        if len(pmf) < 2:
            return None
        # Normalise just in case
        s = pmf.sum()
        if s < 1e-9:
            return None
        pmf = pmf / s
        k = int(round(actual))
        k = max(0, min(k, len(pmf) - 1))
        cdf_upper = float(pmf[: k + 1].sum())
        u = cdf_upper - float(pmf[k]) / 2.0
        u = float(np.clip(u, 0.01, 0.99))
        return float(scipy_stats.norm.ppf(u))
    except Exception:
        return None


# ── Delivery-date discovery ───────────────────────────────────────────────────

_PMF_FILENAMES = [
    "player_prop_pmfs_tonight_MODEL_ONLY.parquet",
    "all_props_model_only.parquet",
]


def _discover_delivery_dates(repo_root: Path, as_of_date: str) -> list[str]:
    delivery_root = repo_root / "deliveries"
    if not delivery_root.exists():
        return []
    dates: list[str] = []
    for canon_dir in sorted(delivery_root.glob("*/canonical_source")):
        date_str = canon_dir.parent.name
        if date_str > as_of_date:
            continue
        if any((canon_dir / fn).exists() for fn in _PMF_FILENAMES):
            dates.append(date_str)
    return dates


def _load_pmf_df(date_str: str, repo_root: Path) -> pd.DataFrame | None:
    canon_dir = repo_root / "deliveries" / date_str / "canonical_source"
    for fn in _PMF_FILENAMES:
        p = canon_dir / fn
        if p.exists():
            try:
                return pd.read_parquet(p)
            except Exception:
                pass
    return None


def _find_pmf_col(pmf_df: pd.DataFrame) -> str | None:
    for c in ("pmf_active", "pmf_json", "pmf_col", "pmf", "pmf_array"):
        if c in pmf_df.columns:
            return c
    return None


def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


# ── Z-score building ──────────────────────────────────────────────────────────

def _build_z_records(
    stats_df: pd.DataFrame,
    repo_root: Path,
    as_of_date: str,
    max_dates: int = 90,
) -> tuple[list[dict], int]:
    """Join player stats with PMF deliveries and compute PIT z-scores.

    Returns (z_records, n_dates_used).
    """
    dates = _discover_delivery_dates(repo_root, as_of_date)
    print(f"  Delivery dates found: {len(dates)}", flush=True)

    date_col = _first_col(stats_df, ["game_date", "slate_date", "date", "DATE"])
    if date_col is None:
        raise ValueError("No date column in player_game_stats")

    pid_col = _first_col(stats_df, ["player_id", "PERSON_ID", "person_id", "player"])
    if pid_col is None:
        raise ValueError("No player_id column in player_game_stats")

    gid_col = _first_col(stats_df, ["game_id", "GAME_ID", "game"])
    team_col = _first_col(stats_df, ["team_id", "TEAM_ID", "team", "team_abbreviation"])

    stats_df = stats_df.copy()
    stats_df["_date_str"] = pd.to_datetime(stats_df[date_col]).dt.strftime("%Y-%m-%d")
    stats_by_date: dict[str, pd.DataFrame] = dict(list(stats_df.groupby("_date_str")))

    z_records: list[dict] = []
    n_dates_used = 0

    for date_str in dates[-max_dates:]:
        if date_str not in stats_by_date:
            continue

        pmf_df = _load_pmf_df(date_str, repo_root)
        if pmf_df is None:
            continue

        pmf_col = _find_pmf_col(pmf_df)
        if pmf_col is None:
            continue

        pmf_pid = _first_col(pmf_df, ["player_id", "PERSON_ID", "person_id"])
        pmf_stat = _first_col(pmf_df, ["stat", "stat_type"])
        if pmf_pid is None or pmf_stat is None:
            continue

        pmf_team = _first_col(pmf_df, ["team_id", "TEAM_ID", "team"])
        pmf_game = _first_col(pmf_df, ["game_id", "GAME_ID"])

        # Build per-player-stat lookup for this date.
        pmf_lookup: dict[tuple[str, str], tuple[np.ndarray, str, str]] = {}
        for _, pr in pmf_df.iterrows():
            arr = _parse_pmf_value(pr[pmf_col])
            if arr is None or len(arr) < 2:
                continue
            pid = str(pr[pmf_pid])
            stat = str(pr[pmf_stat]).lower()
            team = str(pr[pmf_team]) if pmf_team else "UNK"
            gid = str(pr[pmf_game]) if pmf_game else f"{date_str}_unk"
            pmf_lookup[(pid, stat)] = (arr, team, gid)

        if not pmf_lookup:
            continue

        day_df = stats_by_date[date_str]

        for _, row in day_df.iterrows():
            pid = str(row[pid_col])
            gid_stat = str(row[gid_col]) if gid_col and pd.notna(row.get(gid_col)) else None
            team_stat = str(row[team_col]) if team_col and pd.notna(row.get(team_col)) else None

            for stat, cols in _STAT_COL_MAP.items():
                actual: float | None = None
                for c in cols:
                    if c in row.index and pd.notna(row[c]):
                        actual = float(row[c])
                        break
                if actual is None:
                    continue

                key = (pid, stat)
                if key not in pmf_lookup:
                    continue

                arr, team_pmf, gid_pmf = pmf_lookup[key]
                z = _pit_z(arr, actual)
                if z is None or not np.isfinite(z):
                    continue

                z_records.append({
                    "game_date": date_str,
                    "game_id":   gid_stat or gid_pmf,
                    "player_id": pid,
                    "team_id":   team_stat or team_pmf,
                    "stat":      stat,
                    "actual":    actual,
                    "z_score":   z,
                })

        n_dates_used += 1

    return z_records, n_dates_used


# ── Empirical correlation computation ────────────────────────────────────────

def _compute_cross_player_correlations(
    z_df: pd.DataFrame,
    min_pairs: int = 30,
) -> dict[str, dict[str, float]]:
    """Compute empirical Pearson correlations between players in the same game.

    For each stat, builds two vectors of paired z-scores:
      - same_team:  player A and player B on the same team in the same game
      - cross_team: player A and player B on opposite teams in the same game
    Each (game_id, player_A, player_B) contributes one observation pair.

    Returns {stat: {"same_team": rho, "cross_team": rho}}.
    """
    result: dict[str, dict[str, float]] = {}

    for stat, stat_df in z_df.groupby("stat"):
        same_a: list[float] = []
        same_b: list[float] = []
        cross_a: list[float] = []
        cross_b: list[float] = []

        for _gid, grp in stat_df.groupby("game_id"):
            grp = grp.set_index("player_id")[["team_id", "z_score"]]
            pids = list(grp.index)
            if len(pids) < 2:
                continue
            for i in range(len(pids)):
                for j in range(i + 1, len(pids)):
                    za = float(grp.loc[pids[i], "z_score"])
                    zb = float(grp.loc[pids[j], "z_score"])
                    ta = str(grp.loc[pids[i], "team_id"])
                    tb = str(grp.loc[pids[j], "team_id"])
                    if ta != "UNK" and ta == tb:
                        same_a.append(za)
                        same_b.append(zb)
                    else:
                        cross_a.append(za)
                        cross_b.append(zb)

        stat_result: dict[str, float] = {}

        if len(same_a) >= min_pairs:
            r = float(np.corrcoef(same_a, same_b)[0, 1])
            if np.isfinite(r):
                stat_result["same_team"] = r

        if len(cross_a) >= min_pairs:
            r = float(np.corrcoef(cross_a, cross_b)[0, 1])
            if np.isfinite(r):
                stat_result["cross_team"] = r

        if stat_result:
            result[str(stat)] = stat_result

    return result


def _compute_minutes_correlation(z_df: pd.DataFrame) -> dict[str, float]:
    """For each stat, compute corr(z_stat, player_mean_z_across_stats).

    The player's mean z-score across stats in a game is a proxy for their
    minutes played.  Returns values clipped to [0.10, 0.40].
    """
    player_mean = (
        z_df.groupby(["game_date", "player_id"])["z_score"]
        .mean()
        .rename("player_mean_z")
    )
    merged = z_df.join(player_mean, on=["game_date", "player_id"])
    result: dict[str, float] = {}

    for stat, grp in merged.groupby("stat"):
        valid = grp[["z_score", "player_mean_z"]].dropna()
        if len(valid) < 50:
            result[str(stat)] = 0.20
            continue
        r = float(np.corrcoef(valid["z_score"], valid["player_mean_z"])[0, 1])
        result[str(stat)] = float(np.clip(r if np.isfinite(r) else 0.20, 0.10, 0.40))

    return result


# ── Constrained LS factor weight fitting ─────────────────────────────────────

def _group_sq(pairs: list[tuple[str, float]], factor_set: frozenset[str]) -> float:
    return sum(float(w) ** 2 for f, w in pairs if f in factor_set)


def _scale_group(
    pairs: list[tuple[str, float]],
    factor_set: frozenset[str],
    target_sq: float,
) -> list[tuple[str, float]]:
    current_sq = _group_sq(pairs, factor_set)
    if current_sq < 1e-10 or target_sq <= 0.0:
        return pairs
    scale = float(np.sqrt(target_sq / current_sq))
    return [(f, float(w) * scale if f in factor_set else float(w)) for f, w in pairs]


def _fit_weights_for_stat(
    stat: str,
    cross_corrs: dict[str, dict[str, float]],
    minutes_corr: dict[str, float],
) -> list[tuple[str, float]]:
    """Fit one stat's factor weights via constrained LS.

    Correlation model:
      rho_cross_team = w_game²
      rho_same_team  = w_game² + w_team² − w_minutes² × C_dirichlet

    Solving gives:
      w_game    = √max(rho_cross_team, 0)
      w_team    = √max(rho_same_team − w_game² + w_min² × C_dir, 0.0001)
      w_minutes = clip(corr(z_stat, player_mean_z), 0.10, 0.40)

    Remaining variance is kept from defaults and all weights are normalised
    so sum(w²) ≤ 0.95.
    """
    default_pairs = list(_DEFAULT_FACTOR_WEIGHTS.get(stat, []))
    if not default_pairs:
        return default_pairs

    stat_corrs = cross_corrs.get(stat, {})
    rho_cross = stat_corrs.get("cross_team")
    rho_same  = stat_corrs.get("same_team")
    w_min     = minutes_corr.get(stat, 0.20)

    if rho_cross is None and rho_same is None:
        return default_pairs

    pairs = list(default_pairs)

    # ── Scale game-level factors ──────────────────────────────────────────────
    if rho_cross is not None:
        target_game_sq = max(float(rho_cross), 0.0)
        if target_game_sq > 0.0:
            pairs = _scale_group(pairs, _GAME_FACTORS, target_game_sq)

    # ── Scale team-level factors ──────────────────────────────────────────────
    if rho_same is not None:
        game_sq_now = _group_sq(pairs, _GAME_FACTORS)
        target_team_sq = max(
            float(rho_same) - game_sq_now + w_min ** 2 * _C_DIRICHLET,
            0.0001,
        )
        pairs = _scale_group(pairs, _TEAM_FACTORS, target_team_sq)

    # ── Set player_minutes_z directly ────────────────────────────────────────
    pairs = [
        (_MINUTES_FACTOR, w_min) if f == _MINUTES_FACTOR else (f, float(w))
        for f, w in pairs
    ]

    # ── Normalise so sum(w²) ≤ 0.95 ──────────────────────────────────────────
    total_sq = sum(float(w) ** 2 for _, w in pairs)
    if total_sq > 0.95:
        scale = float(np.sqrt(0.95 / total_sq))
        pairs = [(f, float(w) * scale) for f, w in pairs]

    return [(f, round(float(w), 4)) for f, w in pairs]


# ── Main fitting pipeline ─────────────────────────────────────────────────────

def _fit_from_historical(
    stats_df: pd.DataFrame,
    repo_root: Path,
    as_of_date: str,
    min_obs_per_stat: int = 50,
) -> dict[str, Any]:
    print("  Building PIT z-scores from historical PMF deliveries …", flush=True)

    z_records, n_dates = _build_z_records(stats_df, repo_root, as_of_date)

    if not z_records:
        raise ValueError("No PIT z-score records computed (no date overlap or no PMF delivery found)")

    z_df = pd.DataFrame(z_records)
    stat_counts = z_df.groupby("stat").size()
    n_games = int(z_df["game_id"].nunique())

    print(f"  Dates with both PMFs and stats: {n_dates}", flush=True)
    print(f"  Unique games: {n_games}  total z-records: {len(z_df)}", flush=True)
    for stat in sorted(_DEFAULT_FACTOR_WEIGHTS):
        n = int(stat_counts.get(stat, 0))
        print(f"    {stat}: {n} obs", flush=True)

    print("  Computing cross-player Pearson correlations …", flush=True)
    cross_corrs  = _compute_cross_player_correlations(z_df)
    minutes_corr = _compute_minutes_correlation(z_df)

    for stat in sorted(cross_corrs):
        parts = [f"{k}={v:.3f}" for k, v in sorted(cross_corrs[stat].items())]
        print(f"    {stat}: " + "  ".join(parts), flush=True)

    print("  Fitting factor weights …", flush=True)
    fitted: dict[str, list[list]] = {}
    fitted_stats: list[str] = []

    for stat in sorted(_DEFAULT_FACTOR_WEIGHTS):
        n_obs = int(stat_counts.get(stat, 0))
        if n_obs < min_obs_per_stat:
            print(f"    {stat}: insufficient obs ({n_obs} < {min_obs_per_stat}), using defaults",
                  flush=True)
            fitted[stat] = [[f, w] for f, w in _DEFAULT_FACTOR_WEIGHTS[stat]]
        else:
            pairs = _fit_weights_for_stat(stat, cross_corrs, minutes_corr)
            fitted[stat] = [[f, w] for f, w in pairs]
            fitted_stats.append(stat)
            w_game_eff = float(np.sqrt(_group_sq(pairs, _GAME_FACTORS)))
            w_team_eff = float(np.sqrt(_group_sq(pairs, _TEAM_FACTORS)))
            w_min_eff  = minutes_corr.get(stat, 0.20)
            print(
                f"    {stat}: FITTED  "
                f"w_game={w_game_eff:.3f}  w_team={w_team_eff:.3f}  w_minutes={w_min_eff:.3f}",
                flush=True,
            )

    return {
        **fitted,
        "_meta": {
            "fitted_at_utc":         datetime.now(timezone.utc).isoformat(),
            "n_games":               n_games,
            "n_player_stat_obs":     len(z_df),
            "fit_method":            "pit_z_pearson_constrained_ls",
            "min_obs_used":          min_obs_per_stat,
            "as_of_date":            as_of_date,
            "n_dates_scanned":       n_dates,
            "fitted_stats":          sorted(fitted_stats),
            "empirical_correlations": {
                s: {k: round(v, 4) for k, v in d.items()}
                for s, d in sorted(cross_corrs.items())
            },
        },
    }


# ── OOF data path (primary) ───────────────────────────────────────────────────

def _pit_z_array(pmf: np.ndarray, actual: int) -> float | None:
    """Mid-point PIT: Φ⁻¹(CDF(y) − pmf[y]/2) from a numpy PMF array."""
    from scipy.stats import norm as _norm
    try:
        k = max(0, min(int(round(actual)), len(pmf) - 1))
        cdf_at_k = float(pmf[:k + 1].sum())
        u = cdf_at_k - float(pmf[k]) / 2.0
        u = max(1e-6, min(u, 1.0 - 1e-6))
        return float(_norm.ppf(u))
    except Exception:
        return None


def _load_z_from_oof(oof_path: Path, as_of_date: str) -> list[dict]:
    """Load OOF PMF predictions and compute PIT z-scores.

    Works with data/oof_stat_pmf_predictions.parquet which already has
    pmf (numpy array) and outcome in each row — no delivery PMF join needed.
    """
    print(f"  Loading OOF predictions from {oof_path.name} ...", flush=True)
    oof = pd.read_parquet(oof_path)

    if "game_date" in oof.columns:
        oof = oof[oof["game_date"].astype(str) <= as_of_date]

    if oof.empty:
        raise ValueError("OOF data empty after date filter")

    z_records: list[dict] = []
    for _, row in oof.iterrows():
        pmf = row.get("pmf")
        if not isinstance(pmf, np.ndarray) or len(pmf) == 0:
            continue
        try:
            actual = int(round(float(row["outcome"])))
        except (TypeError, ValueError):
            continue
        z = _pit_z_array(pmf, actual)
        if z is None or not np.isfinite(z):
            continue
        z_records.append({
            "game_date": str(row.get("game_date", "")),
            "game_id":   str(row.get("game_id", "")),
            "player_id": str(row.get("player_id", "")),
            "team_id":   str(row.get("team_id", "UNK")),
            "stat":      str(row.get("stat", "")).lower(),
            "actual":    float(actual),
            "z_score":   z,
        })

    print(f"  {len(z_records)} valid PIT z-scores from OOF data", flush=True)
    return z_records


def _fit_from_z_records(
    z_records: list[dict],
    as_of_date: str,
    *,
    min_obs_per_stat: int = 50,
    source: str = "unknown",
) -> dict:
    """Fit factor weights from a pre-computed list of z_score records.

    Shares the weight-fitting logic with _fit_from_historical but accepts
    pre-computed z_records (e.g. from OOF data) instead of raw stats + delivery PMFs.
    """
    z_df = pd.DataFrame(z_records)
    n_games = int(z_df["game_id"].nunique())

    stat_counts = z_df.groupby("stat").size()
    print(f"  Observations per stat: {dict(stat_counts)}", flush=True)

    cross_corrs = _compute_cross_player_correlations(z_df)
    minutes_corr = _compute_minutes_correlation(z_df)

    print("  Empirical cross-player correlations:", flush=True)
    for s in sorted(cross_corrs):
        parts = [f"{k}={v:.3f}" for k, v in sorted(cross_corrs[s].items())]
        print(f"    {s}: " + "  ".join(parts), flush=True)

    print("  Fitting factor weights …", flush=True)
    fitted: dict[str, list[list]] = {}
    fitted_stats: list[str] = []

    for stat in sorted(_DEFAULT_FACTOR_WEIGHTS):
        n_obs = int(stat_counts.get(stat, 0))
        if n_obs < min_obs_per_stat:
            print(f"    {stat}: insufficient obs ({n_obs} < {min_obs_per_stat}), using defaults",
                  flush=True)
            fitted[stat] = [[f, w] for f, w in _DEFAULT_FACTOR_WEIGHTS[stat]]
        else:
            pairs = _fit_weights_for_stat(stat, cross_corrs, minutes_corr)
            fitted[stat] = [[f, w] for f, w in pairs]
            fitted_stats.append(stat)
            w_game_eff = float(np.sqrt(_group_sq(pairs, _GAME_FACTORS)))
            w_team_eff = float(np.sqrt(_group_sq(pairs, _TEAM_FACTORS)))
            w_min_eff  = minutes_corr.get(stat, 0.20)
            print(
                f"    {stat}: FITTED  "
                f"w_game={w_game_eff:.3f}  w_team={w_team_eff:.3f}  w_minutes={w_min_eff:.3f}",
                flush=True,
            )

    return {
        **fitted,
        "_meta": {
            "fitted_at_utc":          datetime.now(timezone.utc).isoformat(),
            "data_source":            source,
            "n_games":                n_games,
            "n_player_stat_obs":      len(z_df),
            "fit_method":             "pit_z_pearson_constrained_ls",
            "min_obs_used":           min_obs_per_stat,
            "as_of_date":             as_of_date,
            "n_dates_scanned":        int(z_df["game_date"].nunique()),
            "fitted_stats":           sorted(fitted_stats),
            "empirical_correlations": {
                s: {k: round(v, 4) for k, v in d.items()}
                for s, d in sorted(cross_corrs.items())
            },
        },
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--as-of-date", default=None,
                    help="As-of date YYYY-MM-DD (default: today)")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument("--min-obs-per-stat", type=int, default=50,
                    help="Minimum PIT z-score rows per stat to fit weights (default: 50)")
    args = ap.parse_args()

    as_of_date = args.as_of_date or _date.today().isoformat()
    repo_root  = Path(args.repo_root).resolve()
    out_path   = (
        repo_root / "artifacts" / "models" / "sgp" / "factor_weights"
        / "factor_weights_latest.json"
    )

    print(f"[FIT FACTORS] as_of_date={as_of_date}  repo_root={repo_root}", flush=True)

    # ── Path 1: OOF PMF predictions (preferred — already has PMF + outcome) ────
    oof_path = repo_root / "data" / "oof_stat_pmf_predictions.parquet"
    if oof_path.exists():
        try:
            z_records_oof = _load_z_from_oof(oof_path, as_of_date)
            if z_records_oof:
                result = _fit_from_z_records(
                    z_records_oof, as_of_date,
                    min_obs_per_stat=args.min_obs_per_stat,
                    source="oof_stat_pmf_predictions.parquet",
                )
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(json.dumps(result, indent=2))
                meta = result["_meta"]
                fitted = meta["fitted_stats"]
                print("\n[FIT FACTORS] Done (OOF path).", flush=True)
                print(f"  Output:  {out_path}", flush=True)
                print(f"  Games:   {meta['n_games']}", flush=True)
                print(f"  Obs:     {meta['n_player_stat_obs']}", flush=True)
                print(f"  Fitted:  {', '.join(fitted) or 'none'}", flush=True)
                return 0
        except Exception as exc:
            print(f"  OOF path failed ({exc}); trying player_game_stats", flush=True)

    # ── Path 2: player_game_stats.parquet + delivery PMFs ─────────────────────
    stats_path = repo_root / "data" / "player_game_stats.parquet"
    if not stats_path.exists():
        _write_defaults(out_path, as_of_date, reason="player_game_stats.parquet_not_found")
        return 0

    try:
        stats_df = pd.read_parquet(stats_path)
    except Exception as exc:
        _write_defaults(out_path, as_of_date, reason=f"could_not_read_stats:{exc}")
        return 0

    if stats_df.empty:
        _write_defaults(out_path, as_of_date, reason="player_game_stats_empty")
        return 0

    print(f"  Loaded {len(stats_df)} rows from player_game_stats.parquet", flush=True)

    try:
        result = _fit_from_historical(
            stats_df, repo_root, as_of_date,
            min_obs_per_stat=args.min_obs_per_stat,
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2))

        meta = result["_meta"]
        fitted = meta["fitted_stats"]
        print("\n[FIT FACTORS] Done.", flush=True)
        print(f"  Output:            {out_path}", flush=True)
        print(f"  Dates with data:   {meta['n_dates_scanned']}", flush=True)
        print(f"  Games:             {meta['n_games']}", flush=True)
        print(f"  Total z-records:   {meta['n_player_stat_obs']}", flush=True)
        print(f"  Fitted stats:      {', '.join(fitted) or 'none (all defaults)'}", flush=True)

    except Exception as exc:
        print(f"  WARNING: Fitting failed ({exc}); writing defaults.", file=sys.stderr)
        _write_defaults(out_path, as_of_date, reason=f"fitting_exception:{exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
