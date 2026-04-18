"""
NBA Props Model — standalone minutes prediction model.

Loads pre-trained quantile models from artifacts/models/minutes_q*.pkl.

Features used in both training and inference:
    p_active                : P(player played > 0 min) over last 20 games
    starter_prob            : P(min >= 28) over last 15 games
    p_20plus / p_28plus / p_34plus : empirical minute-threshold hit rates
    role_change_score       : (mean_last3 - mean_last15) / (mean_last15 + 1)
    bench_fragility_score   : coefficient of variation over last 20 games
    return_restriction_score: 1 if last game was unusually short after rest
    teammate_absence_lift   : extra min this player averages when top teammate sits

This module remains a point-interval quantile model today. Phase 3 of the
rebuild replaces it with a state-aware probabilistic minutes distribution.
"""
import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from nba_props_model.paths import MODEL_DIR

logger = logging.getLogger(__name__)
_CACHE: dict = {}
_FEATURES: Optional[list] = None

# ── Constants ──────────────────────────────────────────────────────────────────
_STARTER_MIN_THRESHOLD = 28.0   # minutes above which we call a game a "start"
_RESTRICTION_RATIO     = 0.55   # last game / mean_last10 below this → restriction flag
_TOP_TEAMMATE_N        = 3      # how many top-usage teammates to track for absence lift
_ABSENCE_LIFT_WINDOW   = 60     # max historical game rows to look back for absence calc


# ── Model loading ──────────────────────────────────────────────────────────────
def _load_models() -> None:
    global _CACHE, _FEATURES
    if _CACHE:
        return
    for q in [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90]:
        p = MODEL_DIR / f"minutes_q{q}.pkl"
        if p.exists():
            _CACHE[q] = joblib.load(p)
    fp = MODEL_DIR / "minutes_features.pkl"
    if fp.exists():
        _FEATURES = joblib.load(fp)


# ── Feature computation helpers ────────────────────────────────────────────────

def _compute_rolling_features(mins: np.ndarray) -> dict:
    """
    Given an array of minutes values (ordered oldest→newest, all games including DNPs),
    return the full suite of rolling features used by both predict and train paths.
    """
    n = len(mins)

    last5  = mins[-5:]  if n >= 5  else mins
    last10 = mins[-10:] if n >= 10 else mins
    last15 = mins[-15:] if n >= 15 else mins
    last20 = mins[-20:] if n >= 20 else mins

    mean_last10 = float(np.mean(last10)) if len(last10) > 0 else 25.0
    std_last10  = float(np.std(last10))  if len(last10) > 1 else 5.0
    mean_last15 = float(np.mean(last15)) if len(last15) > 0 else mean_last10
    mean_last20 = float(np.mean(last20)) if len(last20) > 0 else mean_last10
    std_last20  = float(np.std(last20))  if len(last20) > 1 else std_last10
    mean_season = float(np.mean(mins))   if n > 0 else mean_last10

    # EWMA (decay 0.9, newest = highest weight)
    w = np.array([0.9 ** i for i in range(n)][::-1])
    ewma = float(np.average(mins, weights=w)) if n > 0 else mean_last10

    # Ceiling / trend
    ceiling_last10 = float(np.percentile(last10, 90)) if len(last10) > 0 else mean_last10
    trend_3v10 = float(np.mean(mins[-3:]) / max(mean_last10, 0.1)) if n >= 3 else 1.0

    # v2 new features -----------------------------------------------------------

    # p_active: fraction of recent 20 games with > 0 minutes (DNP detection)
    p_active = float(np.mean(last20 > 0)) if len(last20) > 0 else 1.0

    # active minutes only (exclude DNPs from threshold calcs)
    active20 = last20[last20 > 0]
    active15 = last15[last15 > 0]

    # starter_prob / p_28plus: P(min >= 28) over last 15 active games
    starter_prob = float(np.mean(active15 >= _STARTER_MIN_THRESHOLD)) if len(active15) > 0 else 0.5
    p_28plus     = starter_prob  # alias for clarity in feature name

    # p_20plus: P(min >= 20) over last 20 active games
    p_20plus = float(np.mean(active20 >= 20.0)) if len(active20) > 0 else 0.6

    # p_34plus: P(min >= 34) over last 20 active games
    p_34plus = float(np.mean(active20 >= 34.0)) if len(active20) > 0 else 0.1

    # role_change_score: recent trend vs baseline; >0 = rising role, <0 = falling
    mean_last3 = float(np.mean(mins[-3:])) if n >= 3 else mean_last10
    role_change_score = float((mean_last3 - mean_last15) / (mean_last15 + 1.0))

    # bench_fragility_score: coeff of variation; high = unpredictable bench piece
    bench_fragility_score = float(std_last20 / (mean_last20 + 1.0))

    # return_restriction_score: was last game unusually short? (restriction / ramp-back)
    if n >= 3:
        last_game_min  = float(mins[-1])
        prior_mean     = float(np.mean(mins[-11:-1])) if n >= 11 else mean_last10
        return_restriction_score = (
            1.0 if (last_game_min > 0 and
                    last_game_min < _RESTRICTION_RATIO * prior_mean and
                    prior_mean > 10.0)
            else 0.0
        )
    else:
        return_restriction_score = 0.0

    return {
        "mp_mean_season":           mean_season,
        "mp_mean_last5":            float(np.mean(last5)) if len(last5) > 0 else mean_last10,
        "mp_mean_last10":           mean_last10,
        "mp_ewma":                  ewma,
        "mp_trend_3v10":            trend_3v10,
        "mp_ceiling_last10":        ceiling_last10,
        "mp_std_last10":            std_last10,
        # v2
        "mp_p_active":              p_active,
        "mp_starter_prob":          starter_prob,
        "mp_p_20plus":              p_20plus,
        "mp_p_28plus":              p_28plus,
        "mp_p_34plus":              p_34plus,
        "mp_role_change_score":     role_change_score,
        "mp_bench_fragility":       bench_fragility_score,
        "mp_return_restriction":    return_restriction_score,
    }


def _compute_teammate_absence_lift(
    player_id: int,
    team_id: int,
    target_date: str,
    all_stats_df: pd.DataFrame,
) -> float:
    """
    Estimate how many extra minutes this player averages when top teammates sit.

    Method:
      1. Find top-_TOP_TEAMMATE_N teammates by mean minutes in the last
         _ABSENCE_LIFT_WINDOW games before target_date.
      2. For each top teammate T, split this player's games into:
             with_T    : T played > 5 min in that game
             without_T : T played 0 min (DNP / absent)
      3. Lift = mean(without) - mean(with), averaged across top teammates.
      4. Winsorise to [-8, +15] to avoid noise from tiny samples.
    """
    if all_stats_df is None or all_stats_df.empty:
        return 0.0
    try:
        sdf = all_stats_df[all_stats_df["game_date"].astype(str) < str(target_date)]
        sdf = sdf.sort_values("game_date").tail(_ABSENCE_LIFT_WINDOW * 15)  # rough cap

        team_df = sdf[sdf["team_id"] == team_id]
        player_df = team_df[team_df["player_id"] == player_id]
        if len(player_df) < 8:
            return 0.0

        # Top teammates by mean minutes
        teammate_means = (
            team_df[team_df["player_id"] != player_id]
            .groupby("player_id")["min"]
            .apply(lambda x: pd.to_numeric(x, errors="coerce").mean())
            .nlargest(_TOP_TEAMMATE_N)
        )

        if teammate_means.empty:
            return 0.0

        lifts = []
        for tm_pid in teammate_means.index:
            tm_df = team_df[team_df["player_id"] == tm_pid][["game_id", "min"]].copy()
            tm_df["tm_min"] = pd.to_numeric(tm_df["min"], errors="coerce").fillna(0)
            merged = player_df[["game_id", "min"]].merge(tm_df[["game_id", "tm_min"]], on="game_id", how="inner")
            if len(merged) < 8:
                continue
            p_min = pd.to_numeric(merged["min"], errors="coerce").fillna(0).values
            tm_min = merged["tm_min"].values
            with_mask    = tm_min > 5
            without_mask = tm_min == 0
            if with_mask.sum() < 4 or without_mask.sum() < 2:
                continue
            lift = float(np.mean(p_min[without_mask]) - np.mean(p_min[with_mask]))
            lifts.append(np.clip(lift, -8.0, 15.0))

        return float(np.mean(lifts)) if lifts else 0.0

    except Exception as e:
        logger.debug(f"teammate_absence_lift failed: {e}")
        return 0.0


# ── Public inference API ───────────────────────────────────────────────────────

def predict_minutes(
    prior_stats:  pd.DataFrame,
    game_context: dict,
    is_home:      bool,
    target_date:  str,
    team_id:      int,
    all_stats_df: pd.DataFrame,
    injury_map:   dict,
) -> dict:
    _load_models()

    df   = prior_stats.sort_values("game_date").reset_index(drop=True)
    mins = pd.to_numeric(df["min"], errors="coerce").fillna(0).values if len(df) > 0 else np.array([])

    last10      = mins[-10:] if len(mins) >= 10 else mins
    mean_last10 = float(np.mean(last10)) if len(last10) > 0 else 25.0
    std_last10  = float(np.std(last10))  if len(last10) > 1 else 5.0

    fallback = {
        "mean_min_last10":  mean_last10,
        "exp_mp":           mean_last10,
        "mp_q10":           max(0.0, mean_last10 - 1.5 * std_last10),
        "mp_q25":           max(0.0, mean_last10 - 0.8 * std_last10),
        "mp_q75":           mean_last10 + 0.8 * std_last10,
        "mp_q90":           mean_last10 + 1.5 * std_last10,
        "mp_vol":           std_last10,
        "mp_pred_floor":    max(0.0, mean_last10 - 2.0 * std_last10),
        "mp_pred_ceiling":  mean_last10 + 2.0 * std_last10,
    }

    if not _CACHE:
        return fallback

    try:
        rolling = _compute_rolling_features(mins)

        player_id = int(df["player_id"].iloc[0]) if len(df) > 0 and "player_id" in df.columns else -1

        absence_lift = _compute_teammate_absence_lift(
            player_id, team_id, target_date, all_stats_df
        )

        feat_dict = {
            **rolling,
            "is_home":               float(is_home),
            "rest_days":             float(game_context.get("rest_days", 2)),
            "back_to_back":          float(game_context.get("back_to_back", 0)),
            "mp_teammate_abs_lift":  absence_lift,
        }

        if _FEATURES is not None:
            X = pd.DataFrame([{f: feat_dict.get(f, 0.0) for f in _FEATURES}])
        else:
            X = pd.DataFrame([feat_dict])

        preds = {}
        for q, model in _CACHE.items():
            try:
                preds[q] = float(model.predict(X)[0])
            except Exception:
                preds[q] = mean_last10

        return {
            "mean_min_last10":  mean_last10,
            "exp_mp":           max(0.0, preds.get(50, mean_last10)),
            "mp_q10":           max(0.0, preds.get(10, fallback["mp_q10"])),
            "mp_q25":           max(0.0, preds.get(25, fallback["mp_q25"])),
            "mp_q75":           max(0.0, preds.get(75, fallback["mp_q75"])),
            "mp_q90":           max(0.0, preds.get(90, fallback["mp_q90"])),
            "mp_vol":           std_last10,
            "mp_pred_floor":    max(0.0, preds.get(10, fallback["mp_pred_floor"])),
            "mp_pred_ceiling":  max(0.0, preds.get(90, fallback["mp_pred_ceiling"])),
        }
    except Exception as e:
        logger.debug(f"predict_minutes failed: {e}")
        return fallback


# ── Training ───────────────────────────────────────────────────────────────────

def train_minutes_model(stats_df: pd.DataFrame, odds_df) -> dict:
    import lightgbm as lgb
    import json

    logger.info("=" * 60)
    logger.info("Minutes Model Training — v2 (8 new features)")
    logger.info("=" * 60)

    df = stats_df.copy()
    df["game_date"]   = pd.to_datetime(df["game_date"])
    df["min_numeric"] = pd.to_numeric(df["min"], errors="coerce").fillna(0)
    df = df[df["min_numeric"] >= 0].copy()   # keep DNPs (min=0) — they're signal

    rows = []
    for pid, pdata in df.groupby("player_id"):
        pdata = pdata.sort_values("game_date").reset_index(drop=True)
        mins  = pdata["min_numeric"].values
        n     = len(pdata)
        if n < 12:
            continue

        for i in range(10, n):
            prior     = mins[:i]          # all games before this one (may include 0s)
            target    = mins[i]
            game_row  = pdata.iloc[i]

            rolling = _compute_rolling_features(prior)

            # teammate_absence_lift — compute from full stats_df at training time
            target_date_str = str(game_row["game_date"].date())
            team_id_val     = int(game_row.get("team_id", 0)) if "team_id" in game_row.index else 0

            absence_lift = _compute_teammate_absence_lift(
                int(pid), team_id_val, target_date_str, stats_df
            ) if team_id_val != 0 else 0.0

            # Rest days (from game_date diff)
            prev_date  = pdata.iloc[i - 1]["game_date"]
            rest_days  = float((game_row["game_date"] - prev_date).days) if i > 0 else 2.0
            b2b        = 1.0 if rest_days == 1.0 else 0.0

            # is_home: infer from team_id vs home_team_id if available
            is_home = 0.0
            if "home_team_id" in game_row.index and "team_id" in game_row.index:
                is_home = float(int(game_row["home_team_id"]) == int(game_row["team_id"]))

            rows.append({
                **rolling,
                "is_home":              is_home,
                "rest_days":            rest_days,
                "back_to_back":         b2b,
                "mp_teammate_abs_lift": absence_lift,
                "target":               target,
                "game_date":            game_row["game_date"],
            })

    if not rows:
        logger.warning("Minutes model: no training rows")
        return {}

    train_df  = pd.DataFrame(rows)
    feat_cols = [c for c in train_df.columns if c not in ("target", "game_date")]
    cutoff    = train_df["game_date"].quantile(0.85)
    train_mask = train_df["game_date"] <= cutoff
    X_tr = train_df.loc[train_mask,  feat_cols]
    y_tr = train_df.loc[train_mask,  "target"]
    X_ho = train_df.loc[~train_mask, feat_cols]
    y_ho = train_df.loc[~train_mask, "target"]

    logger.info(f"  {len(train_df)} rows | {len(feat_cols)} features | "
                f"train={len(X_tr)}  holdout={len(X_ho)}")
    logger.info(f"  Feature list: {feat_cols}")

    joblib.dump(feat_cols, MODEL_DIR / "minutes_features.pkl")

    cal_errors = []
    for q in [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90]:
        alpha = q / 100.0
        m = lgb.LGBMRegressor(
            objective="quantile", alpha=alpha,
            n_estimators=600, num_leaves=63,
            learning_rate=0.03, min_child_samples=20,
            feature_fraction=0.8, bagging_fraction=0.8,
            bagging_freq=1, verbosity=-1, random_state=42,
        )
        m.fit(X_tr, y_tr)
        joblib.dump(m, MODEL_DIR /f"minutes_q{q}.pkl")
        if len(X_ho) > 0:
            emp    = float(np.mean(y_ho.values <= m.predict(X_ho)))
            err    = abs(emp - alpha)
            status = "OK" if err < 0.05 else "WARN"
            cal_errors.append(err)
            logger.info(f"    Q{q:02d}: empirical={emp:.3f}  err={err:.3f}  {status}")

    mae = 0.0
    if len(X_ho) > 0:
        q50 = joblib.load(MODEL_DIR /"minutes_q50.pkl")
        mae = float(np.mean(np.abs(y_ho.values - q50.predict(X_ho))))

    # Feature importance
    fi_m = joblib.load(MODEL_DIR /"minutes_q50.pkl")
    fi   = dict(zip(feat_cols, fi_m.feature_importances_))
    fi_sorted = sorted(fi.items(), key=lambda x: -x[1])
    logger.info("  Top-10 feature importances:")
    for fname, fval in fi_sorted[:10]:
        logger.info(f"    {fname:<35} {fval:.0f}")

    max_cal_err = float(max(cal_errors)) if cal_errors else 0.0
    logger.info(f"  Holdout MAE (Q50): {mae:.3f} min")
    logger.info(f"  Max calibration error: {max_cal_err:.3f}")

    meta = {
        "mae":          mae,
        "mae_q50":      mae,
        "max_cal_error": max_cal_err,
        "n_train":      len(X_tr),
        "n_holdout":    len(X_ho),
        "features":     feat_cols,
        "n_features":   len(feat_cols),
    }
    import json
    with open(MODEL_DIR /"minutes_training_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    global _CACHE, _FEATURES
    _CACHE    = {}
    _FEATURES = None
    _load_models()
    return meta
