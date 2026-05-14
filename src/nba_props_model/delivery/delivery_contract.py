"""Single source of truth for daily `deliveries/<DATE>/` layout (M8.8).

Run modes describe *evaluation / publication intent* for downstream
consumers. They map to existing pipeline `--mode` values in
`scripts/run_daily_delivery_pipeline.py` via ``PIPELINE_MODE_BY_RUN_MODE``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


DELIVERY_CONTRACT_VERSION = "1.0.0"


class RunMode(str, Enum):
    """Consumer-facing run mode (M8.8)."""

    MORNING_EXPECTED = "morning_expected"
    T25 = "t25"
    T5 = "t5"
    FINAL_AFTER_GAME = "final_after_game"
    BACKTEST = "backtest"


class FilePresence(str, Enum):
    """Whether a path must exist on disk for a given run mode."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    PENDING_MANIFEST_OK = "pending_manifest_ok"  # explicit placeholder JSON allowed
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class DeliveryFileSpec:
    """One deliverable path relative to ``deliveries/<DATE>/``."""

    relative_path: str
    presence: dict[RunMode, FilePresence]
    required_columns: tuple[str, ...] = ()
    nullable_columns: tuple[str, ...] = ()
    allowed_missing_reason_column: str | None = "unavailable_reason"
    min_rows: int | None = None
    formats: tuple[str, ...] = ("parquet",)  # hint for audit


def _p(p: FilePresence) -> dict[RunMode, FilePresence]:
    """Shorthand: same presence for all modes."""

    return {m: p for m in RunMode}


def _morning_optional_derek() -> dict[RunMode, FilePresence]:
    """WoO-first morning run may omit Derek until near-tip pipeline."""

    out = {m: FilePresence.REQUIRED for m in RunMode}
    out[RunMode.MORNING_EXPECTED] = FilePresence.OPTIONAL
    out[RunMode.BACKTEST] = FilePresence.OPTIONAL
    return out


def _after_game_presence() -> dict[RunMode, FilePresence]:
    """Scored bundle is required only when status says scored; otherwise explicit pending JSON."""

    return {m: FilePresence.PENDING_MANIFEST_OK for m in RunMode}


# Canonical MODEL_ONLY uses a narrower schema than WoO edge tables.
_CANONICAL_MODEL_ONLY_MIN = (
    "player_id",
    "player_name",
    "stat",
    "pmf_active",
    "pmf_source",
)
# WoO / review wide tables share the Phase-10C delivery row shape.
_WOO_ROW_CORE = (
    "player_name",
    "player_id",
    "team",
    "opponent",
    "game_id",
    "stat",
    "pmf_valid",
    "mean",
    "model_p_over",
    "role_bucket",
    "snapshot_type",
    "snapshot_time_utc",
    "market_coverage_status",
    "tov_status",
)
_WOO_EDGE_CORE = _WOO_ROW_CORE + (
    "line",
    "book",
    "fair_over_odds_american",
    "fair_under_odds_american",
    "edge",
)
_OUTCOME_LEVEL_LONG = (
    "player_id",
    "stat",
    "k",
    "p_k",
    "pmf_valid",
    "snapshot_type",
    "snapshot_time_utc",
)


# Derek M8.8 unified forward feed (written by ``build_derek_forward_feed``).
DEREK_UNIFIED_REQUIRED_COLUMNS: tuple[str, ...] = (
    "game_date",
    "run_date",
    "run_id",
    "run_mode",
    "generated_at_utc",
    "pipeline_version",
    "model_version",
    "model_artifact_hash",
    "source_data_asof_utc",
    "player_id",
    "player_name",
    "team",
    "opponent",
    "game_id",
    "event_id",
    "stat",
    "line",
    "role_bucket",
    "projected_minutes",
    "minutes_q10",
    "minutes_q50",
    "minutes_q90",
    "inactive_risk",
    "expected_lineup_status",
    "official_lineup_status",
    "injury_status",
    "injury_source",
    "injury_last_updated_utc",
    "lineup_source",
    "lineup_last_updated_utc",
    "stale_injury_flag",
    "stale_lineup_flag",
    "model_prob_over_raw",
    "model_prob_over_active",
    "model_prob_under_active",
    "fair_over_odds",
    "fair_under_odds",
    "pmf_mean",
    "pmf_variance",
    "pmf_p10",
    "pmf_p50",
    "pmf_p90",
    "market_prob_over",
    "no_vig_market_prob_over",
    "edge",
    "market_status",
    "delivery_status",
    "unavailable_reason",
    "calculation_source",
    "calculation_status",
)


def delivery_file_specs() -> tuple[DeliveryFileSpec, ...]:
    """Return the frozen delivery manifest for audits and printers."""

    return (
        DeliveryFileSpec(
            "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_CANONICAL_MODEL_ONLY_MIN,
        ),
        DeliveryFileSpec(
            "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv",
            _p(FilePresence.REQUIRED),
            required_columns=_CANONICAL_MODEL_ONLY_MIN,
        ),
        DeliveryFileSpec(
            "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.jsonl",
            _p(FilePresence.REQUIRED),
            required_columns=_CANONICAL_MODEL_ONLY_MIN,
        ),
        DeliveryFileSpec(
            "canonical_source/all_props_model_only.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_CANONICAL_MODEL_ONLY_MIN,
        ),
        DeliveryFileSpec(
            "canonical_source/manifest.json",
            _p(FilePresence.REQUIRED),
        ),
        DeliveryFileSpec(
            "wizard_of_odds/fair_odds_board.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_EDGE_CORE,
        ),
        DeliveryFileSpec(
            "wizard_of_odds/fair_odds_board.csv",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_EDGE_CORE,
        ),
        DeliveryFileSpec(
            "wizard_of_odds/fair_odds_board.jsonl",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_EDGE_CORE,
        ),
        DeliveryFileSpec(
            "wizard_of_odds/full_pmfs_outcome_level.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_OUTCOME_LEVEL_LONG,
        ),
        DeliveryFileSpec(
            "wizard_of_odds/full_pmfs_outcome_level.csv",
            _p(FilePresence.REQUIRED),
            required_columns=_OUTCOME_LEVEL_LONG,
        ),
        DeliveryFileSpec(
            "wizard_of_odds/full_pmfs_wide.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_ROW_CORE + ("pmf_json",),
        ),
        DeliveryFileSpec(
            "wizard_of_odds/full_pmfs_wide.csv",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_ROW_CORE + ("pmf_json",),
        ),
        DeliveryFileSpec(
            "wizard_of_odds/market_comparison.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_EDGE_CORE,
        ),
        DeliveryFileSpec(
            "wizard_of_odds/market_comparison.csv",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_EDGE_CORE,
        ),
        DeliveryFileSpec(
            "wizard_of_odds/publishable_edges.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_EDGE_CORE,
        ),
        DeliveryFileSpec(
            "wizard_of_odds/publishable_edges.csv",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_EDGE_CORE,
        ),
        DeliveryFileSpec(
            "wizard_of_odds/run_manifest.json",
            _p(FilePresence.REQUIRED),
        ),
        DeliveryFileSpec(
            "wizard_of_odds/count_diagnostics.json",
            _p(FilePresence.REQUIRED),
        ),
        DeliveryFileSpec(
            "pmf_model_review_package/04_PROP_SUMMARY.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=("player_id", "stat", "mean"),
        ),
        DeliveryFileSpec(
            "pmf_model_review_package/04_PROP_SUMMARY.csv",
            _p(FilePresence.REQUIRED),
            required_columns=("player_id", "stat", "mean"),
        ),
        DeliveryFileSpec(
            "pmf_model_review_package/05_FULL_PMF_WIDE.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_ROW_CORE + ("pmf_json",),
        ),
        DeliveryFileSpec(
            "pmf_model_review_package/05_FULL_PMF_WIDE.csv",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_ROW_CORE + ("pmf_json",),
        ),
        DeliveryFileSpec(
            "pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_OUTCOME_LEVEL_LONG,
        ),
        DeliveryFileSpec(
            "pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv",
            _p(FilePresence.REQUIRED),
            required_columns=_OUTCOME_LEVEL_LONG,
        ),
        DeliveryFileSpec(
            "pmf_model_review_package/machine_readable/model_only.parquet",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_ROW_CORE + ("pmf_json",),
        ),
        DeliveryFileSpec(
            "pmf_model_review_package/machine_readable/model_only.csv",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_ROW_CORE + ("pmf_json",),
        ),
        DeliveryFileSpec(
            "pmf_model_review_package/machine_readable/model_only.jsonl",
            _p(FilePresence.REQUIRED),
            required_columns=_WOO_ROW_CORE + ("pmf_json",),
        ),
        *tuple(
            DeliveryFileSpec(
                f"pmf_model_review_package/{name}",
                _p(FilePresence.REQUIRED),
            )
            for name in (
                "01_START_HERE.html",
                "02_MODEL_REVIEW_OVERVIEW.html",
                "03_PMF_DISTRIBUTION_VIEWER.html",
                "MODEL_PERFORMANCE_AND_CALIBRATION.md",
                "README.md",
            )
        ),
        DeliveryFileSpec(
            "derek_forward_feed/feed_manifest.json",
            _morning_optional_derek(),
        ),
        DeliveryFileSpec(
            "derek_forward_feed/derek_forward_feed.parquet",
            {
                RunMode.MORNING_EXPECTED: FilePresence.OPTIONAL,
                RunMode.T25: FilePresence.REQUIRED,
                RunMode.T5: FilePresence.REQUIRED,
                RunMode.FINAL_AFTER_GAME: FilePresence.OPTIONAL,
                RunMode.BACKTEST: FilePresence.OPTIONAL,
            },
            required_columns=DEREK_UNIFIED_REQUIRED_COLUMNS,
            min_rows=1,
        ),
        DeliveryFileSpec(
            "derek_forward_feed/derek_forward_feed.csv",
            {
                RunMode.MORNING_EXPECTED: FilePresence.OPTIONAL,
                RunMode.T25: FilePresence.REQUIRED,
                RunMode.T5: FilePresence.REQUIRED,
                RunMode.FINAL_AFTER_GAME: FilePresence.OPTIONAL,
                RunMode.BACKTEST: FilePresence.OPTIONAL,
            },
            required_columns=DEREK_UNIFIED_REQUIRED_COLUMNS,
            min_rows=1,
        ),
        DeliveryFileSpec(
            "derek_forward_feed/derek_forward_feed.jsonl",
            {
                RunMode.MORNING_EXPECTED: FilePresence.OPTIONAL,
                RunMode.T25: FilePresence.REQUIRED,
                RunMode.T5: FilePresence.REQUIRED,
                RunMode.FINAL_AFTER_GAME: FilePresence.OPTIONAL,
                RunMode.BACKTEST: FilePresence.OPTIONAL,
            },
            required_columns=DEREK_UNIFIED_REQUIRED_COLUMNS,
            min_rows=1,
        ),
        DeliveryFileSpec(
            "derek_forward_feed/manifest.json",
            {
                RunMode.MORNING_EXPECTED: FilePresence.OPTIONAL,
                RunMode.T25: FilePresence.REQUIRED,
                RunMode.T5: FilePresence.REQUIRED,
                RunMode.FINAL_AFTER_GAME: FilePresence.OPTIONAL,
                RunMode.BACKTEST: FilePresence.OPTIONAL,
            },
        ),
        DeliveryFileSpec(
            "after_game_scoring/after_game_scoring.parquet",
            _after_game_presence(),
            required_columns=("player_id", "game_id", "stat"),
        ),
        DeliveryFileSpec(
            "after_game_scoring/after_game_scoring.csv",
            _after_game_presence(),
            required_columns=("player_id", "game_id", "stat"),
        ),
        DeliveryFileSpec(
            "after_game_scoring/after_game_status.json",
            {m: FilePresence.PENDING_MANIFEST_OK for m in RunMode},
        ),
        DeliveryFileSpec(
            "after_game_scoring/scored_props.parquet",
            _p(FilePresence.OPTIONAL),
            required_columns=("player_id", "game_id", "stat"),
        ),
        DeliveryFileSpec(
            "after_game_scoring/scored_props.csv",
            _p(FilePresence.OPTIONAL),
        ),
        DeliveryFileSpec(
            "after_game_scoring/scored_props.jsonl",
            _p(FilePresence.OPTIONAL),
        ),
        DeliveryFileSpec(
            "after_game_scoring/manifest.json",
            _p(FilePresence.OPTIONAL),
        ),
        DeliveryFileSpec(
            "after_game_scoring/after_game_scoring_placeholder_manifest.json",
            {
                RunMode.MORNING_EXPECTED: FilePresence.OPTIONAL,
                RunMode.T25: FilePresence.OPTIONAL,
                RunMode.T5: FilePresence.OPTIONAL,
                RunMode.FINAL_AFTER_GAME: FilePresence.OPTIONAL,
                RunMode.BACKTEST: FilePresence.OPTIONAL,
            },
        ),
    )


PIPELINE_MODE_BY_RUN_MODE: dict[RunMode, str] = {
    RunMode.MORNING_EXPECTED: "woo_morning_monetization",
    RunMode.T25: "derek_near_lineup",
    RunMode.T5: "close_lock",
    RunMode.FINAL_AFTER_GAME: "after_game",
    RunMode.BACKTEST: "woo_morning_monetization",
}


def banned_placeholder_tokens() -> tuple[str, ...]:
    """Substrings that must not appear in critical string cells."""

    return (
        "tbd",
        "generated_by_llm",
        "hallucinated",
        "dummy",
        "placeholder",
        "fake",
        "lorem",
        "test_player",
        "manual_fill",
    )


def explicit_status_tokens() -> frozenset[str]:
    """Allowed status literals when paired with ``unavailable_reason``."""

    return frozenset(
        {
            "not_available_yet",
            "pending_actuals",
            "no_offered_market",
            "source_unavailable",
            "not_applicable_for_run_mode",
        }
    )


def infer_run_mode_for_delivery_date(repo_root: Path, delivery_date: str) -> RunMode:
    """Infer the strictest consumer run mode represented by on-disk artifacts."""

    root = repo_root / "deliveries" / delivery_date
    scored = root / "after_game_scoring" / "after_game_scoring.parquet"
    if scored.is_file():
        try:
            import pandas as pd

            df = pd.read_parquet(scored, columns=["player_id"])
            if len(df) > 0:
                return RunMode.FINAL_AFTER_GAME
        except Exception:
            pass
    alt = root / "after_game_scoring" / "scored_props.parquet"
    if alt.is_file():
        try:
            import pandas as pd

            df = pd.read_parquet(alt, columns=["player_id"])
            if len(df) > 0:
                return RunMode.FINAL_AFTER_GAME
        except Exception:
            pass

    rm_path = root / "wizard_of_odds" / "run_manifest.json"
    if rm_path.is_file():
        try:
            rm = json.loads(rm_path.read_text(encoding="utf-8"))
        except Exception:
            rm = {}
        snap = str(rm.get("snapshot_type") or "").lower()
        if snap in {"pre_close", "lineup"}:
            return RunMode.T25
        if snap == "close_lock":
            return RunMode.T5
        if snap == "morning":
            return RunMode.MORNING_EXPECTED

    return RunMode.BACKTEST


def assert_contract_coherent() -> None:
    """Internal integrity check (used from tests)."""

    for spec in delivery_file_specs():
        for mode, pres in spec.presence.items():
            if pres == FilePresence.NOT_APPLICABLE and spec.required_columns:
                raise AssertionError(f"Inconsistent spec for {spec.relative_path} mode={mode}")
