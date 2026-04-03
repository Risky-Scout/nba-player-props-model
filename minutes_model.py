"""
minutes_model.py — Standalone Minutes Prediction Model
Loads pre-trained quantile models from model_cache/minutes_q*.pkl
"""
import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)
_CACHE = {}
_FEATURES = None

def _load_models():
    global _CACHE, _FEATURES
    if _CACHE:
        return
    cache_dir = Path("model_cache")
    for q in [10,20,25,30,40,50,60,70,75,80,90]:
        p = cache_dir / f"minutes_q{q}.pkl"
        if p.exists():
            _CACHE[q] = joblib.load(p)
    fp = cache_dir / "minutes_features.pkl"
    if fp.exists():
        _FEATURES = joblib.load(fp)

def predict_minutes(prior_stats, game_context, is_home, target_date,
                    team_id, all_stats_df, injury_map):
    _load_models()
    df = prior_stats.sort_values("game_date").reset_index(drop=True)
    mins = pd.to_numeric(df["min"], errors="coerce").fillna(0).values if len(df) > 0 else np.array([])
    last10 = mins[-10:] if len(mins) >= 10 else mins
    mean_last10 = float(np.mean(last10)) if len(last10) > 0 else 25.0
    std_last10  = float(np.std(last10))  if len(last10) > 1 else 5.0

    fallback = {
        "mean_min_last10":  mean_last10,
        "exp_mp":           mean_last10,
        "mp_q10":           max(0.0, mean_last10 - 1.5*std_last10),
        "mp_q25":           max(0.0, mean_last10 - 0.8*std_last10),
        "mp_q75":           mean_last10 + 0.8*std_last10,
        "mp_q90":           mean_last10 + 1.5*std_last10,
        "mp_vol":           std_last10,
        "mp_pred_floor":    max(0.0, mean_last10 - 2.0*std_last10),
        "mp_pred_ceiling":  mean_last10 + 2.0*std_last10,
    }

    if not _CACHE:
        return fallback

    try:
        prior = mins
        last5 = prior[-5:] if len(prior) >= 5 else prior
        if len(prior) > 0:
            w = np.array([0.9**i for i in range(len(prior))][::-1])
            ewma = float(np.average(prior, weights=w))
        else:
            ewma = mean_last10

        feat_dict = {
            "mp_mean_season":    float(np.mean(prior)) if len(prior) > 0 else mean_last10,
            "mp_mean_last5":     float(np.mean(last5)) if len(last5) > 0 else mean_last10,
            "mp_mean_last10":    mean_last10,
            "mp_ewma":           ewma,
                "mp_trend_3v10":     float(np.mean(prior[-3:]) / max(float(np.mean(last10)), 0.1)),
            "mp_ceiling_last10": float(np.percentile(last10, 90)) if len(last10) > 0 else mean_last10,
            "mp_std_last10":     std_last10,
            "is_home":           float(is_home),
            "rest_days":         float(game_context.get("rest_days", 2)),
            "back_to_back":      float(game_context.get("back_to_back", 0)),
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


def train_minutes_model(stats_df, odds_df):
    import lightgbm as lgb
    import json

    logger.info("=" * 60)
    logger.info("Minutes Model Training")
    logger.info("=" * 60)

    df = stats_df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["min_numeric"] = pd.to_numeric(df["min"], errors="coerce").fillna(0)
    df = df[df["min_numeric"] > 0].copy()

    rows = []
    for pid, pdata in df.groupby("player_id"):
        pdata = pdata.sort_values("game_date").reset_index(drop=True)
        mins = pdata["min_numeric"].values
        for i in range(10, len(pdata)):
            prior = mins[:i]
            last5  = prior[-5:]
            last10 = prior[-10:] if len(prior) >= 10 else prior
            w = np.array([0.9**j for j in range(len(prior))][::-1])
            ewma = float(np.average(prior, weights=w))
            rows.append({
                "mp_mean_season":    float(np.mean(prior)),
                "mp_mean_last5":     float(np.mean(last5)),
                "mp_mean_last10":    float(np.mean(last10)),
                "mp_ewma":           ewma,
                "mp_trend_3v10":     float(np.mean(prior[-3:]) / max(float(np.mean(last10)), 0.1)),
                "mp_ceiling_last10": float(np.percentile(last10, 90)),
                "mp_std_last10":     float(np.std(last10)) if len(last10) > 1 else 0.0,
                "is_home":           float(pdata.iloc[i].get("home_team_id") == pdata.iloc[i].get("team_id")),
                "rest_days":         float((pdata.iloc[i]["game_date"] - pdata.iloc[i-1]["game_date"]).days) if i > 0 else 2.0,
                "back_to_back":      1.0 if i > 0 and (pdata.iloc[i]["game_date"] - pdata.iloc[i-1]["game_date"]).days == 1 else 0.0,
                "target":            mins[i],
                "game_date":         pdata.iloc[i]["game_date"],
            })

    if not rows:
        logger.warning("Minutes model: no training rows")
        return {}

    train_df = pd.DataFrame(rows)
    feat_cols = [c for c in train_df.columns if c not in ("target","game_date")]
    cutoff = train_df["game_date"].quantile(0.85)
    train_mask = train_df["game_date"] <= cutoff
    X_tr = train_df.loc[train_mask, feat_cols]
    y_tr = train_df.loc[train_mask, "target"]
    X_ho = train_df.loc[~train_mask, feat_cols]
    y_ho = train_df.loc[~train_mask, "target"]

    logger.info(f"  {len(train_df)} rows | train={len(X_tr)} holdout={len(X_ho)}")

    cache_dir = Path("model_cache")
    cache_dir.mkdir(exist_ok=True)
    joblib.dump(feat_cols, cache_dir / "minutes_features.pkl")

    for q in [10,20,25,30,40,50,60,70,75,80,90]:
        alpha = q/100.0
        m = lgb.LGBMRegressor(
            objective="quantile", alpha=alpha,
            n_estimators=500, num_leaves=63,
            learning_rate=0.03, min_child_samples=20,
            feature_fraction=0.8, bagging_fraction=0.8,
            bagging_freq=1, verbosity=-1, random_state=42)
        m.fit(X_tr, y_tr)
        joblib.dump(m, cache_dir / f"minutes_q{q}.pkl")
        if len(X_ho) > 0:
            emp = float(np.mean(y_ho.values <= m.predict(X_ho)))
            err = abs(emp - alpha)
            status = "OK" if err < 0.05 else "WARN"
            logger.info(f"    Q{q:02d}: empirical={emp:.3f} err={err:.3f} {status}")

    mae = 0.0
    if len(X_ho) > 0:
        q50 = joblib.load(cache_dir / "minutes_q50.pkl")
        mae = float(np.mean(np.abs(y_ho.values - q50.predict(X_ho))))
    logger.info(f"  Holdout MAE (Q50): {mae:.3f} minutes")
    logger.info(f"  Minutes model saved to model_cache/minutes_q*.pkl")

    # Compute calibration errors for reporting
    cal_errors = []
    coverage_50 = 0.0
    if len(X_ho) > 0:
        for q, model in [(q, joblib.load(cache_dir / f"minutes_q{q}.pkl")) for q in [10,25,50,75,90]]:
            preds = model.predict(X_ho)
            emp = float(np.mean(y_ho.values <= preds))
            cal_errors.append(abs(emp - q/100.0))
            if q == 50:
                coverage_50 = emp
    max_cal_err = max(cal_errors) if cal_errors else 0.0
    meta = {
        "mae": mae,
        "mae_q50": mae,
        "max_cal_error": max_cal_err,
        "coverage_50pct": coverage_50,
        "n_train": len(X_tr),
        "n_holdout": len(X_ho),
        "features": feat_cols,
    }
    with open(cache_dir / "minutes_training_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    global _CACHE, _FEATURES
    _CACHE = {}
    _FEATURES = None
    _load_models()
    return meta
