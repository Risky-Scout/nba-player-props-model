"""
feature_engineering.py — DARKO v4 Feature Engineering
VERSION: 2026-02-28-v10

Expert-reviewed architecture:
  - Per-minute rates computed first, then rolled (not raw totals)
  - 7 rolling features per series: mean_last5/10, mean_season,
    vol_last10 (MAD), ewma_10, p25_last10, p75_last10
  - Vacated opportunity: OUT/DOUBTFUL only, last-15-game teammate
    membership, as-of season averages (no leakage)
  - NaN preserved (not zero-filled) — LightGBM handles natively
  - has_odds / has_advanced_stats / has_injury_data flags
  - Stat-specific feature gating functions per expert spec
"""

import numpy as np
import pandas as pd
from typing import Optional

STATS        = ["pts", "reb", "ast", "fg3m", "stl", "blk", "tov"]
COMBO_STATS  = ["pra", "pr", "pa", "ra", "stocks"]
ALL_TARGETS  = STATS + COMBO_STATS

INACTIVE_STATUSES = {"out", "doubtful"}          # only these count as inactive
TEAMMATE_WINDOW   = 15                            # team games to define membership
VACATED_CAP       = 3.0                           # winsorize per-min rates at 3σ


# ── Rolling helper: 7 features per series ─────────────────────────────────────

def rolling_7(arr: np.ndarray, name: str) -> dict:
    """
    Expert-spec rolling feature pack — 7 features per series.
    Applied to per-minute rates, not raw totals.
    NaN returned where insufficient data (LightGBM handles it).
    """
    arr = arr.astype(float)
    n   = len(arr)
    f   = {}

    def _mean(a):  return float(np.mean(a))   if len(a) > 0 else np.nan
    def _mad(a):   return float(np.mean(np.abs(a - np.median(a)))) if len(a) > 1 else np.nan
    def _p25(a):   return float(np.percentile(a, 25)) if len(a) > 1 else np.nan
    def _p75(a):   return float(np.percentile(a, 75)) if len(a) > 1 else np.nan

    # mean_last5
    f[f"{name}_mean_last5"]   = _mean(arr[-5:])  if n >= 1 else np.nan
    # mean_last10
    f[f"{name}_mean_last10"]  = _mean(arr[-10:]) if n >= 1 else np.nan
    # mean_season
    f[f"{name}_mean_season"]  = _mean(arr)       if n >= 1 else np.nan
    # vol_last10 (MAD — one dispersion measure only)
    f[f"{name}_vol_last10"]   = _mad(arr[-10:])  if n >= 2 else np.nan
    # ewma_10
    if n >= 2:
        s = pd.Series(arr)
        f[f"{name}_ewma_10"]  = float(s.ewm(span=10, min_periods=2).mean().iloc[-1])
    else:
        f[f"{name}_ewma_10"]  = arr[-1] if n == 1 else np.nan
    # p25_last10
    f[f"{name}_p25_last10"]   = _p25(arr[-10:])  if n >= 2 else np.nan
    # p75_last10
    f[f"{name}_p75_last10"]   = _p75(arr[-10:])  if n >= 2 else np.nan

    return f


# ── Per-minute rate ────────────────────────────────────────────────────────────

def per_minute_rate(stat_arr: np.ndarray, min_arr: np.ndarray) -> np.ndarray:
    """Compute per-minute rate array; NaN where minutes == 0."""
    stat_arr = stat_arr.astype(float)
    min_arr  = min_arr.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        rate = np.where(min_arr > 0, stat_arr / min_arr, np.nan)
    return rate


# ── Schedule / fatigue ────────────────────────────────────────────────────────

def schedule_features(prior_dates: list, target_date: pd.Timestamp) -> dict:
    f = {}
    if not prior_dates:
        f.update({"rest_days": np.nan, "back_to_back": 0,
                  "three_in_4": 0, "four_in_6": 0,
                  "games_last_7": 0,
                  "missed_last_game": 0, "missed_2_of_last5": 0})
        return f

    prior_ts  = sorted([pd.Timestamp(d) for d in prior_dates])
    last_game = prior_ts[-1]
    rest      = (target_date - last_game).days

    f["rest_days"]    = max(0, rest)
    f["back_to_back"] = int(rest <= 1)
    f["three_in_4"]   = int(len([d for d in prior_ts if (target_date - d).days <= 3]) >= 2)
    f["four_in_6"]    = int(len([d for d in prior_ts if (target_date - d).days <= 5]) >= 3)
    f["games_last_7"] = len([d for d in prior_ts if (target_date - d).days <= 6])

    # DNP/missing flags: if player has fewer recent games than expected
    f["missed_last_game"]   = int(rest > 2)      # >2 days since last = likely missed
    f["missed_2_of_last5"]  = int(f["games_last_7"] <= 3 and f["games_last_7"] > 0)

    return f


# ── Game script / market odds ─────────────────────────────────────────────────

def game_script_features(game_context: dict, is_home: int) -> dict:
    """
    Odds snapshot policy: Option B.
    Use when available; NaN when not. has_odds flag always set.
    Model trains on both populations.
    """
    LEAGUE_TOTAL = 220.0
    f = {}

    if not game_context or not game_context.get("odds_available"):
        f["game_total"]          = np.nan
        f["spread_for_team"]     = np.nan
        f["implied_team_total"]  = np.nan
        f["blowout_risk"]        = np.nan
        f["has_odds"]            = 0
        f["is_home"]             = int(is_home)
        return f

    total  = game_context.get("consensus_total") or LEAGUE_TOTAL
    spread = game_context.get("consensus_spread_home") or 0.0

    team_spread     = float(spread) if is_home else -float(spread)
    implied_team    = (float(total) / 2.0) + (team_spread / 2.0)

    f["game_total"]          = float(total)
    f["spread_for_team"]     = float(team_spread)
    f["implied_team_total"]  = float(implied_team)
    f["blowout_risk"]        = float(abs(spread))
    f["has_odds"]            = 1
    f["is_home"]             = int(is_home)
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
    Compute vacated opportunity from inactive teammates.

    Rules (expert-reviewed):
      1. INACTIVE = OUT or DOUBTFUL status only (applied identically train+infer)
      2. Teammate membership = players who appeared for this team in last
         TEAMMATE_WINDOW team games as-of target_date (no transaction history needed)
      3. Teammate baselines = their as-of season averages (prior games only, no leakage)
      4. Winsorize per-min rates to prevent pathological outlier games dominating

    injury_map: {player_id: {"status": "out"|"doubtful"|..., ...}}
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
        "num_teammates_inactive":   0,
        "has_injury_data":          0,
    }

    if stats_df.empty or not injury_map:
        return NULL

    # ── Step 1: Identify teammate roster (last TEAMMATE_WINDOW team games) ───
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

    # ── Step 2: Find inactive teammates (OUT/DOUBTFUL only) ─────────────────
    inactive = []
    for tid in teammates:
        status = str(injury_map.get(tid, {}).get("status", "")).lower().strip()
        if status in INACTIVE_STATUSES:
            inactive.append(tid)

    has_inj = 1 if injury_map else 0

    if not inactive:
        null_with_flag = dict(NULL)
        null_with_flag["has_injury_data"] = has_inj
        null_with_flag["num_teammates_inactive"] = 0
        return null_with_flag

    # ── Step 3: Compute as-of season averages for each inactive teammate ────
    # Season = games in the same season as target_date, strictly prior to G

    def _asof_avg(pid: int, col: str) -> float:
        """Per-minute rate for pid on col, as-of target_date."""
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
        # Winsorize at VACATED_CAP std devs
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
        if pdata.empty: return np.nan
        return float(np.nanmean(pdata["min"].values.astype(float)))

    # ── Step 4: Aggregate vacated stats ─────────────────────────────────────
    v_min = v_fga = v_fg3a = v_fta = v_pts = v_ast = v_reb = v_usage = 0.0
    fga_per_inactive  = []
    usage_per_inactive = []

    for pid in inactive:
        m   = _asof_mean_min(pid)
        if np.isnan(m) or m <= 0:
            continue

        fga_rate   = _asof_avg(pid, "fga")
        fg3a_rate  = _asof_avg(pid, "fg3a")
        fta_rate   = _asof_avg(pid, "fta")
        pts_rate   = _asof_avg(pid, "pts")
        ast_rate   = _asof_avg(pid, "ast")
        reb_rate   = _asof_avg(pid, "reb")
        tov_rate   = _asof_avg(pid, "turnover")

        # usage_proxy = fga + 0.44*fta + tov
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

        fga_per_inactive.append((fga_rate * m) if not np.isnan(fga_rate) else 0)
        usage_per_inactive.append(up_rate * m)

    fga_sorted   = sorted(fga_per_inactive,   reverse=True)
    usage_sorted = sorted(usage_per_inactive, reverse=True)

    return {
        "vacated_minutes":          float(v_min),
        "vacated_fga":              float(v_fga),
        "vacated_fg3a":             float(v_fg3a),
        "vacated_fta":              float(v_fta),
        "vacated_pts":              float(v_pts),
        "vacated_ast":              float(v_ast),
        "vacated_reb":              float(v_reb),
        "vacated_usage_proxy":      float(v_usage),
        "vacated_top1_fga":         float(fga_sorted[0])   if fga_sorted   else 0.0,
        "vacated_top2_fga":         float(sum(fga_sorted[:2])) if fga_sorted else 0.0,
        "vacated_top1_usage_proxy": float(usage_sorted[0]) if usage_sorted else 0.0,
        "vacated_top2_usage_proxy": float(sum(usage_sorted[:2])) if usage_sorted else 0.0,
        "num_teammates_inactive":   len(inactive),
        "has_injury_data":          has_inj,
    }


# ── Advanced stats block ──────────────────────────────────────────────────────

def advanced_stats_block(adv_records: list[dict]) -> dict:
    """
    6 fields from BDL v2, last-10 mean only.
    Strictly prior games (caller ensures this).
    NaN when not available. has_advanced_stats flag.
    """
    FIELDS = [
        "usage_percentage",
        "pace",
        "true_shooting_percentage",
        "effective_field_goal_percentage",
        "assist_percentage",
        "assist_to_turnover",
    ]
    f = {f"adv_{field}_mean_last10": np.nan for field in FIELDS}
    f["has_advanced_stats"] = 0

    if not adv_records:
        return f

    adv_records = sorted(adv_records, key=lambda x: x.get("game_date", ""))
    recent = adv_records[-10:]
    f["has_advanced_stats"] = 1

    for field in FIELDS:
        vals = [float(r.get(field) or 0.0) for r in recent if r.get(field) is not None]
        f[f"adv_{field}_mean_last10"] = float(np.mean(vals)) if vals else np.nan

    return f


# ── Main feature builder ──────────────────────────────────────────────────────

def build_player_game_features(
    player_id: int,
    prior_stats: pd.DataFrame,
    prior_adv: list[dict],
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

    Returns flat dict — NaN where data unavailable (not zero).
    """
    f = {}
    df  = prior_stats.sort_values("game_date").reset_index(drop=True)
    tdt = pd.Timestamp(target_date)

    min_arr = df["min"].values.astype(float) if "min" in df.columns else np.array([])

    # ── Minutes rolling ───────────────────────────────────────────────────────
    if len(min_arr) > 0:
        f.update(rolling_7(min_arr, "mp"))
        # Variance driver: minutes volatility
        f["mp_vol_last10"] = f.get("mp_vol_last10", np.nan)  # already in rolling_7
    else:
        f.update({k: np.nan for k in [
            "mp_mean_last5","mp_mean_last10","mp_mean_season",
            "mp_vol_last10","mp_ewma_10","mp_p25_last10","mp_p75_last10"
        ]})

    # ── Per-minute rates + rolling ────────────────────────────────────────────
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
            f.update(rolling_7(rate, f"{feat_name}_per_min"))
        else:
            for sfx in ["mean_last5","mean_last10","mean_season","vol_last10",
                        "ewma_10","p25_last10","p75_last10"]:
                f[f"{feat_name}_per_min_{sfx}"] = np.nan

    # ── Usage proxy ───────────────────────────────────────────────────────────
    if all(c in df.columns for c in ["fga","fta","turnover"]) and len(min_arr) > 0:
        up_raw  = (df["fga"].values + 0.44 * df["fta"].values +
                   df["turnover"].values).astype(float)
        up_rate = per_minute_rate(up_raw, min_arr)
        f.update(rolling_7(up_rate, "usage_proxy_per_min"))
    else:
        for sfx in ["mean_last5","mean_last10","mean_season","vol_last10",
                    "ewma_10","p25_last10","p75_last10"]:
            f[f"usage_proxy_per_min_{sfx}"] = np.nan

    # ── 3PM FINAL: expert spec — fg3_pct_safe only, K10=120, KS=600 ─────────────
    if all(c in df.columns for c in ["fg3m","fg3a"]):
        fg3m_raw = df["fg3m"].values.astype(float)
        fg3a_raw = df["fg3a"].values.astype(float)
        fg3m_arr = np.where(np.isnan(fg3m_raw), 0.0, fg3m_raw)
        fg3a_arr = np.where(np.isnan(fg3a_raw), 0.0, fg3a_raw)

        # A) Integrity flags (read + logged in train_darko_v4.py)
        f["_fg3m_integrity_miss_fg3m"] = float(np.sum(np.isnan(fg3m_raw)))
        f["_fg3m_integrity_miss_fg3a"] = float(np.sum(np.isnan(fg3a_raw)))
        f["_fg3m_integrity_bad_rows"]  = float(np.sum(fg3m_arr > fg3a_arr))

        # B) Zero-mass features (prior games only)
        last10_fg3m = fg3m_arr[-10:]
        n_window    = len(last10_fg3m)
        f["fg3m_p_zero_last10"]          = float(np.mean(last10_fg3m == 0)) if n_window > 0 else np.nan
        f["fg3m_p_ge3_last10"]           = float(np.mean(last10_fg3m >= 3)) if n_window > 0 else np.nan
        f["fg3m_games_in_window_last10"] = float(n_window)

        # C) fg3_pct_safe — K10=120, KS=600, clipped [0.20, 0.50]
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
        f["fg3_pct_safe"]      = float(np.clip(w10*pct10 + (1.0-w10)*pct_base, 0.20, 0.50))
        f["fg3a_count_last10"] = float(att10)
        f["fg3a_count_season"] = float(attS)

        # D) Low-volume gate — threshold 6 per spec
        f["is_low_3pa_last10"] = 1.0 if att10 <= 6 else 0.0

    else:
        for _k in ["fg3m_p_zero_last10","fg3m_p_ge3_last10","fg3m_games_in_window_last10",
                   "fg3_pct_safe","fg3a_count_last10","fg3a_count_season","is_low_3pa_last10",
                   "_fg3m_integrity_miss_fg3m","_fg3m_integrity_miss_fg3a","_fg3m_integrity_bad_rows"]:
            f[_k] = np.nan

    # ── Variance drivers ──────────────────────────────────────────────────────
    f["blowout_risk_x_mp_vol"] = (
        (f.get("blowout_risk", np.nan) or np.nan) *
        (f.get("mp_vol_last10", np.nan) or np.nan)
    ) if (not np.isnan(f.get("blowout_risk", np.nan) or np.nan) and
          not np.isnan(f.get("mp_vol_last10", np.nan) or np.nan)) else np.nan

    # ── Schedule / fatigue ────────────────────────────────────────────────────
    dates = df["game_date"].tolist()
    f.update(schedule_features(dates, tdt))

    # ── Game script / odds ────────────────────────────────────────────────────
    f.update(game_script_features(game_context, is_home))

    # Recompute blowout_risk_x_mp_vol now that blowout_risk is set
    br  = f.get("blowout_risk")
    mpv = f.get("mp_vol_last10")
    if br is not None and mpv is not None and not np.isnan(br) and not np.isnan(mpv):
        f["blowout_risk_x_mp_vol"] = float(br) * float(mpv)
    else:
        f["blowout_risk_x_mp_vol"] = np.nan

    # ── Advanced stats ────────────────────────────────────────────────────────
    f.update(advanced_stats_block(prior_adv))

    # ── Vacated opportunity ───────────────────────────────────────────────────
    f.update(vacated_opportunity_features(
        player_id   = player_id,
        team_id     = team_id,
        target_date = tdt,
        stats_df    = all_stats_df,
        injury_map  = injury_map,
    ))

    # ── STL / BLK: zero-mass features + blended rate (expert fix) ───────────
    # p_zero_last10 and p_ge2_last10 help model place low quantiles near 0
    # and upper quantiles higher when multi-event upside exists.
    # Blended rate: w*r10 + (1-w)*r_season, w = n/(n+k), k=15
    BLEND_K = 15.0
    for sparse_stat, col in [("stl", "stl"), ("blk", "blk")]:
        if col in df.columns and len(min_arr) > 0:
            raw      = df[col].values.astype(float)
            rate     = per_minute_rate(raw, min_arr)

            # Zero-mass features
            last10_raw = raw[-10:]
            f[f"{sparse_stat}_p_zero_last10"] = (
                float(np.mean(last10_raw == 0)) if len(last10_raw) > 0 else np.nan
            )
            f[f"{sparse_stat}_p_ge2_last10"]  = (
                float(np.mean(last10_raw >= 2)) if len(last10_raw) > 0 else np.nan
            )

            # Blended rate: shrink last-10 rate toward season rate
            rate_clean = rate[~np.isnan(rate)]
            n_games    = len(rate_clean)
            r10        = float(np.nanmean(rate[-10:])) if n_games >= 1 else np.nan
            rs         = float(np.nanmean(rate))       if n_games >= 1 else np.nan
            if not np.isnan(r10) and not np.isnan(rs):
                w = min(n_games, 10) / (min(n_games, 10) + BLEND_K)
                f[f"{sparse_stat}_per_min_blended"] = w * r10 + (1.0 - w) * rs
            else:
                f[f"{sparse_stat}_per_min_blended"] = np.nan
        else:
            f[f"{sparse_stat}_p_zero_last10"]    = np.nan
            f[f"{sparse_stat}_p_ge2_last10"]     = np.nan
            f[f"{sparse_stat}_per_min_blended"]  = np.nan

    # ── Player archetype ──────────────────────────────────────────────────────
    f["games_played"]   = len(df)
    f["is_home"]        = int(is_home)

    return f


# ── Stat-specific feature gates ───────────────────────────────────────────────
# Each function returns the exact column list for one target per expert spec.

def _shared_cols() -> list[str]:
    """Columns shared across ALL stat models."""
    return [
        # Minutes
        "mp_mean_last5","mp_mean_last10","mp_mean_season",
        "mp_vol_last10","mp_ewma_10","mp_p25_last10","mp_p75_last10",
        # Variance drivers
        "blowout_risk_x_mp_vol","pf_per_min_mean_last10",
        "missed_last_game","missed_2_of_last5",
        # Schedule
        "rest_days","back_to_back","three_in_4","four_in_6","games_last_7",
        # Context
        "is_home","games_played",
        # Flags
        "has_odds","has_advanced_stats","has_injury_data",
    ]

def _odds_cols() -> list[str]:
    return ["game_total","spread_for_team","implied_team_total","blowout_risk"]

def _adv_cols() -> list[str]:
    return [
        "adv_usage_percentage_mean_last10",
        "adv_pace_mean_last10",
        "adv_true_shooting_percentage_mean_last10",
        "adv_effective_field_goal_percentage_mean_last10",
        "adv_assist_percentage_mean_last10",
        "adv_assist_to_turnover_mean_last10",
    ]

def _injury_base() -> list[str]:
    return ["vacated_minutes","num_teammates_inactive"]


def get_feature_cols_for_stat(stat: str, all_cols: list[str]) -> list[str]:
    """
    Return ordered feature column list for one target.
    Only columns that exist in all_cols are returned (safe for partial data).
    """
    wanted = set(_shared_cols()) | set(_odds_cols()) | set(_adv_cols())

    if stat == "pts":
        wanted |= {
            # Volume
            "fga_per_min_mean_last5","fga_per_min_mean_last10","fga_per_min_vol_last10","fga_per_min_ewma_10",
            "fta_per_min_mean_last10",
            "fg3a_per_min_mean_last10",
            "usage_proxy_per_min_mean_last10","usage_proxy_per_min_vol_last10",
            # Efficiency
            "adv_true_shooting_percentage_mean_last10",
            "adv_effective_field_goal_percentage_mean_last10",
            # Vacated
            "vacated_minutes","vacated_fga","vacated_fta","vacated_usage_proxy",
            "vacated_top2_fga","num_teammates_inactive",
            # Interactions
            "usage_proxy_x_itt","fga_x_itt",
        }

    elif stat == "reb":
        wanted |= {
            "reb_per_min_mean_last5","reb_per_min_mean_last10","reb_per_min_vol_last10","reb_per_min_ewma_10",
            "reb_per_min_p25_last10","reb_per_min_p75_last10",
            "oreb_per_min_mean_last10","dreb_per_min_mean_last10",
            "adv_pace_mean_last10",
            # Vacated
            "vacated_reb","vacated_minutes","num_teammates_inactive",
            # Interaction
            "reb_x_mp",
        }

    elif stat == "ast":
        wanted |= {
            "ast_per_min_mean_last5","ast_per_min_mean_last10","ast_per_min_vol_last10","ast_per_min_ewma_10",
            "ast_per_min_p25_last10","ast_per_min_p75_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_usage_percentage_mean_last10",
            "adv_assist_percentage_mean_last10",
            "adv_assist_to_turnover_mean_last10",
            "tov_per_min_mean_last10",
            # Vacated
            "vacated_ast","vacated_usage_proxy","vacated_minutes",
            "vacated_top2_usage_proxy","num_teammates_inactive",
            # Interactions
            "ast_pct_x_itt","usage_x_itt",
        }

    elif stat == "fg3m":
        # Expert spec FINAL: minimal set only — do not expand
        wanted |= {
            # Minutes
            "mp_mean_last5","mp_mean_last10","mp_vol_last10","mp_ewma_10",
            # 3PA volume / rate
            "fg3a_per_min_mean_last10",
            "fg3a_count_last10","fg3a_count_season",
            # Accuracy — safe shrink only, no old aliases
            "fg3_pct_safe",
            # Zero-mass
            "fg3m_p_zero_last10","fg3m_p_ge3_last10","fg3m_games_in_window_last10",
            # Low-volume gate
            "is_low_3pa_last10",
            # Context (pipeline globals only)
            "game_total","implied_team_total","spread","has_odds",
        }

    elif stat == "stl":
        wanted |= {
            # Blended rate (shrunk toward season average)
            "stl_per_min_blended",
            "stl_per_min_vol_last10",
            "stl_per_min_ewma_10",
            # Zero-mass features (expert requirement)
            "stl_p_zero_last10",
            "stl_p_ge2_last10",
            "adv_pace_mean_last10",
            # Vacated (minutes only — keep tight)
            "vacated_minutes",
        }

    elif stat == "blk":
        wanted |= {
            # Blended rate (shrunk toward season average)
            "blk_per_min_blended",
            "blk_per_min_vol_last10",
            "blk_per_min_ewma_10",
            # Zero-mass features (expert requirement)
            "blk_p_zero_last10",
            "blk_p_ge2_last10",
            "pf_per_min_mean_last10",  # foul trouble → minutes downside
            "adv_pace_mean_last10",
            # Vacated (keep tight)
            "vacated_minutes","num_teammates_inactive",
        }

    elif stat == "tov":
        wanted |= {
            "tov_per_min_mean_last10","tov_per_min_vol_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_usage_percentage_mean_last10",
            "adv_assist_to_turnover_mean_last10",
            "adv_pace_mean_last10",
            # Vacated
            "vacated_usage_proxy","vacated_minutes","num_teammates_inactive",
            # Interaction
            "usage_x_pace",
        }

    # ── Combo targets ─────────────────────────────────────────────────────────
    elif stat == "pra":
        wanted |= {
            # Component rates
            "pts_per_min_mean_last10","reb_per_min_mean_last10","ast_per_min_mean_last10",
            "pts_per_min_vol_last10","reb_per_min_vol_last10","ast_per_min_vol_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_pace_mean_last10","adv_usage_percentage_mean_last10",
            # Expectation proxies
            "E_pts_proxy","E_reb_proxy","E_ast_proxy",
            # Vacated
            "vacated_usage_proxy","vacated_minutes","vacated_ast","vacated_reb","vacated_fga",
            "num_teammates_inactive",
        }

    elif stat == "pr":
        wanted |= {
            "pts_per_min_mean_last10","reb_per_min_mean_last10",
            "pts_per_min_vol_last10","reb_per_min_vol_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_pace_mean_last10",
            "E_pts_proxy","E_reb_proxy",
            "vacated_reb","vacated_fga","vacated_minutes","num_teammates_inactive",
        }

    elif stat == "pa":
        wanted |= {
            "pts_per_min_mean_last10","ast_per_min_mean_last10",
            "pts_per_min_vol_last10","ast_per_min_vol_last10",
            "usage_proxy_per_min_mean_last10",
            "adv_pace_mean_last10","adv_assist_percentage_mean_last10",
            "E_pts_proxy","E_ast_proxy",
            "vacated_ast","vacated_usage_proxy","vacated_fga","vacated_minutes",
            "num_teammates_inactive",
        }

    elif stat == "ra":
        wanted |= {
            "reb_per_min_mean_last10","ast_per_min_mean_last10",
            "reb_per_min_vol_last10","ast_per_min_vol_last10",
            "adv_pace_mean_last10",
            "E_reb_proxy","E_ast_proxy",
            "vacated_ast","vacated_reb","vacated_minutes","num_teammates_inactive",
        }

    elif stat == "stocks":
        wanted |= {
            # Blended rates (same treatment as individual STL/BLK models)
            "stl_per_min_blended","stl_per_min_vol_last10","stl_per_min_ewma_10",
            "blk_per_min_blended","blk_per_min_vol_last10","blk_per_min_ewma_10",
            # Zero-mass features
            "stl_p_zero_last10","stl_p_ge2_last10",
            "blk_p_zero_last10","blk_p_ge2_last10",
            "pf_per_min_mean_last10",
            "adv_pace_mean_last10",
            "vacated_minutes","num_teammates_inactive",
        }

    return [c for c in all_cols if c in wanted]


def add_interaction_features(f: dict, stat: str) -> dict:
    """
    Compute stat-specific interaction features.
    These are computed AFTER the base feature vector is built.
    """
    itt = f.get("implied_team_total")
    mp  = f.get("mp_mean_last10")

    if stat == "pts":
        upm = f.get("usage_proxy_per_min_mean_last10")
        fgm = f.get("fga_per_min_mean_last10")
        f["usage_proxy_x_itt"] = (upm * itt) if (upm is not None and itt is not None and
                                                   not np.isnan(upm) and not np.isnan(itt)) else np.nan
        f["fga_x_itt"]         = (fgm * itt) if (fgm is not None and itt is not None and
                                                   not np.isnan(fgm) and not np.isnan(itt)) else np.nan

    elif stat == "reb":
        rpm = f.get("reb_per_min_mean_last10")
        f["reb_x_mp"] = (rpm * mp) if (rpm is not None and mp is not None and
                                        not np.isnan(rpm) and not np.isnan(mp)) else np.nan

    elif stat == "ast":
        apm = f.get("adv_assist_percentage_mean_last10")
        upm = f.get("adv_usage_percentage_mean_last10")
        f["ast_pct_x_itt"] = (apm * itt) if (apm is not None and itt is not None and
                                               not np.isnan(apm) and not np.isnan(itt)) else np.nan
        f["usage_x_itt"]   = (upm * itt) if (upm is not None and itt is not None and
                                               not np.isnan(upm) and not np.isnan(itt)) else np.nan

    elif stat == "tov":
        upm  = f.get("usage_proxy_per_min_mean_last10")
        pace = f.get("adv_pace_mean_last10")
        f["usage_x_pace"] = (upm * pace) if (upm is not None and pace is not None and
                                               not np.isnan(upm) and not np.isnan(pace)) else np.nan

    # Combo expectation proxies
    if stat in ("pra","pr","pa","ra"):
        pm_pts = f.get("pts_per_min_mean_last10")
        pm_reb = f.get("reb_per_min_mean_last10")
        pm_ast = f.get("ast_per_min_mean_last10")
        f["E_pts_proxy"] = (pm_pts * mp) if (pm_pts and mp and not np.isnan(pm_pts) and not np.isnan(mp)) else np.nan
        f["E_reb_proxy"] = (pm_reb * mp) if (pm_reb and mp and not np.isnan(pm_reb) and not np.isnan(mp)) else np.nan
        f["E_ast_proxy"] = (pm_ast * mp) if (pm_ast and mp and not np.isnan(pm_ast) and not np.isnan(mp)) else np.nan

    return f
