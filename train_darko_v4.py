#!/usr/bin/env python3
"""
train_darko_v4.py — NBA Props Model Training Pipeline
VERSION: 2026-02-28-v10

Architecture:
  - NO lines in training. Labels = real game outcomes only.
  - Targets: pts, reb, ast, fg3m, stl, blk, tov + combos (pra, pr, pa, ra, stocks)
  - 11 quantile LightGBM models per target (Q10-Q90), pinball loss
  - Stat-specific feature gating per expert spec (~30-60 features per stat)
  - NaN preserved throughout (LightGBM handles natively)
  - Residual z-scores computed for correlation engine fitting
  - Quantile calibration validation on held-out 15%
  - Incremental data pipeline (daily fetches new games only)
"""

import json
import logging
import os
import sys
import warnings
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

try:
    from bdl_client import (
        _get_api_key, parse_minutes,
        get_player_game_stats, get_game_odds,
        get_advanced_stats_v2, get_injuries,
        build_game_context_map,
    )
    from feature_engineering import (
        build_player_game_features,
        add_interaction_features,
        get_feature_cols_for_stat,
        STATS, COMBO_STATS, ALL_TARGETS,
    )
    from correlation_engine import (
        quantile_calibration_report,
        compute_residual_zscores,
        WithinPlayerCorrelationEngine,
        enforce_monotonicity,
        usage_bucket, mp_bucket,
        QUANTILES,
    )
except ImportError as e:
    sys.exit(f"Import error: {e}")

DATA_DIR  = Path("data");        DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR = Path("model_cache"); MODEL_DIR.mkdir(exist_ok=True)

TRAIN_SEASONS  = [2023, 2024, 2025]
MIN_GAMES      = 15
HOLDOUT_FRAC   = 0.15

STAT_DISPLAY = {
    "pts":"Points","reb":"Rebounds","ast":"Assists","fg3m":"Threes",
    "stl":"Steals","blk":"Blocks","tov":"Turnovers",
    "pra":"Pts+Reb+Ast","pr":"Pts+Reb","pa":"Pts+Ast",
    "ra":"Reb+Ast","stocks":"Stl+Blk",
}

COMBO_FORMULA = {
    "pra":    ["pts","reb","ast"],
    "pr":     ["pts","reb"],
    "pa":     ["pts","ast"],
    "ra":     ["reb","ast"],
    "stocks": ["stl","blk"],
}

LGB_BASE = dict(
    objective="quantile", metric="quantile",
    n_estimators=800, learning_rate=0.025,
    num_leaves=40, max_depth=7,
    feature_fraction=0.75, bagging_fraction=0.80, bagging_freq=1,
    reg_alpha=0.5, reg_lambda=3.0,
    min_child_samples=50,
    verbose=-1,
)

ADV_FIELDS = [
    "usage_percentage","pace",
    "true_shooting_percentage","effective_field_goal_percentage",
    "assist_percentage","assist_to_turnover",
]


# ── Data parsing ───────────────────────────────────────────────────────────────

def _flat(rec: dict) -> dict | None:
    player = rec.get("player") or {}
    game   = rec.get("game")   or {}
    team   = rec.get("team")   or {}
    pid = player.get("id")
    gid = game.get("id")
    if not pid or not gid:
        return None
    return {
        "player_id":       pid,
        "player_name":     f"{player.get('first_name','')} {player.get('last_name','')}".strip(),
        "game_id":         gid,
        "game_date":       pd.to_datetime(game.get("date","")[:10]),
        "season":          game.get("season"),
        "home_team_id":    (game.get("home_team") or {}).get("id") or game.get("home_team_id"),
        "visitor_team_id": (game.get("visitor_team") or {}).get("id") or game.get("visitor_team_id"),
        "team_id":         team.get("id"),
        "team_abbr":       team.get("abbreviation",""),
        "min":             parse_minutes(rec.get("min","0")),
        "pts":    float(rec.get("pts")     or 0),
        "reb":    float(rec.get("reb")     or 0),
        "ast":    float(rec.get("ast")     or 0),
        "fg3m":   float(rec.get("fg3m")    or 0),
        "stl":    float(rec.get("stl")     or 0),
        "blk":    float(rec.get("blk")     or 0),
        "turnover": float(rec.get("turnover") or 0),
        "fga":    float(rec.get("fga")     or 0),
        "fg3a":   float(rec.get("fg3a")    or 0),
        "fta":    float(rec.get("fta")     or 0),
        "ftm":    float(rec.get("ftm")     or 0),
        "oreb":   float(rec.get("oreb")    or 0),
        "dreb":   float(rec.get("dreb")    or 0),
        "pf":     float(rec.get("pf")      or 0),
        "fg_pct":  float(rec.get("fg_pct")  or 0),
        "fg3_pct": float(rec.get("fg3_pct") or 0),
        "ft_pct":  float(rec.get("ft_pct")  or 0),
    }


def _parse_adv(rec: dict) -> dict | None:
    pid = (rec.get("player") or {}).get("id")
    gid = (rec.get("game")   or {}).get("id")
    if not pid or not gid:
        return None
    r = {
        "player_id": pid, "game_id": gid,
        "game_date": pd.to_datetime((rec.get("game") or {}).get("date","")[:10]),
    }
    for f in ADV_FIELDS:
        r[f] = float(rec.get(f) or 0.0) if rec.get(f) is not None else None
    return r


def _parse_odds(rec: dict) -> dict | None:
    try:
        return {
            "game_id":           rec["game_id"],
            "vendor":            rec.get("vendor",""),
            "total_value":       float(rec["total_value"])       if rec.get("total_value")       else None,
            "spread_home_value": float(rec["spread_home_value"]) if rec.get("spread_home_value") else None,
            "updated_at":        rec.get("updated_at",""),
        }
    except Exception:
        return None


# ── Incremental data pipeline ──────────────────────────────────────────────────

def _last_date(path: Path, col: str = "game_date"):
    if not path.exists(): return None
    try:
        df = pd.read_parquet(path, columns=[col])
        return pd.to_datetime(df[col]).max() if not df.empty else None
    except Exception: return None


def fetch_all_data():
    STATS_PATH = DATA_DIR / "player_game_stats.parquet"
    ADV_PATH   = DATA_DIR / "advanced_stats.parquet"
    ODDS_PATH  = DATA_DIR / "game_odds.parquet"
    yesterday  = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    last       = _last_date(STATS_PATH)

    if last is None:
        logger.info("Full historical load...")
        fetch_start = f"{min(TRAIN_SEASONS)}-10-01"
        is_initial  = True
    else:
        fetch_start = (last + timedelta(days=1)).strftime("%Y-%m-%d")
        is_initial  = False
        if fetch_start > yesterday:
            logger.info(f"Data current through {last.date()} — loading from disk.")
            return (
                pd.read_parquet(STATS_PATH),
                pd.read_parquet(ADV_PATH)  if ADV_PATH.exists()  else pd.DataFrame(),
                pd.read_parquet(ODDS_PATH) if ODDS_PATH.exists() else pd.DataFrame(),
            )
        logger.info(f"Incremental fetch: {fetch_start} → {yesterday}")

    new_stats_raw = []
    if is_initial:
        for season in TRAIN_SEASONS:
            s = f"{season}-10-01"; e = f"{season+1}-06-30"
            logger.info(f"  Season {season}...")
            batch = get_player_game_stats(start_date=s, end_date=e)
            new_stats_raw.extend(batch)
            logger.info(f"    {len(batch)} records")
    else:
        new_stats_raw = get_player_game_stats(start_date=fetch_start, end_date=yesterday)
        logger.info(f"  {len(new_stats_raw)} new records")

    rows = [r for r in (_flat(x) for x in new_stats_raw) if r]
    new_stats_df = pd.DataFrame(rows)
    if not new_stats_df.empty:
        new_stats_df = new_stats_df[new_stats_df["min"] >= 1]

    logger.info("Fetching advanced stats...")
    new_adv_raw = []
    if is_initial:
        for season in TRAIN_SEASONS:
            batch = get_advanced_stats_v2(start_date=f"{season}-10-01", end_date=f"{season+1}-06-30")
            new_adv_raw.extend(batch)
    else:
        new_adv_raw = get_advanced_stats_v2(start_date=fetch_start, end_date=yesterday)
    adv_rows   = [r for r in (_parse_adv(x) for x in new_adv_raw) if r]
    new_adv_df = pd.DataFrame(adv_rows)

    logger.info("Fetching game odds...")
    new_odds_raw = []
    cur = pd.Timestamp(max(fetch_start, f"{min(TRAIN_SEASONS)}-10-01"))
    while cur <= pd.Timestamp(yesterday):
        new_odds_raw.extend(get_game_odds(dates=[cur.strftime("%Y-%m-%d")]))
        cur += timedelta(days=1)
    odds_rows  = [r for r in (_parse_odds(x) for x in new_odds_raw) if r]
    new_odds_df = pd.DataFrame(odds_rows)

    def _merge(path, new_df, dedup, sort):
        if new_df.empty:
            return pd.read_parquet(path) if path.exists() else pd.DataFrame()
        if path.exists() and not is_initial:
            combined = pd.concat([pd.read_parquet(path), new_df], ignore_index=True)
        else:
            combined = new_df
        return combined.drop_duplicates(subset=dedup, keep="last").sort_values(sort).reset_index(drop=True)

    stats_df = _merge(STATS_PATH, new_stats_df, ["player_id","game_id"], ["player_id","game_date"])
    adv_df   = _merge(ADV_PATH,   new_adv_df,   ["player_id","game_id"], ["player_id","game_date"])
    odds_df  = _merge(ODDS_PATH,  new_odds_df,  ["game_id","vendor"],    ["game_id","updated_at"])

    if not stats_df.empty: stats_df.to_parquet(STATS_PATH, index=False)
    if not adv_df.empty:   adv_df.to_parquet(ADV_PATH, index=False)
    if not odds_df.empty:  odds_df.to_parquet(ODDS_PATH, index=False)

    logger.info(f"Data: {len(stats_df)} stats | {len(adv_df)} adv | {len(odds_df)} odds")
    return stats_df, adv_df, odds_df


# ── Training table ─────────────────────────────────────────────────────────────

def build_training_table(stats_df, adv_df, odds_df):
    logger.info("Building training table...")
    ctx_map = build_game_context_map(odds_df.to_dict("records")) if not odds_df.empty else {}

    adv_by_player = defaultdict(list)
    if not adv_df.empty:
        for _, r in adv_df.iterrows():
            adv_by_player[int(r["player_id"])].append(r.to_dict())

    all_rows = []; skipped = 0
    players  = list(stats_df.groupby("player_id"))

    for idx, (player_id, pdata) in enumerate(players):
        pdata = pdata.sort_values("game_date").reset_index(drop=True)
        if len(pdata) < MIN_GAMES:
            continue

        padv = sorted(
            adv_by_player.get(int(player_id), []),
            key=lambda x: x.get("game_date", pd.Timestamp("2000")),
        )

        for i in range(MIN_GAMES, len(pdata)):
            cur   = pdata.iloc[i]
            prior = pdata.iloc[:i]

            gid     = int(cur["game_id"])
            tid     = int(cur["team_id"] or 0)
            hid     = int(cur["home_team_id"] or 0)
            vid     = int(cur["visitor_team_id"] or 0)
            is_home = int(tid == hid)
            td      = str(cur["game_date"])[:10]
            ctx     = ctx_map.get(gid, {})

            # Advanced stats: prior games only
            padv_i = [
                r for r in padv
                if pd.Timestamp(r.get("game_date", pd.Timestamp("2000"))) < cur["game_date"]
            ]

            try:
                base = build_player_game_features(
                    player_id   = int(player_id),
                    prior_stats = prior,
                    prior_adv   = padv_i,
                    game_context= ctx,
                    is_home     = is_home,
                    target_date = td,
                    team_id     = tid,
                    all_stats_df= stats_df,
                    injury_map  = {},   # injuries not available historically
                )
            except Exception as e:
                logger.debug(f"Feature error p={player_id} g={gid}: {e}")
                skipped += 1
                continue

            # Compute combo targets
            pts = float(cur.get("pts",0) or 0)
            reb = float(cur.get("reb",0) or 0)
            ast = float(cur.get("ast",0) or 0)
            stl = float(cur.get("stl",0) or 0)
            blk = float(cur.get("blk",0) or 0)
            tov = float(cur.get("turnover",0) or 0)
            fg3m= float(cur.get("fg3m",0) or 0)

            actuals = {
                "pts":pts,"reb":reb,"ast":ast,"fg3m":fg3m,
                "stl":stl,"blk":blk,"tov":tov,
                "pra":pts+reb+ast, "pr":pts+reb, "pa":pts+ast,
                "ra":reb+ast,      "stocks":stl+blk,
            }

            # Add interaction features for each target
            for target in ALL_TARGETS:
                base_with_ix = add_interaction_features(dict(base), target)
                all_rows.append({
                    **base_with_ix,
                    "player_id":   int(player_id),
                    "player_name": str(cur.get("player_name","")),
                    "game_id":     gid,
                    "game_date":   cur["game_date"],
                    "stat":        target,
                    "actual":      actuals[target],
                    # Buckets for correlation segmentation
                    "usage_bucket": usage_bucket(
                        float(base.get("adv_usage_percentage_mean_last10") or 0)
                    ),
                    "mp_bucket": mp_bucket(
                        float(base.get("mp_mean_last10") or 0)
                    ),
                })

        if (idx + 1) % 100 == 0:
            logger.info(f"  {idx+1}/{len(players)} players | {len(all_rows)} rows")

    df = pd.DataFrame(all_rows)
    if df.empty:
        logger.error(f"Training table EMPTY. skipped={skipped}")
    else:
        logger.info(f"Training table: {len(df)} rows | {df['player_id'].nunique()} players | skipped={skipped}")
        # Do NOT save training_table.parquet — too large; rebuild from raw parquets
    return df


# ── Per-target quantile model training ────────────────────────────────────────

def train_target_model(training_df: pd.DataFrame, target: str) -> dict:
    logger.info(f"Training {STAT_DISPLAY[target]}...")

    df = training_df[training_df["stat"] == target].copy().sort_values("game_date").reset_index(drop=True)
    if len(df) < 500:
        logger.warning(f"  {target}: {len(df)} rows — need 500+, skipping")
        return {}

    # Stat-specific feature gating
    all_cols  = [c for c in df.columns if c not in {
        "player_id","player_name","game_id","game_date",
        "stat","actual","usage_bucket","mp_bucket",
    }]
    feat_cols = get_feature_cols_for_stat(target, all_cols)

    if len(feat_cols) < 5:
        logger.warning(f"  {target}: only {len(feat_cols)} feature cols — skipping")
        return {}

    X    = df[feat_cols].values.astype(float)
    y    = df["actual"].values.astype(float)
    n    = len(X)
    tr_n = int(n * (1.0 - HOLDOUT_FRAC))

    logger.info(f"  {target}: {n} rows | {len(feat_cols)} features | train={tr_n} holdout={n-tr_n}")

    # ── 3PM integrity check (expert spec section 1.2) ─────────────────────────
    if target == "fg3m":
        miss_fg3m = int(df["_fg3m_integrity_miss_fg3m"].sum()) if "_fg3m_integrity_miss_fg3m" in df.columns else 0
        miss_fg3a = int(df["_fg3m_integrity_miss_fg3a"].sum()) if "_fg3m_integrity_miss_fg3a" in df.columns else 0
        bad_rows  = int(df["_fg3m_integrity_bad_rows"].sum())  if "_fg3m_integrity_bad_rows"  in df.columns else 0
        logger.info(f"  [3PM integrity] total={n} | "
                    f"miss_fg3m={miss_fg3m} ({100*miss_fg3m/max(n,1):.1f}%) | "
                    f"miss_fg3a={miss_fg3a} ({100*miss_fg3a/max(n,1):.1f}%) | "
                    f"bad_rows(fg3m>fg3a)={bad_rows}")
        if bad_rows > 0:
            raise ValueError(f"STOP: {bad_rows} rows have fg3m > fg3a — data integrity failure")
        # Drop rows where fg3m target is truly missing (3PM only, per spec)
        valid_mask = ~np.isnan(y)
        X, y = X[valid_mask], y[valid_mask]
        n    = len(X)
        tr_n = int(n * (1.0 - HOLDOUT_FRAC))
        logger.info(f"  [3PM integrity] after dropping missing target: {n} rows")

    holdout_preds = {}
    for q in QUANTILES:
        params = {**LGB_BASE, "alpha": q}

        # Calibration model on train split
        m_cal = lgb.LGBMRegressor(**params)
        m_cal.fit(X[:tr_n], y[:tr_n])
        holdout_preds[q] = m_cal.predict(X[tr_n:])

        # Final model on full dataset
        m_final = lgb.LGBMRegressor(**params)
        m_final.fit(X, y)
        joblib.dump(m_final, MODEL_DIR / f"q{int(q*100):02d}_{target}.pkl")

    joblib.dump(feat_cols, MODEL_DIR / f"features_{target}.pkl")

    # Calibration report — zero_inflated=True skips q <= p0 for discrete stats
    zero_inflated = target in ("stl", "blk", "stocks")
    actuals_ho    = y[tr_n:]
    cal           = quantile_calibration_report(actuals_ho, holdout_preds,
                                                zero_inflated=zero_inflated)

    # max_cal_error uses only graded quantiles (skipped ones are metric artifacts)
    graded_errors = [v["error"] for v in cal.values() if not v.get("skipped", False)]
    max_err       = max(graded_errors) if graded_errors else 0.0

    logger.info(f"  Calibration:")
    for q, row in cal.items():
        if row.get("skipped"):
            logger.info(f"    — Q{int(q*100):02d}: SKIPPED (below zero-mass p0)  empirical={row['empirical_q']:.3f}")
        else:
            flag = "⚠" if row["error"] > 0.05 else "✓"
            logger.info(f"    {flag} Q{int(q*100):02d}: empirical={row['empirical_q']:.3f}  err={row['error']:.3f}")

    # ── Per-quantile diagnostic for zero-inflated stats ───────────────────────
    if target in ("stl", "blk", "stocks"):
        logger.info(f"  [{target.upper()} zero-inflation diagnostic]")
        zero_frac = float(np.mean(actuals_ho == 0))
        logger.info(f"    Holdout zero fraction: {zero_frac:.3f}")
        for q, row in cal.items():
            err_sign = "HIGH" if row["empirical_q"] > q else "LOW"
            logger.info(
                f"    Q{int(q*100):02d}: predicted_coverage={row['empirical_q']:.3f}  "
                f"target={q:.2f}  bias={err_sign}  err={row['error']:.4f}"
            )
        # Confirm zero-mass features are present
        zm_feats = [c for c in feat_cols if "p_zero" in c or "p_ge2" in c or "blended" in c]
        logger.info(f"    Zero-mass/blended features in model: {zm_feats}")

    # ── fg3m-specific diagnostic (section F of expert spec) ───────────────────
    if target == "fg3m":
        logger.info(f"  [3PM diagnostic]")
        zero_frac_3pm = float(np.mean(actuals_ho == 0))
        logger.info(f"    Holdout zero fraction (3PM): {zero_frac_3pm:.3f}")
        for q, row in cal.items():
            err_sign = "HIGH" if row["empirical_q"] > q else "LOW"
            skip_str = " SKIPPED" if row.get("skipped") else ""
            logger.info(
                f"    Q{int(q*100):02d}: cov={row['empirical_q']:.3f}  "
                f"target={q:.2f}  bias={err_sign}  err={row['error']:.4f}{skip_str}"
            )
        zm_feats_3pm = [c for c in feat_cols if "p_zero" in c or "p_ge3" in c
                        or "blend" in c or "is_low" in c or "count_season" in c]
        logger.info(f"    Expert-spec features in model: {zm_feats_3pm}")

    mae = float(np.mean(np.abs(holdout_preds[0.50] - actuals_ho)))
    logger.info(f"  Holdout MAE (Q50): {mae:.3f}")

    # Feature importance (Q50 model)
    m50 = lgb.LGBMRegressor(**{**LGB_BASE, "alpha":0.50})
    m50.fit(X, y)
    fi = pd.DataFrame({"feature":feat_cols,"importance":m50.feature_importances_}).sort_values("importance",ascending=False)
    fi.to_csv(MODEL_DIR / f"feature_importance_{target}.csv", index=False)
    logger.info(f"  Top-5: {fi['feature'].values[:5].tolist()}")

    return {
        "target":        target,
        "n_train":       tr_n,
        "n_holdout":     n - tr_n,
        "feature_count": len(feat_cols),
        "median_mae":    round(mae, 4),
        "max_cal_error": round(max_err, 4),
        "calibration":   {str(k): v for k, v in cal.items()},
    }


# ── Correlation engine fitting ─────────────────────────────────────────────────

def fit_correlation_engine(training_df: pd.DataFrame):
    """
    Fit within-player correlation matrices from residual z-scores.
    Requires Q50, Q25, Q75 predictions from already-trained models.
    """
    logger.info("Fitting correlation engine...")

    z_rows = []
    CORR_STATS = ["pts","reb","ast","fg3m","stl","blk","tov","pra"]

    # Load models needed for residual computation
    models_available = {}
    for s in CORR_STATS:
        fp = MODEL_DIR / f"q50_{s}.pkl"
        fp25 = MODEL_DIR / f"q25_{s}.pkl"
        fp75 = MODEL_DIR / f"q75_{s}.pkl"
        fcols = MODEL_DIR / f"features_{s}.pkl"
        if fp.exists() and fcols.exists():
            models_available[s] = {
                "q50":  joblib.load(fp),
                "q25":  joblib.load(fp25) if fp25.exists() else None,
                "q75":  joblib.load(fp75) if fp75.exists() else None,
                "cols": joblib.load(fcols),
            }

    if len(models_available) < 2:
        logger.warning("Insufficient models for correlation engine — skipping")
        return

    # One z-row per (player_id, game_id)
    # For each game row, compute z-score for each available stat
    base_df = training_df[training_df["stat"] == "pts"][
        ["player_id","game_id","game_date","usage_bucket","mp_bucket"]
    ].copy()

    for s, mods in models_available.items():
        stat_df = training_df[training_df["stat"] == s].copy()
        if stat_df.empty:
            continue

        fcols = mods["cols"]
        X     = stat_df[fcols].values.astype(float)
        y     = stat_df["actual"].values.astype(float)

        q50 = mods["q50"].predict(X)
        q25 = mods["q25"].predict(X) if mods["q25"] else q50 - 1.0
        q75 = mods["q75"].predict(X) if mods["q75"] else q50 + 1.0

        z = compute_residual_zscores(y, q50, q25, q75)
        stat_df[f"z_{s}"] = z

        # Merge z-score back to base_df by player_id + game_id
        base_df = base_df.merge(
            stat_df[["player_id","game_id",f"z_{s}"]],
            on=["player_id","game_id"], how="left"
        )

    engine = WithinPlayerCorrelationEngine(MODEL_DIR)
    engine.fit(base_df)
    joblib.dump(engine, MODEL_DIR / "within_player_corr_engine.pkl")
    logger.info("  Correlation engine saved.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("NBA Props Model TRAINING — VERSION 2026-02-28-v10")
    logger.info("Quantile Regression | Expert-reviewed features | Pinball loss")
    logger.info("=" * 60)

    if not _get_api_key():
        sys.exit("BDL_API_KEY not set.")
    logger.info("BDL_API_KEY ✓")

    stats_df, adv_df, odds_df = fetch_all_data()
    if stats_df.empty:
        sys.exit("No stats data.")

    training_df = build_training_table(stats_df, adv_df, odds_df)
    if training_df.empty:
        sys.exit("Training table empty.")

    results = {}
    for target in ALL_TARGETS:
        r = train_target_model(training_df, target)
        if r:
            results[target] = r

    fit_correlation_engine(training_df)

    meta = {
        "version":       "2026-02-28-v10",
        "trained_at":    datetime.utcnow().isoformat(),
        "train_seasons": TRAIN_SEASONS,
        "quantiles":     QUANTILES,
        "min_games":     MIN_GAMES,
        "architecture":  "quantile_regression_expert_v10",
        "targets":       results,
        "n_players":     int(training_df["player_id"].nunique()),
    }
    with open(MODEL_DIR / "training_meta.json","w") as f:
        json.dump(meta, f, indent=2, default=str)

    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE")
    for t, r in results.items():
        flag = "✓" if r.get("max_cal_error",1) < 0.05 else "⚠"
        logger.info(
            f"  {STAT_DISPLAY[t]:15s} feats={r['feature_count']:3d}  "
            f"MAE={r['median_mae']:.3f}  cal_err={r['max_cal_error']:.3f} {flag}"
        )
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
