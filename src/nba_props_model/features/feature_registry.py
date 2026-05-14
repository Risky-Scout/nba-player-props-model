"""Prediction-time feature registry (M8.6 Phase D — minimal v0).

Rows describe intended contract; many features are not yet materialized in
`build_player_feature_store.py`.  See `inference_allowed` and `training_only`.
"""
from __future__ import annotations

FEATURE_REGISTRY_VERSION = "0.1.0"

# Columns emitted by build_player_feature_store.py for close_lock (subset).
FEATURE_STORE_CLOSE_LOCK_COLUMNS = (
    "player_id",
    "player_name",
    "game_id",
    "game",
    "is_home",
    "team_id",
    "opp_team_id",
    "role_bucket",
    "role_source",
    "mp_bucket",
    "usage_bucket",
    "minutes_mean",
    "minutes_q50",
    "p_inactive_used",
    "injury_freshness_status",
    "injury_context_source",
    "injury_report_fetched_at_utc",
    "availability_table_freshness",
    "availability_table_age_hours",
    "suppress_inactive_risk",
    "availability_blocks_market_superiority",
    "stat",
    "feature_store_version",
    "snapshot",
    "game_context_as_of_utc",
)

FEATURE_REGISTRY: list[dict] = [
    {
        "feature_name": "minutes_mean",
        "feature_group": "player_recent_form",
        "source": "stat_grid_pmfs",
        "as_of_column": "injury_report_fetched_at_utc",
        "allowed_snapshots": ("morning", "close_lock"),
        "training_only": False,
        "inference_allowed": True,
        "can_use_market_context": False,
        "leakage_risk": "low",
        "missing_policy": "allow_null",
        "dtype": "float64",
        "description": "Projected mean minutes (model path in stat_grid).",
    },
    {
        "feature_name": "minutes_q50",
        "feature_group": "player_recent_form",
        "source": "stat_grid_pmfs",
        "as_of_column": "injury_report_fetched_at_utc",
        "allowed_snapshots": ("morning", "close_lock"),
        "training_only": False,
        "inference_allowed": True,
        "can_use_market_context": False,
        "leakage_risk": "low",
        "missing_policy": "allow_null",
        "dtype": "float64",
        "description": "Median minutes projection.",
    },
    {
        "feature_name": "availability_table_freshness",
        "feature_group": "availability_role",
        "source": "availability_guard",
        "as_of_column": "availability_table_age_hours",
        "allowed_snapshots": ("morning", "close_lock"),
        "training_only": False,
        "inference_allowed": True,
        "can_use_market_context": False,
        "leakage_risk": "medium",
        "missing_policy": "stale_flag",
        "dtype": "string",
        "description": "Freshness label from availability table build.",
    },
    {
        "feature_name": "suppress_inactive_risk",
        "feature_group": "availability_role",
        "source": "availability_guard",
        "as_of_column": "injury_report_fetched_at_utc",
        "allowed_snapshots": ("morning", "close_lock"),
        "training_only": False,
        "inference_allowed": True,
        "can_use_market_context": False,
        "leakage_risk": "medium",
        "missing_policy": "false_default",
        "dtype": "bool",
        "description": "Whether inactive-risk PMF path is suppressed due to stale guard.",
    },
    {
        "feature_name": "game_id",
        "feature_group": "game_context",
        "source": "schedule",
        "as_of_column": "static",
        "allowed_snapshots": ("morning", "close_lock"),
        "training_only": False,
        "inference_allowed": True,
        "can_use_market_context": False,
        "leakage_risk": "low",
        "missing_policy": "fail",
        "dtype": "int64",
        "description": "Internal game identifier.",
    },
]


def iter_registry():
    return iter(FEATURE_REGISTRY)
