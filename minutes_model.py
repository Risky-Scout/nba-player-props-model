#!/usr/bin/env python3
from __future__ import annotations
"""
minutes_model.py — NBA Player Props Model: Standalone Minutes Engine
VERSION: 2026-03-09-v12

Dedicated probabilistic minutes model. Trained independently of the stat
models. Outputs a full minutes distribution (Q10–Q90) for each player-game,
which is then fed as first-class input features into every downstream stat
model (pts, reb, ast, fg3m, stl, blk, tov, combos).

Why a standalone minutes model:
  Minutes are the multiplier for every counting stat. A player projected for
  28 minutes has a fundamentally different distribution than the same player
  projected for 34 minutes. Predicting minutes implicitly through stat-level
  rolling features is insufficient — the model cannot separate "fewer points
  because of lower efficiency" from "fewer points because of fewer minutes."

  A dedicated model also captures:
  - Injury-driven role redistribution (teammate out → more minutes)
  - Load management risk (late-season rest for playoff teams)
  - Blowout risk (large spread → garbage time or early exit)
  - Starter vs. bench role changes within a season

Architecture:
  - 11 LightGBM quantile regressors, Q10–Q90, pinball loss
  - Temporal holdout validation (date-split, not random)
  - Feature set purpose-built for minutes prediction (22 features)
  - Saves to model_cache/minutes_q{xx}.pkl

Outputs fed into feature_engineering.py:
  exp_mp          — expected minutes (Q50 prediction)
  mp_q10          — 10th percentile (low floor)
  mp_q25          — 25th percentile
  mp_q75          — 75th percentile
  mp_q90          — 90th percentile (high ceiling)
  mp_vol          — volatility: IQR / median (higher = less reliable)
  mp_pred_floor   — Q10 prediction (low end)
  mp_pred_ceiling — Q90 prediction (high end)
"""

import logging
import warnings
from pathlib import Path
from datetime import datetime

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

MODEL_DIR = Path("model_cache")
MODEL_DIR.mkdir(exist_ok=True)

QUANTILES = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.90]

# Minimum minutes to count as a real appearance (filters DNPs)
MIN_MINUTES_THRESHOLD = 5.0

# Minimum appearances to build features
MIN_APPEARANCES = 10

LGB_MINUTES = dict(
    objective="quantile",
    metric="quantile",
    n_estimators=600,
    learning_rate=0.025,
    num_leaves=31,
    max_depth=6,
    feature_fraction=0.80,
    bagging_fraction=0.80,
    bagging_freq=1,
    reg_alpha=0.5,
    reg_lambda=2.0,
    min_child_samples=40,
    verbose=-1,
)

HOLDOUT_FRAC = 0.15

# ── Feature names (must match build_minutes_features output exactly) ──────────
MINUTES_FEATURE_NAMES = [
    # Rolling minutes history
    "mp_mean_last3",
    "mp_mean_last5",
    "mp_mean_last10",
    "mp_median_last10",
    "mp_mean_season",
    "mp_ewma",
    "mp_std_last10",
    "mp_cv_last10",
    "mp_trend_3v10",
    "mp_floor_last10",
    "mp_ceiling_last10",
    # Role features
    "starter_rate_last10",
    "games_30plus_last10",
    "games_35plus_last10",
    "games_20minus_last10",
    "role_stability_index",
    # Injury / opportunity
    "num_teammates_inactive",
    "vacated_teammate_minutes",
    # Game context
    "is_home",
    "days_rest",
    "b2b_flag",
    "implied_total",
]


# ── Feature builder ────────────────────────────────────────────────────────────

def build_minutes_features(
    prior_stats: pd.DataFrame,
    game_context: dict,
    is_home: int,
    target_date: str,
    team_id: int,
    all_stats_df: pd.DataFrame,
    injury_map: dict,
) -> dict:
    """
    Build the feature vector for one player-game minutes prediction.
    All inputs strictly prior to target_date — zero leakage.

    Returns flat dict with keys matching MINUTES_FEATURE_NAMES.
    NaN where data is unavailable (LightGBM handles natively).
    """
    f = {k: np.nan for k in MINUTES_FEATURE_NAMES}

    df  = prior_stats.sort_values("game_date").reset_index(drop=True)
    tdt = pd.Timestamp(target_date)

    # Filter to real appearances only
    if "min" not in df.columns or df.empty:
        return f

    min_arr_all = df["min"].values.astype(float)
    real_mask   = min_arr_all >= MIN_MINUTES_THRESHOLD
    df_real     = df[real_mask].reset_index(drop=True)

    if len(df_real) < MIN_APPEARANCES:
        return f

    mp = df_real["min"].values.astype(float)
    n  = len(mp)

    # ── Rolling minutes windows ───────────────────────────────────────────────
    def _safe(fn, arr):
        try:
            v = fn(arr)
            return float(v) if np.isfinite(v) else np.nan
        except Exception:
            return np.nan

    last3  = mp[max(0, n-3):]
    last5  = mp[max(0, n-5):]
    last10 = mp[max(0, n-10):]

    f["mp_mean_last3"]    = _safe(np.mean,   last3)
    f["mp_mean_last5"]    = _safe(np.mean,   last5)
    f["mp_mean_last10"]   = _safe(np.mean,   last10)
    f["mp_median_last10"] = _safe(np.median, last10)
    f["mp_std_last10"]    = _safe(np.std,    last10)

    # EWMA — last game weighted at 30%
    weights = np.array([(1 - 0.3) ** i for i in range(len(mp)-1, -1, -1)])
    weights = weights / weights.sum()
    f["mp_ewma"] = _safe(lambda a: float(np.dot(weights, a)), mp)

    # Coefficient of variation — measures role consistency
    mean10 = f["mp_mean_last10"]
    std10  = f["mp_std_last10"]
    if mean10 and std10 and np.isfinite(mean10) and mean10 > 0:
        f["mp_cv_last10"] = std10 / mean10
    else:
        f["mp_cv_last10"] = np.nan

    # Season mean (all real appearances this season)
    if "season" in df_real.columns:
        max_season  = df_real["season"].max()
        season_mp   = df_real[df_real["season"] == max_season]["min"].values.astype(float)
        season_real = season_mp[season_mp >= MIN_MINUTES_THRESHOLD]
        if len(season_real) >= 3:
            # EWMA-weighted season mean
            sw = np.array([(1 - 0.1) ** i for i in range(len(season_real)-1, -1, -1)])
            sw = sw / sw.sum()
            f["mp_mean_season"] = float(np.dot(sw, season_real))
        else:
            f["mp_mean_season"] = f["mp_mean_last10"]
    else:
        f["mp_mean_season"] = f["mp_mean_last10"]

    # Trend: recent (last3) vs medium-term (last10)
    m3  = f["mp_mean_last3"]
    m10 = f["mp_mean_last10"]
    if m3 and m10 and np.isfinite(m3) and np.isfinite(m10) and m10 > 0:
        f["mp_trend_3v10"] = m3 / m10
    else:
        f["mp_trend_3v10"] = np.nan

    # Floor (P10) and ceiling (P90) over last 10
    if len(last10) >= 5:
        f["mp_floor_last10"]   = float(np.percentile(last10, 10))
        f["mp_ceiling_last10"] = float(np.percentile(last10, 90))

    # ── Role features ─────────────────────────────────────────────────────────
    n10 = len(last10)
    if n10 > 0:
        f["starter_rate_last10"]  = float(np.mean(last10 >= 28))
        f["games_30plus_last10"]  = float(np.mean(last10 >= 30))
        f["games_35plus_last10"]  = float(np.mean(last10 >= 35))
        f["games_20minus_last10"] = float(np.mean(last10 < 20))

    mean10_val = f["mp_mean_last10"]
    cv10_val   = f["mp_cv_last10"]
    if (mean10_val and cv10_val
            and np.isfinite(mean10_val) and np.isfinite(cv10_val)):
        f["role_stability_index"] = max(0.0, 1.0 - cv10_val)
    else:
        f["role_stability_index"] = np.nan

    # ── Injury / vacated opportunity ──────────────────────────────────────────
    if injury_map and team_id and all_stats_df is not None and not all_stats_df.empty:
        try:
            # Get teammates from all_stats_df — most recent game within 7 days
            recent_cutoff = tdt - pd.Timedelta(days=7)
            teammates = all_stats_df[
                (all_stats_df["team_id"] == team_id) &
                (all_stats_df["game_date"] >= recent_cutoff) &
                (all_stats_df["game_date"] < tdt)
            ]["player_id"].unique()

            n_inactive   = 0
            vacated_min  = 0.0

            for tm_pid in teammates:
                tm_pid_int = int(tm_pid)
                inj = injury_map.get(tm_pid_int, {})
                status = str(inj.get("status","")).lower().strip()

                if status in ("out", "inactive", "dnp"):
                    n_inactive += 1
                    # Estimate their typical minutes
                    tm_data = all_stats_df[
                        (all_stats_df["player_id"] == tm_pid_int) &
                        (all_stats_df["game_date"] < tdt) &
                        (all_stats_df["min"] >= MIN_MINUTES_THRESHOLD)
                    ].tail(10)
                    if not tm_data.empty:
                        vacated_min += float(tm_data["min"].mean())

            f["num_teammates_inactive"]   = float(n_inactive)
            f["vacated_teammate_minutes"] = float(vacated_min)

        except Exception:
            f["num_teammates_inactive"]   = 0.0
            f["vacated_teammate_minutes"] = 0.0
    else:
        f["num_teammates_inactive"]   = 0.0
        f["vacated_teammate_minutes"] = 0.0

    # ── Game context ──────────────────────────────────────────────────────────
    f["is_home"] = float(is_home)

    # Days rest
    if "game_date" in df_real.columns and len(df_real) > 0:
        last_game_date = pd.Timestamp(df_real.iloc[-1]["game_date"])
        days_rest      = (tdt - last_game_date).days
        f["days_rest"] = float(min(days_rest, 7))  # cap at 7
        f["b2b_flag"]  = float(days_rest <= 1)
    else:
        f["days_rest"] = np.nan
        f["b2b_flag"]  = np.nan

    # Game total (pace proxy — high-total games run faster, more possessions,
    # which slightly inflates minutes usage in close games)
    total = game_context.get("total_value") or game_context.get("game_total")
    f["implied_total"] = float(total) if total and np.isfinite(float(total)) else np.nan

    return f


# ── Training table ─────────────────────────────────────────────────────────────

def build_minutes_training_table(
    stats_df: pd.DataFrame,
    odds_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build training matrix for the minutes model.
    One row per (player, game) where target = actual minutes played.
    Filters to real appearances (>= MIN_MINUTES_THRESHOLD).
    """
    logger.info("Building minutes training table...")

    from collections import defaultdict
    from bdl_client import build_game_context_map

    ctx_map = build_game_context_map(
        odds_df.to_dict("records")
    ) if odds_df is not None and not odds_df.empty else {}

    all_rows = []
    skipped  = 0
    players  = list(stats_df.groupby("player_id"))

    for idx, (player_id, pdata) in enumerate(players):
        pdata = pdata.sort_values("game_date").reset_index(drop=True)

        # Need at least MIN_APPEARANCES real games to compute features
        real_games = pdata[pdata["min"] >= MIN_MINUTES_THRESHOLD]
        if len(real_games) < MIN_APPEARANCES + 5:
            continue

        for i in range(len(pdata)):
            cur = pdata.iloc[i]

            # Target: actual minutes this game
            actual_mp = float(cur.get("min", 0) or 0)
            if actual_mp < MIN_MINUTES_THRESHOLD:
                continue  # Skip DNPs as training targets

            prior = pdata.iloc[:i]
            if len(prior[prior["min"] >= MIN_MINUTES_THRESHOLD]) < MIN_APPEARANCES:
                continue

            gid     = int(cur["game_id"])
            tid     = int(cur["team_id"] or 0)
            hid     = int(cur["home_team_id"] or 0)
            is_home = int(tid == hid)
            td      = str(cur["game_date"])[:10]
            ctx     = ctx_map.get(gid, {})

            try:
                feat = build_minutes_features(
                    prior_stats  = prior,
                    game_context = ctx,
                    is_home      = is_home,
                    target_date  = td,
                    team_id      = tid,
                    all_stats_df = stats_df,
                    injury_map   = {},  # historical: no injury snapshots
                )
            except Exception as e:
                logger.debug(f"Minutes feature error p={player_id} g={gid}: {e}")
                skipped += 1
                continue

            row = {
                **feat,
                "player_id": int(player_id),
                "game_id":   gid,
                "game_date": cur["game_date"],
                "actual_mp": actual_mp,
            }
            all_rows.append(row)

        if (idx + 1) % 100 == 0:
            logger.info(f"  {idx+1}/{len(players)} players | {len(all_rows)} rows")

    df = pd.DataFrame(all_rows)
    if df.empty:
        logger.error(f"Minutes training table EMPTY. skipped={skipped}")
    else:
        logger.info(
            f"Minutes training table: {len(df)} rows | "
            f"{df['player_id'].nunique()} players | skipped={skipped}"
        )
    return df


# ── Temporal split ─────────────────────────────────────────────────────────────

def _temporal_split_idx(game_dates: np.ndarray, holdout_frac: float) -> int:
    dates  = pd.to_datetime(game_dates)
    # Fix: DatetimeIndex.quantile() removed in newer pandas
    # Convert to int64 nanoseconds, compute quantile, convert back
    cutoff = pd.Timestamp(int(np.quantile(dates.astype(np.int64), 1.0 - holdout_frac)))
    return int(np.searchsorted(dates, cutoff))


# ── Training ───────────────────────────────────────────────────────────────────

def train_minutes_model(
    stats_df: pd.DataFrame,
    odds_df: pd.DataFrame,
) -> dict:
    """
    Train 11 quantile LightGBM models for minutes prediction.
    Saves all models and feature list to model_cache/.
    Returns calibration report dict.
    """
    logger.info("=" * 60)
    logger.info("Minutes Model Training — VERSION 2026-03-09-v12")
    logger.info("=" * 60)

    training_df = build_minutes_training_table(stats_df, odds_df)
    if training_df.empty:
        logger.error("Cannot train minutes model — empty training table")
        return {}

    df = training_df.sort_values("game_date").reset_index(drop=True)

    feat_cols = [c for c in MINUTES_FEATURE_NAMES if c in df.columns]
    missing   = [c for c in MINUTES_FEATURE_NAMES if c not in df.columns]
    if missing:
        logger.warning(f"  Missing feature columns: {missing}")

    X = df[feat_cols].values.astype(float)
    y = df["actual_mp"].values.astype(float)
    n = len(X)

    # Temporal split
    tr_n = _temporal_split_idx(df["game_date"].values, HOLDOUT_FRAC)
    if tr_n < 500 or (n - tr_n) < 100:
        logger.warning(
            f"  Temporal split too small (tr={tr_n}, ho={n-tr_n}) "
            f"— falling back to index split"
        )
        tr_n = int(n * (1.0 - HOLDOUT_FRAC))

    holdout_date = str(df.iloc[tr_n]["game_date"])[:10] if tr_n < n else "N/A"
    logger.info(
        f"  {n} rows | {len(feat_cols)} features | "
        f"train={tr_n} holdout={n-tr_n} (cutoff={holdout_date})"
    )

    holdout_preds = {}
    for q in QUANTILES:
        params = {**LGB_MINUTES, "alpha": q}

        # Calibration model
        m_cal = lgb.LGBMRegressor(**params)
        m_cal.fit(X[:tr_n], y[:tr_n])
        holdout_preds[q] = m_cal.predict(X[tr_n:])

        # Final model on full data
        m_final = lgb.LGBMRegressor(**params)
        m_final.fit(X, y)
        joblib.dump(m_final, MODEL_DIR / f"minutes_q{int(q*100):02d}.pkl")
        logger.debug(f"  Saved minutes_q{int(q*100):02d}.pkl")

    joblib.dump(feat_cols, MODEL_DIR / "minutes_features.pkl")

    # ── Calibration report ────────────────────────────────────────────────────
    actuals_ho = y[tr_n:]
    cal        = {}
    logger.info(f"  Calibration (holdout from {holdout_date}):")

    graded_errors = []
    for q in QUANTILES:
        preds    = holdout_preds[q]
        emp_q    = float(np.mean(actuals_ho <= preds))
        error    = abs(emp_q - q)
        graded_errors.append(error)
        cal[q]   = {"empirical_q": round(emp_q, 4), "error": round(error, 4)}
        flag     = "⚠" if error > 0.05 else "✓"
        logger.info(
            f"    {flag} Q{int(q*100):02d}: "
            f"empirical={emp_q:.3f}  target={q:.2f}  err={error:.3f}"
        )

    mae = float(np.mean(np.abs(holdout_preds[0.50] - actuals_ho)))
    logger.info(f"  Holdout MAE (Q50): {mae:.3f} minutes")

    # Minutes-specific diagnostics
    q50_ho  = holdout_preds[0.50]
    q25_ho  = holdout_preds[0.25]
    q75_ho  = holdout_preds[0.75]
    iqr_ho  = q75_ho - q25_ho
    coverage_50 = float(np.mean((actuals_ho >= q25_ho) & (actuals_ho <= q75_ho)))
    logger.info(f"  50% interval coverage: {coverage_50:.1%} (target 50%)")

    # Blowout/DNP detection — how well does Q10 capture sub-20-minute games?
    sub20_mask  = actuals_ho < 20
    q10_ho      = holdout_preds[0.10]
    sub20_pct   = float(np.mean(sub20_mask))
    q10_capture = float(np.mean(q10_ho[sub20_mask] < 20)) if sub20_mask.sum() > 0 else 0.0
    logger.info(
        f"  Sub-20min games: {sub20_pct:.1%} of holdout | "
        f"Q10 captures: {q10_capture:.1%}"
    )

    # Feature importance
    m50 = lgb.LGBMRegressor(**{**LGB_MINUTES, "alpha": 0.50})
    m50.fit(X, y)
    fi = pd.DataFrame({
        "feature":    feat_cols,
        "importance": m50.feature_importances_,
    }).sort_values("importance", ascending=False)
    fi.to_csv(MODEL_DIR / "minutes_feature_importance.csv", index=False)
    logger.info(f"  Top-5 features: {fi['feature'].values[:5].tolist()}")

    result = {
        "version":       "2026-03-09-v12",
        "trained_at":    datetime.utcnow().isoformat(),
        "n_train":       tr_n,
        "n_holdout":     n - tr_n,
        "holdout_cutoff": holdout_date,
        "feature_count": len(feat_cols),
        "mae_q50":       round(mae, 4),
        "max_cal_error": round(max(graded_errors), 4),
        "coverage_50pct": round(coverage_50, 4),
        "sub20_capture": round(q10_capture, 4),
        "calibration":   {str(k): v for k, v in cal.items()},
    }

    import json
    with open(MODEL_DIR / "minutes_training_meta.json", "w") as f_out:
        json.dump(result, f_out, indent=2, default=str)
    logger.info(f"  Minutes model saved → model_cache/minutes_q*.pkl")

    return result


# ── Inference ──────────────────────────────────────────────────────────────────

_CACHED_MINUTES_MODELS = None

def load_minutes_model() -> dict | None:
    """
    Load minutes quantile models from model_cache/.
    Caches in module-level dict after first load.
    Returns None if models not found.
    """
    global _CACHED_MINUTES_MODELS
    if _CACHED_MINUTES_MODELS is not None:
        return _CACHED_MINUTES_MODELS

    fcols_path = MODEL_DIR / "minutes_features.pkl"
    if not fcols_path.exists():
        return None

    feat_cols = joblib.load(fcols_path)
    qmods     = {}
    for q in QUANTILES:
        p = MODEL_DIR / f"minutes_q{int(q*100):02d}.pkl"
        if p.exists():
            qmods[q] = joblib.load(p)

    if not qmods:
        return None

    _CACHED_MINUTES_MODELS = {"quantile_models": qmods, "features": feat_cols}
    return _CACHED_MINUTES_MODELS


def predict_minutes(
    prior_stats: pd.DataFrame,
    game_context: dict,
    is_home: int,
    target_date: str,
    team_id: int,
    all_stats_df: pd.DataFrame,
    injury_map: dict,
    minutes_models: dict | None = None,
) -> dict:
    """
    Predict minutes distribution for one player-game.

    Returns dict with keys:
      exp_mp          — expected minutes (Q50)
      mp_q10          — 10th percentile
      mp_q25          — 25th percentile
      mp_q75          — 75th percentile
      mp_q90          — 90th percentile
      mp_vol          — volatility: IQR / median (0 = perfectly consistent)
      mp_pred_floor   — Q10 (low end, blowout/rest scenario)
      mp_pred_ceiling — Q90 (high end, close game / extra minutes)

    Falls back to rolling mean if models unavailable.
    """
    NULL = {
        "exp_mp":          np.nan,
        "mp_q10":          np.nan,
        "mp_q25":          np.nan,
        "mp_q75":          np.nan,
        "mp_q90":          np.nan,
        "mp_vol":          np.nan,
        "mp_pred_floor":   np.nan,
        "mp_pred_ceiling": np.nan,
    }

    # Load models if not passed in
    mods = minutes_models or load_minutes_model()

    if mods is None:
        # Graceful fallback: use rolling mean ± std from prior stats
        if prior_stats.empty or "min" not in prior_stats.columns:
            return NULL
        real = prior_stats[prior_stats["min"] >= MIN_MINUTES_THRESHOLD]["min"].values.astype(float)
        if len(real) < 3:
            return NULL
        last10 = real[max(0, len(real)-10):]
        mu     = float(np.mean(last10))
        sigma  = float(np.std(last10)) if len(last10) > 1 else 3.0
        return {
            "exp_mp":          round(mu, 2),
            "mp_q10":          round(max(0, mu - 1.28 * sigma), 2),
            "mp_q25":          round(max(0, mu - 0.67 * sigma), 2),
            "mp_q75":          round(mu + 0.67 * sigma, 2),
            "mp_q90":          round(mu + 1.28 * sigma, 2),
            "mp_vol":          round(sigma / mu, 3) if mu > 0 else np.nan,
            "mp_pred_floor":   round(max(0, mu - 1.28 * sigma), 2),
            "mp_pred_ceiling": round(mu + 1.28 * sigma, 2),
        }

    feat = build_minutes_features(
        prior_stats  = prior_stats,
        game_context = game_context,
        is_home      = is_home,
        target_date  = target_date,
        team_id      = team_id,
        all_stats_df = all_stats_df,
        injury_map   = injury_map,
    )

    feat_cols = mods["features"]
    X = np.array([[feat.get(c, np.nan) for c in feat_cols]], dtype=float)

    raw = {}
    for q, mod in mods["quantile_models"].items():
        raw[q] = float(mod.predict(X)[0])

    # Enforce monotonicity
    sorted_q = sorted(raw.keys())
    prev     = 0.0
    for q in sorted_q:
        raw[q] = max(prev, raw[q])
        prev   = raw[q]

    q50 = raw.get(0.50, np.nan)
    q25 = raw.get(0.25, np.nan)
    q75 = raw.get(0.75, np.nan)
    q10 = raw.get(0.10, np.nan)
    q90 = raw.get(0.90, np.nan)

    iqr = q75 - q25 if (np.isfinite(q25) and np.isfinite(q75)) else np.nan
    vol = (iqr / q50) if (np.isfinite(iqr) and np.isfinite(q50) and q50 > 0) else np.nan

    return {
        "exp_mp":          round(q50, 2) if np.isfinite(q50) else np.nan,
        "mp_q10":          round(q10, 2) if np.isfinite(q10) else np.nan,
        "mp_q25":          round(q25, 2) if np.isfinite(q25) else np.nan,
        "mp_q75":          round(q75, 2) if np.isfinite(q75) else np.nan,
        "mp_q90":          round(q90, 2) if np.isfinite(q90) else np.nan,
        "mp_vol":          round(vol, 3) if np.isfinite(vol) else np.nan,
        "mp_pred_floor":   round(q10, 2) if np.isfinite(q10) else np.nan,
        "mp_pred_ceiling": round(q90, 2) if np.isfinite(q90) else np.nan,
    }


# ── Convenience class ──────────────────────────────────────────────────────────

class MinutesModel:
    """
    Convenience wrapper around the minutes model functions.
    Loads models once on instantiation and holds in memory.

    Usage:
        mm = MinutesModel()
        preds = mm.predict(prior_stats, game_context, is_home, target_date,
                           team_id, all_stats_df, injury_map)
        # preds: {"exp_mp": 31.2, "mp_q25": 27.1, "mp_q75": 34.8, ...}
    """

    def __init__(self, model_dir: Path = MODEL_DIR):
        global MODEL_DIR
        MODEL_DIR = model_dir
        self._models = load_minutes_model()
        if self._models is None:
            logger.warning(
                "MinutesModel: no trained models found in model_cache/. "
                "Predictions will use rolling-mean fallback until "
                "train_minutes_model() is run."
            )
        else:
            n_mods = len(self._models["quantile_models"])
            logger.info(f"MinutesModel loaded: {n_mods} quantile models")

    @property
    def is_trained(self) -> bool:
        return self._models is not None

    def predict(
        self,
        prior_stats: pd.DataFrame,
        game_context: dict,
        is_home: int,
        target_date: str,
        team_id: int,
        all_stats_df: pd.DataFrame,
        injury_map: dict,
    ) -> dict:
        return predict_minutes(
            prior_stats  = prior_stats,
            game_context = game_context,
            is_home      = is_home,
            target_date  = target_date,
            team_id      = team_id,
            all_stats_df = all_stats_df,
            injury_map   = injury_map,
            minutes_models = self._models,
        )


# ── Standalone entry point ─────────────────────────────────────────────────────

def main():
    """
    Train the minutes model standalone.
    Called from train_v12.py or directly: python minutes_model.py
    """
    import json
    import sys
    from pathlib import Path

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    DATA_DIR = Path("data")

    try:
        from bdl_client import _get_api_key
        if not _get_api_key():
            sys.exit("BDL_API_KEY not set.")
    except ImportError:
        sys.exit("bdl_client.py not found.")

    stats_path = DATA_DIR / "player_game_stats.parquet"
    odds_path  = DATA_DIR / "game_odds.parquet"

    if not stats_path.exists():
        sys.exit("No stats data. Run train_v12.py first to fetch data.")

    stats_df = pd.read_parquet(stats_path)
    odds_df  = pd.read_parquet(odds_path) if odds_path.exists() else pd.DataFrame()

    result = train_minutes_model(stats_df, odds_df)

    if result:
        print("\n" + "=" * 60)
        print("MINUTES MODEL TRAINING COMPLETE")
        print("=" * 60)
        print(f"  MAE (Q50):      {result['mae_q50']:.3f} minutes")
        print(f"  Max cal error:  {result['max_cal_error']:.3f}")
        print(f"  50% coverage:   {result['coverage_50pct']:.1%}")
        print(f"  Sub-20 capture: {result['sub20_capture']:.1%}")
        print(f"  Holdout from:   {result['holdout_cutoff']}")
        print(f"  Models saved:   model_cache/minutes_q*.pkl")
        print("=" * 60)


if __name__ == "__main__":
    main()
