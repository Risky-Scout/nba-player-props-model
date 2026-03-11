"""
feature_engineering.py — NBA Props Model Feature Engineering
VERSION: 2026-03-09-v12

Key upgrades over v10:
  - rolling_full(): 13 features per series (was 7)
      + median_last10    — anchors P50 correctly for skewed players
      + cv_last10        — flags high-variance players (Prosper, sparse events)
      + trend_3v10       — recency trend (minutes, rate)
      + floor_last10     — min of last 10 (quantile anchor)
      + ceiling_last10   — max of last 10 (quantile anchor)
      + mean_last3       — ultra-recent window
  - EWMA alpha=0.3 (half-life ~2 games) — was span=10 (too slow)
  - mean_season now EWMA-weighted over full season — not arithmetic
  - Expanded advanced stats: 20+ fields with rolling (was 6 fields)
  - Opponent matchup features from game context
  - Starter rate + role stability index
  - Role-conditioned vacated opportunity
  - Raw count rolling alongside per-minute rates
  - Coefficient of variation for all major stats
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

# Advanced stats fields from BDL v2 — grouped by stat relevance
ADV_FIELDS_CORE = [
    "usage_percentage",
    "pace",
    "true_shooting_percentage",
    "effective_field_goal_percentage",
    "assist_percentage",
    "assist_to_turnover",
]

ADV_FIELDS_EXPANDED = [
    # Opportunity / role
    "possessions",
    "estimated_usage_percentage",
    "touches",
    "passes",
    "fouls_drawn",
    "pct_fga",
    "pct_3pa",
    "pct_points",
    # Rebounding
    "rebound_chances_total",
    "rebound_chances_def",
    "rebound_chances_off",
    # Defense / steals / blocks
    "deflections",
    "contested_shots",
    "contested_shots_2pt",
    "contested_shots_3pt",
    "defended_at_rim_fga",
    "defended_at_rim_fg_pct",
    # Matchup
    "matchup_fga",
    "matchup_fg_pct",
    "matchup_player_points",
    "matchup_turnovers",
    "switches_on",
    "partial_possessions",
    # Secondary creation
    "secondary_assists",
    "free_throw_assists",
    # Paint / scoring context
    "points_paint",
    "points_off_turnovers",
    "points_second_chance",
]

ALL_ADV_FIELDS = ADV_FIELDS_CORE + ADV_FIELDS_EXPANDED


# ── Rolling helper: 13 features per series ────────────────────────────────────

def rolling_full(arr: np.ndarray, name: str) -> dict:
    """
    Full rolling feature pack — 13 features per series.
    Applied to per-minute rates OR raw counts depending on caller.
    NaN returned where insufficient data (LightGBM handles natively).

    Features added vs v10:
      - median_last10  : anchors P50 for skewed distributions
      - cv_last10      : coefficient of variation — flags high-variance players
      - trend_3v10     : mean_last3 / mean_last10 — recency drift signal
      - floor_last10   : min of window — quantile lower anchor
      - ceiling_last10 : max of window — quantile upper anchor
      - mean_last3     : ultra-recent 3-game window
    """
    arr = arr.astype(float)
    arr = arr[~np.isnan(arr)]   # strip NaN before computing
    n   = len(arr)
    f   = {}

    def _safe_mean(a):   return float(np.mean(a))           if len(a) > 0 else np.nan
    def _safe_median(a): return float(np.median(a))         if len(a) > 0 else np.nan
    def _safe_mad(a):    return float(np.mean(np.abs(a - np.median(a)))) if len(a) > 1 else np.nan
    def _safe_p25(a):    return float(np.percentile(a, 25)) if len(a) > 1 else np.nan
    def _safe_p75(a):    return float(np.percentile(a, 75)) if len(a) > 1 else np.nan
    def _safe_min(a):    return float(np.min(a))            if len(a) > 0 else np.nan
    def _safe_max(a):    return float(np.max(a))            if len(a) > 0 else np.nan

    last3  = arr[-3:]  if n >= 1 else np.array([])
    last5  = arr[-5:]  if n >= 1 else np.array([])
    last10 = arr[-10:] if n >= 1 else np.array([])

    # ── Core means ────────────────────────────────────────────────────────────
    f[f"{name}_mean_last3"]  = _safe_mean(last3)
    f[f"{name}_mean_last5"]  = _safe_mean(last5)
    f[f"{name}_mean_last10"] = _safe_mean(last10)

    # ── EWMA with alpha=0.3 (half-life ~2 games) — faster than span=10 ───────
    # Previous span=10 gave recent game only ~18% weight. alpha=0.3 gives ~30%.
    if n >= 2:
        s = pd.Series(arr)
        f[f"{name}_ewma_10"] = float(s.ewm(alpha=0.3, min_periods=2).mean().iloc[-1])
    else:
        f[f"{name}_ewma_10"] = arr[-1] if n == 1 else np.nan

    # Season mean: EWMA over all prior games (decays older games)
    # More informative than arithmetic season mean for trend-following stats
    if n >= 2:
        s = pd.Series(arr)
        f[f"{name}_mean_season"] = float(s.ewm(alpha=0.1, min_periods=2).mean().iloc[-1])
    else:
        f[f"{name}_mean_season"] = arr[-1] if n == 1 else np.nan

    # ── Dispersion ───────────────────────────────────────────────────────────
    f[f"{name}_vol_last10"] = _safe_mad(last10)

    # CV = std / mean — zero-safe; NaN if mean is near zero
    if len(last10) > 1:
        mu = np.mean(last10)
        sd = np.std(last10)
        f[f"{name}_cv_last10"] = float(sd / mu) if mu > 0.1 else np.nan
    else:
        f[f"{name}_cv_last10"] = np.nan

    # ── Percentiles + median ──────────────────────────────────────────────────
    f[f"{name}_p25_last10"]    = _safe_p25(last10)
    f[f"{name}_p75_last10"]    = _safe_p75(last10)
    f[f"{name}_median_last10"] = _safe_median(last10)   # anchors P50 for skewed players

    # ── NEW: Floor and ceiling ────────────────────────────────────────────────
    f[f"{name}_floor_last10"]   = _safe_min(last10)
    f[f"{name}_ceiling_last10"] = _safe_max(last10)

    # ── NEW: Trend — recent 3 vs last 10 (ratio) ─────────────────────────────
    # trend > 1.0 = player trending up; < 1.0 = trending down
    m3  = f[f"{name}_mean_last3"]
    m10 = f[f"{name}_mean_last10"]
    if (m3  is not None and not np.isnan(m3) and
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
    Dedicated minutes feature block.
    Minutes are the single most important multiplier for all props.
    """
    f = {}
    if "min" not in df.columns or len(df) == 0:
        keys = [
            "mp_mean_last3","mp_mean_last5","mp_mean_last10","mp_mean_season",
            "mp_ewma_10","mp_vol_last10","mp_cv_last10",
            "mp_p25_last10","mp_p75_last10","mp_floor_last10","mp_ceiling_last10",
            "mp_trend_3v10",
            "starter_rate_last10","games_30plus_last10","games_35plus_last10",
            "games_20minus_last10","role_stability_index",
        ]
        return {k: np.nan for k in keys}

    min_arr = df["min"].values.astype(float)
    f.update(rolling_full(min_arr, "mp"))

    # ── Role features ─────────────────────────────────────────────────────────
    last10_min = min_arr[-10:]
    n = len(last10_min)

    # Starter rate: games >= 28 min as proxy for starter (BDL has no lineup data easily)
    f["starter_rate_last10"]  = float(np.mean(last10_min >= 28)) if n > 0 else np.nan
    f["games_30plus_last10"]  = float(np.sum(last10_min >= 30))  if n > 0 else np.nan
    f["games_35plus_last10"]  = float(np.sum(last10_min >= 35))  if n > 0 else np.nan
    f["games_20minus_last10"] = float(np.sum(last10_min <= 20))  if n > 0 else np.nan

    # Role stability index: 1 - (std / max) over last 10
    # High = consistent role; low = erratic usage
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

    f["rest_days"]    = max(0, rest)
    f["back_to_back"] = int(rest <= 1)
    f["three_in_4"]   = int(len([d for d in prior_ts if (target_date - d).days <= 3]) >= 2)
    f["four_in_6"]    = int(len([d for d in prior_ts if (target_date - d).days <= 5]) >= 3)
    f["games_last_7"] = len([d for d in prior_ts if (target_date - d).days <= 6])
    f["missed_last_game"]  = int(rest > 2)
    f["missed_2_of_last5"] = int(f["games_last_7"] <= 3 and f["games_last_7"] > 0)

    return f


# ── Game script / market odds ─────────────────────────────────────────────────

def game_script_features(game_context: dict, is_home: int) -> dict:
    LEAGUE_TOTAL = 220.0
    f = {}

    if not game_context or not game_context.get("odds_available"):
        f.update({
            "game_total": np.nan, "spread_for_team": np.nan,
            "implied_team_total": np.nan, "blowout_risk": np.nan,
            "has_odds": 0, "is_home": int(is_home),
            # Opponent matchup — null when no odds
            "opp_pace_context": np.nan,
            "opp_implied_total": np.nan,
        })
        return f

    total  = float(game_context.get("consensus_total") or LEAGUE_TOTAL)
    spread = float(game_context.get("consensus_spread_home") or 0.0)

    team_spread      = spread if is_home else -spread
    implied_team     = (total / 2.0) + (team_spread / 2.0)
    opp_implied      = total - implied_team

    f["game_total"]         = total
    f["spread_for_team"]    = team_spread
    f["implied_team_total"] = implied_team
    f["opp_implied_total"]  = opp_implied   # NEW: opponent implied total
    f["blowout_risk"]       = abs(spread)
    f["has_odds"]           = 1
    f["is_home"]            = int(is_home)

    # ── Opponent context features from game context ───────────────────────────
    # These come from odds data (pace proxy via game total, spread as defense signal)
    # A high game total signals fast pace; large spread signals dominant defense
    f["opp_pace_context"]    = total                     # pace proxy
    f["opp_defense_signal"]  = float(abs(spread))       # spread magnitude = defense quality

    return f


# ── Advanced stats block ──────────────────────────────────────────────────────

def advanced_stats_block(adv_records: list) -> dict:
    """
    BDL v2 advanced stats — expanded from 6 to 30+ fields.
    Rolling: last-10 mean + EWMA for opportunity fields.
    NaN preserved. has_advanced_stats flag.
    """
    f = {f"adv_{field}_mean_last10": np.nan for field in ALL_ADV_FIELDS}
    f.update({f"adv_{field}_ewma": np.nan for field in [
        "touches", "passes", "rebound_chances_total", "fouls_drawn",
        "usage_percentage", "deflections",
    ]})
    f["has_advanced_stats"] = 0

    if not adv_records:
        return f

    adv_records = sorted(adv_records, key=lambda x: x.get("game_date", ""))
    recent = adv_records[-10:]
    f["has_advanced_stats"] = 1

    for field in ALL_ADV_FIELDS:
        vals = [
            float(r[field]) for r in recent
            if r.get(field) is not None and r[field] != ""
        ]
        f[f"adv_{field}_mean_last10"] = float(np.mean(vals)) if vals else np.nan

    # EWMA for key opportunity fields — more recency-sensitive
    ewma_fields = ["touches", "passes", "rebound_chances_total",
                   "fouls_drawn", "usage_percentage", "deflections"]
    all_records_sorted = adv_records  # already sorted
    for field in ewma_fields:
        vals = [
            float(r[field]) for r in all_records_sorted
            if r.get(field) is not None and r[field] != ""
        ]
        if len(vals) >= 2:
            s = pd.Series(vals)
            f[f"adv_{field}_ewma"] = float(
                s.ewm(alpha=0.3, min_periods=2).mean().iloc[-1]
            )
        elif len(vals) == 1:
            f[f"adv_{field}_ewma"] = vals[0]

    return f


# ── Vacated opportunity ───────────────────────────────────────────────────────

def vacated_opportunity_features(
    player_id: int,
    team_id: int,
    target_date: pd.Timestamp,
    stats_df: pd.DataFrame,
    injury_map: dict,
) -> dict:
    """
    Role-conditioned vacated opportunity.
    v12 adds role classification (guard/wing/big) so vacated guard minutes
    are distinguished from vacated big minutes for REB vs AST modeling.
    """
    NULL = {
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
        # NEW: role-conditioned
        "vacated_guard_minutes":    np.nan,
        "vacated_big_minutes":      np.nan,
        "vacated_creation_share":   np.nan,
        "vacated_reb_share":        np.nan,
        "num_teammates_inactive":   0,
        "has_injury_data":          0,
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
        null_with_flag = dict(NULL)
        null_with_flag["has_injury_data"] = has_inj
        null_with_flag["num_teammates_inactive"] = 0
        return null_with_flag

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
        """Classify player as guard/big based on reb/ast ratio."""
        pdata = stats_df[
            (stats_df["player_id"] == pid) &
            (stats_df["game_date"] < target_date)
        ]
        if pdata.empty:
            return "unknown"
        avg_reb = np.nanmean(pdata["reb"].values.astype(float)) if "reb" in pdata.columns else 0
        avg_ast = np.nanmean(pdata["ast"].values.astype(float)) if "ast" in pdata.columns else 0
        avg_blk = np.nanmean(pdata["blk"].values.astype(float)) if "blk" in pdata.columns else 0
        # Simple heuristic: big if reb > ast and avg_blk > 0.3
        if avg_reb > avg_ast and avg_blk > 0.3:
            return "big"
        return "guard"

    v_min = v_fga = v_fg3a = v_fta = v_pts = v_ast = v_reb = v_usage = 0.0
    v_guard_min = v_big_min = 0.0
    fga_per_inactive   = []
    usage_per_inactive = []

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

        # Role-conditioned
        role = _classify_role(pid)
        if role == "big":
            v_big_min   += m
        else:
            v_guard_min += m

        fga_per_inactive.append((fga_rate * m) if not np.isnan(fga_rate) else 0)
        usage_per_inactive.append(up_rate * m)

    fga_sorted   = sorted(fga_per_inactive,   reverse=True)
    usage_sorted = sorted(usage_per_inactive, reverse=True)

    # Creation share: vacated AST relative to total vacated usage
    creation_share = (v_ast / v_usage) if v_usage > 0 else np.nan
    reb_share      = (v_reb / v_min)   if v_min  > 0 else np.nan

    return {
        "vacated_minutes":          float(v_min),
        "vacated_fga":              float(v_fga),
        "vacated_fg3a":             float(v_fg3a),
        "vacated_fta":              float(v_fta),
        "vacated_pts":              float(v_pts),
        "vacated_ast":              float(v_ast),
        "vacated_reb":              float(v_reb),
        "vacated_usage_proxy":      float(v_usage),
        "vacated_top1_fga":         float(fga_sorted[0])      if fga_sorted   else 0.0,
        "vacated_top2_fga":         float(sum(fga_sorted[:2])) if fga_sorted  else 0.0,
        "vacated_top1_usage_proxy": float(usage_sorted[0])    if usage_sorted else 0.0,
        "vacated_top2_usage_proxy": float(sum(usage_sorted[:2])) if usage_sorted else 0.0,
        # Role-conditioned
        "vacated_guard_minutes":    float(v_guard_min),
        "vacated_big_minutes":      float(v_big_min),
        "vacated_creation_share":   float(creation_share) if not np.isnan(creation_share) else np.nan,
        "vacated_reb_share":        float(reb_share)      if not np.isnan(reb_share)      else np.nan,
        "num_teammates_inactive":   len(inactive),
        "has_injury_data":          has_inj,
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
) -> dict:
    """
    Build complete pregame feature vector for one player.
    ZERO leakage: all inputs strictly prior to target_date.
    Returns flat dict — NaN where data unavailable.
    """
    f = {}
    df  = prior_stats.sort_values("game_date").reset_index(drop=True)
    tdt = pd.Timestamp(target_date)

    min_arr = df["min"].values.astype(float) if "min" in df.columns else np.array([])

    # ── Minutes model block (historical rolling features) ─────────────────────
    f.update(minutes_model_features(df))

    # ── Standalone minutes model predictions (first-class features) ───────────
    # Loads trained quantile models from model_cache/ and outputs exp_mp,
    # mp_q25, mp_q75, mp_vol etc. as input features for all downstream models.
    # Falls back to rolling-mean approximation if models not yet trained.
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
        # Silently NaN if minutes model unavailable — LightGBM handles natively
        for k in ("exp_mp","mp_q10","mp_q25","mp_q75","mp_q90",
                  "mp_vol","mp_pred_floor","mp_pred_ceiling"):
            f[k] = np.nan

    # ── Per-minute rates + full rolling (13 features) ─────────────────────────
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

            # ALSO: raw count rolling for non-rate context
            # Raw counts capture role-specific absolute volume
            f.update(rolling_full(raw, f"{feat_name}_raw"))
        else:
            sfxs = [
                "mean_last3","mean_last5","mean_last10","mean_season",
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
        for sfx in ["mean_last3","mean_last5","mean_last10","mean_season",
                    "vol_last10","cv_last10","ewma_10","p25_last10","p75_last10",
                    "floor_last10","ceiling_last10","trend_3v10"]:
            f[f"usage_proxy_per_min_{sfx}"] = np.nan

    # ── 3PM block: two-stage (attempt volume × efficiency) ────────────────────
    if all(c in df.columns for c in ["fg3m", "fg3a"]):
        fg3m_raw = df["fg3m"].values.astype(float)
        fg3a_raw = df["fg3a"].values.astype(float)
        fg3m_arr = np.where(np.isnan(fg3m_raw), 0.0, fg3m_raw)
        fg3a_arr = np.where(np.isnan(fg3a_raw), 0.0, fg3a_raw)

        f["_fg3m_integrity_miss_fg3m"] = float(np.sum(np.isnan(fg3m_raw)))
        f["_fg3m_integrity_miss_fg3a"] = float(np.sum(np.isnan(fg3a_raw)))
        f["_fg3m_integrity_bad_rows"]  = float(np.sum(fg3m_arr > fg3a_arr))

        last10_fg3m = fg3m_arr[-10:]
        n_window    = len(last10_fg3m)
        f["fg3m_p_zero_last10"]          = float(np.mean(last10_fg3m == 0)) if n_window > 0 else np.nan
        f["fg3m_p_ge3_last10"]           = float(np.mean(last10_fg3m >= 3)) if n_window > 0 else np.nan
        f["fg3m_games_in_window_last10"] = float(n_window)

        # Shrinkage-blended shooting percentage
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

        # NEW: attempt trend — are 3PA attempts trending up or down?
        last3_att  = float(np.sum(fg3a_arr[-3:]))
        last10_att = float(np.sum(fg3a_arr[-10:]))
        f["fg3a_attempt_trend"] = (last3_att / 3.0) / (last10_att / 10.0) \
            if last10_att > 0 else np.nan

    else:
        for _k in [
            "fg3m_p_zero_last10","fg3m_p_ge3_last10","fg3m_games_in_window_last10",
            "fg3_pct_safe","fg3a_count_last10","fg3a_count_season","is_low_3pa_last10",
            "fg3a_attempt_trend",
            "_fg3m_integrity_miss_fg3m","_fg3m_integrity_miss_fg3a","_fg3m_integrity_bad_rows",
        ]:
            f[_k] = np.nan

    # ── STL / BLK: sparse-event treatment ────────────────────────────────────
    BLEND_K = 15.0
    for sparse_stat, col in [("stl", "stl"), ("blk", "blk")]:
        if col in df.columns and len(min_arr) > 0:
            raw      = df[col].values.astype(float)
            rate     = per_minute_rate(raw, min_arr)

            last10_raw = raw[-10:]
            f[f"{sparse_stat}_p_zero_last10"] = (
                float(np.mean(last10_raw == 0)) if len(last10_raw) > 0 else np.nan
            )
            f[f"{sparse_stat}_p_ge2_last10"] = (
                float(np.mean(last10_raw >= 2)) if len(last10_raw) > 0 else np.nan
            )

            # Blended rate: shrink last-10 toward season
            rate_clean = rate[~np.isnan(rate)]
            n_games    = len(rate_clean)
            r10 = float(np.nanmean(rate[-10:])) if n_games >= 1 else np.nan
            rs  = float(np.nanmean(rate))       if n_games >= 1 else np.nan
            if not np.isnan(r10) and not np.isnan(rs):
                w = min(n_games, 10) / (min(n_games, 10) + BLEND_K)
                f[f"{sparse_stat}_per_min_blended"] = w * r10 + (1.0 - w) * rs
            else:
                f[f"{sparse_stat}_per_min_blended"] = np.nan

            # NEW: Upper tail probability (p_ge1 for blk since blk >= 2 is rarer)
            f[f"{sparse_stat}_p_ge1_last10"] = (
                float(np.mean(last10_raw >= 1)) if len(last10_raw) > 0 else np.nan
            )
        else:
            for k in [f"{sparse_stat}_p_zero_last10", f"{sparse_stat}_p_ge2_last10",
                      f"{sparse_stat}_per_min_blended", f"{sparse_stat}_p_ge1_last10"]:
                f[k] = np.nan

    # ── Variance driver ───────────────────────────────────────────────────────
    br  = f.get("blowout_risk")
    mpv = f.get("mp_vol_last10")
    if br is not None and mpv is not None and not np.isnan(float(br)) and not np.isnan(float(mpv)):
        f["blowout_risk_x_mp_vol"] = float(br) * float(mpv)
    else:
        f["blowout_risk_x_mp_vol"] = np.nan

    # ── Schedule ──────────────────────────────────────────────────────────────
    dates = df["game_date"].tolist()
    f.update(schedule_features(dates, tdt))

    # ── Game script / odds ────────────────────────────────────────────────────
    f.update(game_script_features(game_context, is_home))

    # Recompute blowout_risk_x_mp_vol after odds are populated
    br  = f.get("blowout_risk")
    mpv = f.get("mp_vol_last10")
    if (br is not None and mpv is not None and
            not np.isnan(float(br) if br is not None else np.nan) and
            not np.isnan(float(mpv) if mpv is not None else np.nan)):
        f["blowout_risk_x_mp_vol"] = float(br) * float(mpv)

    # ── Advanced stats ────────────────────────────────────────────────────────
    f.update(advanced_stats_block(prior_adv))

    # ── Vacated opportunity ───────────────────────────────────────────────────
    f.update(vacated_opportunity_features(
        player_id=player_id,
        team_id=team_id,
        target_date=tdt,
        stats_df=all_stats_df,
        injury_map=injury_map,
    ))

    # ── Player metadata ───────────────────────────────────────────────────────
    f["games_played"] = len(df)
    f["is_home"]      = int(is_home)

    return f


# ── Stat-specific feature gates ───────────────────────────────────────────────

def _shared_cols() -> list:
    return [
        # ── Standalone minutes model predictions (first-class) ─────────────
        # These are the output of the dedicated minutes quantile model.
        # exp_mp is the single most important predictor for all counting stats.
        "exp_mp",           # expected minutes (Q50 from minutes model)
        "mp_q25",           # lower bound — blowout / rest scenario
        "mp_q75",           # upper bound — close game / extra minutes
        "mp_vol",           # IQR/median — role consistency signal
        "mp_pred_floor",    # Q10 — extreme low scenario
        "mp_pred_ceiling",  # Q90 — extreme high scenario
        # ── Rolling minutes history ────────────────────────────────────────
        "mp_mean_last3","mp_mean_last5","mp_mean_last10","mp_mean_season",
        "mp_vol_last10","mp_cv_last10","mp_ewma_10",
        "mp_p25_last10","mp_p75_last10",
        "mp_floor_last10","mp_ceiling_last10","mp_trend_3v10",
        # ── Role ──────────────────────────────────────────────────────────
        "starter_rate_last10","games_30plus_last10","games_20minus_last10",
        "role_stability_index",
        # ── Variance drivers ──────────────────────────────────────────────
        "blowout_risk_x_mp_vol","pf_per_min_mean_last10",
        "missed_last_game","missed_2_of_last5",
        # ── Schedule ──────────────────────────────────────────────────────
        "rest_days","back_to_back","three_in_4","four_in_6","games_last_7",
        # ── Context ───────────────────────────────────────────────────────
        "is_home","games_played",
        # ── Flags ─────────────────────────────────────────────────────────
        "has_odds","has_advanced_stats","has_injury_data",
    ]

def _odds_cols() -> list:
    return [
        "game_total","spread_for_team","implied_team_total",
        "blowout_risk","opp_implied_total","opp_pace_context","opp_defense_signal",
    ]

def _adv_core_cols() -> list:
    return [f"adv_{f}_mean_last10" for f in ADV_FIELDS_CORE]

def _injury_base() -> list:
    return ["vacated_minutes","num_teammates_inactive","vacated_guard_minutes","vacated_big_minutes"]


def get_feature_cols_for_stat(stat: str, all_cols: list) -> list:
    wanted = set(_shared_cols()) | set(_odds_cols()) | set(_adv_core_cols())

    if stat == "pts":
        wanted |= {
            "fga_per_min_mean_last3","fga_per_min_mean_last5","fga_per_min_mean_last10",
            "fga_per_min_vol_last10","fga_per_min_cv_last10","fga_per_min_ewma_10",
            "fga_per_min_trend_3v10",
            "fga_raw_mean_last10",
            "fta_per_min_mean_last10","fg3a_per_min_mean_last10",
            "usage_proxy_per_min_mean_last10","usage_proxy_per_min_vol_last10",
            "usage_proxy_per_min_cv_last10","usage_proxy_per_min_trend_3v10",
            "adv_true_shooting_percentage_mean_last10",
            "adv_effective_field_goal_percentage_mean_last10",
            "adv_touches_mean_last10","adv_touches_ewma",
            "adv_fouls_drawn_mean_last10","adv_fouls_drawn_ewma",
            "adv_pct_fga_mean_last10","adv_pct_points_mean_last10",
            "adv_points_paint_mean_last10","adv_estimated_usage_percentage_mean_last10",
            "vacated_minutes","vacated_fga","vacated_fta","vacated_usage_proxy",
            "vacated_top2_fga","vacated_guard_minutes","num_teammates_inactive",
            "usage_proxy_x_itt","fga_x_itt",
        }

    elif stat == "reb":
        wanted |= {
            "reb_per_min_mean_last3","reb_per_min_mean_last5","reb_per_min_mean_last10",
            "reb_per_min_median_last10",   # KEY — anchors P50 for skewed rebounders
            "reb_per_min_vol_last10","reb_per_min_cv_last10","reb_per_min_ewma_10",
            "reb_per_min_p25_last10","reb_per_min_p75_last10",
            "reb_per_min_floor_last10","reb_per_min_ceiling_last10",
            "reb_per_min_trend_3v10",
            "reb_raw_mean_last10","reb_raw_median_last10","reb_raw_cv_last10",
            "oreb_per_min_mean_last10","dreb_per_min_mean_last10",
            "adv_pace_mean_last10",
            "adv_rebound_chances_total_mean_last10","adv_rebound_chances_total_ewma",
            "adv_rebound_chances_def_mean_last10","adv_rebound_chances_off_mean_last10",
            "vacated_reb","vacated_reb_share","vacated_big_minutes",
            "vacated_minutes","num_teammates_inactive",
            "reb_x_mp",
        }

    elif stat == "ast":
        wanted |= {
            "ast_per_min_mean_last3","ast_per_min_mean_last5","ast_per_min_mean_last10",
            "ast_per_min_vol_last10","ast_per_min_cv_last10","ast_per_min_ewma_10",
            "ast_per_min_p25_last10","ast_per_min_p75_last10","ast_per_min_trend_3v10",
            "ast_raw_mean_last10","ast_raw_cv_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_usage_percentage_mean_last10","adv_assist_percentage_mean_last10",
            "adv_assist_to_turnover_mean_last10",
            "adv_passes_mean_last10","adv_passes_ewma",
            "adv_touches_mean_last10","adv_secondary_assists_mean_last10",
            "adv_free_throw_assists_mean_last10",
            "tov_per_min_mean_last10",
            "vacated_ast","vacated_creation_share","vacated_guard_minutes",
            "vacated_usage_proxy","vacated_minutes","vacated_top2_usage_proxy",
            "num_teammates_inactive",
            "ast_pct_x_itt","usage_x_itt",
        }

    elif stat == "fg3m":
        wanted |= {
            "mp_mean_last5","mp_mean_last10","mp_vol_last10","mp_ewma_10","mp_trend_3v10",
            "fg3a_per_min_mean_last10","fg3a_per_min_trend_3v10",
            "fg3a_count_last10","fg3a_count_season","fg3a_attempt_trend",
            "fg3_pct_safe",
            "fg3m_p_zero_last10","fg3m_p_ge3_last10","fg3m_games_in_window_last10",
            "is_low_3pa_last10",
            "adv_pct_3pa_mean_last10","adv_contested_shots_3pt_mean_last10",
            "game_total","implied_team_total","opp_implied_total","has_odds",
        }

    elif stat == "stl":
        wanted |= {
            "stl_per_min_blended","stl_per_min_vol_last10","stl_per_min_ewma_10",
            "stl_p_zero_last10","stl_p_ge2_last10","stl_p_ge1_last10",
            "adv_pace_mean_last10",
            "adv_deflections_mean_last10","adv_deflections_ewma",
            "adv_partial_possessions_mean_last10","adv_switches_on_mean_last10",
            "adv_matchup_turnovers_mean_last10",
            "vacated_minutes",
        }

    elif stat == "blk":
        wanted |= {
            "blk_per_min_blended","blk_per_min_vol_last10","blk_per_min_ewma_10",
            "blk_p_zero_last10","blk_p_ge2_last10","blk_p_ge1_last10",
            "pf_per_min_mean_last10",
            "adv_pace_mean_last10",
            "adv_defended_at_rim_fga_mean_last10","adv_defended_at_rim_fg_pct_mean_last10",
            "adv_contested_shots_2pt_mean_last10","adv_switches_on_mean_last10",
            "vacated_minutes","vacated_big_minutes","num_teammates_inactive",
        }

    elif stat == "tov":
        wanted |= {
            "tov_per_min_mean_last10","tov_per_min_vol_last10","tov_per_min_trend_3v10",
            "tov_raw_mean_last10","tov_raw_cv_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_usage_percentage_mean_last10","adv_assist_to_turnover_mean_last10",
            "adv_pace_mean_last10","adv_passes_mean_last10","adv_touches_mean_last10",
            "adv_matchup_turnovers_mean_last10",
            "vacated_usage_proxy","vacated_minutes","num_teammates_inactive",
            "usage_x_pace",
        }

    elif stat == "pra":
        wanted |= {
            "pts_per_min_mean_last10","reb_per_min_mean_last10","ast_per_min_mean_last10",
            "pts_per_min_vol_last10","reb_per_min_vol_last10","ast_per_min_vol_last10",
            "pts_per_min_cv_last10","reb_per_min_cv_last10","ast_per_min_cv_last10",
            "reb_per_min_median_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_pace_mean_last10","adv_usage_percentage_mean_last10",
            "E_pts_proxy","E_reb_proxy","E_ast_proxy",
            "vacated_usage_proxy","vacated_minutes","vacated_ast","vacated_reb","vacated_fga",
            "vacated_creation_share","vacated_reb_share","num_teammates_inactive",
        }

    elif stat == "pr":
        wanted |= {
            "pts_per_min_mean_last10","reb_per_min_mean_last10",
            "pts_per_min_vol_last10","reb_per_min_vol_last10",
            "reb_per_min_median_last10","reb_per_min_cv_last10",
            "usage_proxy_per_min_mean_last10","adv_pace_mean_last10",
            "E_pts_proxy","E_reb_proxy",
            "vacated_reb","vacated_fga","vacated_minutes","num_teammates_inactive",
        }

    elif stat == "pa":
        wanted |= {
            "pts_per_min_mean_last10","ast_per_min_mean_last10",
            "pts_per_min_vol_last10","ast_per_min_vol_last10","ast_per_min_cv_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_pace_mean_last10","adv_assist_percentage_mean_last10",
            "E_pts_proxy","E_ast_proxy",
            "vacated_ast","vacated_usage_proxy","vacated_fga","vacated_minutes",
            "vacated_creation_share","num_teammates_inactive",
        }

    elif stat == "ra":
        wanted |= {
            "reb_per_min_mean_last10","ast_per_min_mean_last10",
            "reb_per_min_vol_last10","ast_per_min_vol_last10",
            "reb_per_min_median_last10","reb_per_min_cv_last10",
            "adv_pace_mean_last10",
            "E_reb_proxy","E_ast_proxy",
            "vacated_ast","vacated_reb","vacated_minutes","num_teammates_inactive",
        }

    elif stat == "stocks":
        wanted |= {
            "stl_per_min_blended","stl_per_min_vol_last10","stl_per_min_ewma_10",
            "blk_per_min_blended","blk_per_min_vol_last10","blk_per_min_ewma_10",
            "stl_p_zero_last10","stl_p_ge2_last10","stl_p_ge1_last10",
            "blk_p_zero_last10","blk_p_ge2_last10","blk_p_ge1_last10",
            "adv_deflections_mean_last10","adv_deflections_ewma",
            "adv_defended_at_rim_fga_mean_last10",
            "pf_per_min_mean_last10","adv_pace_mean_last10",
            "vacated_minutes","num_teammates_inactive",
        }

    return [c for c in all_cols if c in wanted]


def add_interaction_features(f: dict, stat: str) -> dict:
    """Stat-specific interaction features computed after base vector."""
    itt = f.get("implied_team_total")
    mp  = f.get("mp_mean_last10")

    def _mul(a, b):
        if a is None or b is None: return np.nan
        a, b = float(a), float(b)
        return (a * b) if (not np.isnan(a) and not np.isnan(b)) else np.nan

    if stat == "pts":
        f["usage_proxy_x_itt"] = _mul(f.get("usage_proxy_per_min_mean_last10"), itt)
        f["fga_x_itt"]         = _mul(f.get("fga_per_min_mean_last10"), itt)

    elif stat == "reb":
        f["reb_x_mp"] = _mul(f.get("reb_per_min_mean_last10"), mp)

    elif stat == "ast":
        f["ast_pct_x_itt"] = _mul(f.get("adv_assist_percentage_mean_last10"), itt)
        f["usage_x_itt"]   = _mul(f.get("adv_usage_percentage_mean_last10"), itt)

    elif stat == "tov":
        f["usage_x_pace"] = _mul(
            f.get("usage_proxy_per_min_mean_last10"),
            f.get("adv_pace_mean_last10"),
        )

    if stat in ("pra", "pr", "pa", "ra"):
        pm_pts = f.get("pts_per_min_mean_last10")
        pm_reb = f.get("reb_per_min_mean_last10")
        pm_ast = f.get("ast_per_min_mean_last10")
        f["E_pts_proxy"] = _mul(pm_pts, mp)
        f["E_reb_proxy"] = _mul(pm_reb, mp)
        f["E_ast_proxy"] = _mul(pm_ast, mp)

    return f
