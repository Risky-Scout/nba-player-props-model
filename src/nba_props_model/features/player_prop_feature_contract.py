"""M8.9 as-of-safe feature contract for player-prop PMF modeling."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


FEATURE_CONTRACT_VERSION = "1.0.0"


class RunMode(str, Enum):
    MORNING_EXPECTED = "morning_expected"
    T25 = "t25"
    T5 = "t5"
    FINAL_AFTER_GAME = "final_after_game"
    BACKTEST = "backtest"


class LeakageStatus(str, Enum):
    SAFE = "safe"
    MARKET_RESIDUAL_ONLY = "market_residual_only"
    FORBIDDEN_MODEL_ONLY = "forbidden_model_only"


ALL_STATS = (
    "pts",
    "reb",
    "ast",
    "fg3m",
    "tov",
    "stl",
    "blk",
    "stocks",
    "pa",
    "pr",
    "ra",
    "pra",
)


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    nullable: bool = False
    fallback_behavior: str = "explicit_unavailable_reason"
    diagnostics_exposed: bool = True


@dataclass(frozen=True)
class FeatureFamily:
    name: str
    source: str
    asof_column: str
    allowed_run_modes: tuple[RunMode, ...]
    leakage_status: LeakageStatus
    stat_applicability: tuple[str, ...]
    unavailable_status_column: str
    unavailable_reason_column: str
    features: tuple[FeatureSpec, ...]


def _all_modes() -> tuple[RunMode, ...]:
    return tuple(RunMode)


def _all_stats() -> tuple[str, ...]:
    return ALL_STATS


def _f(names: tuple[str, ...], nullable: tuple[str, ...] = ()) -> tuple[FeatureSpec, ...]:
    out: list[FeatureSpec] = []
    nullable_set = set(nullable)
    for n in names:
        out.append(FeatureSpec(name=n, nullable=n in nullable_set))
    return tuple(out)


IDENTITY_FEATURES = (
    "game_date",
    "run_date",
    "run_id",
    "run_mode",
    "generated_at_utc",
    "source_data_asof_utc",
    "player_id",
    "player_name",
    "team",
    "opponent",
    "game_id",
    "event_id",
    "stat",
    "role_bucket",
    "model_version",
    "feature_contract_version",
    "feature_snapshot_id",
)

INJURY_AVAILABILITY_FEATURES = (
    "injury_status_current",
    "injury_status_previous",
    "injury_status_changed_since_morning",
    "injury_source",
    "injury_report_asof_utc",
    "injury_last_updated_utc",
    "injury_freshness_minutes",
    "injury_freshness_status",
    "stale_injury_flag",
    "prob_active_current",
    "prob_active_previous",
    "prob_active_delta_since_morning",
    "inactive_risk_current",
    "inactive_risk_reason",
    "has_injury_data",
    "availability_confidence",
    "minutes_restriction_flag",
    "returning_from_injury_flag",
    "first_game_back_flag",
    "probable_flag",
    "questionable_flag",
    "doubtful_flag",
    "out_flag",
    "rest_flag",
    "personal_absence_flag",
    "coach_dnp_risk_flag",
)

TEAMMATE_AVAILABILITY_FEATURES = (
    "num_teammates_inactive",
    "num_teammates_questionable",
    "num_teammates_probable",
    "num_teammates_out_total",
    "teammates_out_usage_sum",
    "teammates_out_minutes_sum",
    "teammates_out_fga_sum",
    "high_usage_teammates_out_count",
    "primary_ballhandler_out",
    "primary_creator_out",
    "primary_rebounder_out",
    "primary_rim_protector_out",
    "top_usage_teammate_out",
    "top_assist_teammate_out",
    "top_rebound_teammate_out",
    "same_position_teammate_out",
    "starter_out_same_position",
    "starter_out_any_position",
    "teammate_out_count_guard",
    "teammate_out_count_wing",
    "teammate_out_count_big",
)

EXPECTED_LINEUP_FEATURES = (
    "expected_lineup_available",
    "expected_lineup_source",
    "expected_lineup_asof_utc",
    "expected_lineup_last_updated_utc",
    "expected_lineup_freshness_minutes",
    "expected_lineup_freshness_status",
    "expected_starter",
    "expected_bench_role",
    "expected_rotation_rank",
    "expected_lineup_confidence",
    "expected_starter_prob",
    "projected_rotation_slot",
    "projected_closing_lineup_flag",
    "projected_blowout_rotation_risk",
)

OFFICIAL_LINEUP_FEATURES = (
    "official_lineup_available",
    "official_lineup_source",
    "official_lineup_asof_utc",
    "official_lineup_last_updated_utc",
    "official_lineup_freshness_minutes",
    "official_lineup_freshness_status",
    "official_starter",
    "confirmed_starter",
    "official_lineup_status",
    "official_lineup_override_used",
    "lineup_changed_since_morning",
    "projected_to_official_role_delta",
    "expected_lineup_mislabeled_as_official_flag",
)

MINUTES_DISTRIBUTION_FEATURES = (
    "projected_minutes",
    "minutes_q05",
    "minutes_q10",
    "minutes_q25",
    "minutes_q50",
    "minutes_q75",
    "minutes_q90",
    "minutes_q95",
    "minutes_mean",
    "minutes_std",
    "minutes_floor",
    "minutes_ceiling",
    "prob_minutes_lt_10",
    "prob_minutes_10_20",
    "prob_minutes_20_30",
    "prob_minutes_30_plus",
    "prob_minutes_35_plus",
    "minutes_role_volatility",
    "minutes_projection_source",
    "minutes_model_version",
    "minutes_model_oof_quality_bucket",
    "minutes_uncertainty_reason",
)

ROLE_STATE_FEATURES = (
    "p_inactive",
    "p_fringe",
    "p_bench",
    "p_rotation",
    "p_core",
    "p_starter",
    "role_entropy",
    "role_bucket_confidence",
    "role_change_probability",
    "role_source",
    "role_source_asof_utc",
    "hard_role_bucket",
    "role_mixture_enabled",
)

USAGE_OPPORTUNITY_FEATURES = (
    "usage_projection",
    "usage_projection_source",
    "usage_proxy_current",
    "usage_proxy_last3",
    "usage_proxy_last5",
    "usage_proxy_last10",
    "usage_ewma",
    "usage_trend_3v10",
    "fga_projection",
    "fga_per_min_projection",
    "fg3a_projection",
    "assist_chance_projection",
    "rebound_chance_projection",
    "touch_projection",
    "time_of_possession_projection",
    "vacated_usage_proxy",
    "vacated_fga",
    "vacated_fg3a",
    "vacated_assist_chances",
    "vacated_rebound_chances",
    "usage_delta_without_top_creator",
    "fga_delta_without_top_scorer",
    "ast_delta_without_primary_handler",
    "reb_delta_without_starting_big",
)

TEAMMATE_ON_OFF_FEATURES = (
    "usage_with_top_usage_teammates_off",
    "fga_with_top_usage_teammates_off",
    "ast_rate_with_primary_ballhandler_off",
    "reb_rate_with_starting_center_off",
    "fg3a_rate_with_spacing_lineup",
    "points_per_min_with_high_usage_teammate_off",
    "assist_chances_with_starting_pg_out",
    "rebound_chances_with_starting_center_out",
    "minutes_with_current_projected_lineup",
    "possessions_with_current_projected_lineup",
    "on_off_sample_size",
    "on_off_shrinkage_weight",
)

SCHEDULE_CONTEXT_FEATURES = (
    "rest_days",
    "back_to_back",
    "three_in_four",
    "days_since_last_played",
    "travel_distance_proxy",
    "home_away",
    "spread_for_team",
    "consensus_total",
    "implied_team_total",
    "blowout_risk",
    "close_game_minutes_multiplier",
    "pace_projection",
    "team_possessions_projection",
    "opponent_possessions_projection",
    "total_move",
    "spread_move",
    "steam_total_up",
    "steam_total_down",
)

OPPONENT_MATCHUP_FEATURES = (
    "opponent_def_rating_recent",
    "opponent_pace_recent",
    "opp_allowed_pts_by_position",
    "opp_allowed_reb_by_position",
    "opp_allowed_ast_by_position",
    "opp_allowed_fg3m_by_position",
    "opp_allowed_stl_by_position",
    "opp_allowed_blk_by_position",
    "opp_allowed_tov_by_position",
    "opp_rebound_chances_allowed_by_position",
    "opp_assist_chances_allowed_to_primary_handlers",
    "opp_3pa_allowed",
    "opp_3p_rate_allowed",
    "opp_corner_3_allowed",
    "opp_above_break_3_allowed",
    "opp_rim_attempts_allowed",
    "opp_blockable_fga_rate",
    "opp_live_ball_turnover_rate",
    "opp_bad_pass_rate",
    "opp_steals_allowed_to_guards",
    "opp_steals_allowed_to_wings",
    "opp_blocks_allowed_to_bigs",
    "player_archetype",
    "matchup_archetype",
)

SPARSE_STAT_FEATURES = (
    "player_deflection_rate",
    "player_steal_rate_per_min",
    "player_block_rate_per_min",
    "player_contested_shot_rate",
    "player_rim_protection_role",
    "opponent_turnover_rate",
    "opponent_bad_pass_rate",
    "opponent_drive_rate",
    "opponent_blockable_attempts",
    "expected_defensive_possessions",
    "expected_steal_opportunities",
    "expected_block_opportunities",
    "sparse_p0_prior",
    "sparse_positive_tail_prior",
)

COMBO_COVARIANCE_FEATURES = (
    "cov_pts_reb_player",
    "cov_pts_ast_player",
    "cov_reb_ast_player",
    "cov_pts_reb_role",
    "cov_pts_ast_role",
    "cov_reb_ast_role",
    "cov_pts_reb_minutes_conditioned",
    "cov_pts_ast_usage_conditioned",
    "cov_reb_ast_lineup_conditioned",
    "combo_covariance_sample_size",
    "combo_covariance_shrinkage_weight",
    "combo_independence_warning_flag",
)

PMF_SHAPE_FEATURES = (
    "pmf_mean",
    "pmf_variance",
    "pmf_std",
    "pmf_skew_proxy",
    "pmf_p0",
    "pmf_p10",
    "pmf_p25",
    "pmf_p50",
    "pmf_p75",
    "pmf_p90",
    "pmf_p95",
    "pmf_tail_ge_1",
    "pmf_tail_ge_2",
    "pmf_tail_ge_3",
    "pmf_valid",
    "pmf_sum",
    "pmf_support_min",
    "pmf_support_max",
    "pmf_shape_source",
    "pmf_repair_applied_flags",
)

MARKET_FEATURES = (
    "market_prob_over",
    "no_vig_market_prob_over",
    "market_line",
    "book_count",
    "line_dispersion",
    "market_width",
    "open_to_close_delta",
    "alternate_line_slope",
    "market_snapshot_age_minutes",
)


def feature_families() -> tuple[FeatureFamily, ...]:
    return (
        FeatureFamily(
            name="identity_metadata",
            source="pipeline_runtime_and_slate",
            asof_column="generated_at_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="identity_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(IDENTITY_FEATURES, nullable=("event_id",)),
        ),
        FeatureFamily(
            name="injury_availability",
            source="player_availability_asof",
            asof_column="injury_report_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="injury_freshness_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(INJURY_AVAILABILITY_FEATURES),
        ),
        FeatureFamily(
            name="teammate_availability",
            source="availability_and_roster_context",
            asof_column="source_data_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="teammate_availability_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(TEAMMATE_AVAILABILITY_FEATURES),
        ),
        FeatureFamily(
            name="expected_lineup",
            source="expected_lineup_provider",
            asof_column="expected_lineup_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="expected_lineup_freshness_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(EXPECTED_LINEUP_FEATURES),
        ),
        FeatureFamily(
            name="official_lineup",
            source="official_lineup_provider",
            asof_column="official_lineup_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="official_lineup_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(OFFICIAL_LINEUP_FEATURES),
        ),
        FeatureFamily(
            name="minutes_distribution",
            source="minutes_model_and_context",
            asof_column="source_data_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="minutes_feature_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(MINUTES_DISTRIBUTION_FEATURES),
        ),
        FeatureFamily(
            name="role_state",
            source="role_state_model",
            asof_column="role_source_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="role_state_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(ROLE_STATE_FEATURES),
        ),
        FeatureFamily(
            name="usage_opportunity",
            source="usage_projection_builder",
            asof_column="source_data_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=("pts", "reb", "ast", "fg3m", "tov", "pa", "pr", "ra", "pra"),
            unavailable_status_column="usage_feature_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(USAGE_OPPORTUNITY_FEATURES, nullable=("time_of_possession_projection",)),
        ),
        FeatureFamily(
            name="teammate_on_off",
            source="historical_on_off_splits",
            asof_column="source_data_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="teammate_on_off_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(TEAMMATE_ON_OFF_FEATURES),
        ),
        FeatureFamily(
            name="schedule_context",
            source="schedule_and_market_context",
            asof_column="source_data_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="schedule_context_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(SCHEDULE_CONTEXT_FEATURES, nullable=("travel_distance_proxy",)),
        ),
        FeatureFamily(
            name="opponent_matchup",
            source="opponent_rolling_profile",
            asof_column="source_data_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="opponent_matchup_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(OPPONENT_MATCHUP_FEATURES),
        ),
        FeatureFamily(
            name="sparse_stat_opportunity",
            source="sparse_stat_builder",
            asof_column="source_data_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=("stl", "blk", "stocks"),
            unavailable_status_column="sparse_feature_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(SPARSE_STAT_FEATURES),
        ),
        FeatureFamily(
            name="combo_covariance",
            source="combo_covariance_builder",
            asof_column="source_data_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=("pa", "pr", "ra", "pra"),
            unavailable_status_column="combo_covariance_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(COMBO_COVARIANCE_FEATURES),
        ),
        FeatureFamily(
            name="pmf_shape",
            source="pmf_model_outputs",
            asof_column="generated_at_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.SAFE,
            stat_applicability=_all_stats(),
            unavailable_status_column="pmf_shape_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(PMF_SHAPE_FEATURES),
        ),
        FeatureFamily(
            name="market_residual_only",
            source="odds_market_snapshots",
            asof_column="source_data_asof_utc",
            allowed_run_modes=_all_modes(),
            leakage_status=LeakageStatus.MARKET_RESIDUAL_ONLY,
            stat_applicability=_all_stats(),
            unavailable_status_column="market_feature_status",
            unavailable_reason_column="unavailable_reason",
            features=_f(MARKET_FEATURES),
        ),
    )


def all_feature_names() -> tuple[str, ...]:
    out: list[str] = []
    for fam in feature_families():
        out.extend(f.name for f in fam.features)
    return tuple(out)


def model_only_feature_names() -> tuple[str, ...]:
    out: list[str] = []
    for fam in feature_families():
        if fam.leakage_status == LeakageStatus.SAFE:
            out.extend(f.name for f in fam.features)
    return tuple(out)


def forbidden_model_only_training_features() -> tuple[str, ...]:
    return MARKET_FEATURES


def explicit_unavailable_statuses() -> frozenset[str]:
    return frozenset(
        {
            "not_available_yet",
            "source_unavailable",
            "not_applicable_for_run_mode",
            "pending_actuals",
            "missing_source_snapshot",
        }
    )


def assert_feature_contract_coherent() -> None:
    seen: set[str] = set()
    for fam in feature_families():
        if not fam.features:
            raise AssertionError(f"Feature family has no features: {fam.name}")
        if not fam.allowed_run_modes:
            raise AssertionError(f"Feature family has no run modes: {fam.name}")
        for feat in fam.features:
            if feat.name in seen:
                raise AssertionError(f"Duplicate feature name: {feat.name}")
            seen.add(feat.name)

    model_only = set(model_only_feature_names())
    forbidden = set(forbidden_model_only_training_features())
    overlap = model_only.intersection(forbidden)
    if overlap:
        raise AssertionError(f"Model-only features include forbidden market columns: {sorted(overlap)}")
