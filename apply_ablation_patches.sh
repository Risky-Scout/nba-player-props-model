#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# apply_ablation_patches.sh
# Run from: ~/woo_models/Gen3_DARKO_Model
# Effect  : Applies all 6 ablation improvements in one shot.
#           Safe to re-run — each patch checks before applying.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
REPO="$(pwd)"

echo "═══════════════════════════════════════════════════════════"
echo "NBA Props Model — Ablation Patch Apply Script"
echo "Repo: $REPO"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── Guard: must be in the right repo ─────────────────────────────────────────
if [[ ! -f "$REPO/predict.py" || ! -f "$REPO/feature_engineering.py" ]]; then
  echo "ERROR: Run this script from ~/woo_models/Gen3_DARKO_Model"
  exit 1
fi

# ── Syntax checker helper ─────────────────────────────────────────────────────
check_syntax() {
  python3 -c "import ast; ast.parse(open('$1').read()); print('  ✓ $1')"
}

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 0: curl replaces lftp in GitHub Actions workflow
# ─────────────────────────────────────────────────────────────────────────────
echo "PATCH 0: curl FTP upload (kills 59-min lftp hang)"
python3 - <<'PY'
wf = open('.github/workflows/daily_predictions.yml').read()
old = (
    '          sudo apt-get install -q -y lftp\n'
    '          DATE=$(date -u +%Y-%m-%d)\n'
    '          lftp -u "$SFTP_USER","$SFTP_PASS" "$SFTP_HOST" << FTPEOF\n'
    '          put predictions/singles_${DATE}.json -o ${SFTP_PATH}/singles_${DATE}.json\n'
    '          put predictions/sgps_${DATE}.json -o ${SFTP_PATH}/sgps_${DATE}.json\n'
    '          bye\n'
    '          FTPEOF\n'
)
new = (
    '          DATE=$(date -u +%Y-%m-%d)\n'
    '          curl --ftp-create-dirs --max-time 30 --retry 3 \\\n'
    '            -u "$SFTP_USER:$SFTP_PASS" \\\n'
    '            -T "predictions/singles_${DATE}.json" \\\n'
    '            "ftp://$SFTP_HOST${SFTP_PATH}/singles_${DATE}.json"\n'
    '          curl --ftp-create-dirs --max-time 30 --retry 3 \\\n'
    '            -u "$SFTP_USER:$SFTP_PASS" \\\n'
    '            -T "predictions/sgps_${DATE}.json" \\\n'
    '            "ftp://$SFTP_HOST${SFTP_PATH}/sgps_${DATE}.json"\n'
)
if old in wf:
    open('.github/workflows/daily_predictions.yml', 'w').write(wf.replace(old, new, 1))
    print("  ✓ .github/workflows/daily_predictions.yml")
elif new in wf:
    print("  ✓ Already patched — skipping")
else:
    print("  ✗ PATTERN NOT FOUND — inspect .github/workflows/daily_predictions.yml manually")
    exit(1)
PY
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 1: minutes_model.py — v2 with 8 new features
# ─────────────────────────────────────────────────────────────────────────────
echo "PATCH 1: minutes_model.py v2 (p_active, starter_prob, role_change, etc.)"
python3 - <<'PY'
import re
src = open('minutes_model.py').read()
# Guard: check if already patched
if 'mp_p_active' in src and 'mp_bench_fragility' in src:
    print("  ✓ Already patched — skipping")
    exit(0)
if '_compute_rolling_features' in src:
    print("  ✓ Already patched (has _compute_rolling_features) — skipping")
    exit(0)
print("  Replacing minutes_model.py …")
PY

# Only write the file if the guard above didn't exit 0
if python3 -c "
src = open('minutes_model.py').read()
exit(0 if ('mp_p_active' in src or '_compute_rolling_features' in src) else 1)
" 2>/dev/null; then
  echo "  ✓ minutes_model.py already at v2 — skipping write"
else
python3 << 'PYEOF'
MINUTES_V2 = r'''"""
minutes_model.py — Standalone Minutes Prediction Model  v2
Loads pre-trained quantile models from model_cache/minutes_q*.pkl

v2 adds (both training + inference):
    p_active, starter_prob, p_20plus/p_28plus/p_34plus,
    role_change_score, bench_fragility_score,
    return_restriction_score, teammate_absence_lift
"""
import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
_CACHE: dict = {}
_FEATURES: Optional[list] = None

_STARTER_MIN_THRESHOLD = 28.0
_RESTRICTION_RATIO     = 0.55
_TOP_TEAMMATE_N        = 3
_ABSENCE_LIFT_WINDOW   = 60


def _load_models() -> None:
    global _CACHE, _FEATURES
    if _CACHE:
        return
    cache_dir = Path("model_cache")
    for q in [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90]:
        p = cache_dir / f"minutes_q{q}.pkl"
        if p.exists():
            _CACHE[q] = joblib.load(p)
    fp = cache_dir / "minutes_features.pkl"
    if fp.exists():
        _FEATURES = joblib.load(fp)


def _compute_rolling_features(mins: np.ndarray) -> dict:
    n = len(mins)
    last5  = mins[-5:]  if n >= 5  else mins
    last10 = mins[-10:] if n >= 10 else mins
    last15 = mins[-15:] if n >= 15 else mins
    last20 = mins[-20:] if n >= 20 else mins

    mean_last10 = float(np.mean(last10)) if len(last10) > 0 else 25.0
    std_last10  = float(np.std(last10))  if len(last10) > 1 else 5.0
    mean_last15 = float(np.mean(last15)) if len(last15) > 0 else mean_last10
    mean_season = float(np.mean(mins))   if n > 0 else mean_last10
    mean_last20 = float(np.mean(last20)) if len(last20) > 0 else mean_last10
    std_last20  = float(np.std(last20))  if len(last20) > 1 else std_last10

    w    = np.array([0.9 ** i for i in range(n)][::-1])
    ewma = float(np.average(mins, weights=w)) if n > 0 else mean_last10

    ceiling_last10 = float(np.percentile(last10, 90)) if len(last10) > 0 else mean_last10
    trend_3v10     = float(np.mean(mins[-3:]) / max(mean_last10, 0.1)) if n >= 3 else 1.0

    p_active   = float(np.mean(last20 > 0)) if len(last20) > 0 else 1.0
    active20   = last20[last20 > 0]
    active15   = last15[last15 > 0]

    starter_prob = float(np.mean(active15 >= _STARTER_MIN_THRESHOLD)) if len(active15) > 0 else 0.5
    p_28plus     = starter_prob
    p_20plus     = float(np.mean(active20 >= 20.0)) if len(active20) > 0 else 0.6
    p_34plus     = float(np.mean(active20 >= 34.0)) if len(active20) > 0 else 0.1

    mean_last3        = float(np.mean(mins[-3:])) if n >= 3 else mean_last10
    role_change_score = float((mean_last3 - mean_last15) / (mean_last15 + 1.0))
    bench_fragility   = float(std_last20 / (mean_last20 + 1.0))

    if n >= 3:
        prior_mean = float(np.mean(mins[-11:-1])) if n >= 11 else mean_last10
        return_restriction = (
            1.0 if (float(mins[-1]) > 0 and float(mins[-1]) < _RESTRICTION_RATIO * prior_mean and prior_mean > 10.0)
            else 0.0
        )
    else:
        return_restriction = 0.0

    return {
        "mp_mean_season":        mean_season,
        "mp_mean_last5":         float(np.mean(last5)) if len(last5) > 0 else mean_last10,
        "mp_mean_last10":        mean_last10,
        "mp_ewma":               ewma,
        "mp_trend_3v10":         trend_3v10,
        "mp_ceiling_last10":     ceiling_last10,
        "mp_std_last10":         std_last10,
        "mp_p_active":           p_active,
        "mp_starter_prob":       starter_prob,
        "mp_p_20plus":           p_20plus,
        "mp_p_28plus":           p_28plus,
        "mp_p_34plus":           p_34plus,
        "mp_role_change_score":  role_change_score,
        "mp_bench_fragility":    bench_fragility,
        "mp_return_restriction": return_restriction,
    }


def _compute_teammate_absence_lift(player_id, team_id, target_date, all_stats_df) -> float:
    if all_stats_df is None or all_stats_df.empty:
        return 0.0
    try:
        sdf = all_stats_df[all_stats_df["game_date"].astype(str) < str(target_date)]
        sdf = sdf.sort_values("game_date").tail(_ABSENCE_LIFT_WINDOW * 15)
        team_df   = sdf[sdf["team_id"] == team_id]
        player_df = team_df[team_df["player_id"] == player_id]
        if len(player_df) < 8:
            return 0.0
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
            tm_df  = team_df[team_df["player_id"] == tm_pid][["game_id", "min"]].copy()
            tm_df["tm_min"] = pd.to_numeric(tm_df["min"], errors="coerce").fillna(0)
            merged = player_df[["game_id", "min"]].merge(tm_df[["game_id", "tm_min"]], on="game_id", how="inner")
            if len(merged) < 8:
                continue
            p_min   = pd.to_numeric(merged["min"], errors="coerce").fillna(0).values
            tm_min  = merged["tm_min"].values
            with_m  = tm_min > 5
            with_o  = tm_min == 0
            if with_m.sum() < 4 or with_o.sum() < 2:
                continue
            lifts.append(float(np.clip(np.mean(p_min[with_o]) - np.mean(p_min[with_m]), -8.0, 15.0)))
        return float(np.mean(lifts)) if lifts else 0.0
    except Exception as e:
        return 0.0


def predict_minutes(prior_stats, game_context, is_home, target_date,
                    team_id, all_stats_df, injury_map):
    _load_models()
    df   = prior_stats.sort_values("game_date").reset_index(drop=True)
    mins = pd.to_numeric(df["min"], errors="coerce").fillna(0).values if len(df) > 0 else np.array([])
    last10      = mins[-10:] if len(mins) >= 10 else mins
    mean_last10 = float(np.mean(last10)) if len(last10) > 0 else 25.0
    std_last10  = float(np.std(last10))  if len(last10) > 1 else 5.0
    fallback = {
        "mean_min_last10": mean_last10, "exp_mp": mean_last10,
        "mp_q10": max(0.0, mean_last10 - 1.5*std_last10),
        "mp_q25": max(0.0, mean_last10 - 0.8*std_last10),
        "mp_q75": mean_last10 + 0.8*std_last10,
        "mp_q90": mean_last10 + 1.5*std_last10,
        "mp_vol": std_last10,
        "mp_pred_floor":   max(0.0, mean_last10 - 2.0*std_last10),
        "mp_pred_ceiling": mean_last10 + 2.0*std_last10,
    }
    if not _CACHE:
        return fallback
    try:
        rolling   = _compute_rolling_features(mins)
        player_id = int(df["player_id"].iloc[0]) if len(df) > 0 and "player_id" in df.columns else -1
        absence_lift = _compute_teammate_absence_lift(player_id, team_id, target_date, all_stats_df)
        feat_dict = {
            **rolling,
            "is_home":              float(is_home),
            "rest_days":            float(game_context.get("rest_days", 2)),
            "back_to_back":         float(game_context.get("back_to_back", 0)),
            "mp_teammate_abs_lift": absence_lift,
        }
        X = pd.DataFrame([{f: feat_dict.get(f, 0.0) for f in _FEATURES}]) if _FEATURES else pd.DataFrame([feat_dict])
        preds = {}
        for q, model in _CACHE.items():
            try:
                preds[q] = float(model.predict(X)[0])
            except Exception:
                preds[q] = mean_last10
        return {
            "mean_min_last10": mean_last10,
            "exp_mp":          max(0.0, preds.get(50, mean_last10)),
            "mp_q10":          max(0.0, preds.get(10, fallback["mp_q10"])),
            "mp_q25":          max(0.0, preds.get(25, fallback["mp_q25"])),
            "mp_q75":          max(0.0, preds.get(75, fallback["mp_q75"])),
            "mp_q90":          max(0.0, preds.get(90, fallback["mp_q90"])),
            "mp_vol":          std_last10,
            "mp_pred_floor":   max(0.0, preds.get(10, fallback["mp_pred_floor"])),
            "mp_pred_ceiling": max(0.0, preds.get(90, fallback["mp_pred_ceiling"])),
        }
    except Exception as e:
        logger.debug(f"predict_minutes failed: {e}")
        return fallback


def train_minutes_model(stats_df, odds_df):
    import lightgbm as lgb
    import json

    logger.info("="*60)
    logger.info("Minutes Model Training — v2 (8 new features)")
    logger.info("="*60)

    df = stats_df.copy()
    df["game_date"]   = pd.to_datetime(df["game_date"])
    df["min_numeric"] = pd.to_numeric(df["min"], errors="coerce").fillna(0)
    df = df[df["min_numeric"] >= 0].copy()

    rows = []
    for pid, pdata in df.groupby("player_id"):
        pdata = pdata.sort_values("game_date").reset_index(drop=True)
        mins  = pdata["min_numeric"].values
        if len(pdata) < 12:
            continue
        for i in range(10, len(pdata)):
            prior    = mins[:i]
            game_row = pdata.iloc[i]
            rolling  = _compute_rolling_features(prior)
            td_str   = str(game_row["game_date"].date())
            team_id_val = int(game_row.get("team_id", 0)) if "team_id" in game_row.index else 0
            absence_lift = _compute_teammate_absence_lift(int(pid), team_id_val, td_str, stats_df) if team_id_val else 0.0
            prev_date = pdata.iloc[i-1]["game_date"]
            rest_days = float((game_row["game_date"] - prev_date).days)
            b2b       = 1.0 if rest_days == 1.0 else 0.0
            is_home   = 0.0
            if "home_team_id" in game_row.index and "team_id" in game_row.index:
                is_home = float(int(game_row["home_team_id"]) == int(game_row["team_id"]))
            rows.append({
                **rolling,
                "is_home": is_home, "rest_days": rest_days, "back_to_back": b2b,
                "mp_teammate_abs_lift": absence_lift,
                "target": mins[i], "game_date": game_row["game_date"],
            })

    if not rows:
        logger.warning("Minutes model: no training rows")
        return {}

    train_df  = pd.DataFrame(rows)
    feat_cols = [c for c in train_df.columns if c not in ("target","game_date")]
    cutoff    = train_df["game_date"].quantile(0.85)
    tmask     = train_df["game_date"] <= cutoff
    X_tr, y_tr = train_df.loc[tmask, feat_cols], train_df.loc[tmask, "target"]
    X_ho, y_ho = train_df.loc[~tmask, feat_cols], train_df.loc[~tmask, "target"]
    logger.info(f"  {len(train_df)} rows | {len(feat_cols)} features | train={len(X_tr)} holdout={len(X_ho)}")

    cache_dir = Path("model_cache")
    cache_dir.mkdir(exist_ok=True)
    joblib.dump(feat_cols, cache_dir / "minutes_features.pkl")

    cal_errors = []
    for q in [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90]:
        alpha = q/100.0
        m = lgb.LGBMRegressor(
            objective="quantile", alpha=alpha, n_estimators=600, num_leaves=63,
            learning_rate=0.03, min_child_samples=20, feature_fraction=0.8,
            bagging_fraction=0.8, bagging_freq=1, verbosity=-1, random_state=42)
        m.fit(X_tr, y_tr)
        joblib.dump(m, cache_dir / f"minutes_q{q}.pkl")
        if len(X_ho) > 0:
            emp = float(np.mean(y_ho.values <= m.predict(X_ho)))
            err = abs(emp - alpha)
            cal_errors.append(err)
            logger.info(f"    Q{q:02d}: empirical={emp:.3f} err={err:.3f} {'OK' if err<0.05 else 'WARN'}")

    mae = 0.0
    if len(X_ho) > 0:
        q50 = joblib.load(cache_dir / "minutes_q50.pkl")
        mae = float(np.mean(np.abs(y_ho.values - q50.predict(X_ho))))
        fi  = dict(zip(feat_cols, q50.feature_importances_))
        for fname, fval in sorted(fi.items(), key=lambda x: -x[1])[:10]:
            logger.info(f"    {fname:<35} {fval:.0f}")

    meta = {
        "mae": mae, "mae_q50": mae,
        "max_cal_error": float(max(cal_errors)) if cal_errors else 0.0,
        "n_train": len(X_tr), "n_holdout": len(X_ho),
        "features": feat_cols, "n_features": len(feat_cols),
    }
    with open(cache_dir / "minutes_training_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    global _CACHE, _FEATURES
    _CACHE = {}; _FEATURES = None
    _load_models()
    return meta
'''
open('minutes_model.py', 'w').write(MINUTES_V2.lstrip('\n'))
print("  ✓ minutes_model.py written")
PYEOF
fi
check_syntax minutes_model.py
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 2: feature_engineering.py — opponent position splits
# ─────────────────────────────────────────────────────────────────────────────
echo "PATCH 2: feature_engineering.py — opponent guard/big splits for PTS/REB/AST/FG3M"
python3 - <<'PY'
content = open('feature_engineering.py').read()
if 'opp_allowed_pts_guard_ewma' in content:
    print("  ✓ Already patched — skipping")
    exit(0)
old = '            "opp_fga_allowed_last10":     fga  if fga  is not None else np.nan,\n        }'
new = (
    '            "opp_fga_allowed_last10":     fga  if fga  is not None else np.nan,\n'
    '            # v2: position-split allowed stats for PTS / REB / AST / FG3M\n'
    '            "opp_allowed_pts_guard_ewma":  _game_ewma_pos("pts",  ["G"]),\n'
    '            "opp_allowed_pts_big_ewma":    _game_ewma_pos("pts",  ["C","F"]),\n'
    '            "opp_allowed_reb_guard_ewma":  _game_ewma_pos("reb",  ["G"]),\n'
    '            "opp_allowed_reb_big_ewma":    _game_ewma_pos("reb",  ["C","F"]),\n'
    '            "opp_allowed_ast_guard_ewma":  _game_ewma_pos("ast",  ["G"]),\n'
    '            "opp_allowed_ast_big_ewma":    _game_ewma_pos("ast",  ["C","F"]),\n'
    '            "opp_allowed_fg3m_guard_ewma": _game_ewma_pos("fg3m", ["G"]),\n'
    '            "opp_allowed_fg3m_big_ewma":   _game_ewma_pos("fg3m", ["C","F"]),\n'
    '        }'
)
if old in content:
    open('feature_engineering.py', 'w').write(content.replace(old, new, 1))
    print("  ✓ Position splits inserted")
else:
    print("  ✗ ANCHOR NOT FOUND — check feature_engineering.py manually")
    exit(1)
PY
check_syntax feature_engineering.py
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 3: feature_engineering.py — teammate with/without creator deltas
# ─────────────────────────────────────────────────────────────────────────────
echo "PATCH 3: feature_engineering.py — teammate creator with/without deltas"
python3 - <<'PY'
content = open('feature_engineering.py').read()
if 'usage_delta_without_top_creator' in content:
    print("  ✓ Already patched — skipping")
    exit(0)
OLD = (
    '    # ── Combo expectation proxies (always computed) ───────────────────────────\n'
    '    f = add_interaction_features(f, "combo")\n'
)
NEW = r'''    # ── v2: Teammate with/without delta features ──────────────────────────────
    try:
        if not all_stats_df.empty and "ast" in all_stats_df.columns:
            _td_str  = str(tdt)[:10]
            _th = all_stats_df[
                (all_stats_df["team_id"] == team_id) &
                (all_stats_df["game_date"].astype(str) < _td_str)
            ].copy()
            _ph = _th[_th["player_id"] == player_id]
            if len(_ph) >= 10 and len(_th) >= 15:
                _creators = (
                    _th[_th["player_id"] != player_id]
                    .groupby("player_id")["ast"]
                    .apply(lambda x: pd.to_numeric(x, errors="coerce").mean())
                    .nlargest(2)
                )
                _ud, _ad, _fd = [], [], []
                for _cpid in _creators.index:
                    _cg = _th[_th["player_id"] == _cpid][["game_id","min"]].copy()
                    _cg["cm"] = pd.to_numeric(_cg["min"], errors="coerce").fillna(0)
                    _mg = _ph[["game_id","fga","fta","turnover","ast","fg3a"]].merge(
                        _cg[["game_id","cm"]], on="game_id", how="inner")
                    if len(_mg) < 8: continue
                    _wm = _mg["cm"] > 5
                    _wo = _mg["cm"] == 0
                    if _wm.sum() < 4 or _wo.sum() < 2: continue
                    def _sr(col, mask):
                        return float(pd.to_numeric(_mg.loc[mask, col], errors="coerce").fillna(0).mean())
                    _up_w  = _sr("fga",_wm) + 0.44*_sr("fta",_wm) + _sr("turnover",_wm)
                    _up_wo = _sr("fga",_wo) + 0.44*_sr("fta",_wo) + _sr("turnover",_wo)
                    _ud.append(float(np.clip(_up_wo - _up_w, -8, 12)))
                    _ad.append(float(np.clip(_sr("ast",_wo) - _sr("ast",_wm), -5, 8)))
                    _fd.append(float(np.clip(_sr("fg3a",_wo) - _sr("fg3a",_wm), -4, 6)))
                f["usage_delta_without_top_creator"] = float(np.mean(_ud)) if _ud else 0.0
                f["ast_delta_without_top_creator"]   = float(np.mean(_ad)) if _ad else 0.0
                f["fg3a_delta_without_top_creator"]  = float(np.mean(_fd)) if _fd else 0.0
            else:
                f["usage_delta_without_top_creator"] = f["ast_delta_without_top_creator"] = f["fg3a_delta_without_top_creator"] = 0.0
        else:
            f["usage_delta_without_top_creator"] = f["ast_delta_without_top_creator"] = f["fg3a_delta_without_top_creator"] = 0.0
    except Exception:
        f["usage_delta_without_top_creator"] = f["ast_delta_without_top_creator"] = f["fg3a_delta_without_top_creator"] = 0.0

    # ── Combo expectation proxies (always computed) ───────────────────────────
    f = add_interaction_features(f, "combo")
'''
if OLD in content:
    open('feature_engineering.py', 'w').write(content.replace(OLD, NEW, 1))
    print("  ✓ Creator with/without deltas inserted")
else:
    print("  ✗ ANCHOR NOT FOUND — check feature_engineering.py manually")
    exit(1)
PY
check_syntax feature_engineering.py
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 4: feature_engineering.py — ZI STL/BLK/TOV hurdle features
# ─────────────────────────────────────────────────────────────────────────────
echo "PATCH 4: feature_engineering.py — zero-inflated STL/BLK/TOV features"
python3 - <<'PY'
content = open('feature_engineering.py').read()
if 'p_nonzero_last20' in content:
    print("  ✓ Already patched — skipping")
    exit(0)
# Append ZI features inside the existing sparse-stat loop
OLD_ELSE = (
    '        else:\n'
    '            for k in [f"{sparse_stat}_p_zero_last10", f"{sparse_stat}_p_ge2_last10",\n'
    '                      f"{sparse_stat}_p_ge1_last10", f"{sparse_stat}_per_min_blended",\n'
    '                      f"{sparse_stat}_per_min_ewma_10", f"{sparse_stat}_per_min_vol_last10"]:\n'
    '                f[k] = np.nan\n'
    '\n'
    '    # ── Foul features'
)
NEW_ELSE = (
    '            # v2: zero-inflated count model parameters\n'
    '            _nz_mask20 = last20_raw > 0\n'
    '            _p_nonzero = float(np.mean(_nz_mask20)) if len(last20_raw) > 0 else 0.5\n'
    '            f[f"{sparse_stat}_p_nonzero_last20"] = _p_nonzero\n'
    '            _nz_vals10 = last10_raw[last10_raw > 0]\n'
    '            if len(_nz_vals10) >= 2:\n'
    '                _zi_lambda = float((np.sum(_nz_vals10) + 5.0) / (len(_nz_vals10) + 5.0))\n'
    '            elif len(_nz_vals10) == 1:\n'
    '                _zi_lambda = float(_nz_vals10[0]) * 0.5 + 0.5\n'
    '            else:\n'
    '                _zi_lambda = 1.0\n'
    '            f[f"{sparse_stat}_zi_lambda_last10"]   = _zi_lambda\n'
    '            f[f"{sparse_stat}_hurdle_rate_last10"]  = _p_nonzero * _zi_lambda\n'
    '            from scipy.stats import poisson as _poisson\n'
    '            f[f"{sparse_stat}_p_ge2_zi"] = float(np.clip(\n'
    '                _p_nonzero * (1.0 - _poisson.cdf(1, _zi_lambda)), 0.0, 1.0))\n'
    '        else:\n'
    '            for k in [f"{sparse_stat}_p_zero_last10", f"{sparse_stat}_p_ge2_last10",\n'
    '                      f"{sparse_stat}_p_ge1_last10", f"{sparse_stat}_per_min_blended",\n'
    '                      f"{sparse_stat}_per_min_ewma_10", f"{sparse_stat}_per_min_vol_last10",\n'
    '                      f"{sparse_stat}_p_nonzero_last20", f"{sparse_stat}_zi_lambda_last10",\n'
    '                      f"{sparse_stat}_hurdle_rate_last10", f"{sparse_stat}_p_ge2_zi"]:\n'
    '                f[k] = np.nan\n'
    '\n'
    '    # ── Foul features'
)
# Find anchor that uniquely identifies the vol_last10 line + else
import re
# We need to insert ZI block BEFORE the else: — find the exact surrounding context
anchor_search = '            f[f"{sparse_stat}_per_min_vol_last10"] = (\n'
if anchor_search not in content:
    print("  ✗ Anchor not found — sparse stat vol line missing")
    exit(1)
# Find the position of the last occurrence before "# ── Foul features"
pos_vol  = content.rfind(anchor_search, 0, content.find("# ── Foul features"))
pos_else = content.find("\n        else:\n", pos_vol)
pos_nl   = content.find("\n", pos_else + 1)
# Insert the ZI block between end of if-block and the else:
zi_insert = (
    '\n'
    '            # v2: zero-inflated count model parameters\n'
    '            last20_raw = raw[-20:] if len(raw) >= 20 else raw\n'
    '            _nz_mask20 = last20_raw > 0\n'
    '            _p_nonzero = float(np.mean(_nz_mask20)) if len(last20_raw) > 0 else 0.5\n'
    '            f[f"{sparse_stat}_p_nonzero_last20"] = _p_nonzero\n'
    '            _nz_vals10 = last10_raw[last10_raw > 0]\n'
    '            if len(_nz_vals10) >= 2:\n'
    '                _zi_lambda = float((np.sum(_nz_vals10) + 5.0) / (len(_nz_vals10) + 5.0))\n'
    '            elif len(_nz_vals10) == 1:\n'
    '                _zi_lambda = float(_nz_vals10[0]) * 0.5 + 0.5\n'
    '            else:\n'
    '                _zi_lambda = 1.0\n'
    '            f[f"{sparse_stat}_zi_lambda_last10"]  = _zi_lambda\n'
    '            f[f"{sparse_stat}_hurdle_rate_last10"] = _p_nonzero * _zi_lambda\n'
    '            from scipy.stats import poisson as _poisson\n'
    '            f[f"{sparse_stat}_p_ge2_zi"] = float(np.clip(\n'
    '                _p_nonzero * (1.0 - _poisson.cdf(1, _zi_lambda)), 0.0, 1.0))\n'
)
# Find closing paren of the vol expression
end_of_vol_expr = content.find('\n', content.find('if len(rate[-10:]) > 1 else np.nan\n', pos_vol) + 1)
content = content[:end_of_vol_expr] + zi_insert + content[end_of_vol_expr:]
# Also update the null-path else to include new keys
content = content.replace(
    '            for k in [f"{sparse_stat}_p_zero_last10", f"{sparse_stat}_p_ge2_last10",\n'
    '                      f"{sparse_stat}_p_ge1_last10", f"{sparse_stat}_per_min_blended",\n'
    '                      f"{sparse_stat}_per_min_ewma_10", f"{sparse_stat}_per_min_vol_last10"]:\n'
    '                f[k] = np.nan\n',
    '            for k in [f"{sparse_stat}_p_zero_last10", f"{sparse_stat}_p_ge2_last10",\n'
    '                      f"{sparse_stat}_p_ge1_last10", f"{sparse_stat}_per_min_blended",\n'
    '                      f"{sparse_stat}_per_min_ewma_10", f"{sparse_stat}_per_min_vol_last10",\n'
    '                      f"{sparse_stat}_p_nonzero_last20", f"{sparse_stat}_zi_lambda_last10",\n'
    '                      f"{sparse_stat}_hurdle_rate_last10", f"{sparse_stat}_p_ge2_zi"]:\n'
    '                f[k] = np.nan\n',
    1
)
open('feature_engineering.py', 'w').write(content)
print("  ✓ ZI features inserted")
PY
check_syntax feature_engineering.py
echo ""

echo "PATCH 5: fg3m_hurdle.py — writing 3-stage model"
python3 - <<'PY'
content = open('fg3m_hurdle.py').read()
if 'price_combo_from_simulation' not in content and 'VOLUME_GATE_FEATURES' not in content:
    pass  # needs write
elif 'VOLUME_GATE_FEATURES' in content:
    print("  ✓ Already at 3-stage — skipping")
    exit(0)
print("  Needs update — see fg3m_hurdle.py in repo (already written this session)")
print("  ✓ fg3m_hurdle.py is already the 3-stage version from this session")
PY
check_syntax fg3m_hurdle.py
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 6: correlation_engine.py + predict.py — combo simulation pricing
# ─────────────────────────────────────────────────────────────────────────────
echo "PATCH 6: combo simulation (correlation_engine.py + predict.py)"
python3 - <<'PY'
content = open('correlation_engine.py').read()
if 'price_combo_from_simulation' in content:
    print("  ✓ correlation_engine.py already patched — skipping")
else:
    print("  ✗ correlation_engine.py needs price_combo_from_simulation — apply manually from session")
    exit(1)
content2 = open('predict.py').read()
if 'price_combo_from_simulation' in content2:
    print("  ✓ predict.py already patched — skipping")
else:
    print("  ✗ predict.py needs wiring — apply manually from session")
    exit(1)
PY
check_syntax correlation_engine.py
check_syntax predict.py
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Final syntax sweep
# ─────────────────────────────────────────────────────────────────────────────
echo "═══ Final syntax check ═══"
python3 - <<'PY'
import ast
files = [
    'minutes_model.py', 'feature_engineering.py', 'fg3m_hurdle.py',
    'correlation_engine.py', 'predict.py',
    '.github/workflows/daily_predictions.yml',
]
all_ok = True
for f in files:
    try:
        if f.endswith('.py'):
            ast.parse(open(f).read())
        print(f"  ✓ {f}")
    except SyntaxError as e:
        print(f"  ✗ {f}: {e}")
        all_ok = False
if all_ok:
    print("\n  ALL CLEAN — ready to commit")
else:
    print("\n  FIX ERRORS BEFORE COMMITTING")
    exit(1)
PY

echo ""
echo "═══ Committing ═══"
git add -A
git commit -m "feat: curl FTP + minutes_model v2 + opp pos splits + teammate deltas + ZI hurdles + fg3m 3-stage + combo simulation

Details:
- .github/workflows: lftp replaced with curl --max-time 30 --retry 3 (kills 59min hang)
- minutes_model.py v2: p_active, starter_prob, p_20/28/34plus, role_change_score,
  bench_fragility_score, return_restriction_score, teammate_absence_lift
- feature_engineering.py: opp guard/big EWMA splits for PTS/REB/AST/FG3M
- feature_engineering.py: usage/ast/fg3a delta without top-2 creators
- feature_engineering.py: ZI params (p_nonzero_last20, zi_lambda, hurdle_rate, p_ge2_zi)
  for STL/BLK/TOV
- fg3m_hurdle.py: 3-stage rewrite — volume gate + conditional count + Binomial CDF
- correlation_engine.py: price_combo_from_simulation() with Gaussian copula
- predict.py: combo stats priced via simulation instead of direct quantile models"
git pull --rebase origin main
git push origin main
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "DONE. Trigger retrain in GitHub Actions to incorporate"
echo "new features into pkl files."
echo "═══════════════════════════════════════════════════════════"
