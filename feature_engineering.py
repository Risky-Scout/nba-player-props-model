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


# ── Rolling helper: 13 features per series ────────────────────────────────────

def rolling_full(arr: np.ndarray, name: str) -> dict:
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

    # EWMA alpha=0.3 (half-life ~2 games) — fast recency
    if n >= 2:
        s = pd.Series(arr)
        f[f"{name}_ewma_10"] = float(s.ewm(alpha=0.3, min_periods=2).mean().iloc[-1])
    else:
        f[f"{name}_ewma_10"] = arr[-1] if n == 1 else np.nan

    # EWMA alpha=0.15 (half-life ~4.5 games) — medium recency, recommended by expert review
    # Different from ewma_10: captures slower role/usage drift (e.g. 10-game role shift)
    if n >= 2:
        s = pd.Series(arr)
        f[f"{name}_ewma_5"] = float(s.ewm(alpha=0.15, min_periods=2).mean().iloc[-1])
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
            "mp_ewma_10","mp_vol_last10","mp_cv_last10",
            "mp_p25_last10","mp_p75_last10","mp_floor_last10","mp_ceiling_last10",
            "mp_trend_3v10","mp_median_last10",
            "starter_rate_last10","games_30plus_last10","games_35plus_last10",
            "games_20minus_last10","role_stability_index",
        ]
        return {k: np.nan for k in keys}

    min_arr = df["min"].values.astype(float)
    f.update(rolling_full(min_arr, "mp"))

    last10_min = min_arr[-10:]
    n = len(last10_min)

    f["starter_rate_last10"]  = float(np.mean(last10_min >= 28)) if n > 0 else np.nan
    f["games_30plus_last10"]  = float(np.sum(last10_min >= 30))  if n > 0 else np.nan
    f["games_35plus_last10"]  = float(np.sum(last10_min >= 35))  if n > 0 else np.nan
    f["games_20minus_last10"] = float(np.sum(last10_min <= 20))  if n > 0 else np.nan

    if n > 1 and np.max(last10_min) > 0:
        f["role_stability_index"] = float(
            1.0 - (np.std(last10_min) / np.max(last10_min))
        )
    else:
        f["role_stability_index"] = np.nan

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
            "game_total": np.nan, "spread_for_team": np.nan,
            "implied_team_total": np.nan, "blowout_risk": np.nan,
            "opp_implied_total": np.nan,
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
    f["game_total"]         = total
    f["spread_for_team"]    = team_spread
    f["implied_team_total"] = implied_team
    f["opp_implied_total"]  = opp_implied
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

def opponent_defensive_features(
    opp_team_id: Optional[int],
    target_date: pd.Timestamp,
    all_stats_df: pd.DataFrame,
    window: int = 10,
) -> dict:
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
        "opp_pts_allowed_last10":     np.nan,
        "opp_reb_allowed_last10":     np.nan,
        "opp_oreb_allowed_last10":    np.nan,
        "opp_ast_allowed_last10":     np.nan,
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
        df = all_stats_df.copy()
        df["game_date"] = pd.to_datetime(df["game_date"])

        # Find opponent's recent game IDs (before target date)
        opp_rows = df[
            (df["team_id"] == opp_team_id) &
            (df["game_date"] < target_date)
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

        pts  = _game_avg("pts")
        reb  = _game_avg("reb")
        oreb = _game_avg("oreb")
        ast  = _game_avg("ast")
        fg3a = _game_avg("fg3a")
        fg3m = _game_avg("fg3m")
        fga  = _game_avg("fga")
        fta  = _game_avg("fta")
        tov  = _game_avg("turnover")

        result = {
            "opp_pts_allowed_last10":  pts  if pts  is not None else np.nan,
            "opp_reb_allowed_last10":  reb  if reb  is not None else np.nan,
            "opp_oreb_allowed_last10": oreb if oreb is not None else np.nan,
            "opp_ast_allowed_last10":  ast  if ast  is not None else np.nan,
            "opp_3pa_allowed_last10":  fg3a if fg3a is not None else np.nan,
            "opp_3pm_allowed_last10":  fg3m if fg3m is not None else np.nan,
            "opp_fga_allowed_last10":  fga  if fga  is not None else np.nan,
        }

        # 3P rate allowed
        if fg3a is not None and fga is not None and fga > 0:
            result["opp_3p_rate_allowed_last10"] = float(fg3a / fga)
        else:
            result["opp_3p_rate_allowed_last10"] = np.nan

        # Pace proxy: FGA + 0.44*FTA + TOV - OREB
        if all(v is not None for v in [fga, fta, tov, oreb]):
            result["opp_pace_proxy_last10"] = float(
                fga + 0.44 * fta + tov - oreb
            )
        else:
            result["opp_pace_proxy_last10"] = np.nan

        return result

    except Exception:
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

    adv_records = sorted(adv_records, key=lambda x: x.get("game_date", ""))
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
        (stats_df["game_date"] < target_date)
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
            (stats_df["game_date"] < target_date)
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
            (stats_df["game_date"] < target_date)
        ]
        if pdata.empty:
            return np.nan
        return float(np.nanmean(pdata["min"].values.astype(float)))

    def _classify_role(pid: int) -> str:
        pdata = stats_df[
            (stats_df["player_id"] == pid) &
            (stats_df["game_date"] < target_date)
        ]
        if pdata.empty:
            return "unknown"
        avg_reb = np.nanmean(pdata["reb"].values.astype(float)) if "reb" in pdata.columns else 0
        avg_ast = np.nanmean(pdata["ast"].values.astype(float)) if "ast" in pdata.columns else 0
        avg_blk = np.nanmean(pdata["blk"].values.astype(float)) if "blk" in pdata.columns else 0
        if avg_reb > avg_ast and avg_blk > 0.3:
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
) -> dict:
    """
    Build complete pregame feature vector for one player.
    ZERO leakage: all inputs strictly prior to target_date.
    Returns flat dict — NaN where data unavailable.

    NEW v13: opp_team_id parameter for opponent_defensive_features().
    Pass from game_context['opp_team_id'] or derive from BDL game data.
    """
    f = {}
    df  = prior_stats.sort_values("game_date").reset_index(drop=True)
    tdt = pd.Timestamp(target_date)

    min_arr = df["min"].values.astype(float) if "min" in df.columns else np.array([])

    # ── Minutes model block ───────────────────────────────────────────────────
    f.update(minutes_model_features(df))

    # ── Standalone minutes model predictions ─────────────────────────────────
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
        for k in ("exp_mp","mp_q10","mp_q25","mp_q75","mp_q90",
                  "mp_vol","mp_pred_floor","mp_pred_ceiling"):
            f[k] = np.nan

    # ── Per-minute rates + full rolling ──────────────────────────────────────
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

    # ── Usage proxy ───────────────────────────────────────────────────────────
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

    # ── 3PM block: two-stage ──────────────────────────────────────────────────
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

        PRIOR_3P = 0.36
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
            f["fg3a_per_min_mean_last10"] = float(np.nanmean(r3a_10)) if len(r3a_10) > 0 else np.nan
            if len(min_arr) >= 3:
                r3a_3 = per_minute_rate(fg3a_arr[-3:], min_arr[-3:])
                m3a   = float(np.nanmean(r3a_3))
                m10a  = f["fg3a_per_min_mean_last10"]
                f["fg3a_per_min_trend_3v10"] = (m3a / m10a) if (m10a and m10a > 0.001) else np.nan
            else:
                f["fg3a_per_min_trend_3v10"] = np.nan
        else:
            f["fg3a_per_min_mean_last10"]  = np.nan
            f["fg3a_per_min_trend_3v10"]   = np.nan
    else:
        for _k in [
            "fg3m_p_zero_last10","fg3m_p_ge3_last10",
            "fg3_pct_safe","fg3a_count_last10","fg3a_count_season","is_low_3pa_last10",
            "fg3a_attempt_trend","fg3a_per_min_mean_last10","fg3a_per_min_trend_3v10",
        ]:
            f[_k] = np.nan

    # ── STL / BLK sparse treatment ────────────────────────────────────────────
    BLEND_K = 15.0
    for sparse_stat, col in [("stl", "stl"), ("blk", "blk")]:
        if col in df.columns and len(min_arr) > 0:
            raw  = df[col].values.astype(float)
            rate = per_minute_rate(raw, min_arr)
            last10_raw = raw[-10:]

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

            # EWMA for sparse stats
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
        else:
            for k in [f"{sparse_stat}_p_zero_last10", f"{sparse_stat}_p_ge2_last10",
                      f"{sparse_stat}_p_ge1_last10", f"{sparse_stat}_per_min_blended",
                      f"{sparse_stat}_per_min_ewma_10", f"{sparse_stat}_per_min_vol_last10"]:
                f[k] = np.nan

    # ── Schedule ──────────────────────────────────────────────────────────────
    dates = df["game_date"].tolist()
    f.update(schedule_features(dates, tdt))

    # ── Game script / market odds ─────────────────────────────────────────────
    f.update(game_script_features(game_context, is_home))

    # ── Advanced stats (causal only) ──────────────────────────────────────────
    f.update(advanced_stats_block(prior_adv))

    # ── Opponent defensive environment ────────────────────────────────────────
    # opp_team_id can be passed directly or extracted from game_context
    _opp_id = opp_team_id or (game_context or {}).get("opp_team_id")
    f.update(opponent_defensive_features(
        opp_team_id  = _opp_id,
        target_date  = tdt,
        all_stats_df = all_stats_df,
    ))

    # ── Vacated opportunity + binary injury flags ─────────────────────────────
    f.update(vacated_opportunity_features(
        player_id   = player_id,
        team_id     = team_id,
        target_date = tdt,
        stats_df    = all_stats_df,
        injury_map  = injury_map,
    ))

    # ── Combo expectation proxies (always computed) ───────────────────────────
    f = add_interaction_features(f, "combo")

    # ── Player metadata ───────────────────────────────────────────────────────
    f["games_played"] = len(df)
    f["is_home"]      = int(is_home)

    return f


# ── Interaction features ──────────────────────────────────────────────────────

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
    mp = f.get("exp_mp") or f.get("mp_mean_last10")

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
        "exp_mp","mp_q25","mp_q75","mp_vol","mp_pred_floor","mp_pred_ceiling",
        # Rolling minutes history
        "mp_mean_last3","mp_mean_last5","mp_mean_last10","mp_mean_season",
        "mp_vol_last10","mp_cv_last10","mp_ewma_10","mp_ewma_5",
        "mp_p25_last10","mp_p75_last10","mp_floor_last10","mp_ceiling_last10","mp_trend_3v10",
        # Role
        "starter_rate_last10","games_30plus_last10","games_20minus_last10","role_stability_index",
        # Schedule
        "rest_days","back_to_back","three_in_4","four_in_6",
        # Injury binary flags (in gates immediately — low noise)
        "starter_out_flag","primary_creator_out_flag","center_out_flag",
        # Causal advanced: universal
        "adv_usage_percentage_mean_last10","adv_usage_percentage_ewma",
        "adv_estimated_usage_percentage_mean_last10",
        "adv_true_shooting_percentage_mean_last10",
        "adv_effective_field_goal_percentage_mean_last10",
        # Opponent environment — universal
        "opp_pace_proxy_last10","opp_fga_allowed_last10","opp_pts_allowed_last10",
        # pf as latent role proxy (keep until ablation disproves)
        "pf_per_min_mean_last10",
        # Line movement (accumulating from snapshots)
        "total_move","total_move_abs","steam_total_up","steam_total_down",
        # Context
        "is_home","games_played",
    ]


def get_feature_cols_for_stat(stat: str, all_cols: list) -> list:
    """
    Stat-specific feature gate — v13.

    Philosophy:
      - Minutes + rolling player stats remain dominant (correct hierarchy)
      - Opponent environment is now real (not a proxy)
      - Market features: total_move/steam in gates; game_total etc. in MONITOR
      - Injury continuous: in MONITOR; binary flags in gates
      - Dead interactions: removed entirely
      - Dead advanced stats (28 fields): removed entirely
      - Causal advanced stats only: 6 universal + 3 reb-specific

    MONITOR (computed but NOT in gates):
      game_total, implied_team_total, spread_for_team, blowout_risk,
      opp_implied_total, has_odds, missed_last_game, missed_2_of_last5,
      all vacated_* continuous features, num_teammates_inactive, has_injury_data
    """
    wanted = set(_shared_cols())

    if stat == "pts":
        wanted |= {
            "fga_per_min_mean_last3","fga_per_min_mean_last5","fga_per_min_mean_last10",
            "fga_per_min_vol_last10","fga_per_min_cv_last10","fga_per_min_ewma_10","fga_per_min_ewma_5",
            "fga_per_min_trend_3v10",
            "fga_raw_mean_last10",
            "fta_per_min_mean_last10",
            "pts_per_min_mean_last10","pts_per_min_vol_last10","pts_per_min_cv_last10",
            "usage_proxy_per_min_mean_last10","usage_proxy_per_min_vol_last10",
            "usage_proxy_per_min_cv_last10","usage_proxy_per_min_trend_3v10",
            # Scoring-specific causal advanced (v14)
            "adv_free_throw_attempt_rate_mean_last10","adv_free_throw_attempt_rate_ewma",
            "adv_pct_fga_mean_last10",
            "adv_pct_fta_mean_last10",
            "adv_pct_points_mean_last10",
        }

    elif stat == "reb":
        wanted |= {
            "reb_per_min_mean_last3","reb_per_min_mean_last5","reb_per_min_mean_last10",
            "reb_per_min_median_last10",
            "reb_per_min_vol_last10","reb_per_min_cv_last10",
            "reb_per_min_ewma_10","reb_per_min_ewma_5",
            "reb_per_min_p25_last10","reb_per_min_p75_last10","reb_per_min_trend_3v10",
            "reb_raw_mean_last10","reb_raw_cv_last10",
            "oreb_per_min_mean_last10","dreb_per_min_mean_last10",
            # Opponent reb environment
            "opp_reb_allowed_last10","opp_oreb_allowed_last10",
            # Only surviving interaction
            "reb_x_mp",
            # Causal advanced: player's own rebound chances + rate (v14 adds pct)
            "adv_rebound_chances_total_mean_last10",
            "adv_rebound_chances_def_mean_last10",
            "adv_rebound_chances_off_mean_last10",
            "adv_rebound_percentage_mean_last10",
            "adv_offensive_rebound_percentage_mean_last10",
            "adv_defensive_rebound_percentage_mean_last10",
        }

    elif stat == "ast":
        wanted |= {
            "ast_per_min_mean_last3","ast_per_min_mean_last5","ast_per_min_mean_last10",
            "ast_per_min_vol_last10","ast_per_min_cv_last10",
            "ast_per_min_ewma_10","ast_per_min_ewma_5",
            "ast_per_min_p25_last10","ast_per_min_p75_last10","ast_per_min_trend_3v10",
            "ast_raw_mean_last10","ast_raw_cv_last10",
            "usage_proxy_per_min_mean_last10",
            "tov_per_min_mean_last10",
            # Causal advanced: creation quality (v14 adds assist_ratio)
            "adv_assist_percentage_mean_last10","adv_assist_percentage_ewma",
            "adv_assist_to_turnover_mean_last10",
            "adv_assist_ratio_mean_last10","adv_assist_ratio_ewma",
            # Opponent assist environment
            "opp_ast_allowed_last10",
        }

    elif stat == "fg3m":
        wanted |= {
            "mp_mean_last5","mp_mean_last10","mp_vol_last10","mp_ewma_10","mp_ewma_5","mp_trend_3v10",
            "fg3a_per_min_mean_last10","fg3a_per_min_trend_3v10",
            "fg3a_count_last10","fg3a_count_season","fg3a_attempt_trend",
            "fg3_pct_safe","fg3m_p_zero_last10","fg3m_p_ge3_last10","is_low_3pa_last10",
            # Share of shots that are 3s (v14)
            "adv_pct_3pa_mean_last10",
            # Opponent 3P environment
            "opp_3pa_allowed_last10","opp_3pm_allowed_last10","opp_3p_rate_allowed_last10",
        }

    elif stat == "stl":
        wanted |= {
            "stl_per_min_blended","stl_per_min_vol_last10","stl_per_min_ewma_10",
            "stl_p_zero_last10","stl_p_ge2_last10","stl_p_ge1_last10",
            "adv_pct_steals_mean_last10",     # player's steal share while on court (v14)
            "opp_pace_proxy_last10",
        }

    elif stat == "blk":
        wanted |= {
            "blk_per_min_blended","blk_per_min_vol_last10","blk_per_min_ewma_10",
            "blk_p_zero_last10","blk_p_ge2_last10","blk_p_ge1_last10",
            "adv_pct_blocks_mean_last10",      # player's block share while on court (v14)
            "center_out_flag",
            "opp_fga_allowed_last10",
        }

    elif stat == "tov":
        wanted |= {
            "tov_per_min_mean_last10","tov_per_min_vol_last10","tov_per_min_trend_3v10",
            "tov_raw_mean_last10","tov_raw_cv_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_usage_percentage_mean_last10",
            "adv_assist_to_turnover_mean_last10",
            "opp_pace_proxy_last10",
        }

    elif stat == "pra":
        wanted |= {
            "pts_per_min_mean_last10","reb_per_min_mean_last10","ast_per_min_mean_last10",
            "pts_per_min_vol_last10","reb_per_min_vol_last10","ast_per_min_vol_last10",
            "pts_per_min_cv_last10","reb_per_min_cv_last10","ast_per_min_cv_last10",
            "reb_per_min_median_last10","usage_proxy_per_min_mean_last10",
            "E_pts_proxy","E_reb_proxy","E_ast_proxy",
            "opp_pts_allowed_last10","opp_reb_allowed_last10","opp_ast_allowed_last10",
            "adv_assist_percentage_mean_last10","adv_assist_to_turnover_mean_last10",
            "adv_assist_ratio_mean_last10",
            "adv_rebound_chances_total_mean_last10",
            "adv_rebound_percentage_mean_last10",
        }

    elif stat == "pr":
        wanted |= {
            "pts_per_min_mean_last10","reb_per_min_mean_last10",
            "pts_per_min_vol_last10","reb_per_min_vol_last10",
            "reb_per_min_median_last10","reb_per_min_cv_last10",
            "usage_proxy_per_min_mean_last10",
            "E_pts_proxy","E_reb_proxy",
            "opp_pts_allowed_last10","opp_reb_allowed_last10",
            "adv_rebound_chances_total_mean_last10",
            "adv_rebound_percentage_mean_last10",
        }

    elif stat == "pa":
        wanted |= {
            "pts_per_min_mean_last10","ast_per_min_mean_last10",
            "pts_per_min_vol_last10","ast_per_min_vol_last10","ast_per_min_cv_last10",
            "usage_proxy_per_min_mean_last10",
            "E_pts_proxy","E_ast_proxy",
            "opp_pts_allowed_last10","opp_ast_allowed_last10",
            "adv_assist_percentage_mean_last10","adv_assist_to_turnover_mean_last10",
            "adv_assist_ratio_mean_last10",
        }

    elif stat == "ra":
        wanted |= {
            "reb_per_min_mean_last10","ast_per_min_mean_last10",
            "reb_per_min_vol_last10","ast_per_min_vol_last10",
            "reb_per_min_median_last10","reb_per_min_cv_last10",
            "E_reb_proxy","E_ast_proxy",
            "opp_reb_allowed_last10","opp_ast_allowed_last10",
            "adv_rebound_chances_total_mean_last10","adv_rebound_percentage_mean_last10",
            "adv_assist_percentage_mean_last10","adv_assist_ratio_mean_last10",
        }

    elif stat == "stocks":
        wanted |= {
            "stl_per_min_blended","stl_per_min_vol_last10","stl_per_min_ewma_10",
            "blk_per_min_blended","blk_per_min_vol_last10","blk_per_min_ewma_10",
            "stl_p_zero_last10","stl_p_ge2_last10","stl_p_ge1_last10",
            "blk_p_zero_last10","blk_p_ge2_last10","blk_p_ge1_last10",
            "adv_pct_steals_mean_last10","adv_pct_blocks_mean_last10",
            "opp_pace_proxy_last10",
        }

    return [c for c in all_cols if c in wanted]
