# Issue 15 fix: dynamic league 3P% prior
_LEAGUE_3P_PRIOR = 0.365

# ── Profiling counters (runtime-unblock pass 2026-04-22) ─────────────────────
# Gated by PROFILE_BUILD_TABLE env var; zero-overhead when off.
import os as _prof_os
import time as _prof_time
PROFILE_BUILD_TABLE = _prof_os.environ.get("PROFILE_BUILD_TABLE", "0") == "1"
_OPP_DEF_STATS: dict = {
    "hits": 0,
    "misses": 0,
    "total_s": 0.0,
    "hit_s": 0.0,
    "miss_s": 0.0,
    "miss_copy_s": 0.0,
    "miss_groupby_s": 0.0,
}

# Per-block accumulators inside build_player_game_features. Populated only
# when PROFILE_BUILD_TABLE=1.
_BPGF_STATS: dict = {}

_BPGF_KEYS = (
    "df_sort_reset",
    "minutes_model_features",
    "predict_minutes",
    "rate_stats_loop",
    "usage_proxy",
    "fg3m_block",
    "sparse_zi_loop",
    "foul_block",
    "per_min_aliases",
    "prior_adv_block",
    "safe_gated_block",
    "schedule_features",
    "game_script_features",
    "advanced_stats_block",
    "opponent_defensive_features",
    "vacated_block",
    "combo_interactions",
    "player_metadata_tail",
)


def reset_profile_counters() -> None:
    for k in _OPP_DEF_STATS:
        _OPP_DEF_STATS[k] = 0 if isinstance(_OPP_DEF_STATS[k], int) else 0.0
    _BPGF_STATS.clear()
    for k in _BPGF_KEYS:
        _BPGF_STATS[k] = 0.0


def snapshot_profile_counters() -> dict:
    out = dict(_OPP_DEF_STATS)
    for k in _BPGF_KEYS:
        out[f"bpgf_{k}_s"] = _BPGF_STATS.get(k, 0.0)
    return out

def set_league_3p_prior(fg3m_series, fg3a_series):
    global _LEAGUE_3P_PRIOR
    total_made = float(fg3m_series.sum())
    total_att  = float(fg3a_series.sum())
    if total_att > 1000:
        _LEAGUE_3P_PRIOR = round(total_made / total_att, 4)

"""
feature_engineering.py — NBA Props Model Feature Engineering
VERSION: 2026-03-13-v14

MAJOR CHANGES FROM v12 (based on feature importance analysis of 1,026 graded picks):

CUTS (noise reduction):
  - Removed entire ADV_FIELDS_EXPANDED block (28 fields, 0% importance)
    Replaced with ADV_FIELDS_CAUSAL: only 6 fields with direct causal ties to targets
  - Removed all dead interaction terms:
      usage_proxy_x_itt, fga_x_itt, ast_pct_x_itt, usage_x_itt,
      usage_x_pace, blowout_risk_x_mp_vol
  - Removed dead metadata flags from feature gates:
      has_advanced_stats, has_injury_data, opp_has_env_data
  - Removed all vacancy/injury features from feature gates (still computed,
    returned as monitor columns — will reactivate once snapshot coverage builds)
  - Removed raw market features (game_total, implied_team_total, spread_for_team,
    blowout_risk) from feature gates — still computed, moved to MONITOR block
  - Removed fg3m_games_in_window_last10 (redundant with fg3a_count_last10)

ADDITIONS (signal improvement):
  - NEW: opponent_defensive_features() — rolling team defensive stats from box scores
      opp_pts_allowed_last10, opp_reb_allowed_last10, opp_oreb_allowed_last10
      opp_ast_allowed_last10, opp_3pa_allowed_last10, opp_3pm_allowed_last10
      opp_3p_rate_allowed_last10, opp_fga_allowed_last10, opp_pace_proxy_last10
  - NEW: injury binary flags (lower noise than continuous vacated volumes)
      starter_out_flag, primary_creator_out_flag, center_out_flag
  - MOVED market features to MONITOR block (non-zero once coverage builds)
  - MOVED vacancy features to MONITOR block

KEEPS (confirmed working):
  - All core minutes history features
  - All minutes model outputs (exp_mp, mp_q25, mp_q75, mp_pred_floor, mp_pred_ceiling)
  - Core rolling player stat families (per-min rates + raw counts)
  - 3PM two-stage block (attempts x efficiency)
  - Sparse-stat treatment (STL/BLK blended rates + zero-mass features)
  - reb_x_mp interaction (only interaction surviving ablation)
  - E_pts_proxy, E_reb_proxy, E_ast_proxy (combo expectation proxies)
  - schedule features (rest_days, back_to_back, three_in_4, four_in_6)
  - pf_per_min_mean_last10 (oddly universal - keep until ablation disproves)
  - games_played (monitor: useful but may be a role-stability crutch)
"""

import numpy as np
import pandas as pd
from typing import Optional

STATS        = ["pts", "reb", "ast", "fg3m", "stl", "blk", "tov"]
COMBO_STATS  = ["pra", "pr", "pa", "ra", "stocks"]
ALL_TARGETS  = STATS + COMBO_STATS

INACTIVE_STATUSES = {"out", "doubtful"}
TEAMMATE_WINDOW   = 15
VACATED_CAP       = 3.0

# ── Advanced stats: causal fields by stat family ──────────────────────────────
# v13 had 6 universal + 3 reb. v14 adds stat-specific causal fields confirmed
# by BDL v2/advanced endpoint and prescribed by expert review.
# Fields removed from v12 expanded block (touches, passes, deflections, etc.)
# remain cut — they were dead in feature importance even with BDL GOAT coverage.

# Universal causal — included for all stat models
ADV_FIELDS_CAUSAL = [
    "usage_percentage",                  # pts / ast / tov — core usage
    "estimated_usage_percentage",        # pts — usage estimate (more coverage than usage_pct)
    "true_shooting_percentage",          # pts — composite shooting efficiency
    "effective_field_goal_percentage",   # pts — eFG%
    "assist_percentage",                 # ast — creation rate
    "assist_to_turnover",                # ast / tov — creation quality
    "pace",                              # universal — raw pace
]

# Rebound-specific — causal for reb/pra/pr/ra, gated into those models only
ADV_FIELDS_REB = [
    "rebound_chances_total",             # opportunity-side of rebounding
    "rebound_chances_def",
    "rebound_chances_off",
    "rebound_percentage",                # % of available rebounds captured — overall
    "offensive_rebound_percentage",      # oreb-specific rate
    "defensive_rebound_percentage",      # dreb-specific rate
]

# Scoring-specific — causal for pts model only
ADV_FIELDS_PTS = [
    "free_throw_attempt_rate",           # FTA/FGA — FT-generation archetype
    "pct_fga",                           # player's share of team FGA
    "pct_fta",                           # player's share of team FTA
    "pct_points",                        # player's share of team points
]

# Assist-specific — causal for ast/pa/pra models
ADV_FIELDS_AST = [
    "assist_ratio",                      # AST / (FGA + 0.44*FTA + AST + TOV)
]

# 3PM-specific — causal for fg3m model
ADV_FIELDS_3PM = [
    "pct_3pa",                           # player's share of team 3PA
]

# STL/BLK-specific — causal for stocks/stl/blk models
ADV_FIELDS_STOCKS = [
    "pct_steals",                        # player's share of team steals while on court
    "pct_blocks",                        # player's share of team blocks while on court
]

ALL_ADV_FIELDS = (
    ADV_FIELDS_CAUSAL
    + ADV_FIELDS_REB
    + ADV_FIELDS_PTS
    + ADV_FIELDS_AST
    + ADV_FIELDS_3PM
    + ADV_FIELDS_STOCKS
)


# Per-stat EWMA alphas from within-player lag-1 autocorrelation analysis
# Low autocorr → high alpha (recent games dominate)
_EWMA_ALPHA_BY_STAT = {
    "pts": 0.25, "reb": 0.30, "ast": 0.30, "fg3m": 0.30,
    "stl": 0.30, "blk": 0.30, "tov": 0.30, "pra": 0.25,
    "pr":  0.25, "pa":  0.25, "ra":  0.30, "stocks": 0.30,
}

# Per-stat EWMA alphas from within-player lag-1 autocorrelation analysis
# Low autocorr → high alpha (recent games dominate)
_EWMA_ALPHA_BY_STAT = {
    "pts": 0.25, "reb": 0.30, "ast": 0.30, "fg3m": 0.30,
    "stl": 0.30, "blk": 0.30, "tov": 0.30, "pra": 0.25,
    "pr":  0.25, "pa":  0.25, "ra":  0.30, "stocks": 0.30,
}

# ── Rolling helper: 13 features per series ────────────────────────────────────

def rolling_full(arr: np.ndarray, name: str, stat: str = "") -> dict:
    """
    Full rolling feature pack — 13 features per series.
    Applied to per-minute rates OR raw counts depending on caller.
    NaN returned where insufficient data (LightGBM handles natively).
    """
    arr = arr.astype(float)
    arr = arr[~np.isnan(arr)]
    n   = len(arr)
    f   = {}

    def _safe_mean(a):    return float(np.mean(a))           if len(a) > 0 else np.nan
    def _safe_median(a):  return float(np.median(a))         if len(a) > 0 else np.nan
    def _safe_mad(a):     return float(np.mean(np.abs(a - np.median(a)))) if len(a) > 1 else np.nan
    def _safe_p25(a):     return float(np.percentile(a, 25)) if len(a) > 1 else np.nan
    def _safe_p75(a):     return float(np.percentile(a, 75)) if len(a) > 1 else np.nan
    def _safe_min(a):     return float(np.min(a))            if len(a) > 0 else np.nan
    def _safe_max(a):     return float(np.max(a))            if len(a) > 0 else np.nan

    last3  = arr[-3:]  if n >= 1 else np.array([])
    last5  = arr[-5:]  if n >= 1 else np.array([])
    last10 = arr[-10:] if n >= 1 else np.array([])

    f[f"{name}_mean_last3"]     = _safe_mean(last3)
    f[f"{name}_mean_last5"]     = _safe_mean(last5)
    f[f"{name}_mean_last10"]    = _safe_mean(last10)
    f[f"{name}_median_last10"]  = _safe_median(last10)
    f[f"{name}_p25_last10"]     = _safe_p25(last10)
    f[f"{name}_p75_last10"]     = _safe_p75(last10)
    f[f"{name}_floor_last10"]   = _safe_min(last10)
    f[f"{name}_ceiling_last10"] = _safe_max(last10)
    f[f"{name}_vol_last10"]     = _safe_mad(last10)

    # CV: zero-safe
    if len(last10) > 1:
        mu = np.mean(last10)
        sd = np.std(last10)
        f[f"{name}_cv_last10"] = float(sd / mu) if mu > 0.1 else np.nan
    else:
        f[f"{name}_cv_last10"] = np.nan

    # Bug 7 fix: ewma_10 = slow decay (alpha=0.15, ~4.5 game half-life) — matches "10" convention
    if n >= 2:
        s = pd.Series(arr)
        _alpha = _EWMA_ALPHA_BY_STAT.get(stat, 0.25)
        f[f"{name}_ewma_10"] = float(s.ewm(alpha=_alpha, min_periods=2).mean().iloc[-1])
    else:
        f[f"{name}_ewma_10"] = arr[-1] if n == 1 else np.nan

    # Bug 7 fix: ewma_5 = fast decay (alpha=0.3, ~2 game half-life)
    if n >= 2:
        s = pd.Series(arr)
        f[f"{name}_ewma_5"] = float(s.ewm(alpha=0.3, min_periods=2).mean().iloc[-1])
    else:
        f[f"{name}_ewma_5"] = arr[-1] if n == 1 else np.nan

    # Season EWMA
    if n >= 2:
        s = pd.Series(arr)
        f[f"{name}_mean_season"] = float(s.ewm(alpha=0.1, min_periods=2).mean().iloc[-1])
    else:
        f[f"{name}_mean_season"] = arr[-1] if n == 1 else np.nan

    # Trend: mean_last3 / mean_last10
    m3  = f[f"{name}_mean_last3"]
    m10 = f[f"{name}_mean_last10"]
    if (m3 is not None and not np.isnan(m3) and
        m10 is not None and not np.isnan(m10) and m10 > 0.01):
        f[f"{name}_trend_3v10"] = float(m3 / m10)
    else:
        f[f"{name}_trend_3v10"] = np.nan

    return f


# ── Per-minute rate ────────────────────────────────────────────────────────────

def per_minute_rate(stat_arr: np.ndarray, min_arr: np.ndarray) -> np.ndarray:
    """Per-minute rate; NaN where minutes == 0."""
    stat_arr = stat_arr.astype(float)
    min_arr  = min_arr.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        rate = np.where(min_arr > 0, stat_arr / min_arr, np.nan)
    return rate


# ── Minutes model features ────────────────────────────────────────────────────

def minutes_model_features(df: pd.DataFrame) -> dict:
    """
    Minutes feature block — the single most important feature group (34-44% importance).
    Includes role stability and minute distribution features.
    """
    f = {}
    if "min" not in df.columns or len(df) == 0:
        keys = [
            "mp_mean_last3","mp_mean_last5","mp_mean_last10","mp_mean_season",
            "ewma10_min","std_min_last10","mp_cv_last10",
            "mp_p25_last10","mp_p75_last10","mp_floor_last10","mp_ceiling_last10",
            "trend_min","mp_median_last10",
            "above_mean_pct_min","games_30plus_last10","games_35plus_last10",
            "games_20minus_last10","cv_min",
        ]
        return {k: np.nan for k in keys}

    min_arr = df["min"].values.astype(float)
    f.update(rolling_full(min_arr, "mp"))
    # Manifest naming aliases for minutes features
    f["mp_ewma_10"]    = f.get("ewma10_min",      f.get("mp_mean_last10", np.nan))
    f["mp_vol_last10"] = f.get("std_min_last10",  f.get("mp_cv_last10",   np.nan))
    f["mp_mean_last10"]= f.get("mp_mean_last10",  np.nan)
    # mp_trend_3v10: recent 3-game mean vs last 10
    _mp3  = f.get("mp_mean_last3",  np.nan)
    _mp10 = f.get("mp_mean_last10", np.nan)
    f["mp_trend_3v10"] = (_mp3 / _mp10) if (not np.isnan(_mp3) and not np.isnan(_mp10) and _mp10 > 0) else np.nan

    last10_min = min_arr[-10:]
    n = len(last10_min)

    f["above_mean_pct_min"]  = float(np.mean(last10_min >= 28)) if n > 0 else np.nan
    f["games_30plus_last10"]  = float(np.sum(last10_min >= 30))  if n > 0 else np.nan
    f["games_35plus_last10"]  = float(np.sum(last10_min >= 35))  if n > 0 else np.nan
    f["games_20minus_last10"] = float(np.sum(last10_min <= 20))  if n > 0 else np.nan

    if n > 1 and np.max(last10_min) > 0:
        f["cv_min"] = float(np.std(last10_min) / np.mean(last10_min)) if np.mean(last10_min) > 0 else np.nan
    else:
        f["cv_min"] = np.nan

    return f


# ── Schedule / fatigue ────────────────────────────────────────────────────────

def schedule_features(prior_dates: list, target_date: pd.Timestamp) -> dict:
    f = {}
    if not prior_dates:
        f.update({
            "rest_days": np.nan, "back_to_back": 0,
            "three_in_4": 0, "four_in_6": 0,
            "games_last_7": 0,
            "missed_last_game": 0, "missed_2_of_last5": 0,
        })
        return f

    prior_ts  = sorted([pd.Timestamp(d) for d in prior_dates])
    last_game = prior_ts[-1]
    rest      = (target_date - last_game).days

    f["rest_days"]         = max(0, rest)
    f["back_to_back"]      = int(rest <= 1)
    f["three_in_4"]        = int(len([d for d in prior_ts if (target_date - d).days <= 3]) >= 2)
    f["four_in_6"]         = int(len([d for d in prior_ts if (target_date - d).days <= 5]) >= 3)
    f["games_last_7"]      = len([d for d in prior_ts if (target_date - d).days <= 6])
    f["missed_last_game"]  = int(rest > 2)
    f["missed_2_of_last5"] = int(f["games_last_7"] <= 3 and f["games_last_7"] > 0)

    return f


# ── Game script / market odds ─────────────────────────────────────────────────

def game_script_features(game_context: dict, is_home: int) -> dict:
    """
    Market odds features.

    game_total, implied_team_total, spread_for_team, blowout_risk: MONITOR
    (computed, returned, but NOT in feature gates until coverage > 50%).

    total_move, steam_total_up/down, spread_move_abs, sharp_home_move: IN GATES
    (accumulating from opening/closing snapshots starting 2026-03-13).
    """
    LEAGUE_TOTAL = 220.0
    f = {}

    if not game_context or not game_context.get("odds_available"):
        f.update({
            "consensus_total": np.nan, "spread_for_team": np.nan,
            "implied_team_total": np.nan, "blowout_risk": np.nan,
            "implied_team_total": np.nan,
            "has_odds": 0, "is_home": int(is_home),
            "total_move": np.nan, "spread_move": np.nan,
            "total_move_abs": np.nan, "spread_move_abs": np.nan,
            "steam_total_up": np.nan, "steam_total_down": np.nan,
            "sharp_home_move": np.nan,
        })
        return f

    total       = float(game_context.get("consensus_total") or LEAGUE_TOTAL)
    spread      = float(game_context.get("consensus_spread_home") or 0.0)
    team_spread = spread if is_home else -spread
    implied_team = (total / 2.0) - (team_spread / 2.0)
    opp_implied  = total - implied_team

    # MONITOR: computed but not in feature gates
    f["consensus_total"]         = total
    f["spread_for_team"]    = team_spread
    f["implied_team_total"] = implied_team
    f["opp_implied_team_total"]  = opp_implied
    f["blowout_risk"]       = abs(spread)
    f["has_odds"]           = 1
    f["is_home"]            = int(is_home)

    # IN GATES: line movement signals
    raw_total_move  = game_context.get("total_move") or game_context.get("open_close_total_delta")
    raw_spread_move = game_context.get("spread_move") or game_context.get("open_close_spread_delta")

    f["total_move"]  = float(raw_total_move)  if raw_total_move  is not None else np.nan
    f["spread_move"] = float(raw_spread_move) if raw_spread_move is not None else np.nan

    if raw_total_move is not None and not np.isnan(f["total_move"]):
        f["steam_total_up"]   = 1.0 if f["total_move"] > 0.5  else 0.0
        f["steam_total_down"] = 1.0 if f["total_move"] < -0.5 else 0.0
        f["total_move_abs"]   = abs(f["total_move"])
    else:
        f["steam_total_up"]   = np.nan
        f["steam_total_down"] = np.nan
        f["total_move_abs"]   = np.nan

    if raw_spread_move is not None and not np.isnan(f["spread_move"]):
        f["spread_move_abs"] = abs(f["spread_move"])
        f["sharp_home_move"] = 1.0 if f["spread_move"] < -0.5 else 0.0
    else:
        f["spread_move_abs"] = np.nan
        f["sharp_home_move"] = np.nan

    return f


# ── Opponent defensive environment ────────────────────────────────────────────

_OPP_DEF_CACHE: dict = {}

def opponent_defensive_features(
    opp_team_id: Optional[int],
    target_date: pd.Timestamp,
    all_stats_df: pd.DataFrame,
    window: int = 10,
) -> dict:
    global _OPP_DEF_CACHE
    if PROFILE_BUILD_TABLE:
        _prof_t0 = _prof_time.perf_counter()
    _ck = (opp_team_id, str(target_date)[:10])
    if _ck in _OPP_DEF_CACHE:
        if PROFILE_BUILD_TABLE:
            _elapsed = _prof_time.perf_counter() - _prof_t0
            _OPP_DEF_STATS["hits"] += 1
            _OPP_DEF_STATS["hit_s"] += _elapsed
            _OPP_DEF_STATS["total_s"] += _elapsed
        return _OPP_DEF_CACHE[_ck]
    """
    Rolling opponent team defensive stats computed from historical box scores.

    Replaces the inadequate opp_pace_context (which was just game_total).
    Computes actual per-game defensive stats by finding what the opponent
    team ALLOWED in their last `window` games.

    Method:
      1. Find recent games where opp_team_id played (before target_date)
      2. For each such game, aggregate stats of the OTHER team
         (the team that played against opp_team_id) = what opp ALLOWED
      3. Average across last window games

    Features:
      opp_pts_allowed_last10     — points allowed per game
      opp_reb_allowed_last10     — total rebounds allowed per game
      opp_oreb_allowed_last10    — offensive rebounds allowed per game
      opp_ast_allowed_last10     — assists allowed per game
      opp_3pa_allowed_last10     — 3-point attempts allowed per game
      opp_3pm_allowed_last10     — 3-pointers made against per game
      opp_3p_rate_allowed_last10 — 3PA / total FGA allowed
      opp_fga_allowed_last10     — shot volume allowed per game
      opp_pace_proxy_last10      — possession proxy per game
    """
    NULL = {
        "opp_allowed_pts_ewma":     np.nan,
        "opp_allowed_reb_ewma":     np.nan,
        "opp_oreb_allowed_last10":    np.nan,
        "opp_allowed_ast_ewma":     np.nan,
        "opp_3pa_allowed_last10":     np.nan,
        "opp_3pm_allowed_last10":     np.nan,
        "opp_3p_rate_allowed_last10": np.nan,
        "opp_fga_allowed_last10":     np.nan,
        "opp_pace_proxy_last10":      np.nan,
    }

    if opp_team_id is None or all_stats_df is None or all_stats_df.empty:
        return NULL

    required_cols = {"team_id", "game_id", "game_date", "pts"}
    if not required_cols.issubset(all_stats_df.columns):
        return NULL

    try:
        if PROFILE_BUILD_TABLE:
            _prof_tc = _prof_time.perf_counter()
        df = all_stats_df.copy()
        df["game_date"] = pd.to_datetime(df["game_date"])
        if PROFILE_BUILD_TABLE:
            _OPP_DEF_STATS["miss_copy_s"] += _prof_time.perf_counter() - _prof_tc

        # Find opponent's recent game IDs (before target date)
        opp_rows = df[
            (df["team_id"] == opp_team_id) &
            (df["game_date"].astype(str) < str(target_date))
        ]
        if opp_rows.empty:
            return NULL

        # Get last `window` games by date
        opp_game_dates = (
            opp_rows.groupby("game_id")["game_date"].max().sort_values()
        )
        recent_game_ids = opp_game_dates.index[-window:].tolist()

        # Stats scored BY the opponent's opponents (= what opp ALLOWED)
        allowed_rows = df[
            (df["game_id"].isin(recent_game_ids)) &
            (df["team_id"] != opp_team_id)
        ]

        if allowed_rows.empty:
            return NULL

        def _game_avg(col: str) -> Optional[float]:
            if col not in allowed_rows.columns:
                return None
            per_game = (
                allowed_rows.groupby("game_id")[col]
                .apply(lambda x: np.nansum(x.values.astype(float)))
            )
            return float(np.mean(per_game)) if len(per_game) > 0 else None

        def _game_ewma(col: str, alpha: float = 0.20) -> Optional[float]:
            """True EWMA over per-game opponent totals — recency-weighted."""
            if col not in allowed_rows.columns:
                return None
            per_game = (
                allowed_rows.groupby("game_id")[col]
                .apply(lambda x: np.nansum(x.values.astype(float)))
                .sort_index()
            )
            if len(per_game) == 0:
                return None
            if len(per_game) == 1:
                return float(per_game.iloc[0])
            s = pd.Series(per_game.values)
            return float(s.ewm(alpha=alpha, min_periods=2).mean().iloc[-1])

        def _game_ewma_pos(col: str, pos_groups: list, alpha: float = 0.20) -> Optional[float]:
            """EWMA of opponent allowed stats filtered by position group (e.g. guards vs bigs)."""
            if col not in allowed_rows.columns:
                return None
            pos_col = "position" if "position" in allowed_rows.columns else None
            if pos_col is None:
                return _game_ewma(col, alpha)
            # Filter to target position group
            pos_mask = allowed_rows[pos_col].fillna("").str.upper().str[:1].isin(
                [p[0].upper() for p in pos_groups]
            )
            pos_rows = allowed_rows[pos_mask]
            if pos_rows.empty:
                return _game_ewma(col, alpha)  # fallback to full team
            per_game = (
                pos_rows.groupby("game_id")[col]
                .apply(lambda x: np.nansum(x.values.astype(float)))
                .sort_index()
            )
            if len(per_game) == 0:
                return None
            if len(per_game) == 1:
                return float(per_game.iloc[0])
            s = pd.Series(per_game.values)
            return float(s.ewm(alpha=alpha, min_periods=2).mean().iloc[-1])

        pts  = _game_avg("pts")
        reb  = _game_avg("reb")
        oreb = _game_avg("oreb")
        ast  = _game_avg("ast")
        fg3a = _game_avg("fg3a")
        fg3m = _game_avg("fg3m")
        fga  = _game_avg("fga")
        fta  = _game_avg("fta")
        tov  = _game_avg("turnover")

        # League averages for factor computation
        # Bug 12 fix: league averages at team-game level, not player-game level
        def _team_game_avg(col, default):
            if col not in all_stats_df.columns:
                return default
            return float(all_stats_df.groupby(["game_id","team_id"])[col].sum().mean())

        if PROFILE_BUILD_TABLE:
            _prof_tg = _prof_time.perf_counter()
        _lg_pts  = _team_game_avg("pts",  110.0)
        _lg_reb  = _team_game_avg("reb",  43.0)
        _lg_ast  = _team_game_avg("ast",  24.0)
        _lg_fg3m = _team_game_avg("fg3m", 12.0)
        _lg_blk  = _team_game_avg("blk",  4.8)
        _lg_stl  = _team_game_avg("stl",  7.5)
        if PROFILE_BUILD_TABLE:
            _OPP_DEF_STATS["miss_groupby_s"] += _prof_time.perf_counter() - _prof_tg

        blk  = _game_avg("blk")
        stl  = _game_avg("stl")

        result = {
            # pts
            "opp_allowed_pts_ewma":   _game_ewma("pts"),
            "opp_allowed_pts_mean":   pts  if pts  is not None else np.nan,
            "opp_allowed_pts_factor": (pts / max(_lg_pts, 1)) if pts is not None else np.nan,
            # reb
            "opp_allowed_reb_ewma":   _game_ewma("reb"),
            "opp_allowed_reb_mean":   reb  if reb  is not None else np.nan,
            "opp_allowed_reb_factor": (reb / max(_lg_reb, 1)) if reb is not None else np.nan,
            # ast
            "opp_allowed_ast_ewma":   _game_ewma("ast"),
            "opp_allowed_ast_mean":   ast  if ast  is not None else np.nan,
            "opp_allowed_ast_factor": (ast / max(_lg_ast, 1)) if ast is not None else np.nan,
            # fg3m
            "opp_allowed_fg3m_ewma":   _game_ewma("fg3m"),
            "opp_allowed_fg3m_mean":   fg3m if fg3m is not None else np.nan,
            "opp_allowed_fg3m_factor": (fg3m / max(_lg_fg3m, 1)) if fg3m is not None else np.nan,
            # blk
            "opp_allowed_blk_ewma":       _game_ewma("blk"),
            "opp_allowed_blk_mean":       blk  if blk  is not None else np.nan,
            "opp_allowed_blk_factor":     (blk / max(_lg_blk, 1)) if blk is not None else np.nan,
            "opp_allowed_blk_big_ewma":   _game_ewma_pos("blk", ["C","F"]),
            "opp_allowed_blk_guard_ewma": _game_ewma_pos("blk", ["G"]),
            # stl
            "opp_allowed_stl_ewma":         _game_ewma("stl"),
            "opp_allowed_stl_mean":         stl  if stl  is not None else np.nan,
            "opp_allowed_stl_factor":       (stl / max(_lg_stl, 1)) if stl is not None else np.nan,
            "opp_allowed_stl_guard_ewma":   _game_ewma_pos("stl", ["G"]),
            "opp_allowed_stl_big_ewma":     _game_ewma_pos("stl", ["C","F"]),
            # existing
            "opp_oreb_allowed_last10":    oreb if oreb is not None else np.nan,
            "opp_3pa_allowed_last10":     fg3a if fg3a is not None else np.nan,
            "opp_3pm_allowed_last10":     fg3m if fg3m is not None else np.nan,
            "opp_fga_allowed_last10":     fga  if fga  is not None else np.nan,
            # ── v2: position-split allowed stats for PTS / REB / AST / FG3M ──
            # Guards (G, G-F) — PTS/AST/FG3M guard-matchup; Bigs (C, F) — REB/BLK
            "opp_allowed_pts_guard_ewma":  _game_ewma_pos("pts",  ["G"]),
            "opp_allowed_pts_big_ewma":    _game_ewma_pos("pts",  ["C","F"]),
            "opp_allowed_reb_guard_ewma":  _game_ewma_pos("reb",  ["G"]),
            "opp_allowed_reb_big_ewma":    _game_ewma_pos("reb",  ["C","F"]),
            "opp_allowed_ast_guard_ewma":  _game_ewma_pos("ast",  ["G"]),
            "opp_allowed_ast_big_ewma":    _game_ewma_pos("ast",  ["C","F"]),
            "opp_allowed_fg3m_guard_ewma": _game_ewma_pos("fg3m", ["G"]),
            "opp_allowed_fg3m_big_ewma":   _game_ewma_pos("fg3m", ["C","F"]),
        }

        # 3P rate allowed
        if fg3a is not None and fga is not None and fga > 0:
            result["opp_3p_rate_allowed_last10"] = float(fg3a / fga)
        else:
            result["opp_3p_rate_allowed_last10"] = np.nan

        # Issue 14 fix: pace proxy normalized per 48 min at team-game level
        if all(v is not None for v in [fga, fta, tov, oreb]):
            raw_poss = fga + 0.44 * fta + tov - oreb
            # Normalize to per-48: divide by avg players * avg min
            # raw_poss is team-game sum already (via _game_avg)
            result["opp_pace_proxy_last10"] = float(raw_poss / 5.0 * 48.0 / 40.0)  # ~possessions per 48 per team
        else:
            result["opp_pace_proxy_last10"] = np.nan
        # ── Additional box-score derived opponent features ─────────────────
        # opp_fg_miss_volume: real FGA * (1 - FG%) per opponent allowed row
        if "fga" in allowed_rows.columns and "fg_pct" in allowed_rows.columns:
            try:
                _fg_miss_per_game = (
                    allowed_rows.assign(_miss=allowed_rows["fga"] * (1 - allowed_rows["fg_pct"]))
                    .groupby("game_id")["_miss"].sum()
                )
                result["opp_fg_miss_volume"] = float(_fg_miss_per_game.mean())
            except Exception:
                result["opp_fg_miss_volume"] = np.nan
        else:
            result["opp_fg_miss_volume"] = np.nan

        # opp_3pt_miss_volume: real FG3A * (1 - FG3%) per opponent allowed row
        if "fg3a" in allowed_rows.columns and "fg3_pct" in allowed_rows.columns:
            try:
                _fg3_miss_per_game = (
                    allowed_rows.assign(_miss=allowed_rows["fg3a"] * (1 - allowed_rows["fg3_pct"]))
                    .groupby("game_id")["_miss"].sum()
                )
                result["opp_3pt_miss_volume"] = float(_fg3_miss_per_game.mean())
            except Exception:
                result["opp_3pt_miss_volume"] = np.nan
        else:
            result["opp_3pt_miss_volume"] = np.nan

        # opp_3pa_allowed, opp_3pm_allowed, opp_3p_rate_allowed
        result["opp_3pa_allowed"]     = fg3a if fg3a is not None else np.nan
        result["opp_3pm_allowed"]     = fg3m if fg3m is not None else np.nan
        if fg3a is not None and fga is not None and fga > 0:
            result["opp_3p_rate_allowed"] = float(fg3a / fga)
        else:
            result["opp_3p_rate_allowed"] = np.nan

        _OPP_DEF_CACHE[_ck] = result
        if PROFILE_BUILD_TABLE:
            _elapsed = _prof_time.perf_counter() - _prof_t0
            _OPP_DEF_STATS["misses"] += 1
            _OPP_DEF_STATS["miss_s"] += _elapsed
            _OPP_DEF_STATS["total_s"] += _elapsed
        return result

    except Exception:
        if PROFILE_BUILD_TABLE:
            _elapsed = _prof_time.perf_counter() - _prof_t0
            _OPP_DEF_STATS["misses"] += 1
            _OPP_DEF_STATS["miss_s"] += _elapsed
            _OPP_DEF_STATS["total_s"] += _elapsed
        return NULL


# ── Advanced stats block (causal only) ────────────────────────────────────────

def advanced_stats_block(adv_records: list) -> dict:
    """
    BDL v2 advanced stats — causal fields only, grouped by stat family.

    v14 adds stat-specific causal groups:
      ADV_FIELDS_PTS:    free_throw_attempt_rate, pct_fga, pct_fta, pct_points
      ADV_FIELDS_REB:    rebound_percentage, oreb_pct, dreb_pct (+ chances)
      ADV_FIELDS_AST:    assist_ratio
      ADV_FIELDS_3PM:    pct_3pa
      ADV_FIELDS_STOCKS: pct_steals, pct_blocks

    EWMA computed for recency-sensitive fields: pace, assist_percentage,
    usage_percentage, assist_ratio, free_throw_attempt_rate.
    """
    f = {f"adv_{field}_mean_last10": np.nan for field in ALL_ADV_FIELDS}
    f["adv_pace_ewma"]                  = np.nan
    f["adv_assist_percentage_ewma"]     = np.nan
    f["adv_usage_percentage_ewma"]      = np.nan
    f["adv_assist_ratio_ewma"]          = np.nan
    f["adv_free_throw_attempt_rate_ewma"] = np.nan

    if not adv_records:
        return f

    # Deduplicate by game_id — keep period=0 (game total row)
    # BDL advanced stats: period=0 is the full-game aggregate
    adv_by_game = {}
    for r in adv_records:
        gid = r.get("game_id")
        period = r.get("period", -1)
        if period == 0:
            adv_by_game[gid] = r  # always prefer the game total
        elif gid not in adv_by_game:
            adv_by_game[gid] = r  # fallback if no period=0 exists
    adv_records = sorted(adv_by_game.values(), key=lambda x: x.get("game_date", ""))
    recent = adv_records[-10:]

    for field in ALL_ADV_FIELDS:
        vals = [
            float(r[field]) for r in recent
            if r.get(field) is not None and r[field] != ""
        ]
        f[f"adv_{field}_mean_last10"] = float(np.mean(vals)) if vals else np.nan

    # EWMA for recency-sensitive fields
    for field, out_key in [
        ("pace",                    "adv_pace_ewma"),
        ("assist_percentage",       "adv_assist_percentage_ewma"),
        ("usage_percentage",        "adv_usage_percentage_ewma"),
        ("assist_ratio",            "adv_assist_ratio_ewma"),
        ("free_throw_attempt_rate", "adv_free_throw_attempt_rate_ewma"),
    ]:
        vals = [
            float(r[field]) for r in adv_records
            if r.get(field) is not None and r[field] != ""
        ]
        if len(vals) >= 2:
            s = pd.Series(vals)
            f[out_key] = float(s.ewm(alpha=0.3, min_periods=2).mean().iloc[-1])
        elif len(vals) == 1:
            f[out_key] = vals[0]

    return f


# ── Vacated opportunity + binary injury flags ─────────────────────────────────

def vacated_opportunity_features(
    player_id: int,
    team_id: int,
    target_date: pd.Timestamp,
    stats_df: pd.DataFrame,
    injury_map: dict,
) -> dict:
    """
    Role-conditioned vacated opportunity + binary injury flags.

    v13 adds: starter_out_flag, primary_creator_out_flag, center_out_flag
    Binary flags are low-noise and effective even with sparse injury coverage.
    The continuous vacated_* features remain computed but are in MONITOR
    (not in feature gates) until historical snapshot coverage is sufficient.
    """
    NULL = {
        # Continuous vacancy — MONITOR (not in feature gates)
        "vacated_minutes":          np.nan,
        "vacated_fga":              np.nan,
        "vacated_fg3a":             np.nan,
        "vacated_fta":              np.nan,
        "vacated_pts":              np.nan,
        "vacated_ast":              np.nan,
        "vacated_reb":              np.nan,
        "vacated_usage_proxy":      np.nan,
        "vacated_top1_fga":         np.nan,
        "vacated_top2_fga":         np.nan,
        "vacated_top1_usage_proxy": np.nan,
        "vacated_top2_usage_proxy": np.nan,
        "vacated_guard_minutes":    np.nan,
        "vacated_big_minutes":      np.nan,
        "vacated_creation_share":   np.nan,
        "vacated_reb_share":        np.nan,
        "num_teammates_inactive":   0,
        "has_injury_data":          0,
        # Binary flags — IN feature gates
        "starter_out_flag":         0,
        "primary_creator_out_flag": 0,
        "center_out_flag":          0,
    }

    if stats_df.empty or not injury_map:
        return NULL

    team_games = stats_df[
        (stats_df["team_id"] == team_id) &
        (stats_df["game_date"].astype(str) < str(target_date))
    ].sort_values("game_date")

    if team_games.empty:
        return NULL

    recent_team_games = team_games["game_id"].unique()[-TEAMMATE_WINDOW:]
    teammates = set(
        stats_df[
            (stats_df["game_id"].isin(recent_team_games)) &
            (stats_df["team_id"] == team_id) &
            (stats_df["player_id"] != player_id)
        ]["player_id"].unique()
    )

    if not teammates:
        return NULL

    inactive = [
        tid for tid in teammates
        if str(injury_map.get(tid, {}).get("status", "")).lower().strip()
        in INACTIVE_STATUSES
    ]

    has_inj = 1 if injury_map else 0

    if not inactive:
        result = dict(NULL)
        result["has_injury_data"] = has_inj
        result["num_teammates_inactive"] = 0
        return result

    def _asof_avg(pid: int, col: str) -> float:
        pdata = stats_df[
            (stats_df["player_id"] == pid) &
            (stats_df["game_date"].astype(str) < str(target_date))
        ]
        if pdata.empty or col not in pdata.columns:
            return np.nan
        stat_vals = pdata[col].values.astype(float)
        min_vals  = pdata["min"].values.astype(float)
        total_min = np.nansum(min_vals)
        if total_min <= 0:
            return np.nan
        rate = np.nansum(stat_vals) / total_min
        all_rates = np.where(min_vals > 0, stat_vals / min_vals, np.nan)
        all_rates = all_rates[~np.isnan(all_rates)]
        if len(all_rates) > 2:
            mu, sigma = np.nanmean(all_rates), np.nanstd(all_rates)
            if sigma > 0:
                rate = np.clip(rate, mu - VACATED_CAP * sigma, mu + VACATED_CAP * sigma)
        return float(rate)

    def _asof_mean_min(pid: int) -> float:
        pdata = stats_df[
            (stats_df["player_id"] == pid) &
            (stats_df["game_date"].astype(str) < str(target_date))
        ]
        if pdata.empty:
            return np.nan
        return float(np.nanmean(pdata["min"].values.astype(float)))

    def _classify_role(pid: int) -> str:
        """
        Issue 20 fix: use BDL position field first, fall back to stat-based heuristic.
        Position field values: G, G-F, F, F-G, F-C, C
        """
        pdata = stats_df[
            (stats_df["player_id"] == pid) &
            (stats_df["game_date"].astype(str) < str(target_date))
        ]
        if pdata.empty:
            return "unknown"
        # Use BDL position field if available
        if "position" in pdata.columns:
            pos = str(pdata["position"].iloc[-1]).upper().strip()
            if pos in ("C", "F-C", "C-F"):
                return "big"
            if pos in ("G", "G-F", "F-G"):
                return "guard"
            if pos == "F":
                # Forward — use blk to distinguish big vs wing
                avg_blk = np.nanmean(pdata["blk"].values.astype(float)) if "blk" in pdata.columns else 0
                return "big" if avg_blk > 0.4 else "guard"
        # Fallback: stat-based heuristic
        avg_reb = np.nanmean(pdata["reb"].values.astype(float)) if "reb" in pdata.columns else 0
        avg_ast = np.nanmean(pdata["ast"].values.astype(float)) if "ast" in pdata.columns else 0
        avg_blk = np.nanmean(pdata["blk"].values.astype(float)) if "blk" in pdata.columns else 0
        avg_fg3a = np.nanmean(pdata["fg3a"].values.astype(float)) if "fg3a" in pdata.columns else 0
        # Bigs: high reb, low 3PA, some blocks
        if avg_reb > avg_ast and avg_blk > 0.3 and avg_fg3a < 3.0:
            return "big"
        return "guard"

    v_min = v_fga = v_fg3a = v_fta = v_pts = v_ast = v_reb = v_usage = 0.0
    v_guard_min = v_big_min = 0.0
    fga_per_inactive   = []
    usage_per_inactive = []
    max_usage_inactive = 0.0

    starter_out         = 0
    primary_creator_out = 0
    center_out          = 0

    for pid in inactive:
        m = _asof_mean_min(pid)
        if np.isnan(m) or m <= 0:
            continue

        fga_rate  = _asof_avg(pid, "fga")
        fg3a_rate = _asof_avg(pid, "fg3a")
        fta_rate  = _asof_avg(pid, "fta")
        pts_rate  = _asof_avg(pid, "pts")
        ast_rate  = _asof_avg(pid, "ast")
        reb_rate  = _asof_avg(pid, "reb")
        tov_rate  = _asof_avg(pid, "turnover")

        up_rate = (
            (fga_rate  if not np.isnan(fga_rate)  else 0) +
            0.44 * (fta_rate if not np.isnan(fta_rate) else 0) +
            (tov_rate  if not np.isnan(tov_rate)  else 0)
        )

        v_min   += m
        v_fga   += (fga_rate  * m) if not np.isnan(fga_rate)  else 0
        v_fg3a  += (fg3a_rate * m) if not np.isnan(fg3a_rate) else 0
        v_fta   += (fta_rate  * m) if not np.isnan(fta_rate)  else 0
        v_pts   += (pts_rate  * m) if not np.isnan(pts_rate)  else 0
        v_ast   += (ast_rate  * m) if not np.isnan(ast_rate)  else 0
        v_reb   += (reb_rate  * m) if not np.isnan(reb_rate)  else 0
        v_usage += up_rate * m

        role = _classify_role(pid)
        if role == "big":
            v_big_min += m
        else:
            v_guard_min += m

        fga_per_inactive.append((fga_rate * m) if not np.isnan(fga_rate) else 0)
        usage_per_inactive.append(up_rate * m)

        # Binary injury flags
        if m >= 25:
            starter_out = 1
        if up_rate * m > max_usage_inactive:
            max_usage_inactive = up_rate * m
        if m >= 20 and role == "big":
            center_out = 1

    # Primary creator: most-used inactive player contributes > 3.5 usage units
    if max_usage_inactive > 3.5:
        primary_creator_out = 1

    fga_sorted   = sorted(fga_per_inactive,   reverse=True)
    usage_sorted = sorted(usage_per_inactive, reverse=True)

    creation_share = (v_ast / v_usage) if v_usage > 0 else np.nan
    reb_share      = (v_reb / v_min)   if v_min  > 0 else np.nan

    return {
        # Continuous vacancy — MONITOR
        "vacated_minutes":          float(v_min),
        "vacated_fga":              float(v_fga),
        "vacated_fg3a":             float(v_fg3a),
        "vacated_fta":              float(v_fta),
        "vacated_pts":              float(v_pts),
        "vacated_ast":              float(v_ast),
        "vacated_reb":              float(v_reb),
        "vacated_usage_proxy":      float(v_usage),
        "vacated_top1_fga":         float(fga_sorted[0])       if fga_sorted   else 0.0,
        "vacated_top2_fga":         float(sum(fga_sorted[:2])) if fga_sorted   else 0.0,
        "vacated_top1_usage_proxy": float(usage_sorted[0])     if usage_sorted else 0.0,
        "vacated_top2_usage_proxy": float(sum(usage_sorted[:2])) if usage_sorted else 0.0,
        "vacated_guard_minutes":    float(v_guard_min),
        "vacated_big_minutes":      float(v_big_min),
        "vacated_creation_share":   float(creation_share) if not np.isnan(creation_share) else np.nan,
        "vacated_reb_share":        float(reb_share)      if not np.isnan(reb_share)      else np.nan,
        "num_teammates_inactive":   len(inactive),
        "has_injury_data":          has_inj,
        # Binary flags — IN feature gates
        "starter_out_flag":         starter_out,
        "primary_creator_out_flag": primary_creator_out,
        "center_out_flag":          center_out,
    }


# ── Main feature builder ──────────────────────────────────────────────────────

def build_player_game_features(
    player_id: int,
    prior_stats: pd.DataFrame,
    prior_adv: list,
    game_context: dict,
    is_home: int,
    target_date: str,
    team_id: int,
    all_stats_df: pd.DataFrame,
    injury_map: dict,
    opp_team_id: Optional[int] = None,
    training_mode: bool = False,
) -> dict:
    """
    Build complete pregame feature vector for one player.
    ZERO leakage: all inputs strictly prior to target_date.
    Returns flat dict — NaN where data unavailable.

    NEW v13: opp_team_id parameter for opponent_defensive_features().
    Pass from game_context['opp_team_id'] or derive from BDL game data.
    """
    f = {}
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    df  = prior_stats.sort_values("game_date").reset_index(drop=True)
    tdt = pd.Timestamp(target_date)
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["df_sort_reset"] += _prof_time.perf_counter() - _t

    min_arr = df["min"].values.astype(float) if "min" in df.columns else np.array([])

    # ── Minutes model block ───────────────────────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    f.update(minutes_model_features(df))
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["minutes_model_features"] += _prof_time.perf_counter() - _t

    # ── Standalone minutes model predictions ─────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    if training_mode:
        # Do not run predict_minutes during training-table build.
        # Rationale:
        #   1. Profiling on 2026-04-22 measured predict_minutes at 92.5% of
        #      build_player_game_features wall-clock — the dominant hotspot.
        #   2. predict_minutes is a prediction-layer call that returns
        #      model outputs (exp_mp, mp_q10/25/75/90, mp_vol, pred_floor,
        #      pred_ceiling). Injecting those outputs into the training
        #      feature vector for downstream stat models is a training-
        #      contamination path: the stat models would learn against
        #      features that the minutes model produces, not raw history.
        #   3. Only mean_min_last10 is semantically a raw rolling stat
        #      and can be sourced directly from df["min"].tail(10).mean().
        #      The model-predicted quantiles/bounds are set to NaN so the
        #      removal of contamination is visible; LightGBM handles NaN
        #      natively.
        #   4. Commit ab6c7e7 (2026-04-07) previously short-circuited this
        #      by passing an empty stats_df to predict_minutes during
        #      training. That guardrail was lost during the src-layout
        #      reorg (e680c2e, 2026-04-18). This block restores the gate.
        if len(df) >= 10 and "min" in df.columns:
            f["mean_min_last10"] = float(
                pd.to_numeric(df["min"].tail(10), errors="coerce")
                .fillna(0).mean()
            )
        else:
            f["mean_min_last10"] = np.nan
        for k in ("exp_mp", "mp_q10", "mp_q25", "mp_q75", "mp_q90",
                  "mp_vol", "mp_pred_floor", "mp_pred_ceiling"):
            f[k] = np.nan
    else:
        try:
            from minutes_model import predict_minutes
            mp_preds = predict_minutes(
                prior_stats  = prior_stats,
                game_context = game_context,
                is_home      = is_home,
                target_date  = target_date,
                team_id      = team_id,
                all_stats_df = all_stats_df,
                injury_map   = injury_map,
            )
            f.update(mp_preds)
        except Exception:
            for k in ("mean_min_last10","exp_mp","mp_q10","mp_q25","mp_q75","mp_q90",
                      "mp_vol","mp_pred_floor","mp_pred_ceiling"):
                f[k] = np.nan
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["predict_minutes"] += _prof_time.perf_counter() - _t

    # ── Per-minute rates + full rolling ──────────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    RATE_STATS = {
        "pts": "pts", "reb": "reb", "ast": "ast",
        "fg3m": "fg3m", "stl": "stl", "blk": "blk",
        "tov": "turnover",
        "fga": "fga", "fg3a": "fg3a", "fta": "fta",
        "oreb": "oreb", "dreb": "dreb",
        "pf": "pf",
    }

    for feat_name, col in RATE_STATS.items():
        if col in df.columns and len(min_arr) > 0:
            raw  = df[col].values.astype(float)
            rate = per_minute_rate(raw, min_arr)
            f.update(rolling_full(rate, f"{feat_name}_per_min"))
            f.update(rolling_full(raw,  f"{feat_name}_raw"))
        else:
            sfxs = [
                "mean_last3","mean_last5","mean_last10","mean_season","median_last10",
                "vol_last10","cv_last10","ewma_10","p25_last10","p75_last10",
                "floor_last10","ceiling_last10","trend_3v10",
            ]
            for sfx in sfxs:
                f[f"{feat_name}_per_min_{sfx}"] = np.nan
                f[f"{feat_name}_raw_{sfx}"]     = np.nan
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["rate_stats_loop"] += _prof_time.perf_counter() - _t

    # ── Usage proxy ───────────────────────────────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    if all(c in df.columns for c in ["fga", "fta", "turnover"]) and len(min_arr) > 0:
        up_raw  = (df["fga"].values + 0.44 * df["fta"].values +
                   df["turnover"].values).astype(float)
        up_rate = per_minute_rate(up_raw, min_arr)
        f.update(rolling_full(up_rate, "usage_proxy_per_min"))
    else:
        sfxs = ["mean_last3","mean_last5","mean_last10","mean_season","median_last10",
                "vol_last10","cv_last10","ewma_10","p25_last10","p75_last10",
                "floor_last10","ceiling_last10","trend_3v10"]
        for sfx in sfxs:
            f[f"usage_proxy_per_min_{sfx}"] = np.nan
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["usage_proxy"] += _prof_time.perf_counter() - _t

    # ── 3PM block: two-stage ──────────────────────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    if all(c in df.columns for c in ["fg3m", "fg3a"]):
        fg3m_raw = df["fg3m"].values.astype(float)
        fg3a_raw = df["fg3a"].values.astype(float)
        fg3m_arr = np.where(np.isnan(fg3m_raw), 0.0, fg3m_raw)
        fg3a_arr = np.where(np.isnan(fg3a_raw), 0.0, fg3a_raw)

        last10_fg3m = fg3m_arr[-10:]
        n_window    = len(last10_fg3m)

        f["fg3m_p_zero_last10"] = float(np.mean(last10_fg3m == 0)) if n_window > 0 else np.nan
        f["fg3m_p_ge3_last10"]  = float(np.mean(last10_fg3m >= 3)) if n_window > 0 else np.nan
        # fg3m_games_in_window_last10 REMOVED (redundant)

        PRIOR_3P = _LEAGUE_3P_PRIOR  # Issue 15 fix: dynamic rolling league prior
        K10, KS  = 120.0, 600.0
        att10  = float(np.sum(fg3a_arr[-10:]))
        made10 = float(np.sum(fg3m_arr[-10:]))
        attS   = float(np.sum(fg3a_arr))
        madeS  = float(np.sum(fg3m_arr))
        pct10  = made10 / max(att10, 1)
        pctS   = madeS  / max(attS,  1)
        w10    = att10  / (att10 + K10)
        wS     = attS   / (attS  + KS)
        pct_base = wS * pctS + (1.0 - wS) * PRIOR_3P

        f["fg3_pct_safe"]      = float(np.clip(w10 * pct10 + (1.0 - w10) * pct_base, 0.20, 0.50))
        f["fg3a_count_last10"] = float(att10)
        f["fg3a_count_season"] = float(attS)
        f["is_low_3pa_last10"] = 1.0 if att10 <= 6 else 0.0

        last3_att = float(np.sum(fg3a_arr[-3:]))
        f["fg3a_attempt_trend"] = (last3_att / 3.0) / (att10 / 10.0) \
            if att10 > 0 else np.nan

        # Per-minute rate for 3PA
        if len(min_arr) >= 10:
            r3a_10 = per_minute_rate(fg3a_arr[-10:], min_arr[-10:])
            f["per_min_fg3a_last10"] = float(np.nanmean(r3a_10)) if len(r3a_10) > 0 else np.nan
            if len(min_arr) >= 3:
                r3a_3 = per_minute_rate(fg3a_arr[-3:], min_arr[-3:])
                m3a   = float(np.nanmean(r3a_3))
                m10a  = f["per_min_fg3a_last10"]
                f["fg3a_per_min_trend_3v10"] = (m3a / m10a) if (m10a and m10a > 0.001) else np.nan
            else:
                f["fg3a_per_min_trend_3v10"] = np.nan
        else:
            f["per_min_fg3a_last10"]  = np.nan
            f["fg3a_per_min_trend_3v10"]   = np.nan
    else:
        for _k in [
            "fg3m_p_zero_last10","fg3m_p_ge3_last10",
            "fg3_pct_safe","fg3a_count_last10","fg3a_count_season","is_low_3pa_last10",
            "fg3a_attempt_trend","per_min_fg3a_last10","fg3a_per_min_trend_3v10",
        ]:
            f[_k] = np.nan
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["fg3m_block"] += _prof_time.perf_counter() - _t

    # ── STL / BLK / TOV — zero-inflated count model features ────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    # v2: Add ZI-specific parameters:
    #   {stat}_p_nonzero_last20   : empirical P(stat > 0) over last 20 games (ZI mixing weight)
    #   {stat}_zi_lambda_last10   : Poisson lambda estimated from nonzero games only
    #   {stat}_hurdle_rate_last10 : p_nonzero * zi_lambda  (ZI mean)
    #   {stat}_p_ge2_zi           : ZI-adjusted P(stat >= 2)
    # Legacy features retained for backward-compat with existing pkl feature lists.
    BLEND_K = 15.0
    for sparse_stat, col in [("stl", "stl"), ("blk", "blk"), ("tov", "turnover")]:
        if col in df.columns and len(min_arr) > 0:
            raw  = df[col].values.astype(float)
            rate = per_minute_rate(raw, min_arr)
            last10_raw = raw[-10:]
            last20_raw = raw[-20:] if len(raw) >= 20 else raw

            # ── Legacy features (unchanged) ──
            f[f"{sparse_stat}_p_zero_last10"] = float(np.mean(last10_raw == 0)) if len(last10_raw) > 0 else np.nan
            f[f"{sparse_stat}_p_ge2_last10"]  = float(np.mean(last10_raw >= 2)) if len(last10_raw) > 0 else np.nan
            f[f"{sparse_stat}_p_ge1_last10"]  = float(np.mean(last10_raw >= 1)) if len(last10_raw) > 0 else np.nan

            rate_clean = rate[~np.isnan(rate)]
            n_games    = len(rate_clean)
            r10 = float(np.nanmean(rate[-10:])) if n_games >= 1 else np.nan
            rs  = float(np.nanmean(rate))       if n_games >= 1 else np.nan
            if not np.isnan(r10) and not np.isnan(rs):
                w = min(n_games, 10) / (min(n_games, 10) + BLEND_K)
                f[f"{sparse_stat}_per_min_blended"] = w * r10 + (1.0 - w) * rs
            else:
                f[f"{sparse_stat}_per_min_blended"] = np.nan

            rate_series = pd.Series(rate_clean)
            if len(rate_series) >= 2:
                f[f"{sparse_stat}_per_min_ewma_10"] = float(
                    rate_series.ewm(alpha=0.3, min_periods=2).mean().iloc[-1]
                )
            elif len(rate_series) == 1:
                f[f"{sparse_stat}_per_min_ewma_10"] = float(rate_series.iloc[0])
            else:
                f[f"{sparse_stat}_per_min_ewma_10"] = np.nan

            f[f"{sparse_stat}_per_min_vol_last10"] = (
                float(np.mean(np.abs(rate[-10:] - np.median(rate[-10:]))))
                if len(rate[-10:]) > 1 else np.nan
            )

            # ── v2: Zero-inflated count model parameters ──
            # p_nonzero: empirical ZI mixing weight (P the process is "on")
            _nz_mask20 = last20_raw > 0
            _p_nonzero = float(np.mean(_nz_mask20)) if len(last20_raw) > 0 else 0.5
            f[f"{sparse_stat}_p_nonzero_last20"] = _p_nonzero

            # zi_lambda: Poisson lambda from nonzero games only (count | active)
            _nz_vals10 = last10_raw[last10_raw > 0]
            if len(_nz_vals10) >= 2:
                # Shrink toward 1.0 with weight 5 to prevent extreme estimates
                _zi_lambda = float(
                    (np.sum(_nz_vals10) + 5.0) / (len(_nz_vals10) + 5.0)
                )
            elif len(_nz_vals10) == 1:
                _zi_lambda = float(_nz_vals10[0]) * 0.5 + 0.5
            else:
                _zi_lambda = 1.0
            f[f"{sparse_stat}_zi_lambda_last10"] = _zi_lambda

            # hurdle_rate: ZI unconditional mean = p_nonzero * lambda
            f[f"{sparse_stat}_hurdle_rate_last10"] = _p_nonzero * _zi_lambda

            # p_ge2_zi: ZI-adjusted P(stat >= 2)
            # = p_nonzero * P(Poisson(lambda) >= 2)
            from scipy.stats import poisson as _poisson
            _p_ge2_zi = _p_nonzero * float(1.0 - _poisson.cdf(1, _zi_lambda))
            f[f"{sparse_stat}_p_ge2_zi"] = float(np.clip(_p_ge2_zi, 0.0, 1.0))

        else:
            for k in [f"{sparse_stat}_p_zero_last10", f"{sparse_stat}_p_ge2_last10",
                      f"{sparse_stat}_p_ge1_last10", f"{sparse_stat}_per_min_blended",
                      f"{sparse_stat}_per_min_ewma_10", f"{sparse_stat}_per_min_vol_last10",
                      f"{sparse_stat}_p_nonzero_last20", f"{sparse_stat}_zi_lambda_last10",
                      f"{sparse_stat}_hurdle_rate_last10", f"{sparse_stat}_p_ge2_zi"]:
                f[k] = np.nan
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["sparse_zi_loop"] += _prof_time.perf_counter() - _t

    # ── Foul features ─────────────────────────────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    if "pf" in df.columns and len(min_arr) > 0:
        _pf_arr  = pd.to_numeric(df["pf"], errors="coerce").fillna(0).values
        _mins10  = min_arr[-10:] if len(min_arr) >= 10 else min_arr
        _pfs10   = _pf_arr[-10:] if len(_pf_arr)  >= 10 else _pf_arr
        _tot10   = _mins10.sum()
        f["per_min_pf_last10"] = float(_pfs10.sum() / _tot10) if _tot10 > 0 else 0.0
        if len(_pfs10) >= 5:
            _xs = np.arange(len(_pfs10), dtype=float) - np.arange(len(_pfs10), dtype=float).mean()
            f["slope5_pf"] = float(np.polyfit(_xs[-5:], _pfs10[-5:], 1)[0])
        else:
            f["slope5_pf"] = 0.0
    else:
        f["per_min_pf_last10"] = 0.0
        f["slope5_pf"] = 0.0
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["foul_block"] += _prof_time.perf_counter() - _t


    # ── Per-minute aliases — v19 manifest naming parity ─────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    for _src, _dst in [
        ("pts_per_min_mean_last10",  "per_min_pts_last10"),
        ("reb_per_min_mean_last10",  "per_min_reb_last10"),
        ("ast_per_min_mean_last10",  "per_min_ast_last10"),
        ("fga_per_min_mean_last10",  "per_min_fga_last10"),
        ("fta_per_min_mean_last10",  "per_min_fta_last10"),
        ("stl_per_min_mean_last10",  "per_min_stl_last10"),
        ("blk_per_min_mean_last10",  "per_min_blk_last10"),
        ("stl_ewma_10",              "ewma10_stl"),
        ("blk_ewma_10",              "ewma10_blk"),
    ]:
        f[_dst] = f.get(_src, np.nan)

    # adv_<X>_mean_last10 -> adv_mean_<X>_last10 naming parity
    for _k in list(f.keys()):
        if _k.startswith("adv_") and "_mean_last10" in _k:
            _field = _k[4:_k.index("_mean_last10")]
            _mirror = f"adv_mean_{_field}_last10"
            if _mirror not in f:
                f[_mirror] = f[_k]
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["per_min_aliases"] += _prof_time.perf_counter() - _t

    # ── Real advanced features from prior_adv (non-zero fields only) ─────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    if prior_adv and len(prior_adv) > 0:
        _adf = pd.DataFrame(prior_adv).sort_values("game_date").reset_index(drop=True)
        _last10 = _adf.tail(10)
        _n10    = len(_last10)
        _exp_mp = max(f.get("exp_mp") or 25.0, 1.0)

        def _m10(col):
            if col not in _adf.columns: return np.nan
            v = _last10[col].dropna().values
            return float(np.mean(v)) if len(v) > 0 else np.nan

        # usage_percentage — mean=0.152, real data
        _up = _m10("usage_percentage")
        if not np.isnan(_up):
            f["adv_mean_usage_percentage_last10"] = _up

        # rebound_chances — mean=0.404, real data
        _rct = _m10("rebound_chances_total")
        if not np.isnan(_rct):
            f["reb_chances_per_game"]                  = _rct
            f["reb_chances_sample_last10"]             = float(_n10)
            f["adv_mean_rebound_chances_total_last10"] = _rct

        _rcd = _m10("rebound_chances_def")
        if not np.isnan(_rcd):
            f["reb_chances_def_per_game"] = _rcd

        _rco = _m10("rebound_chances_off")
        if not np.isnan(_rco):
            f["reb_chances_off_per_game"] = _rco
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["prior_adv_block"] += _prof_time.perf_counter() - _t

    # ── Safe gated / derived features ────────────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    _exp_mp2 = max(f.get("exp_mp") or 25.0, 1.0)

    # pts_per_poss_adj, ast_per_poss_adj using pace proxy
    _pace = f.get("opp_pace_proxy_last10") or 0.0
    if _pace > 10:
        _pmpts = f.get("per_min_pts_last10") or 0.0
        _pmast = f.get("per_min_ast_last10") or 0.0
        f["pts_per_poss_adj"] = _pmpts / max(_pace / 48.0, 1e-6)
        f["ast_per_poss_adj"] = _pmast / max(_pace / 48.0, 1e-6)

    # tov_per_min gated
    _tov_rate = f.get("tov_per_min_mean_last10", np.nan)
    if _tov_rate is not None and not (isinstance(_tov_rate, float) and np.isnan(_tov_rate)):
        f["tov_per_min_mean_last10_gated"] = float(_tov_rate) * int(_exp_mp2 >= 18)

    # regime shift gated
    _reb5  = f.get("reb_per_min_mean_last5",  0.0) or 0.0
    _reb10 = f.get("reb_per_min_mean_last10", 0.0) or 0.0
    f["reb_regime_shift_gated"] = abs(_reb5 - _reb10) * int(_exp_mp2 >= 18)

    _pts5  = f.get("pts_per_min_mean_last5",  0.0) or 0.0
    _pts10 = f.get("pts_per_min_mean_last10", 0.0) or 0.0
    f["pts_regime_shift_gated"] = abs(_pts5 - _pts10) * int(_exp_mp2 >= 18)

    # blowout_risk_x_mp_vol_gated
    _br  = f.get("blowout_risk", 0.0) or 0.0
    _mpv = f.get("mp_vol", 0.0)       or 0.0
    _hmd = int(f.get("has_market_data", 0))
    f["blowout_risk_x_mp_vol_gated"] = _br * _mpv * _hmd
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["safe_gated_block"] += _prof_time.perf_counter() - _t

    # ── Schedule ──────────────────────────────────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    dates = df["game_date"].tolist()
    f.update(schedule_features(dates, tdt))
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["schedule_features"] += _prof_time.perf_counter() - _t

    # ── Game script / market odds ─────────────────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    f.update(game_script_features(game_context, is_home))
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["game_script_features"] += _prof_time.perf_counter() - _t

    # ── Advanced stats (causal only) ──────────────────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    f.update(advanced_stats_block(prior_adv))
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["advanced_stats_block"] += _prof_time.perf_counter() - _t

    # ── Opponent defensive environment ────────────────────────────────────────
    # opp_team_id can be passed directly or extracted from game_context
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    _opp_id = opp_team_id or (game_context or {}).get("opp_team_id")
    f.update(opponent_defensive_features(
        opp_team_id  = _opp_id,
        target_date  = tdt,
        all_stats_df = all_stats_df,
    ))
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["opponent_defensive_features"] += _prof_time.perf_counter() - _t

    # ── Vacated opportunity + binary injury flags ─────────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    if training_mode:
        f.update({
            "vacated_minutes": np.nan, "vacated_fga": np.nan,
            "vacated_fg3a": np.nan, "vacated_fta": np.nan,
            "vacated_pts": np.nan, "vacated_ast": np.nan,
            "vacated_reb": np.nan, "vacated_usage_proxy": np.nan,
            "vacated_top1_fga": np.nan, "vacated_top2_fga": np.nan,
            "vacated_top1_usage_proxy": np.nan, "vacated_top2_usage_proxy": np.nan,
            "vacated_guard_minutes": np.nan, "vacated_big_minutes": np.nan,
            "vacated_creation_share": np.nan, "vacated_reb_share": np.nan,
            "num_teammates_inactive": 0, "has_injury_data": 0,
            "starter_out_flag": 0, "primary_creator_out_flag": 0, "center_out_flag": 0,
        })
    else:
        f.update(vacated_opportunity_features(
            player_id   = player_id,
            team_id     = team_id,
            target_date = tdt,
            stats_df    = all_stats_df,
            injury_map  = injury_map,
        ))
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["vacated_block"] += _prof_time.perf_counter() - _t

    # ── v2: Teammate with/without delta features (skipped during training for speed)
    if training_mode:
        f["usage_delta_without_top_creator"] = 0.0
        f["ast_delta_without_top_creator"]   = 0.0
        f["fg3a_delta_without_top_creator"]  = 0.0

    # ── Combo expectation proxies (always computed) ───────────────────────────
    if PROFILE_BUILD_TABLE:
        _t = _prof_time.perf_counter()
    # RA-specific: rolling joint reb+ast features and covariance
    if "reb" in df.columns and "ast" in df.columns:
        _reb_raw = df["reb"].values.astype(float)
        _ast_raw = df["ast"].values.astype(float)
        _ra_raw  = _reb_raw + _ast_raw
        f.update(rolling_full(_ra_raw, "ra_raw", stat="ra"))
        _last10_reb = _reb_raw[-10:]
        _last10_ast = _ast_raw[-10:]
        if len(_last10_reb) > 2:
            try:
                _cov_mat = np.cov(_last10_reb, _last10_ast)
                f["reb_ast_covariance_last10"] = float(_cov_mat[0, 1])
            except Exception:
                f["reb_ast_covariance_last10"] = np.nan
        else:
            f["reb_ast_covariance_last10"] = np.nan
    else:
        f["reb_ast_covariance_last10"] = np.nan
        for _sfx in ["mean_last3","mean_last5","mean_last10","mean_season","median_last10",
                     "vol_last10","cv_last10","ewma_10","p25_last10","p75_last10",
                     "floor_last10","ceiling_last10","trend_3v10","ewma_5"]:
            f[f"ra_raw_{_sfx}"] = np.nan
    f = add_interaction_features(f, "combo")
    if PROFILE_BUILD_TABLE:
        _BPGF_STATS["combo_interactions"] += _prof_time.perf_counter() - _t

    # ── Player metadata ───────────────────────────────────────────────────────
    f["games_played"] = len(df)
    f["is_home"]      = int(is_home)

    # ── [v19] Compute advanced matchup + archetype + shrinkage features ────────
    # [v19] Full feature compute runs at predict time with external maps
    # During training, archetype flags computed from available features above

    # ── Item 3: Primary ball-handler absence proxy ────────────────────────────
    if training_mode:
        f["primary_handler_limited"] = 0.0
    else:
        try:
            if not all_stats_df.empty and "ast" in all_stats_df.columns:
                team_games = all_stats_df[all_stats_df["team_id"] == team_id].copy()
                team_games["game_date"] = pd.to_datetime(team_games["game_date"])
                team_games = team_games[team_games["game_date"].astype(str) < str(tdt)[:10]]
                if len(team_games) >= 10:
                    last20_dates = sorted(team_games["game_date"].unique())[-20:]
                    recent = team_games[team_games["game_date"].isin(last20_dates)]
                    ast_by_player = recent.groupby("player_id")["ast"].mean()
                    if len(ast_by_player) > 0:
                        primary_id = ast_by_player.idxmax()
                        last_date = team_games["game_date"].max()
                        last_game = team_games[team_games["game_date"] == last_date]
                        handler_rows = last_game[last_game["player_id"] == primary_id]
                        if len(handler_rows) > 0:
                            handler_mp = pd.to_numeric(handler_rows["min"].iloc[0], errors="coerce")
                            f["primary_handler_limited"] = 1.0 if (pd.notna(handler_mp) and handler_mp < 15.0) else 0.0
                        else:
                            f["primary_handler_limited"] = 1.0
                    else:
                        f["primary_handler_limited"] = 0.0
                else:
                    f["primary_handler_limited"] = 0.0
            else:
                f["primary_handler_limited"] = 0.0
        except Exception:
            f["primary_handler_limited"] = 0.0
    return f

def add_interaction_features(f: dict, stat: str) -> dict:
    """
    Interaction features — v13.

    REMOVED (dead, 0% importance):
      usage_proxy_x_itt, fga_x_itt, ast_pct_x_itt, usage_x_itt,
      usage_x_pace, blowout_risk_x_mp_vol

    KEPT:
      reb_x_mp       — only interaction surviving ablation (5.6% for reb)
      E_pts_proxy    — pts_per_min x exp_mp (combo expectation)
      E_reb_proxy    — reb_per_min x exp_mp (combo expectation)
      E_ast_proxy    — ast_per_min x exp_mp (combo expectation)
    """
    mp = f.get("mean_min_last10") or f.get("mp_mean_last10")

    def _mul(a, b):
        if a is None or b is None: return np.nan
        a, b = float(a), float(b)
        return (a * b) if (not np.isnan(a) and not np.isnan(b)) else np.nan

    if stat in ("reb", "all", "combo"):
        f["reb_x_mp"] = _mul(f.get("reb_per_min_mean_last10"), mp)

    if stat in ("pra", "pr", "pa", "ra", "combo", "all"):
        f["E_pts_proxy"] = _mul(f.get("pts_per_min_mean_last10"), mp)
        f["E_reb_proxy"] = _mul(f.get("reb_per_min_mean_last10"), mp)
        f["E_ast_proxy"] = _mul(f.get("ast_per_min_mean_last10"), mp)

    if stat in ("stocks", "combo", "all"):
        # E_stocks_proxy: unconditional ZI means (per-game) for STL + BLK
        # hurdle_rate = p_nonzero * zi_lambda = E[count per game] from the ZI model
        _stl_h = f.get("stl_hurdle_rate_last10")
        _blk_h = f.get("blk_hurdle_rate_last10")
        if (_stl_h is not None and not (isinstance(_stl_h, float) and np.isnan(_stl_h)) and
                _blk_h is not None and not (isinstance(_blk_h, float) and np.isnan(_blk_h))):
            f["E_stocks_proxy"] = float(_stl_h) + float(_blk_h)
        else:
            f["E_stocks_proxy"] = np.nan

    return f


# ── Stat-specific feature gates ───────────────────────────────────────────────

def _shared_cols() -> list:
    """
    Universal features for all stat models.

    v13 changes:
      REMOVED: has_advanced_stats, has_injury_data, opp_has_env_data
      REMOVED: blowout_risk_x_mp_vol
      ADDED: starter_out_flag, primary_creator_out_flag, center_out_flag
      ADDED: opp_pace_proxy_last10, opp_fga_allowed_last10, opp_pts_allowed_last10
      ADDED: adv_usage_percentage + efficiency cols (causal for pts, universal)
    """
    return [
        # Standalone minutes model predictions
        "mean_min_last10","mp_q25","mp_q75","mp_vol","mp_pred_floor","mp_pred_ceiling",
        # Rolling minutes history
        "mp_mean_last3","mp_mean_last5","mp_mean_last10","mp_mean_season",
        "std_min_last10","mp_cv_last10","ewma10_min","mp_ewma_5",
        "mp_p25_last10","mp_p75_last10","mp_floor_last10","mp_ceiling_last10","trend_min",
        # Role
        "above_mean_pct_min","games_30plus_last10","games_20minus_last10","cv_min",
        # Schedule
        "rest_days","back_to_back","three_in_4","four_in_6",
        # Injury binary flags (in gates immediately — low noise)
        "starter_out_flag","primary_creator_out_flag","center_out_flag",
        # Causal advanced: universal
        "adv_mean_usage_percentage_last10","adv_usage_percentage_ewma",
        "adv_estimated_usage_percentage_mean_last10",
        "adv_true_shooting_percentage_mean_last10",
        "adv_effective_field_goal_percentage_mean_last10",
        # Opponent environment — universal
        "opp_pace_proxy_last10","opp_fga_allowed_last10","opp_allowed_pts_ewma",
        # pf as latent role proxy (keep until ablation disproves)
        "pf_per_min_mean_last10",
        # Line movement (accumulating from snapshots)
        "total_move","total_move_abs","steam_total_up","steam_total_down",
        # Context
        "is_home","games_played",
    ]



# =============================================================================
# LAYER 1
# =============================================================================

LAYER_1_CORE = [
    "mp_ewma_10",
    "mp_vol_last10",
    "mp_trend_3v10",
    "mp_mean_last10",
]

LAYER_1_COMBO_EXTENSION = [
    "mp_q25",
    "mp_q75",
    "mp_pred_floor",
    "mp_pred_ceiling",
]


# =============================================================================
# LAYER 2: STAT-SPECIFIC POSSESSION ENVIRONMENT
# =============================================================================

LAYER_2_PTS = [
    "implied_team_total",
    "opp_allowed_pts_ewma",
    "opp_allowed_pts_factor",
    "opp_allowed_pts_mean",
    "consensus_total",
    "spread_for_team",
    "is_home",
]

LAYER_2_AST = [
    "implied_team_total",
    "opp_allowed_ast_ewma",
    "opp_allowed_ast_factor",
    "opp_allowed_ast_mean",
    "consensus_total",
    "spread_for_team",
    "is_home",
    # opp_implied_total excluded — ablation Q4 will confirm
]

LAYER_2_REB = [
    "consensus_total",
    "opp_allowed_reb_ewma",
    "opp_allowed_reb_factor",
    "opp_allowed_reb_mean",
    "spread_for_team",
    "is_home",
    "implied_team_total",
]

LAYER_2_FG3M = [
    "implied_team_total",
    "opp_allowed_fg3m_ewma",
    "opp_allowed_fg3m_factor",
    "opp_allowed_fg3m_mean",
    "consensus_total",
    "spread_for_team",
    "is_home",
]

LAYER_2_BLK = [
    "opp_allowed_blk_ewma",
    "opp_allowed_blk_big_ewma",
    "opp_allowed_blk_guard_ewma",
    "opp_allowed_blk_factor",
    "opp_allowed_blk_mean",
    "spread_for_team",
    "is_home",
]

LAYER_2_STL = [
    "opp_allowed_stl_ewma",
    "opp_allowed_stl_guard_ewma",
    "opp_allowed_stl_big_ewma",
    "opp_allowed_stl_factor",
    "opp_allowed_stl_mean",
    "spread_for_team",
    "is_home",
]

LAYER_2_COMBO = [
    "implied_team_total",
    "implied_team_total",
    "consensus_total",
    "spread_for_team",
    "is_home",
]

# Stocks (STL+BLK) environment — pace and defensive opportunity, not scoring
LAYER_2_STOCKS = [
    "opp_allowed_stl_ewma",
    "opp_allowed_stl_guard_ewma",
    "opp_allowed_blk_ewma",
    "opp_allowed_blk_big_ewma",
    "opp_fga_allowed_last10",
    "opp_pace_proxy_last10",
    "spread_for_team",
    "is_home",
]

LAYER_2_MAP = {
    "pts":    LAYER_2_PTS,
    "ast":    LAYER_2_AST,
    "reb":    LAYER_2_REB,
    "fg3m":   LAYER_2_FG3M,
    "blk":    LAYER_2_BLK,
    "stl":    LAYER_2_STL,
    "stocks": LAYER_2_STOCKS,
    "pra":    LAYER_2_COMBO,
    "pr":     LAYER_2_COMBO,
    "pa":     LAYER_2_COMBO,
    "ra":     LAYER_2_COMBO,
}


# =============================================================================
# LAYER 3: ROLE / OPPORTUNITY
# =============================================================================

LAYER_3_ROLE = [
    "above_mean_pct_min",
    "cv_min",

    # ── TRUE PARTICIPATION FEATURES ───────────────────────────────────────────
    "did_not_play_last_team_game",  # any DNP last game
    "dnp_coach_decision",           # NEW: 0 min, NOT on injury report
    "dnp_injury",                   # NEW: 0 min + on injury report
    "dnp_rest",                     # NEW: 0 min + rest designation
    "limited_return_game",          # NEW: < 20 min after absence (rust game)
    "returned_from_absence",        # binary: returned after DNP streak
    "games_since_return",           # tightened: actual absence-based count

    # ── ROLE-STATE FLAGS ──────────────────────────────────────────────────────
    "is_stable_role_player",
    "is_recent_rotation_change",
    "is_injury_elevated_role",
    "is_high_minutes_uncertainty",
    "is_bench_fragile_minutes",

    # ── ARCHETYPE FLAGS (TIGHTENED TAXONOMY) ──────────────────────────────────
    # PRIMARY TIER — mutually exclusive
    # OVERLAY FLAGS
    # Continuous 0-1: how clearly does this player fit their archetype?
    # High = model can trust archetype-conditioned features
    # Low = player sits between buckets, uncertainty should widen predictions
    "per_min_pf_last10",
    "slope5_pf",

    # ── TEAMMATE ABSENCE SEVERITY (NEW) ──────────────────────────────────────
    # Not a replacement for transfer scores — a stabilizer
    # Captures overall absence burden regardless of who transfers

    # ── GLOBAL SAMPLE QUALITY FLAGS (NEW) ────────────────────────────────────
    # Fires when multiple thin-sample mechanics are unreliable simultaneously

    # ── PRECISE INJURY TRANSFER SCORES ───────────────────────────────────────
    "back_to_back",
    "four_in_6",
    "three_in_4",
    "rest_days",
]


# =============================================================================
# SHRINKAGE PARAMETERS
# =============================================================================

SHRINKAGE_PARAMS = {
    "iso_ppp":               (1.00, 30.0),
    "pnr_bh_ppp":            (0.90, 25.0),
    "spotup_ppp":            (0.98, 25.0),
    "transition_ppp":        (1.05, 20.0),
    "cs_open_3p_pct":        (0.38, 50.0),
    "cs_covered_3p_pct":     (0.31, 40.0),
    "spotup_matchup_edge":   (0.00, 20.0),
    "iso_matchup_edge":      (0.00, 30.0),
    "pnr_matchup_edge":      (0.00, 25.0),
    "rim_fg_pct_allowed":    (0.62, 40.0),
    "potential_ast_per_game":(7.0,  15.0),
}

# Sample-size thresholds for low-sample flags
LOW_SAMPLE_THRESHOLDS = {
    "iso_possessions":        15.0,
    "pnr_bh_possessions":     15.0,
    "spotup_possessions":     20.0,
    "transition_possessions": 12.0,
    "cs_3pa_sample":          30.0,
    "potential_ast_sample":   8.0,
    "rim_defended_sample":    15.0,
    "reb_chances_sample":     8.0,
}

def shrink_to_prior(
    observed: float,
    n_obs: float,
    prior: float,
    k: float,
) -> float:
    """Empirical Bayes shrinkage. weight = n / (n + k)."""
    if np.isnan(observed) or np.isnan(n_obs) or n_obs <= 0:
        return prior
    w = n_obs / (n_obs + k)
    return w * observed + (1.0 - w) * prior


# =============================================================================
# LAYER 4: STAT-SPECIFIC MECHANICS
# =============================================================================

def get_feature_cols_for_stat(stat: str, all_cols: list) -> list:
    """
    v19 final feature set. Stat map: pts, ast, reb, fg3m, blk, stl, pra, pr, pa, ra.
    Every feature has a direct causal mechanism.
    Noise blacklist enforced via audit_features_for_noise().
    """

    # ── PTS Layer 4 ───────────────────────────────────────────────────────────
    # standalone blowout_risk REMOVED (was in v18, removed in v19)
    PTS_L4 = [
        "per_min_pts_last10",
        "pts_per_min_mean_last5",
        "pts_per_min_mean_last10",
        "pts_per_min_trend_3v10",
        "per_min_fga_last10",
        "fga_per_min_trend_3v10",
        "per_min_fta_last10",




        "adv_mean_usage_percentage_last10",
        "adv_true_shooting_percentage_mean_last10",
        "opp_allowed_pts_ewma",
        "opp_allowed_pts_factor",

        "opp_fg_miss_volume",





        "pts_regime_shift_gated",
        "vacated_fga",
        "vacated_minutes",
        # standalone blowout_risk REMOVED — keep only:
        "blowout_risk_x_mp_vol_gated",
    ]

    # ── AST Layer 4 ───────────────────────────────────────────────────────────
    AST_L4 = [
        "per_min_ast_last10",
        "ast_per_min_mean_last5",
        "ast_per_min_mean_last10",
        "ast_per_min_trend_3v10",




        "adv_assist_percentage_mean_last10",






        "opp_allowed_ast_factor",
        "tov_per_min_mean_last10_gated",
        "vacated_ast",

        "blowout_risk_x_mp_vol_gated",
    ]

    # ── REB Layer 4 ───────────────────────────────────────────────────────────
    REB_L4 = [
        "per_min_reb_last10",
        "reb_per_min_mean_last5",
        "reb_per_min_mean_last10",
        "reb_per_min_trend_3v10",
        "reb_per_min_vol_last10",
        "oreb_per_min_mean_last10",
        "dreb_per_min_mean_last10",
        "reb_chances_per_game",
        "reb_chances_def_per_game",
        "reb_chances_off_per_game",

        "reb_chances_sample_last10",    # explicitly surfaced
        "adv_rebound_chances_total_mean_last10",
        "adv_rebound_chances_off_mean_last10",
        "adv_rebound_chances_def_mean_last10",
        "adv_mean_rebound_chances_total_last10",



        "opp_fg_miss_volume",

        "opp_allowed_reb_factor",
        "vacated_reb",
        "vacated_big_minutes",
        "reb_regime_shift_gated",
        "blowout_risk_x_mp_vol_gated",
    ]

    # ── FG3M Layer 4 ──────────────────────────────────────────────────────────
    # vacated_minutes REMOVED (too blunt; wing transfer in Layer 3 covers it)
    FG3M_L4 = [
        "per_min_fg3a_last10",
        "fg3a_per_min_trend_3v10",



        "fg3_pct_safe",


        "adv_pct_3pa_mean_last10",
        "is_low_3pa_last10",
        "fg3m_p_zero_last10",
        "fg3m_p_ge3_last10",




        "opp_3pa_allowed",
        "opp_3pm_allowed",
        "opp_3p_rate_allowed",
        "opp_3pt_miss_volume",


        # vacated_minutes REMOVED
        "blowout_risk_x_mp_vol_gated",
    ]

    # ── BLK Layer 4 ───────────────────────────────────────────────────────────
    BLK_L4 = [
        "per_min_blk_last10",
        "ewma10_blk",
        "blk_per_min_vol_last10",
        "blk_p_zero_last10",
        "blk_p_ge1_last10",
        "blk_p_ge2_last10",
        # ZI hurdle features — directly fix positive mean bias across all BLK roles
        "blk_p_nonzero_last20",
        "blk_zi_lambda_last10",
        "blk_hurdle_rate_last10",
        # Opponent FGA volume: more attempts = more block opportunities
        "opp_fga_allowed_last10",
        "opp_allowed_blk_big_ewma",




        "vacated_big_minutes",
        "vacated_minutes",
        "blowout_risk_x_mp_vol_gated",
    ]

    # ── STL Layer 4 ───────────────────────────────────────────────────────────
    # blowout_risk REMOVED (cleanest sparse model)
    # opp_tov_per_game REMOVED from model (fallback in compute block only)
    STL_L4 = [
        "per_min_stl_last10",
        "ewma10_stl",
        "stl_per_min_vol_last10",
        "stl_p_zero_last10",
        "stl_p_ge1_last10",
        "stl_p_ge2_last10",
        "tov_p_zero_last10",
        "tov_p_ge1_last10",
        "tov_p_ge2_last10",
        # ZI hurdle features — directly fix positive mean bias across all STL roles
        "stl_p_nonzero_last20",
        "stl_zi_lambda_last10",
        "stl_hurdle_rate_last10",
        # Opponent pace: faster games = more steal opportunities
        "opp_pace_proxy_last10",






        "vacated_minutes",
        # blowout_risk REMOVED
    ]

    # ── COMBO PROPS Layer 4 ───────────────────────────────────────────────────

    PRA_L4 = [
        "per_min_pts_last10", "pts_per_min_trend_3v10",
        "per_min_fga_last10",
        "opp_allowed_pts_ewma",
        "per_min_reb_last10", "reb_chances_per_game",
        "per_min_ast_last10",
        "adv_mean_usage_percentage_last10",
        "vacated_minutes",
        "pts_regime_shift_gated", "blowout_risk_x_mp_vol_gated",
    ]

    PR_L4 = [
        "per_min_pts_last10", "pts_per_min_trend_3v10",
        "per_min_fga_last10", "opp_allowed_pts_ewma",

        "per_min_reb_last10", "reb_chances_per_game",
        "opp_fg_miss_volume",
        "adv_mean_usage_percentage_last10",

        "vacated_minutes", "blowout_risk_x_mp_vol_gated",
    ]

    PA_L4 = [
        "per_min_pts_last10", "pts_per_min_trend_3v10",
        "per_min_fga_last10", "opp_allowed_pts_ewma",
        "per_min_ast_last10",
        "opp_allowed_ast_factor",
        "adv_mean_usage_percentage_last10",
        "vacated_minutes", "blowout_risk_x_mp_vol_gated",
    ]

    RA_L4 = [
        "per_min_reb_last10", "reb_chances_per_game",
        "opp_fg_miss_volume",
        "per_min_ast_last10",
        "opp_allowed_ast_factor",
        "adv_mean_usage_percentage_last10",
        # RA covariance features — joint reb+ast rolling stats
        "ra_raw_mean_last10",
        "ra_raw_ewma_10",
        "reb_ast_covariance_last10",
        "vacated_minutes", "blowout_risk_x_mp_vol_gated",
    ]

    # ── STOCKS Layer 4 ────────────────────────────────────────────────────────
    # Previously: stocks had NO dedicated L4 — it used empty list fallback.
    # Root cause of positive mean bias across all stocks role cells.
    STOCKS_L4 = [
        # STL predictors
        "per_min_stl_last10",
        "ewma10_stl",
        "stl_p_nonzero_last20",
        "stl_zi_lambda_last10",
        "stl_hurdle_rate_last10",
        # BLK predictors
        "per_min_blk_last10",
        "ewma10_blk",
        "blk_p_nonzero_last20",
        "blk_zi_lambda_last10",
        "blk_hurdle_rate_last10",
        # Stocks expectation proxy = ZI unconditional means summed
        "E_stocks_proxy",
        # Opportunity
        "vacated_minutes",
        "blowout_risk_x_mp_vol_gated",
    ]

    STAT_L4 = {
        "pts":    PTS_L4,    "ast":  AST_L4, "reb": REB_L4,
        "fg3m":   FG3M_L4,   "blk":  BLK_L4, "stl": STL_L4,
        "stocks": STOCKS_L4,
        "pra":    PRA_L4,    "pr":   PR_L4,  "pa":  PA_L4, "ra": RA_L4,
    }

    is_combo = stat in ("pra", "pr", "pa", "ra", "stocks")
    l1 = LAYER_1_CORE + (LAYER_1_COMBO_EXTENSION if is_combo else [])
    l2 = LAYER_2_MAP.get(stat, LAYER_2_PTS)
    l3 = LAYER_3_ROLE
    l4 = STAT_L4.get(stat, [])
    full = l1 + l2 + l3 + l4

    seen, deduped = set(), []
    for feat in full:
        if feat not in seen:
            seen.add(feat)
            deduped.append(feat)

    all_cols_set = set(all_cols)
    available = [f for f in deduped if f in all_cols_set]
    missing   = [f for f in deduped if f not in all_cols_set]

    if missing:
        import logging
        logging.getLogger(__name__).warning(
            f"[v19] {stat}: {len(missing)} absent: {missing[:15]}"
        )

    return available


# =============================================================================
# NOISE BLACKLIST
# =============================================================================

NOISE_FEATURES_BLACKLIST = {
    "revenge_game", "is_revenge",
    "pts_vs_opp_mean", "ast_vs_opp_mean", "reb_vs_opp_mean", "fg3m_vs_opp_mean",
    "pts_vs_opp_n",    "ast_vs_opp_n",    "reb_vs_opp_n",    "fg3m_vs_opp_n",
    "usage_proxy_per_min_mean_last10", "usage_proxy_per_min_cv_last10",
    "usage_proxy_per_min_vol_last10",  "usage_proxy_per_min_trend_3v10",
    "mp_mean_last3", "mp_mean_last5", "mp_mean_last10", "mp_mean_season",
    "mp_ceiling_last10", "mp_floor_last10", "mp_p25_last10", "mp_p75_last10",
    "mp_cv_last10",
    "iso_matchup_edge", "pnr_matchup_edge", "spotup_matchup_edge",
    "cs_open_3p_pct", "cs_covered_3p_pct",
    "spotup_ppp", "pnr_bh_ppp", "transition_ppp", "rim_fg_pct_allowed",
    "potential_ast_per_game",
    "clv_proxy", "line_movement", "opening_line_vs_close",
    "missed_last_game", "num_teammates_inactive",
    "blowout_risk_x_mp_vol", "pts_regime_shift", "reb_regime_shift",
    "tov_per_min_mean_last10", "vacated_guard_minutes",
}

STAT_SPECIFIC_NOISE = {
    "blk": {"adv_assist_percentage_mean_last10", "adv_assist_to_turnover_mean_last10",
             "adv_effective_field_goal_percentage_mean_last10",
             "adv_mean_usage_percentage_last10", "implied_team_total",
             "consensus_total", "implied_team_total"},
    "stl": {"adv_assist_percentage_mean_last10", "adv_assist_to_turnover_mean_last10",
             "opp_tov_per_game", "implied_team_total", "opp_implied_team_total",
             "consensus_total", "blowout_risk"},
    "pts": {"blowout_risk"},    # standalone removed in v19; gated version only
    "fg3m":{"blowout_risk", "vacated_minutes"},  # removed in v19
    "ast": {"blowout_risk"},    # standalone removed; gated version only
}


def audit_features_for_noise(feature_list: list, stat: str) -> dict:
    """Run after get_feature_cols_for_stat(). Hard fail on any noise."""
    universal  = [f for f in feature_list if f in NOISE_FEATURES_BLACKLIST]
    stat_noise = STAT_SPECIFIC_NOISE.get(stat, set())
    specific   = [f for f in feature_list if f in stat_noise]
    all_viol   = list(set(universal + specific))
    clean      = [f for f in feature_list if f not in set(all_viol)]

    import logging
    log = logging.getLogger(__name__)
    if all_viol:
        log.error(f"[v19 NOISE AUDIT FAIL] {stat}: {all_viol}")
    else:
        log.info(f"[v19 NOISE AUDIT PASS] {stat}: {len(clean)} features")

    return {"clean": clean, "violations": all_viol,
            "passed": len(all_viol) == 0, "n_features": len(clean)}

