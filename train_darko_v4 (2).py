#!/usr/bin/env python3
"""
train_darko_v4.py  VERSION: 2026-02-28-v9
=============================================
DARKO v4 — Quantile Regression Training Pipeline

Architecture:
  - NO sportsbook lines in training. Labels are real game outcomes only.
  - Trains Q10, Q20, Q25, Q33, Q40, Q50, Q60, Q67, Q75, Q80, Q90 per stat
    using LightGBM quantile regression (pinball loss — a proper scoring rule).
  - Validation via quantile calibration curves, not accuracy.
  - At inference time, quantile predictions interpolate to a CDF,
    and P(over line) is computed against the current sportsbook line.

Data pipeline:
  - Incremental: first run does full historical load (2023-2026).
  - Daily: fetches only new games since last stored date.
  - No props fetching — labels are box score outcomes only.
"""

import os, sys, json, logging, warnings
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
import lightgbm as lgb
import joblib

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
        get_advanced_stats_v2,
        build_game_context_map,
    )
    from feature_engineering import build_player_game_features, STATS
    from correlation_engine import quantile_calibration_report, QUANTILES
except ImportError as e:
    sys.exit(f"Import error: {e}\nEnsure bdl_client.py, feature_engineering.py, correlation_engine.py are present.")

DATA_DIR  = Path("data");        DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR = Path("model_cache"); MODEL_DIR.mkdir(exist_ok=True)

TRAIN_SEASONS = [2023, 2024, 2025]
MIN_GAMES     = 15
N_SPLITS      = 5

STAT_DISPLAY = {
    "pts": "Points", "reb": "Rebounds", "ast": "Assists",
    "fg3m": "Threes", "stl": "Steals", "blk": "Blocks",
}

LGB_QUANTILE_BASE = dict(
    objective="quantile", metric="quantile",
    n_estimators=1000, learning_rate=0.02,
    num_leaves=48, max_depth=8,
    feature_fraction=0.75, bagging_fraction=0.80, bagging_freq=1,
    reg_alpha=0.3, reg_lambda=2.0, min_child_samples=40, verbose=-1,
)

LGB_MINUTES = dict(
    objective="regression", metric="mae",
    n_estimators=800, learning_rate=0.02,
    num_leaves=48, max_depth=8,
    feature_fraction=0.75, bagging_fraction=0.80, bagging_freq=1,
    reg_alpha=0.3, reg_lambda=2.0, min_child_samples=40, verbose=-1,
)

ADV_FIELDS = [
    "usage_percentage","pace","possessions","pace_per_40","touches","passes",
    "effective_field_goal_percentage","true_shooting_percentage",
    "rebound_chances_total","rebound_chances_def","rebound_chances_off",
    "defended_at_rim_fga","defended_at_rim_fgm","defended_at_rim_fg_pct",
    "assist_percentage","assist_ratio","assist_to_turnover",
    "net_rating","offensive_rating","defensive_rating",
    "contested_shots","deflections","rebound_percentage","turnover_ratio",
]


def _flat(rec):
    player = rec.get("player", {}); game = rec.get("game", {}); team = rec.get("team", {})
    return {
        "player_id":       player.get("id"),
        "player_name":     f"{player.get('first_name','')} {player.get('last_name','')}".strip(),
        "game_id":         game.get("id"),
        "game_date":       pd.to_datetime(game.get("date","")[:10]),
        "season":          game.get("season"),
        "home_team_id":    (game.get("home_team") or {}).get("id") or game.get("home_team_id"),
        "visitor_team_id": (game.get("visitor_team") or {}).get("id") or game.get("visitor_team_id"),
        "team_id":         team.get("id"),
        "team_abbr":       team.get("abbreviation",""),
        "min":             parse_minutes(rec.get("min","0")),
        "pts":  float(rec.get("pts")  or 0), "reb":  float(rec.get("reb")  or 0),
        "ast":  float(rec.get("ast")  or 0), "fg3m": float(rec.get("fg3m") or 0),
        "stl":  float(rec.get("stl")  or 0), "blk":  float(rec.get("blk")  or 0),
        "fga":  float(rec.get("fga")  or 0), "fg3a": float(rec.get("fg3a") or 0),
        "fta":  float(rec.get("fta")  or 0), "ftm":  float(rec.get("ftm")  or 0),
        "fg_pct":    float(rec.get("fg_pct")    or 0),
        "fg3_pct":   float(rec.get("fg3_pct")   or 0),
        "ft_pct":    float(rec.get("ft_pct")    or 0),
        "oreb":      float(rec.get("oreb")      or 0),
        "dreb":      float(rec.get("dreb")      or 0),
        "turnover":  float(rec.get("turnover")  or 0),
        "pf":        float(rec.get("pf")        or 0),
        "plus_minus":float(rec.get("plus_minus")or 0),
    }


def _parse_adv(rec):
    pid = (rec.get("player") or {}).get("id")
    gid = (rec.get("game")   or {}).get("id")
    if not pid or not gid: return None
    r = {
        "player_id": pid, "game_id": gid,
        "game_date": pd.to_datetime((rec.get("game") or {}).get("date","")[:10]),
    }
    for f in ADV_FIELDS: r[f] = float(rec.get(f) or 0.0)
    return r


def _parse_odds(rec):
    try:
        return {
            "game_id":           rec["game_id"],
            "vendor":            rec.get("vendor",""),
            "total_value":       float(rec["total_value"])       if rec.get("total_value")       else None,
            "spread_home_value": float(rec["spread_home_value"]) if rec.get("spread_home_value") else None,
            "updated_at":        rec.get("updated_at",""),
        }
    except Exception: return None


def _last_stored_date(path, col="game_date"):
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
    last_date  = _last_stored_date(STATS_PATH)

    if last_date is None:
        logger.info("No existing data — performing FULL historical load...")
        fetch_start = f"{min(TRAIN_SEASONS)}-10-01"; is_initial = True
    else:
        fetch_start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d"); is_initial = False
        if fetch_start > yesterday:
            logger.info(f"Data current through {last_date.date()} — loading from disk.")
            return (
                pd.read_parquet(STATS_PATH),
                pd.read_parquet(ADV_PATH)  if ADV_PATH.exists()  else pd.DataFrame(),
                pd.read_parquet(ODDS_PATH) if ODDS_PATH.exists() else pd.DataFrame(),
            )
        logger.info(f"Incremental fetch: {fetch_start} → {yesterday}")

    fetch_end = yesterday

    logger.info("Fetching box scores...")
    new_stats_raw = []
    if is_initial:
        for season in TRAIN_SEASONS:
            s = f"{season}-10-01"; e = f"{season+1}-06-30"
            logger.info(f"  Season {season}...")
            batch = get_player_game_stats(start_date=s, end_date=e)
            new_stats_raw.extend(batch); logger.info(f"    {len(batch)} records")
    else:
        new_stats_raw = get_player_game_stats(start_date=fetch_start, end_date=fetch_end)
        logger.info(f"  {len(new_stats_raw)} new records")

    rows = [_flat(r) for r in new_stats_raw if r.get("player") and r.get("game",{}).get("id")]
    new_stats_df = pd.DataFrame(rows)
    if not new_stats_df.empty: new_stats_df = new_stats_df[new_stats_df["min"] >= 1]

    logger.info("Fetching advanced stats v2...")
    new_adv_raw = []
    if is_initial:
        for season in TRAIN_SEASONS:
            batch = get_advanced_stats_v2(start_date=f"{season}-10-01", end_date=f"{season+1}-06-30")
            new_adv_raw.extend(batch); logger.info(f"  Season {season}: {len(batch)} records")
    else:
        new_adv_raw = get_advanced_stats_v2(start_date=fetch_start, end_date=fetch_end)
        logger.info(f"  {len(new_adv_raw)} new adv records")
    adv_rows = [r for r in (_parse_adv(x) for x in new_adv_raw) if r]
    new_adv_df = pd.DataFrame(adv_rows)

    logger.info("Fetching game odds (totals/spreads)...")
    new_odds_raw = []
    cur = max(pd.Timestamp(fetch_start), pd.Timestamp(f"{min(TRAIN_SEASONS)}-10-01"))
    while cur <= pd.Timestamp(fetch_end):
        new_odds_raw.extend(get_game_odds(dates=[cur.strftime("%Y-%m-%d")])); cur += timedelta(days=1)
    odds_rows = [r for r in (_parse_odds(x) for x in new_odds_raw) if r]
    new_odds_df = pd.DataFrame(odds_rows)
    logger.info(f"  {len(odds_rows)} game odds records")

    def append_dedup(path, new_df, dedup_cols, sort_cols):
        if new_df.empty: return pd.read_parquet(path) if path.exists() else pd.DataFrame()
        if path.exists() and not is_initial:
            combined = pd.concat([pd.read_parquet(path), new_df], ignore_index=True)
        else: combined = new_df
        return combined.drop_duplicates(subset=dedup_cols, keep="last").sort_values(sort_cols).reset_index(drop=True)

    stats_df = append_dedup(STATS_PATH, new_stats_df, ["player_id","game_id"], ["player_id","game_date"])
    adv_df   = append_dedup(ADV_PATH,   new_adv_df,   ["player_id","game_id"], ["player_id","game_date"])
    odds_df  = append_dedup(ODDS_PATH,  new_odds_df,  ["game_id","vendor"],    ["game_id","updated_at"])

    if not stats_df.empty: stats_df.to_parquet(STATS_PATH, index=False)
    if not adv_df.empty:   adv_df.to_parquet(ADV_PATH, index=False)
    if not odds_df.empty:  odds_df.to_parquet(ODDS_PATH, index=False)

    logger.info(f"Data: {len(stats_df)} stats | {len(adv_df)} adv | {len(odds_df)} odds")
    return stats_df, adv_df, odds_df


def build_training_table(stats_df, adv_df, odds_df):
    """
    Build training table. Labels = actual stat outcomes. No lines, no props.
    One row per (player, game, stat).
    """
    logger.info("Building training table...")
    ctx_map = build_game_context_map(odds_df.to_dict("records")) if not odds_df.empty else {}
    adv_by_player = defaultdict(list)
    if not adv_df.empty:
        for _, r in adv_df.iterrows(): adv_by_player[int(r["player_id"])].append(r.to_dict())

    all_rows = []; skipped = 0
    players = list(stats_df.groupby("player_id"))
    total   = len(players)

    for idx, (player_id, pdata) in enumerate(players):
        pdata = pdata.sort_values("game_date").reset_index(drop=True)
        if len(pdata) < MIN_GAMES: continue
        padv = sorted(adv_by_player.get(int(player_id),[]), key=lambda x: x.get("game_date", pd.Timestamp("2000")))

        for i in range(MIN_GAMES, len(pdata)):
            cur   = pdata.iloc[i]; prior = pdata.iloc[:i]
            gid   = int(cur["game_id"]); tid = int(cur["team_id"] or 0)
            hid   = int(cur["home_team_id"] or 0); vid = int(cur["visitor_team_id"] or 0)
            is_home = int(tid == hid); opp_id = vid if is_home else hid
            td = str(cur["game_date"])[:10]; ctx = ctx_map.get(gid, {})

            opp_prior  = stats_df[(stats_df["team_id"]==opp_id)&(stats_df["game_date"]<cur["game_date"])]
            team_prior = stats_df[(stats_df["team_id"]==tid)   &(stats_df["game_date"]<cur["game_date"])]
            padv_i = [r for r in padv if pd.Timestamp(r.get("game_date",pd.Timestamp("2000"))) < cur["game_date"]]

            try:
                base = build_player_game_features(
                    player_id=int(player_id), prior_stats=prior, prior_adv=padv_i,
                    game_context=ctx, is_home=is_home, target_date=td,
                    team_game_stats=team_prior, injury_map={}, player_profile_map={},
                    opp_team_id=opp_id, opp_game_stats=opp_prior,
                )
            except Exception as e:
                logger.debug(f"Feature error p={player_id} g={gid}: {e}"); skipped += 1; continue

            for stat in STATS:
                all_rows.append({
                    **base,
                    "player_id": int(player_id), "player_name": str(cur.get("player_name","")),
                    "game_id": gid, "game_date": cur["game_date"],
                    "stat": stat, "actual": float(cur.get(stat, 0) or 0),
                })

        if (idx + 1) % 100 == 0:
            logger.info(f"  {idx+1}/{total} players | {len(all_rows)} rows")

    df = pd.DataFrame(all_rows)
    if df.empty:
        logger.error(f"Training table EMPTY. Skipped {skipped}. Check data pipeline.")
    else:
        logger.info(f"Training table: {len(df)} rows | {df['player_id'].nunique()} players | skipped={skipped}")
        df.to_parquet(DATA_DIR / "training_table.parquet", index=False)
    return df


def get_feature_cols(df):
    exclude = {"player_id","player_name","game_id","game_date","stat","actual"}
    return [c for c in df.columns if c not in exclude]


def train_minutes_model(stats_df, adv_df):
    logger.info("Training minutes model...")
    adv_by_p = defaultdict(list)
    if not adv_df.empty:
        for _, r in adv_df.iterrows(): adv_by_p[int(r["player_id"])].append(r.to_dict())
    rows = []
    for pid, pdata in stats_df.groupby("player_id"):
        pdata = pdata.sort_values("game_date").reset_index(drop=True)
        if len(pdata) < MIN_GAMES: continue
        padv = sorted(adv_by_p.get(int(pid),[]), key=lambda x: x.get("game_date",pd.Timestamp("2000")))
        for i in range(MIN_GAMES, len(pdata)):
            cur = pdata.iloc[i]; prior = pdata.iloc[:i]
            padv_i = [r for r in padv if pd.Timestamp(r.get("game_date",pd.Timestamp("2000"))) < cur["game_date"]]
            try:
                base = build_player_game_features(
                    player_id=int(pid), prior_stats=prior, prior_adv=padv_i,
                    game_context={}, is_home=0, target_date=str(cur["game_date"])[:10],
                    team_game_stats=pd.DataFrame(), injury_map={}, player_profile_map={},
                    opp_team_id=0, opp_game_stats=pd.DataFrame(),
                )
                rows.append({**base, "actual_min": float(cur["min"])})
            except Exception: continue
    if len(rows) < 200:
        logger.warning(f"Minutes: {len(rows)} rows — skipping"); return {}
    df = pd.DataFrame(rows)
    fcols = [c for c in df.columns if c not in {"player_id","actual_min"}]
    X = df[fcols].fillna(0).values; y = df["actual_min"].values.astype(float)
    tscv = TimeSeriesSplit(n_splits=N_SPLITS); oof = np.zeros(len(X))
    for tr, va in tscv.split(X):
        m = lgb.LGBMRegressor(**LGB_MINUTES); m.fit(X[tr],y[tr]); oof[va] = m.predict(X[va])
    mae = float(np.mean(np.abs(oof - y))); logger.info(f"  Minutes OOF MAE: {mae:.2f}")
    final = lgb.LGBMRegressor(**LGB_MINUTES); final.fit(X, y)
    joblib.dump(final, MODEL_DIR/"minutes_model.pkl"); joblib.dump(fcols, MODEL_DIR/"minutes_features.pkl")
    return {"oof_mae": mae}


def train_stat_model(training_df, stat):
    """
    Train Q10-Q90 quantile regression models for one stat.
    Pinball loss. Validated by quantile calibration curves.
    """
    logger.info(f"Training {STAT_DISPLAY[stat]}...")
    if training_df.empty or "stat" not in training_df.columns:
        logger.warning(f"  {stat}: empty — skipping"); return {}
    df = training_df[training_df["stat"]==stat].copy().sort_values("game_date").reset_index(drop=True)
    if len(df) < 500:
        logger.warning(f"  {stat}: {len(df)} rows — need 500+, skipping"); return {}

    fcols = get_feature_cols(df)
    X     = df[fcols].fillna(0).values
    y     = df["actual"].values.astype(float)
    n     = len(X)
    tr_end = int(n * 0.85)

    logger.info(f"  {stat}: {n} rows | {len(fcols)} features | train={tr_end} holdout={n-tr_end}")

    holdout_preds = {}
    for q in QUANTILES:
        params = {**LGB_QUANTILE_BASE, "alpha": q}
        # Train on train split only for calibration check
        m_cal = lgb.LGBMRegressor(**params)
        m_cal.fit(X[:tr_end], y[:tr_end])
        holdout_preds[q] = m_cal.predict(X[tr_end:])
        # Train final model on full dataset
        m_final = lgb.LGBMRegressor(**params)
        m_final.fit(X, y)
        joblib.dump(m_final, MODEL_DIR / f"q{int(q*100):02d}_{stat}.pkl")

    # Quantile calibration
    actuals_holdout = y[tr_end:]
    cal = quantile_calibration_report(actuals_holdout, holdout_preds)
    max_err = 0.0
    logger.info(f"  Calibration (empirical_q ≈ predicted_q = well calibrated):")
    for q, row in cal.items():
        err = row["error"]; max_err = max(max_err, err)
        flag = "⚠" if err > 0.05 else "✓"
        logger.info(f"    {flag} Q{int(q*100):02d}: pred={q:.2f}  empirical={row['empirical_q']:.3f}  err={err:.3f}")

    mae = float(np.mean(np.abs(holdout_preds[0.50] - actuals_holdout)))
    logger.info(f"  Holdout median MAE: {mae:.3f}")

    # Feature importance from Q50 model
    m50 = lgb.LGBMRegressor(**{**LGB_QUANTILE_BASE, "alpha": 0.50})
    m50.fit(X, y)
    fi = pd.DataFrame({"feature": fcols, "importance": m50.feature_importances_}).sort_values("importance", ascending=False)
    fi.to_csv(MODEL_DIR / f"feature_importance_{stat}.csv", index=False)
    logger.info(f"  Top-5: {fi['feature'].values[:5].tolist()}")

    joblib.dump(fcols, MODEL_DIR / f"features_{stat}.pkl")

    return {
        "stat": stat, "n_train": tr_end, "n_holdout": n - tr_end,
        "feature_count": len(fcols), "median_mae": round(mae, 4),
        "max_cal_error": round(max_err, 4),
        "calibration": {str(k): v for k, v in cal.items()},
    }


def main():
    logger.info("=" * 60)
    logger.info("DARKO v4 TRAINING — VERSION 2026-02-28-v9")
    logger.info("Quantile Regression | No lines in training | Pinball loss")
    logger.info("=" * 60)

    if not _get_api_key():
        sys.exit("BDL_API_KEY not set.")
    logger.info("BDL_API_KEY ✓")

    stats_df, adv_df, odds_df = fetch_all_data()
    if stats_df.empty: sys.exit("No stats data. Cannot train.")

    training_df = build_training_table(stats_df, adv_df, odds_df)
    if training_df.empty: sys.exit("Training table empty.")

    minutes_meta = train_minutes_model(stats_df, adv_df)

    stat_results = {}
    for stat in STATS:
        r = train_stat_model(training_df, stat)
        if r: stat_results[stat] = r

    meta = {
        "version":       "2026-02-28-v9",
        "trained_at":    datetime.utcnow().isoformat(),
        "train_seasons": TRAIN_SEASONS,
        "quantiles":     QUANTILES,
        "min_games":     MIN_GAMES,
        "architecture":  "quantile_regression_no_lines",
        "minutes_model": minutes_meta,
        "stats":         stat_results,
        "n_players":     int(training_df["player_id"].nunique()),
        "n_rows":        int(len(training_df)),
    }
    with open(MODEL_DIR / "training_meta.json", "w") as f:
        json.dump(meta, f, indent=2, default=str)

    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE")
    for stat, r in stat_results.items():
        flag = "✓" if r.get("max_cal_error", 1.0) < 0.05 else "⚠"
        logger.info(f"  {STAT_DISPLAY[stat]:10s} MAE={r['median_mae']:.3f}  max_cal_err={r['max_cal_error']:.3f} {flag}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
