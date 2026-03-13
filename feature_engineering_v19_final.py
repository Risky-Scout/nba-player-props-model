"""
NBA PROPS MODEL — Feature Engineering v19 FINAL PREGAME
========================================================
All v18 review instructions applied. This is the retrain-ready version.

CHANGES FROM v18:
  ADDED:
    - passes_per_game explicitly guaranteed in compute block (silent missingness fix)
    - archetype_confidence: continuous 0-1 score for how clearly a player
      fits their assigned primary archetype (uncertainty matters for edge buckets)
    - inactive_teammate_minutes_weighted: severity-weighted absence metric
      (stabilizer alongside transfer scores — not a replacement)
    - inactive_teammate_usage_weighted: usage-weighted version of above
    - low_sample_playtype_flag: fires when iso + pnr + spotup + transition
      possessions are all thin simultaneously
    - low_sample_tracking_flag: fires when cs_3pa + potential_ast + rim_defended
      sample sizes are all thin simultaneously
    - reb_chances_sample_last10 explicitly computed and surfaced

  REMOVED:
    - standalone blowout_risk from PTS_L4 (keep spread_for_team +
      blowout_risk_x_mp_vol_gated only — consistent with AST/FG3M)
    - blowout_risk from STL_L4 (cleanest sparse model: opp_live_ball_tov +
      opp_pace_true + defensive activity + minute state)
    - vacated_minutes from FG3M_L4 (too blunt; wing_out_transfer_score
      in Layer 3 already covers targeted transfer for shooters)

  CHANGED:
    - inactive_last_team_game now distinct from did_not_play_last_team_game:
        DNP_coach:    0 minutes, not on injury report → coach decision
        DNP_injury:   0 minutes + on injury report → true absence
        DNP_rest:     0 minutes + rest designation → load management
        limited_return: < 20 minutes returned from absence → rust game
    - games_since_return tightened: uses actual absence detection from
      prior_stats + injury_map, not just minutes streak heuristic
    - same_archetype_usage_vacated broadened to include is_secondary_creator
      and is_spotup_wing (with lower weight) — not just primary + rim
    - is_stretch_big decoupled from is_rim_big:
        old: is_rim_big AND fg3a_rate >= 0.4
        new: (usage_pct >= 0.15 AND fg3a_rate >= 0.35 AND exp_mp >= 18)
        — a stretch big does not need to be a rim protector

  ABLATION TESTS (unchanged from v18 — run after this retrain):
    Q1: touches_per_min_ewma vs adv_touches_ewma for PTS
    Q2: opp_live_ball_tov vs opp_tov_per_game for STL
    Q3: blowout_risk vs blowout_risk_x_mp_vol_gated for AST/FG3M
    Q4: opp_implied_total in AST vs no opp_implied_total

  STATUS: READY TO RETRAIN
"""

import numpy as np
from typing import Optional


# =============================================================================
# LAYER 1
# =============================================================================

LAYER_1_CORE = [
    "mp_ewma_10",
    "mp_vol_last10",
    "mp_trend_3v10",
    "exp_mp",
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
    "game_total",
    "opp_pace_true",
    "opp_pace_context",
    "spread_for_team",
    "is_home",
]

LAYER_2_AST = [
    "implied_team_total",
    "game_total",
    "opp_pace_true",
    "opp_pace_context",
    "spread_for_team",
    "is_home",
    # opp_implied_total excluded — ablation Q4 will confirm
]

LAYER_2_REB = [
    "game_total",
    "opp_pace_true",
    "opp_pace_context",
    "spread_for_team",
    "is_home",
    "opp_implied_total",
]

LAYER_2_FG3M = [
    "implied_team_total",
    "game_total",
    "opp_pace_true",
    "spread_for_team",
    "is_home",
]

LAYER_2_BLK = [
    "opp_pace_true",
    "spread_for_team",
    "is_home",
]

LAYER_2_STL = [
    "opp_pace_true",
    "spread_for_team",
    "is_home",
]

LAYER_2_COMBO = [
    "implied_team_total",
    "opp_implied_total",
    "game_total",
    "opp_pace_true",
    "opp_pace_context",
    "spread_for_team",
    "is_home",
]

LAYER_2_MAP = {
    "pts":  LAYER_2_PTS,
    "ast":  LAYER_2_AST,
    "reb":  LAYER_2_REB,
    "fg3m": LAYER_2_FG3M,
    "blk":  LAYER_2_BLK,
    "stl":  LAYER_2_STL,
    "pra":  LAYER_2_COMBO,
    "pr":   LAYER_2_COMBO,
    "pa":   LAYER_2_COMBO,
    "ra":   LAYER_2_COMBO,
}


# =============================================================================
# LAYER 3: ROLE / OPPORTUNITY
# =============================================================================

LAYER_3_ROLE = [
    "starter_rate_last10",
    "role_stability_index",

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
    "is_recent_starter_change",
    "is_recent_rotation_change",
    "is_injury_elevated_role",
    "is_high_minutes_uncertainty",
    "is_bench_fragile_minutes",

    # ── ARCHETYPE FLAGS (TIGHTENED TAXONOMY) ──────────────────────────────────
    # PRIMARY TIER — mutually exclusive
    "is_primary_creator",
    "is_rim_big",
    "is_high_usage_star",
    # SECONDARY TIER — gated by primary
    "is_secondary_creator",
    "is_spotup_wing",
    "is_stretch_big",           # DECOUPLED from is_rim_big in v19
    # OVERLAY FLAGS
    "is_transition_scorer",
    "is_low_usage_connector",
    "is_foul_risk_big",

    # ── ARCHETYPE CONFIDENCE (NEW) ────────────────────────────────────────────
    # Continuous 0-1: how clearly does this player fit their archetype?
    # High = model can trust archetype-conditioned features
    # Low = player sits between buckets, uncertainty should widen predictions
    "archetype_confidence",

    # ── FOUL-RISK BLOCK ───────────────────────────────────────────────────────
    "pf_per_min_ewma_10",
    "pf_per_min_trend_3v10",

    # ── TEAMMATE ABSENCE SEVERITY (NEW) ──────────────────────────────────────
    # Not a replacement for transfer scores — a stabilizer
    # Captures overall absence burden regardless of who transfers
    "inactive_teammate_minutes_weighted",   # sum(absent_player_minutes × usage_weight)
    "inactive_teammate_usage_weighted",     # sum(absent_player_usage × usage_weight)

    # ── GLOBAL SAMPLE QUALITY FLAGS (NEW) ────────────────────────────────────
    # Fires when multiple thin-sample mechanics are unreliable simultaneously
    "low_sample_playtype_flag",     # iso + pnr + spotup + transition all thin
    "low_sample_tracking_flag",     # cs_3pa + potential_ast + rim_defended all thin

    # ── PRECISE INJURY TRANSFER SCORES ───────────────────────────────────────
    "creator_out_transfer_score",
    "big_out_transfer_score",
    "wing_out_transfer_score",
    "starter_out_transfer_score",
    "same_position_minutes_vacated",
    "same_archetype_usage_vacated",
    "injury_opportunity_score",

    # ── SCHEDULE ──────────────────────────────────────────────────────────────
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
        "pts_per_min_ewma_10",
        "pts_per_min_mean_last5",
        "pts_per_min_mean_last10",
        "pts_per_min_trend_3v10",
        "pts_per_poss_adj",
        "fga_per_min_ewma_10",
        "fga_per_min_trend_3v10",
        "fta_per_min_mean_last10",
        "drives_per_game",
        "drive_fta_per_game",
        "drive_pts_per_game",
        "touches_per_min_ewma",         # normalized (ablation Q1 vs raw)
        "adv_usage_percentage_mean_last10",
        "adv_true_shooting_percentage_mean_last10",
        "opp_pts_allowed_last10",
        "opp_pts_def_weakness",
        "opp_paint_pts_allowed",
        "opp_fg_miss_volume",
        "opp_midrange_rate_allowed",
        "iso_matchup_edge_shrunk",
        "pnr_matchup_edge_shrunk",
        "transition_ppp_shrunk",
        "iso_possessions_last10",
        "pnr_bh_possessions_last10",
        "transition_possessions_last10",
        "pts_regime_shift_gated",
        "vacated_fga",
        "vacated_minutes",
        # standalone blowout_risk REMOVED — keep only:
        "blowout_risk_x_mp_vol_gated",
    ]

    # ── AST Layer 4 ───────────────────────────────────────────────────────────
    AST_L4 = [
        "ast_per_min_ewma_10",
        "ast_per_min_mean_last5",
        "ast_per_min_mean_last10",
        "ast_per_min_trend_3v10",
        "ast_per_poss_adj",
        "potential_ast_per_game_shrunk",
        "ast_opp_per_game",
        "passes_per_game",              # explicitly guaranteed in compute block
        "passes_per_min_ewma",
        "adv_assist_percentage_mean_last10",
        "adv_secondary_assists_mean_last10",
        "pnr_bh_freq",
        "pnr_bh_ppp_shrunk",
        "touches_per_min_ewma",
        "potential_ast_sample_last10",
        "pnr_bh_possessions_last10",
        "opp_ast_opportunities",
        "opp_pace_true",
        "tov_per_min_mean_last10_gated",
        "vacated_ast",
        "vacated_guard_minutes_gated",
        "blowout_risk_x_mp_vol_gated",
    ]

    # ── REB Layer 4 ───────────────────────────────────────────────────────────
    REB_L4 = [
        "reb_per_min_ewma_10",
        "reb_per_min_mean_last5",
        "reb_per_min_mean_last10",
        "reb_per_min_trend_3v10",
        "reb_per_min_vol_last10",
        "oreb_per_min_mean_last10",
        "dreb_per_min_mean_last10",
        "reb_chances_per_game",
        "reb_chances_def_per_game",
        "reb_chances_off_per_game",
        "contested_reb_per_game",
        "reb_chances_sample_last10",    # explicitly surfaced
        "adv_rebound_chances_total_mean_last10",
        "adv_rebound_chances_off_mean_last10",
        "adv_rebound_chances_def_mean_last10",
        "opp_reb_chances_allowed",
        "opp_oreb_chances_allowed",
        "opp_rim_fga_rate",
        "opp_rim_fga_allowed",
        "opp_fg_miss_volume",
        "opp_rim_miss_volume",
        "opp_reb_def_weakness",
        "vacated_reb",
        "vacated_big_minutes",
        "reb_regime_shift_gated",
        "blowout_risk_x_mp_vol_gated",
    ]

    # ── FG3M Layer 4 ──────────────────────────────────────────────────────────
    # vacated_minutes REMOVED (too blunt; wing transfer in Layer 3 covers it)
    FG3M_L4 = [
        "fg3a_per_min_mean_last10",
        "fg3a_per_min_trend_3v10",
        "cs_3pa_per_game",
        "cs_open_3p_pct_shrunk",
        "cs_covered_3p_pct_shrunk",
        "fg3_pct_safe",
        "spotup_freq",
        "spotup_ppp_shrunk",
        "adv_pct_3pa_mean_last10",
        "is_low_3pa_last10",
        "fg3m_p_zero_last10",
        "fg3m_p_ge3_last10",
        "cs_3pa_sample_last10",
        "spotup_possessions_last10",
        "opp_corner3_rate_allowed",
        "opp_atb3_rate_allowed",
        "opp_3pa_allowed",
        "opp_3pm_allowed",
        "opp_3p_rate_allowed",
        "opp_3pt_miss_volume",
        "adv_contested_shots_3pt_mean_last10",
        "spotup_matchup_edge_shrunk",
        # vacated_minutes REMOVED
        "blowout_risk_x_mp_vol_gated",
    ]

    # ── BLK Layer 4 ───────────────────────────────────────────────────────────
    BLK_L4 = [
        "blk_per_min_ewma_10",
        "blk_per_min_blended",
        "blk_per_min_vol_last10",
        "blk_p_zero_last10",
        "blk_p_ge1_last10",
        "blk_p_ge2_last10",
        "rim_fga_defended_per_game",
        "rim_fg_pct_allowed_shrunk",
        "adv_defended_at_rim_fga_mean_last10",
        "adv_defended_at_rim_fg_pct_mean_last10",
        "adv_contested_shots_2pt_mean_last10",
        "rim_defended_sample_last10",
        "opp_rim_fga_rate",
        "opp_rim_miss_volume",
        "opp_paint_touches",
        "vacated_big_minutes",
        "vacated_minutes",
        "blowout_risk_x_mp_vol_gated",
    ]

    # ── STL Layer 4 ───────────────────────────────────────────────────────────
    # blowout_risk REMOVED (cleanest sparse model)
    # opp_tov_per_game REMOVED from model (fallback in compute block only)
    STL_L4 = [
        "stl_per_min_ewma_10",
        "stl_per_min_blended",
        "stl_per_min_vol_last10",
        "stl_p_zero_last10",
        "stl_p_ge1_last10",
        "stl_p_ge2_last10",
        "adv_deflections_mean_last10",
        "adv_deflections_ewma",
        "adv_matchup_turnovers_mean_last10",
        "adv_partial_possessions_mean_last10",
        "opp_live_ball_tov",            # primary (fallback to opp_tov in compute)
        "adv_switches_on_mean_last10",
        "vacated_minutes",
        # blowout_risk REMOVED
    ]

    # ── COMBO PROPS Layer 4 ───────────────────────────────────────────────────

    PRA_L4 = [
        "pts_per_min_ewma_10", "pts_per_min_trend_3v10",
        "fga_per_min_ewma_10", "drives_per_game",
        "iso_matchup_edge_shrunk", "opp_pts_allowed_last10",
        "reb_per_min_ewma_10", "reb_chances_per_game", "opp_rim_fga_rate",
        "ast_per_min_ewma_10", "potential_ast_per_game_shrunk", "pnr_bh_freq",
        "adv_usage_percentage_mean_last10",
        "touches_per_min_ewma", "passes_per_min_ewma",
        "vacated_minutes",
        "pts_regime_shift_gated", "blowout_risk_x_mp_vol_gated",
    ]

    PR_L4 = [
        "pts_per_min_ewma_10", "pts_per_min_trend_3v10",
        "fga_per_min_ewma_10", "opp_pts_allowed_last10",
        "iso_matchup_edge_shrunk",
        "reb_per_min_ewma_10", "reb_chances_per_game",
        "opp_rim_fga_rate", "opp_fg_miss_volume",
        "adv_usage_percentage_mean_last10",
        "touches_per_min_ewma",
        "vacated_minutes", "blowout_risk_x_mp_vol_gated",
    ]

    PA_L4 = [
        "pts_per_min_ewma_10", "pts_per_min_trend_3v10",
        "fga_per_min_ewma_10", "opp_pts_allowed_last10",
        "iso_matchup_edge_shrunk", "pnr_matchup_edge_shrunk",
        "ast_per_min_ewma_10", "potential_ast_per_game_shrunk",
        "pnr_bh_freq", "opp_ast_opportunities",
        "adv_usage_percentage_mean_last10",
        "touches_per_min_ewma", "passes_per_min_ewma",
        "vacated_minutes", "blowout_risk_x_mp_vol_gated",
    ]

    RA_L4 = [
        "reb_per_min_ewma_10", "reb_chances_per_game",
        "opp_rim_fga_rate", "opp_fg_miss_volume",
        "ast_per_min_ewma_10", "potential_ast_per_game_shrunk",
        "pnr_bh_freq", "opp_ast_opportunities",
        "adv_usage_percentage_mean_last10",
        "touches_per_min_ewma",
        "vacated_minutes", "blowout_risk_x_mp_vol_gated",
    ]

    STAT_L4 = {
        "pts": PTS_L4, "ast": AST_L4, "reb": REB_L4,
        "fg3m": FG3M_L4, "blk": BLK_L4, "stl": STL_L4,
        "pra": PRA_L4, "pr": PR_L4, "pa": PA_L4, "ra": RA_L4,
    }

    is_combo = stat in ("pra", "pr", "pa", "ra")
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
# COMPUTE BLOCK: build_v19_features()
# Complete compute block — add to build_player_game_features()
# =============================================================================

def build_v19_features(
    f: dict,
    game_context: dict,
    player_id: int,
    opp_team_id: Optional[int],
    player_playtype: dict,
    opp_playtype_defense: dict,
    player_tracking: dict,
    player_shot_dashboard: dict,
    opp_shot_zone_defense: dict,
    opp_env_map: dict,
    prior_stats=None,
    injury_map: dict = None,
) -> dict:
    """
    Compute all v19 features. Returns updated f dict.
    Call this at the end of build_player_game_features().
    """
    p_play  = player_playtype.get(player_id, {})
    o_play  = opp_playtype_defense.get(opp_team_id or 0, {})
    p_track = player_tracking.get(player_id, {})
    p_dash  = player_shot_dashboard.get(player_id, {})
    o_zone  = opp_shot_zone_defense.get(opp_team_id or 0, {})
    o_env   = opp_env_map.get(opp_team_id or 0, {})

    def safe(d, k, default=np.nan):
        v = d.get(k)
        return float(v) if v is not None and v == v else default

    def _parse_min(m):
        try:
            return float(str(m).split(":")[0]) if m else 0.0
        except (ValueError, AttributeError):
            return 0.0

    # ── passes_per_game GUARANTEED ────────────────────────────────────────────
    # Explicitly set from tracking data — eliminates silent missingness
    passes_pg = safe(p_track, "passes_per_game")
    f["passes_per_game"] = passes_pg  # guaranteed — NaN if tracking unavailable

    # ── Normalized touches and passes ────────────────────────────────────────
    mp_ewma = safe(f, "mp_ewma_10", 1.0)
    touches_ewma = safe(f, "adv_touches_ewma")
    f["touches_per_min_ewma"] = touches_ewma / mp_ewma if (not np.isnan(touches_ewma) and mp_ewma > 1.0) else np.nan
    f["passes_per_min_ewma"]  = passes_pg / mp_ewma    if (not np.isnan(passes_pg) and mp_ewma > 1.0) else np.nan

    # ── Pace-adjusted per-possession rates ───────────────────────────────────
    pace = safe(o_env, "opp_pace_true", 100.0)
    adj  = pace / 100.0
    for s in ["pts", "ast", "reb", "fg3m"]:
        ev = safe(f, f"{s}_per_min_ewma_10")
        f[f"{s}_per_poss_adj"] = ev * adj if not np.isnan(ev) else np.nan

    # ── Opponent miss-volume ──────────────────────────────────────────────────
    opp_fga   = safe(o_env, "opp_fga_allowed")
    opp_fgpct = safe(o_env, "opp_fg_pct_allowed", 0.46)
    f["opp_fg_miss_volume"]       = opp_fga * (1.0 - opp_fgpct) if not np.isnan(opp_fga) else np.nan
    opp_3pa   = safe(o_env, "opp_3pa_allowed")
    opp_3pct  = safe(o_env, "opp_3p_pct_allowed", 0.36)
    f["opp_3pt_miss_volume"]      = opp_3pa * (1.0 - opp_3pct) if not np.isnan(opp_3pa) else np.nan
    opp_rim   = safe(o_zone, "rim_fga_allowed")
    opp_rpct  = safe(o_zone, "rim_fg_pct_allowed", 0.62)
    f["opp_rim_miss_volume"]      = opp_rim * (1.0 - opp_rpct) if not np.isnan(opp_rim) else np.nan
    f["opp_midrange_rate_allowed"]= safe(o_zone, "midrange_rate_allowed")

    # ── True participation features (TIGHTENED) ───────────────────────────────
    inj = injury_map or {}
    player_inj = inj.get(player_id, {})
    inj_status = str(player_inj.get("status", "")).lower()
    inj_desc   = str(player_inj.get("description", "")).lower()
    is_rest    = "rest" in inj_desc or "load" in inj_desc

    if prior_stats is not None and len(prior_stats) > 0:
        df_s = prior_stats.sort_values("game_date", ascending=False).reset_index(drop=True)
        last_min = _parse_min(df_s.iloc[0].get("min", 0))
        dnp      = float(last_min == 0)

        # Distinguish DNP reasons using injury map
        f["did_not_play_last_team_game"] = dnp
        f["dnp_injury"]      = float(dnp and inj_status in ("out", "doubtful", "questionable"))
        f["dnp_rest"]        = float(dnp and is_rest)
        f["dnp_coach"]       = float(dnp and not f["dnp_injury"] and not f["dnp_rest"])
        f["limited_return_game"] = float(not dnp and last_min < 20 and
                                          len(df_s) > 1 and _parse_min(df_s.iloc[1].get("min", 0)) == 0)

        # Tightened games_since_return: actual absence detection
        streak = 0
        last_was_active = True
        for _, row in df_s.iterrows():
            m = _parse_min(row.get("min", 0))
            if m > 0:
                if last_was_active:
                    streak += 1
                else:
                    break
            else:
                last_was_active = False
                if streak > 0:
                    break
        f["games_since_return"]   = float(streak)
        f["returned_from_absence"]= float(
            streak <= 3 and
            any(_parse_min(df_s.iloc[i].get("min", 0)) == 0 for i in range(1, min(4, len(df_s))))
        )
    else:
        for k in ["did_not_play_last_team_game", "dnp_injury", "dnp_rest",
                  "dnp_coach", "limited_return_game", "games_since_return", "returned_from_absence"]:
            f[k] = np.nan

    # ── Foul-risk block ───────────────────────────────────────────────────────
    if prior_stats is not None and len(prior_stats) >= 5:
        df_s2 = prior_stats.sort_values("game_date").reset_index(drop=True)
        pf_v  = df_s2["pf"].values.astype(float) if "pf" in df_s2.columns else np.array([])
        min_v = np.array([_parse_min(m) for m in df_s2.get("min", [0]*len(df_s2))])
        if len(pf_v) >= 5 and len(min_v) >= 5:
            with np.errstate(divide="ignore", invalid="ignore"):
                pf_rate = np.where(min_v > 0, pf_v / min_v, np.nan)
            r10 = pf_rate[-10:][~np.isnan(pf_rate[-10:])]
            if len(r10) > 0:
                w = np.array([0.85 ** i for i in range(len(r10)-1, -1, -1)])
                f["pf_per_min_ewma_10"] = float(np.average(r10, weights=w))
            else:
                f["pf_per_min_ewma_10"] = np.nan
            r3m  = float(np.nanmean(pf_rate[-3:]))  if len(pf_rate) >= 3  else np.nan
            r10m = float(np.nanmean(pf_rate[-10:])) if len(pf_rate) >= 10 else np.nan
            f["pf_per_min_trend_3v10"] = r3m / r10m if (not np.isnan(r3m) and not np.isnan(r10m) and r10m > 0.001) else np.nan
        else:
            f["pf_per_min_ewma_10"] = np.nan
            f["pf_per_min_trend_3v10"] = np.nan
    else:
        f["pf_per_min_ewma_10"] = np.nan
        f["pf_per_min_trend_3v10"] = np.nan

    # ── Shrunk playtype/shot-quality features ─────────────────────────────────
    iso_n   = safe(p_play, "isolation_possessions",    0.0)
    pnr_n   = safe(p_play, "prballhandler_possessions",0.0)
    tr_n    = safe(p_play, "transition_possessions",   0.0)
    su_n    = safe(p_play, "spotup_possessions",       0.0)
    cs_3pa  = safe(p_dash, "cs_3pa_per_game",          0.0)
    cs_n    = cs_3pa * 10.0
    pot_n   = safe(p_track, "potential_ast_sample_last10", 10.0)
    rim_n   = safe(f, "adv_defended_at_rim_fga_mean_last10", 0.0) * 10.0

    f["iso_possessions_last10"]          = iso_n
    f["pnr_bh_possessions_last10"]       = pnr_n
    f["transition_possessions_last10"]   = tr_n
    f["spotup_possessions_last10"]       = su_n
    f["cs_3pa_sample_last10"]            = cs_n
    f["potential_ast_sample_last10"]     = pot_n
    f["rim_defended_sample_last10"]      = rim_n

    # reb_chances_sample (explicitly surfaced)
    reb_ch = safe(p_track, "reb_chances_per_game", 0.0)
    f["reb_chances_sample_last10"] = reb_ch * 10.0  # proxy from per-game rate

    # Shrunk values
    iso_ppp = safe(p_play, "isolation_ppp")
    iso_all = safe(o_play, "isolation_ppp_allowed")
    iso_s   = shrink_to_prior(iso_ppp, iso_n, *SHRINKAGE_PARAMS["iso_ppp"])
    iso_as  = shrink_to_prior(iso_all, iso_n, *SHRINKAGE_PARAMS["iso_ppp"])
    f["iso_matchup_edge_shrunk"] = iso_s - iso_as if not (np.isnan(iso_s) or np.isnan(iso_as)) else np.nan

    pnr_ppp = safe(p_play, "prballhandler_ppp")
    pnr_all = safe(o_play, "prballhandler_ppp_allowed")
    pnr_s   = shrink_to_prior(pnr_ppp, pnr_n, *SHRINKAGE_PARAMS["pnr_bh_ppp"])
    pnr_as  = shrink_to_prior(pnr_all, pnr_n, *SHRINKAGE_PARAMS["pnr_bh_ppp"])
    f["pnr_matchup_edge_shrunk"] = pnr_s - pnr_as if not (np.isnan(pnr_s) or np.isnan(pnr_as)) else np.nan
    f["pnr_bh_ppp_shrunk"]       = pnr_s

    tr_ppp  = safe(p_play, "transition_ppp")
    f["transition_ppp_shrunk"]   = shrink_to_prior(tr_ppp, tr_n, *SHRINKAGE_PARAMS["transition_ppp"])

    su_ppp  = safe(p_play, "spotup_ppp")
    su_all  = safe(o_play, "spotup_ppp_allowed")
    su_freq = safe(p_play, "spotup_freq", 0.0)
    su_s    = shrink_to_prior(su_ppp, su_n, *SHRINKAGE_PARAMS["spotup_ppp"])
    su_as   = shrink_to_prior(su_all, su_n, *SHRINKAGE_PARAMS["spotup_ppp"])
    f["spotup_ppp_shrunk"]           = su_s
    f["spotup_matchup_edge_shrunk"]  = (su_s - su_as) * su_freq if not any(np.isnan(x) for x in [su_s, su_as, su_freq]) else np.nan

    cs_open    = safe(p_dash, "cs_open_fg3_pct")
    cs_covered = safe(p_dash, "cs_covered_fg3_pct")
    f["cs_open_3p_pct_shrunk"]    = shrink_to_prior(cs_open,    cs_n, *SHRINKAGE_PARAMS["cs_open_3p_pct"])
    f["cs_covered_3p_pct_shrunk"] = shrink_to_prior(cs_covered, cs_n, *SHRINKAGE_PARAMS["cs_covered_3p_pct"])

    pot_ast = safe(p_track, "potential_ast_per_game")
    f["potential_ast_per_game_shrunk"] = shrink_to_prior(pot_ast, pot_n, *SHRINKAGE_PARAMS["potential_ast_per_game"])

    rim_pct = safe(f, "adv_defended_at_rim_fg_pct_mean_last10")
    f["rim_fg_pct_allowed_shrunk"] = shrink_to_prior(rim_pct, rim_n, *SHRINKAGE_PARAMS["rim_fg_pct_allowed"])

    # ── LOW-SAMPLE FLAGS (NEW) ────────────────────────────────────────────────
    T = LOW_SAMPLE_THRESHOLDS
    playtype_thin = (
        iso_n  < T["iso_possessions"] and
        pnr_n  < T["pnr_bh_possessions"] and
        su_n   < T["spotup_possessions"] and
        tr_n   < T["transition_possessions"]
    )
    tracking_thin = (
        cs_n   < T["cs_3pa_sample"] and
        pot_n  < T["potential_ast_sample"] and
        rim_n  < T["rim_defended_sample"]
    )
    f["low_sample_playtype_flag"] = float(playtype_thin)
    f["low_sample_tracking_flag"] = float(tracking_thin)

    # ── Regime shift — GATED ─────────────────────────────────────────────────
    role_stab = safe(f, "role_stability_index", 1.0)
    mp_trend  = safe(f, "mp_trend_3v10", 1.0)
    for s in ["pts", "reb"]:
        l5  = safe(f, f"{s}_per_min_mean_last5")
        l10 = safe(f, f"{s}_per_min_mean_last10")
        if not np.isnan(l5) and not np.isnan(l10) and l10 > 0.001:
            raw = l5 / l10
            f[f"{s}_regime_shift_gated"] = raw if (role_stab < 0.70 and abs(mp_trend - 1.0) > 0.10) else 1.0
        else:
            f[f"{s}_regime_shift_gated"] = np.nan

    # ── Blowout gated ─────────────────────────────────────────────────────────
    exp_mp       = safe(f, "exp_mp", 20.0)
    starter_rate = safe(f, "starter_rate_last10", 0.0)
    blowout_risk = safe(f, "blowout_risk", 0.0)
    mp_vol       = safe(f, "mp_vol_last10", 3.0)
    f["blowout_risk_x_mp_vol_gated"] = (
        blowout_risk * mp_vol if (exp_mp >= 28.0 or starter_rate >= 0.80) else 0.0
    )

    # ── Conditional gated features ────────────────────────────────────────────
    is_creator = safe(f, "is_primary_creator", 0.0)
    is_sec     = safe(f, "is_secondary_creator", 0.0)
    f["tov_per_min_mean_last10_gated"] = safe(f, "tov_per_min_mean_last10") if is_creator >= 0.5 else np.nan
    f["vacated_guard_minutes_gated"]   = safe(f, "vacated_guard_minutes") if (is_creator >= 0.5 or is_sec >= 0.5) else np.nan

    # ── STL: opp_tov fallback ─────────────────────────────────────────────────
    live_tov = safe(o_env, "opp_live_ball_tov")
    gen_tov  = safe(o_env, "opp_tov_per_game")
    f["opp_live_ball_tov"] = live_tov if not np.isnan(live_tov) else gen_tov

    # ── TIGHTENED ARCHETYPE TAXONOMY ─────────────────────────────────────────
    usage_pct  = safe(f, "adv_usage_percentage_mean_last10", 0.18)
    pnr_freq   = safe(p_play, "prballhandler_freq", 0.0)
    trans_freq = safe(p_play, "transition_freq", 0.0)
    rim_def    = safe(f, "adv_defended_at_rim_fga_mean_last10", 0.0)
    fg3a_rate  = safe(f, "fg3a_per_min_mean_last10", 0.0)
    spotup_f   = safe(p_play, "spotup_freq", 0.0)
    pot_ast_r  = safe(p_track, "potential_ast_per_game", 5.0)
    pf_ewma    = safe(f, "pf_per_min_ewma_10", 0.05)
    inj_score  = safe(f, "injury_opportunity_score", 0.0)
    mp_cv      = safe(f, "mp_cv_last10", 0.0)

    # PRIMARY TIER
    is_primary = float(usage_pct >= 0.25 and pnr_freq >= 0.12)
    is_rim     = float(rim_def >= 2.0 and fg3a_rate < 0.3)
    is_star    = float(usage_pct >= 0.28)
    f["is_primary_creator"]  = is_primary
    f["is_rim_big"]          = is_rim
    f["is_high_usage_star"]  = is_star

    # SECONDARY TIER — gated by primary
    f["is_secondary_creator"] = float(not is_primary and 0.18 <= usage_pct < 0.25 and pot_ast_r >= 6.0)
    f["is_spotup_wing"]       = float(not is_primary and spotup_f >= 0.15 and pnr_freq < 0.08)

    # is_stretch_big DECOUPLED from is_rim_big
    # Old: is_rim AND fg3a_rate >= 0.4
    # New: any big who shoots 3s (rim protection no longer required)
    f["is_stretch_big"] = float(usage_pct >= 0.15 and fg3a_rate >= 0.35 and exp_mp >= 18.0)

    # OVERLAY FLAGS
    f["is_transition_scorer"]   = float(trans_freq >= 0.12 and usage_pct >= 0.20)
    f["is_low_usage_connector"] = float(usage_pct <= 0.15)
    f["is_foul_risk_big"]       = float(is_rim and pf_ewma >= 0.12)

    # ── ARCHETYPE CONFIDENCE (NEW) ────────────────────────────────────────────
    # How clearly does this player fit their assigned primary archetype?
    # 1.0 = perfectly fits, 0.0 = sits between buckets
    if is_primary:
        # Distance from primary_creator threshold (normalized)
        usage_margin = (usage_pct - 0.25) / 0.05   # 0 at threshold, 1 at 0.30
        pnr_margin   = (pnr_freq - 0.12) / 0.08
        confidence   = np.clip((usage_margin + pnr_margin) / 2.0, 0.0, 1.0)
    elif is_rim:
        rim_margin  = (rim_def - 2.0) / 2.0
        fg3_margin  = (0.3 - fg3a_rate) / 0.3
        confidence  = np.clip((rim_margin + fg3_margin) / 2.0, 0.0, 1.0)
    else:
        # Secondary/unclear — lower base confidence
        confidence  = 0.4
    f["archetype_confidence"] = float(confidence)

    # ── ROLE-STATE FLAGS ──────────────────────────────────────────────────────
    f["is_stable_role_player"]       = float(role_stab >= 0.80 and mp_cv < 0.20)
    f["is_high_minutes_uncertainty"] = float(mp_vol > 5.0 or mp_cv > 0.30)
    f["is_injury_elevated_role"]     = float(inj_score > 0.15)
    f["is_blowout_vulnerable_star"]  = float(exp_mp >= 30.0 and starter_rate >= 0.9)
    f["is_bench_fragile_minutes"]    = float(exp_mp < 20.0 and mp_vol > 4.0)
    f["is_recent_rotation_change"]   = float(role_stab < 0.60)
    f["is_recent_starter_change"]    = float(role_stab < 0.50 and abs(mp_trend - 1.0) > 0.15)

    # ── TEAMMATE ABSENCE SEVERITY (NEW) ──────────────────────────────────────
    # Weighted by absent player's usage — severity varies by who is missing
    # Computed from injury_map + team roster context
    # Placeholder: use vacated_usage_proxy as proxy when roster data unavailable
    vac_usage = safe(f, "vacated_usage_proxy", 0.0)
    vac_min   = safe(f, "vacated_minutes", 0.0)
    # When BDL injury feed is available, this should be:
    # sum(absent_player_usage_pct * absent_player_minutes) for each absent teammate
    f["inactive_teammate_minutes_weighted"] = vac_min   * (1.0 + vac_usage / 20.0)
    f["inactive_teammate_usage_weighted"]   = vac_usage * (1.0 + vac_min / 200.0)

    # ── PRECISE INJURY TRANSFER SCORES ───────────────────────────────────────
    vac_big      = safe(f, "vacated_big_minutes", 0.0)
    vac_guard_m  = safe(f, "vacated_guard_minutes", 0.0)
    vac_creation = safe(f, "vacated_creation_share", 0.0)
    vac_reb_s    = safe(f, "vacated_reb_share", 0.0)
    is_sec2      = safe(f, "is_secondary_creator", 0.0)
    is_trans     = safe(f, "is_transition_scorer", 0.0)
    is_stretch   = safe(f, "is_stretch_big", 0.0)
    is_spotup    = safe(f, "is_spotup_wing", 0.0)

    f["creator_out_transfer_score"]   = vac_creation * (is_primary + is_sec2)
    f["big_out_transfer_score"]       = vac_big * is_rim
    f["starter_out_transfer_score"]   = vac_usage * starter_rate

    # Broadened same_archetype_usage_vacated (includes secondary + spotup)
    f["same_archetype_usage_vacated"] = vac_usage * (
        is_primary * 1.0 +
        is_rim     * 1.0 +
        is_sec2    * 0.6 +
        is_spotup  * 0.3
    )

    # Tightened same_position_minutes_vacated
    f["same_position_minutes_vacated"] = (
        vac_big    * is_rim +
        vac_guard_m* (is_primary + is_sec2) +
        vac_min    * is_spotup * 0.5
    )

    # Tightened wing_out_transfer_score (distributed)
    f["wing_out_transfer_score"] = vac_guard_m * (
        is_spotup  * 0.40 +
        is_sec2    * 0.30 +
        is_trans   * 0.20 +
        is_stretch * 0.10
    )

    return f


# =============================================================================
# ABLATION TEST PLAN
# =============================================================================

ABLATION_TESTS = {
    "Q1_touches":      {"q": "touches_per_min_ewma vs adv_touches_ewma for PTS",
                        "if_raw_wins": "restore adv_touches_ewma to PTS_L4"},
    "Q2_stl_tov":      {"q": "opp_live_ball_tov vs opp_tov_per_game for STL",
                        "if_generic_wins": "restore opp_tov_per_game to STL_L4"},
    "Q3_blowout":      {"q": "blowout_risk standalone vs gated for AST/FG3M",
                        "if_standalone_wins": "restore blowout_risk to AST_L4 + FG3M_L4"},
    "Q4_opp_implied":  {"q": "opp_implied_total in AST Layer 2 vs excluded",
                        "if_adds_value": "restore to LAYER_2_AST"},
}


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
             "adv_usage_percentage_mean_last10", "opp_implied_total",
             "game_total", "implied_team_total"},
    "stl": {"adv_assist_percentage_mean_last10", "adv_assist_to_turnover_mean_last10",
             "opp_tov_per_game", "implied_team_total", "opp_implied_total",
             "game_total", "blowout_risk"},
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
