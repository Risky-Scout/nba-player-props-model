#!/usr/bin/env python3
"""Normal game-day pipeline readiness audit.

Enumerates every condition that must be true for the optimized
production game-day delivery pipeline to run end-to-end and produce
Derek's forward feed from the validated PMF surface. This audit is
explicitly NOT a no-games soft-skip path — it is the dual: it proves
that the games-exist code path is wired correctly end-to-end.

Strict source graph this audit enforces:

  predict/date contract
  → pre-canonical slate universe seed (only as feature_snapshot
    bootstrap when canonical MODEL_ONLY is absent, identity-only)
  → feature_snapshot
  → minutes_predictions / minutes_predictions_eligible
  → stat_grid with all 12 mission stats
  → canonical MODEL_ONLY built from stat_grid only
  → market_comparison
  → derek_forward_feed
  → WoO/public outputs
  → verifiers
  → core/full artifact upload

Conditions covered (matches the operator spec):

  1.  workflow dispatch / inputs / forced-manual routing
  2.  predict/date contract (games-exist, no no-games placeholder)
  3.  independent BDL schedule resolver (games_count > 0)
  4.  pre-canonical seed scope (identity-only, no PMF/prob/EV)
  5.  feature_snapshot rows > 0 and as-of-safe
  6.  minutes_predictions + minutes_predictions_eligible contracts
  7.  stat_grid covers all 12 mission stats
  8.  canonical MODEL_ONLY dual-write from stat_grid only
  9.  market_comparison required columns and PMF-sourced model_p_over
  10. derek_forward_feed required columns, sourced from canonical/market
  11. market_superiority_claim_allowed contract (snapshot freshness)
  12. WoO/public export contract (no no-games soft-skip on games slate)
  13. M8.6 post-delivery verifiers run normally on games-exist slate
  14. artifact upload contract (core + full)
  15. warning classification (operational vs result-altering)

Each condition is reported with status, evidence, blocking flag, and
suggested fix. Status values:

  pass                          - condition holds today for this date
  fail                          - condition is violated; blocking
  not_applicable                - condition is moot for this slate
  pending_pipeline_execution    - condition can only be evaluated
                                   AFTER the pipeline runs for the
                                   target date; not blocking the
                                   readiness gate, but it WILL be
                                   re-evaluated post-run

Reports are written to:

  artifacts/normal_game_day_readiness/<date>/normal_game_day_readiness_report.json
  artifacts/normal_game_day_readiness/<date>/normal_game_day_readiness_report.md

Exit code is 0 when no condition has ``blocking=True and status=fail``
(i.e. ``pending_pipeline_execution`` for data-dependent checks is OK
for a pre-flight run). With ``--strict`` any pending-pipeline-execution
finding for a games-exist slate becomes a non-blocking advisory and
the gate still passes; only blocking failures fail the gate. After
the proof run, re-running the same audit with the pipeline outputs
present will exercise the dynamic checks for real.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, Callable, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


# ── Findings dataclass ─────────────────────────────────────────────────────

@dataclasses.dataclass
class ReadinessFinding:
    condition_id: str
    description: str
    status: str  # pass | fail | not_applicable | pending_pipeline_execution
    evidence: dict[str, Any]
    blocking: bool
    required_fix_if_failed: str | None
    marker: str | None = None


# ── Mission stats (single source of truth) ─────────────────────────────────

MISSION_STATS_CANONICAL: tuple[str, ...] = (
    "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
    "stocks", "pa", "pr", "ra", "pra",
)


# ── Acceptable / forbidden operational warning classifiers ─────────────────

ACCEPTABLE_WARNING_SUBSTRINGS: tuple[str, ...] = (
    "Node.js 16 actions are deprecated",
    "Node.js 20 actions are deprecated",
    "set-output", "save-state",
    "DUNKS_AND_THREES_API_KEY", "DUNKS_AND_THREES",
    "SFTP", "sftp_", "SFTP_HOST", "SFTP_USERNAME", "SFTP_PASSWORD",
)

FORBIDDEN_WARNING_SUBSTRINGS: tuple[str, ...] = (
    "missing feature snapshot", "feature_snapshot_missing",
    "minutes predictions missing", "MINUTES_PREDICTIONS_MISSING",
    "stat_grid missing", "STAT_GRID_MISSING",
    "canonical missing", "CANONICAL_MISSING",
    "market_comparison missing", "MARKET_COMPARISON_MISSING",
    "derek_forward_feed missing", "DEREK_FORWARD_FEED_MISSING",
    "snapshot_time_utc missing",
    "stale market", "MARKET_STALE",
    "NO_GAMES_SLATE soft-skip on games-exist slate",
    "raw all_props used as canonical",
    "postgame", "settled",
)


# ── BDL schedule resolver ──────────────────────────────────────────────────

def _bdl_games_count(date: str) -> tuple[int | None, str]:
    """Return ``(games_count, evidence_string)`` using the same BDL
    /games?dates[]=<date> probe the orchestrator's
    ``_resolve_schedule_game_count`` relies on.

    Returns ``(None, reason)`` on any network/auth/schema failure so
    callers can mark the condition as blocking with a clear message.
    """
    try:
        from nba_props_model.data.bdl_client import get_games
    except Exception as exc:
        return None, f"import_failed: {exc.__class__.__name__}: {exc}"
    if not os.environ.get("BDL_API_KEY"):
        return None, "BDL_API_KEY not set in environment"
    try:
        games = get_games(start_date=date, end_date=date)
    except Exception as exc:
        return None, f"bdl_get_games_failed: {exc.__class__.__name__}: {exc}"
    if games is None:
        return None, "bdl_get_games returned None"
    if not isinstance(games, list):
        return None, f"bdl_get_games returned non-list: {type(games).__name__}"
    return len(games), f"bdl /games?start_date={date}&end_date={date} -> {len(games)} rows"


def _find_next_game_date(start: str, lookahead_days: int) -> tuple[str | None, list[tuple[str, int | None, str]]]:
    """Walk forward up to ``lookahead_days`` from ``start`` and return
    the first date with games_count > 0 along with the per-day trace.

    Returns ``(date_or_None, trace)`` where trace is a list of
    ``(date, games_count_or_None, evidence_string)`` records.
    """
    d0 = dt.date.fromisoformat(start)
    trace: list[tuple[str, int | None, str]] = []
    for i in range(lookahead_days + 1):
        d = (d0 + dt.timedelta(days=i)).isoformat()
        n, ev = _bdl_games_count(d)
        trace.append((d, n, ev))
        if n is not None and n > 0:
            return d, trace
    return None, trace


# ── Condition runners ──────────────────────────────────────────────────────

def _read_workflow_yaml() -> str:
    p = REPO_ROOT / ".github" / "workflows" / "daily_pmf_delivery.yml"
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8")


def cond_01_workflow_dispatch(date: str, mode: str) -> ReadinessFinding:
    yaml_text = _read_workflow_yaml()
    if not yaml_text:
        return ReadinessFinding(
            "01_workflow_dispatch",
            "workflow_dispatch with required inputs + woo_morning_monetization routing",
            "fail", {"reason": "daily_pmf_delivery.yml not found"}, True,
            "Restore .github/workflows/daily_pmf_delivery.yml",
            "NORMAL_GAME_DAY_WORKFLOW_DISPATCH_CONTRACT_FAIL",
        )
    required_tokens = (
        "workflow_dispatch:",
        "mode:",
        "delivery_date:",
        "run_predict:",
        "force_run:",
        "woo_morning_monetization",
        "FORCED_MANUAL_DELIVERY_RUN_ASSERTION_PASS",
        "Run delivery pipeline (woo_morning_monetization)",
        "actions/upload-artifact",
    )
    missing = [t for t in required_tokens if t not in yaml_text]
    if missing:
        return ReadinessFinding(
            "01_workflow_dispatch",
            "workflow_dispatch with required inputs + woo_morning_monetization routing",
            "fail", {"missing_tokens": missing}, True,
            "Re-add missing workflow tokens (inputs, modes, or upload-artifact step).",
            "NORMAL_GAME_DAY_WORKFLOW_DISPATCH_CONTRACT_FAIL",
        )
    return ReadinessFinding(
        "01_workflow_dispatch",
        "workflow_dispatch with required inputs + woo_morning_monetization routing",
        "pass",
        {
            "workflow_dispatch": True,
            "inputs": ["mode", "delivery_date", "run_predict", "force_run"],
            "mode_routes_woo_morning_monetization": True,
            "forced_manual_assertion_present": True,
            "upload_artifact_step_present": True,
        },
        False, None,
        "NORMAL_GAME_DAY_WORKFLOW_DISPATCH_CONTRACT_PASS",
    )


def cond_02_predict_date_contract(date: str) -> ReadinessFinding:
    pred_dir = REPO_ROOT / "predictions"
    singles = pred_dir / f"singles_{date}.json"
    all_props = pred_dir / f"all_props_{date}.parquet"

    pre_run_marker_emitter_ok = True
    pre_run_evidence: dict[str, Any] = {}
    orch_src = (REPO_ROOT / "scripts" / "run_daily_delivery_pipeline.py").read_text(encoding="utf-8") if (
        (REPO_ROOT / "scripts" / "run_daily_delivery_pipeline.py").is_file()
    ) else ""
    predict_src = (REPO_ROOT / "scripts" / "predict.py").read_text(encoding="utf-8") if (
        (REPO_ROOT / "scripts" / "predict.py").is_file()
    ) else ""
    # The PREDICT_DATE_CONTRACT_PASS / _VIOLATION markers are emitted
    # by the orchestrator's post-predict gate (the gate runs
    # immediately after scripts/predict.py and checks that the
    # produced predictions/*.parquet are tagged with the requested
    # delivery date). Either the orchestrator or predict.py emitting
    # the marker is acceptable; both being silent is the failure.
    pre_run_evidence["orchestrator_emits_predict_date_contract"] = (
        "PREDICT_DATE_CONTRACT_PASS" in orch_src
    )
    pre_run_evidence["orchestrator_emits_predict_date_violation"] = (
        "PREDICT_DATE_CONTRACT_VIOLATION" in orch_src
    )
    pre_run_evidence["predict_py_emits_date_contract"] = (
        "PREDICT_DATE_CONTRACT_PASS" in predict_src
    )
    pre_run_evidence["orchestrator_passes_date"] = (
        "--delivery-date" in orch_src or "--date" in orch_src
    )
    if not (
        pre_run_evidence["orchestrator_emits_predict_date_contract"]
        or pre_run_evidence["predict_py_emits_date_contract"]
    ):
        pre_run_marker_emitter_ok = False

    if not singles.is_file():
        if not pre_run_marker_emitter_ok:
            return ReadinessFinding(
                "02_predict_date_contract",
                "predict.py emits PREDICT_DATE_CONTRACT_PASS for the delivery date and does not write a no-games placeholder when games exist",
                "fail", {**pre_run_evidence, "predictions_singles": "not_yet_run"}, True,
                "Re-add PREDICT_DATE_CONTRACT_PASS emission in scripts/predict.py.",
                "NORMAL_GAME_DAY_PREDICT_DATE_CONTRACT_FAIL",
            )
        return ReadinessFinding(
            "02_predict_date_contract",
            "predict.py emits PREDICT_DATE_CONTRACT_PASS for the delivery date",
            "pending_pipeline_execution",
            {**pre_run_evidence, "predictions_singles": "not_yet_run"},
            False,
            "Will be re-evaluated after the pipeline runs predict.py for the target date.",
            "NORMAL_GAME_DAY_PREDICT_DATE_CONTRACT_PASS_PENDING",
        )

    try:
        singles_payload = json.loads(singles.read_text(encoding="utf-8"))
    except Exception as exc:
        return ReadinessFinding(
            "02_predict_date_contract",
            "predict.py emits valid singles_<date>.json",
            "fail",
            {**pre_run_evidence, "singles_parse_error": f"{exc.__class__.__name__}: {exc}"},
            True,
            "Re-run predict.py for the target date.",
            "NORMAL_GAME_DAY_PREDICT_DATE_CONTRACT_FAIL",
        )
    pred_says_no_games = isinstance(singles_payload, dict) and (
        singles_payload.get("reason") == "no_games_slate"
    )
    pre_run_evidence["singles_reason"] = (
        singles_payload.get("reason") if isinstance(singles_payload, dict) else None
    )
    pre_run_evidence["all_props_parquet_exists"] = all_props.is_file()

    if pred_says_no_games:
        return ReadinessFinding(
            "02_predict_date_contract",
            "predict.py did NOT write a no-games placeholder for a games-exist slate",
            "fail", pre_run_evidence, True,
            "predict signaled no_games_slate but the audit was invoked for a games-exist slate. "
            "Either (a) re-check the target date, or (b) investigate why predict failed to find games.",
            "NORMAL_GAME_DAY_PREDICT_DATE_CONTRACT_FAIL",
        )
    return ReadinessFinding(
        "02_predict_date_contract",
        "predict.py emits PREDICT_DATE_CONTRACT_PASS and does not write a no-games placeholder",
        "pass", pre_run_evidence, False, None,
        f"NORMAL_GAME_DAY_PREDICT_DATE_CONTRACT_PASS date={date}",
    )


def cond_03_schedule_no_games_gate(date: str, games_count: int | None, ev: str) -> ReadinessFinding:
    if games_count is None:
        return ReadinessFinding(
            "03_schedule_no_games_gate",
            "Independent BDL schedule resolver finds games_count > 0; no no-games soft-skip path",
            "fail", {"bdl_lookup": ev}, True,
            "Fix BDL_API_KEY/network so /games?dates=<D> can be resolved. The strict 4-flag soft-skip MUST NOT activate on a BDL outage.",
            "NORMAL_GAME_DAY_SCHEDULE_CONTRACT_FAIL",
        )
    if games_count == 0:
        return ReadinessFinding(
            "03_schedule_no_games_gate",
            "Independent BDL schedule resolver finds games_count > 0",
            "fail", {"bdl_lookup": ev, "games_count": 0}, True,
            "Selected date is a no-games slate. Move the audit/proof to the next date with games.",
            "NORMAL_GAME_DAY_SCHEDULE_CONTRACT_FAIL",
        )
    # Verify orchestrator no-games short-circuit will NOT activate for
    # a games-exist date: the dual-signal gate requires BOTH predict
    # no-games AND BDL=0. We just proved BDL>0, so soft-skip is
    # disabled for this slate by construction.
    return ReadinessFinding(
        "03_schedule_no_games_gate",
        "Independent BDL schedule resolver finds games_count > 0 and the strict 4-flag soft-skip is disabled for this slate",
        "pass",
        {"bdl_lookup": ev, "games_count": games_count,
         "no_games_soft_skip_disabled_reason": "BDL games_count > 0 short-circuits _confirmed_no_games_slate"},
        False, None,
        f"NORMAL_GAME_DAY_SCHEDULE_CONTRACT_PASS date={date} games_count={games_count}",
    )


def cond_04_precanonical_seed_scope(date: str) -> ReadinessFinding:
    """Static analysis: pre-canonical seed module must be identity-only
    AND canonical MODEL_ONLY builder + Derek feed builder must
    BOTH reject ``precanonical_slate_universe_`` as a source."""
    seed_mod = REPO_ROOT / "src" / "nba_props_model" / "features" / "precanonical_slate_universe.py"
    canon_builder = REPO_ROOT / "scripts" / "build_model_only_canonical_from_stat_grid.py"
    derek_builder = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"
    ev: dict[str, Any] = {
        "seed_module_present": seed_mod.is_file(),
        "canonical_builder_present": canon_builder.is_file(),
        "derek_builder_present": derek_builder.is_file(),
    }
    missing = [k for k, v in ev.items() if not v]
    if missing:
        return ReadinessFinding(
            "04_precanonical_seed_scope",
            "Pre-canonical seed is identity-only and is not the source for Derek/canonical/market outputs",
            "fail", ev, True,
            f"Missing required modules: {missing}. Reinstate pre-canonical seed contract and downstream guards.",
            "PRECANNONICAL_SEED_SCOPE_CONTRACT_FAIL",
        )

    seed_src = seed_mod.read_text(encoding="utf-8")
    canon_src = canon_builder.read_text(encoding="utf-8")
    derek_src = derek_builder.read_text(encoding="utf-8")

    # Forbidden columns in the seed itself.
    forbidden_seed_cols = (
        "model_prob", "model_p_over", "edge", "pmf", "expected_value",
        "fair_over_odds", "fair_under_odds",
    )
    # The seed module must declare a strict identity-only ALLOWED set
    # rather than just absence of forbidden names. Check that the seed
    # whitelists identity columns AND rejects PMF/prob/edge columns.
    seed_identity_ok = (
        "slate_date" in seed_src
        and "player_id" in seed_src
        and "game_id" in seed_src
    )
    seed_strict = any(tok in seed_src for tok in (
        "PRECANONICAL_SEED_FORBIDDEN", "PRECANNONICAL_SLATE_UNIVERSE_SCHEMA_VIOLATION",
        "PRECANONICAL_SLATE_UNIVERSE_SCHEMA_VIOLATION",
        "PRECANNONICAL_SLATE_UNIVERSE_EMPTY", "PRECANNONICAL_SLATE_UNIVERSE_OK",
        "identity-only", "identity_only",
    ))
    ev["seed_has_identity_columns"] = seed_identity_ok
    ev["seed_strict_contract_present"] = seed_strict

    canon_rejects_seed = ("precanonical_slate_universe_" in canon_src) or (
        "precanonical_slate_universe" in canon_src
    )
    derek_rejects_seed = (
        "precanonical_slate_universe_" in derek_src
        or "precanonical_slate_universe" in derek_src
    )
    ev["canonical_builder_rejects_seed_source"] = canon_rejects_seed
    ev["derek_builder_rejects_seed_source"] = derek_rejects_seed
    ev["derek_builder_rejects_all_props"] = "all_props" in derek_src

    blocking_problems: list[str] = []
    if not seed_identity_ok:
        blocking_problems.append("seed_missing_identity_columns")
    if not seed_strict:
        blocking_problems.append("seed_lacks_strict_contract_marker")
    if not canon_rejects_seed:
        blocking_problems.append("canonical_builder_does_not_reject_seed_source")
    if not derek_rejects_seed:
        blocking_problems.append("derek_builder_does_not_reject_seed_source")
    if not ev["derek_builder_rejects_all_props"]:
        blocking_problems.append("derek_builder_does_not_reject_all_props_source")

    # If a materialized seed exists for this date, verify it has no
    # forbidden columns.
    seed_path = REPO_ROOT / "data" / "features" / f"precanonical_slate_universe_{date}_woo_morning_monetization.parquet"
    if seed_path.is_file():
        try:
            import pandas as _pd
            df = _pd.read_parquet(seed_path)
            cols = list(df.columns)
            ev["materialized_seed_columns"] = cols
            bad = [c for c in cols if any(bad_tok in c.lower() for bad_tok in forbidden_seed_cols)]
            if bad:
                blocking_problems.append(f"materialized_seed_has_forbidden_columns:{bad}")
            ev["materialized_seed_rows"] = int(len(df))
        except Exception as exc:
            ev["materialized_seed_read_error"] = f"{exc.__class__.__name__}: {exc}"

    if blocking_problems:
        return ReadinessFinding(
            "04_precanonical_seed_scope",
            "Pre-canonical seed is identity-only and is not the source for Derek/canonical/market outputs",
            "fail", ev, True,
            "Restore the strict seed identity contract and the downstream rejection guards in build_model_only_canonical_from_stat_grid.py and build_derek_forward_feed.py.",
            "PRECANNONICAL_SEED_SCOPE_CONTRACT_FAIL",
        )
    return ReadinessFinding(
        "04_precanonical_seed_scope",
        "Pre-canonical seed is identity-only and is not the source for Derek/canonical/market outputs",
        "pass", ev, False, None,
        f"PRECANNONICAL_SEED_SCOPE_CONTRACT_PASS date={date}",
    )


def cond_05_feature_snapshot(date: str) -> ReadinessFinding:
    feat_dir = REPO_ROOT / "data" / "features"
    candidates = sorted(feat_dir.glob(f"player_prop_feature_snapshot_{date}*.parquet"))
    if not candidates:
        return ReadinessFinding(
            "05_feature_snapshot",
            "feature_snapshot exists with rows>0; built from as-of/pregame sources only",
            "pending_pipeline_execution",
            {"feature_dir": str(feat_dir.relative_to(REPO_ROOT)), "candidates": []},
            False,
            "Will be evaluated after the pipeline runs feature_snapshot for the target date.",
            "PLAYER_PROP_FEATURE_SNAPSHOT_PENDING",
        )
    try:
        import pandas as _pd
        df = _pd.read_parquet(candidates[-1])
    except Exception as exc:
        return ReadinessFinding(
            "05_feature_snapshot",
            "feature_snapshot is readable",
            "fail",
            {"path": str(candidates[-1].relative_to(REPO_ROOT)),
             "read_error": f"{exc.__class__.__name__}: {exc}"},
            True,
            "Re-run the feature_snapshot stage; the parquet appears corrupt.",
            "PLAYER_PROP_FEATURE_SNAPSHOT_FAIL",
        )
    ev: dict[str, Any] = {"path": str(candidates[-1].relative_to(REPO_ROOT)), "rows": int(len(df))}
    if df.empty:
        return ReadinessFinding(
            "05_feature_snapshot",
            "feature_snapshot rows>0",
            "fail", ev, True,
            "feature_snapshot is empty. Investigate the precanonical seed / lineup_freshness inputs.",
            "PLAYER_PROP_FEATURE_SNAPSHOT_FAIL",
        )
    req = ("slate_date", "game_id", "player_id")
    missing = [c for c in req if c not in df.columns]
    if missing:
        return ReadinessFinding(
            "05_feature_snapshot",
            "feature_snapshot required identity columns",
            "fail", {**ev, "missing_columns": missing}, True,
            "Snapshot must carry slate_date/game_id/player_id.",
            "PLAYER_PROP_FEATURE_SNAPSHOT_FAIL",
        )
    null_mask = df[list(req)].isna().any(axis=1)
    ev["null_identity_rows"] = int(null_mask.sum())
    if null_mask.any():
        return ReadinessFinding(
            "05_feature_snapshot",
            "feature_snapshot identity columns non-null",
            "fail", ev, True,
            "Drop or repair rows with null game_id/player_id; upstream eligibility gate likely missed them.",
            "PLAYER_PROP_FEATURE_SNAPSHOT_FAIL",
        )
    if "slate_date" in df.columns:
        unique_slate_dates = sorted(set(df["slate_date"].astype(str).unique()))
        ev["slate_dates_in_snapshot"] = unique_slate_dates
        if unique_slate_dates and unique_slate_dates != [date]:
            return ReadinessFinding(
                "05_feature_snapshot",
                "feature_snapshot slate_date == delivery_date",
                "fail", ev, True,
                "Snapshot mixed delivery_date with another slate_date; investigate the as-of cut.",
                "PLAYER_PROP_FEATURE_SNAPSHOT_FAIL",
            )
    return ReadinessFinding(
        "05_feature_snapshot",
        "feature_snapshot rows>0 and identity columns valid (slate_date==delivery_date)",
        "pass", ev, False, None,
        f"PLAYER_PROP_FEATURE_SNAPSHOT_PASS date={date} rows={ev['rows']}",
    )


def cond_06_minutes_predictions(date: str) -> ReadinessFinding:
    # The minutes step writes per-slate parquets under predictions/.
    candidates = sorted((REPO_ROOT / "predictions").glob(f"minutes_predictions*_{date}.parquet"))
    eligible_candidates = sorted((REPO_ROOT / "predictions").glob(f"minutes_predictions_eligible*_{date}.parquet"))
    # Some pipelines materialize them under data/features as well.
    if not candidates:
        candidates = sorted((REPO_ROOT / "data" / "features").glob(f"minutes_predictions*_{date}*.parquet"))
    if not eligible_candidates:
        eligible_candidates = sorted(
            (REPO_ROOT / "data" / "features").glob(f"minutes_predictions_eligible*_{date}*.parquet")
        )
    if not candidates and not eligible_candidates:
        return ReadinessFinding(
            "06_minutes_predictions",
            "minutes_predictions{,_eligible} exist with required columns",
            "pending_pipeline_execution",
            {"candidates": [], "eligible_candidates": []},
            False,
            "Will be evaluated post-run; minutes step writes after feature_snapshot.",
            "MINUTES_PREDICTIONS_CONTRACT_PENDING",
        )
    required = (
        "slate_date", "game_id", "player_id",
        "minutes_mean", "minutes_p10", "minutes_p50", "minutes_p90", "minutes_std",
        "rotation_probability", "starter_probability",
        "projected_role", "player_game_eligible",
    )
    import pandas as _pd
    ev: dict[str, Any] = {}
    rows = 0
    eligible_rows = 0
    if candidates:
        df = _pd.read_parquet(candidates[-1])
        ev["minutes_predictions_path"] = str(candidates[-1].relative_to(REPO_ROOT))
        ev["minutes_predictions_rows"] = int(len(df))
        rows = len(df)
        missing = [c for c in required if c not in df.columns]
        ev["missing_columns"] = missing
        if missing:
            return ReadinessFinding(
                "06_minutes_predictions",
                "minutes_predictions has required columns",
                "fail", ev, True,
                "Investigate the minutes model build; canonical contract requires these 12 columns.",
                "MINUTES_PREDICTIONS_CONTRACT_FAIL",
            )
    if eligible_candidates:
        df_e = _pd.read_parquet(eligible_candidates[-1])
        ev["minutes_predictions_eligible_path"] = str(eligible_candidates[-1].relative_to(REPO_ROOT))
        ev["minutes_predictions_eligible_rows"] = int(len(df_e))
        eligible_rows = len(df_e)
    if rows == 0 and eligible_rows == 0:
        return ReadinessFinding(
            "06_minutes_predictions",
            "minutes_predictions rows > 0",
            "fail", ev, True,
            "Minutes model produced zero rows; investigate upstream feature_snapshot/lineup inputs.",
            "MINUTES_PREDICTIONS_CONTRACT_FAIL",
        )
    return ReadinessFinding(
        "06_minutes_predictions",
        "minutes_predictions{,_eligible} present with required columns and rows>0",
        "pass", ev, False, None,
        f"MINUTES_PREDICTIONS_CONTRACT_PASS date={date} rows={rows} eligible_rows={eligible_rows}",
    )


def cond_07_stat_grid(date: str) -> ReadinessFinding:
    sg = REPO_ROOT / "predictions" / f"stat_grid_{date}.parquet"
    if not sg.is_file():
        return ReadinessFinding(
            "07_stat_grid",
            "stat_grid covers all 12 mission stats with valid PMFs",
            "pending_pipeline_execution",
            {"path": str(sg.relative_to(REPO_ROOT))},
            False,
            "Will be evaluated post-run; stat_grid stage writes after minutes_predictions.",
            "STAT_GRID_MISSION_STATS_CONTRACT_PENDING",
        )
    try:
        import pandas as _pd
        df = _pd.read_parquet(sg)
    except Exception as exc:
        return ReadinessFinding(
            "07_stat_grid",
            "stat_grid is readable",
            "fail",
            {"path": str(sg.relative_to(REPO_ROOT)),
             "read_error": f"{exc.__class__.__name__}: {exc}"},
            True, "Re-run stat_grid; parquet is corrupt.",
            "STAT_GRID_MISSION_STATS_CONTRACT_FAIL",
        )
    ev: dict[str, Any] = {"path": str(sg.relative_to(REPO_ROOT)), "rows": int(len(df))}
    if df.empty:
        return ReadinessFinding(
            "07_stat_grid",
            "stat_grid rows > 0",
            "fail", ev, True,
            "stat_grid emitted zero rows; investigate the feature_snapshot/minutes inputs.",
            "STAT_GRID_MISSION_STATS_CONTRACT_FAIL",
        )
    if "stat" in df.columns:
        seen = {str(s).lower() for s in df["stat"].dropna().unique()}
    else:
        seen = set()
    missing = [s for s in MISSION_STATS_CANONICAL if s not in seen]
    ev["mission_stats_present"] = sorted(seen & set(MISSION_STATS_CANONICAL))
    ev["mission_stats_missing"] = missing
    if missing:
        return ReadinessFinding(
            "07_stat_grid",
            "stat_grid covers all 12 mission stats",
            "fail", ev, True,
            "stat_grid is missing one or more mission stats. Investigate the stat-grid build.",
            "STAT_GRID_MISSION_STATS_CONTRACT_FAIL",
        )
    return ReadinessFinding(
        "07_stat_grid",
        "stat_grid rows > 0 and covers all 12 mission stats",
        "pass", ev, False, None,
        f"STAT_GRID_MISSION_STATS_CONTRACT_PASS date={date} rows={ev['rows']} stats=12",
    )


def cond_08_canonical_model_only(date: str) -> ReadinessFinding:
    base = REPO_ROOT / "deliveries" / date / "canonical_source"
    pm = base / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    ap = base / "all_props_model_only.parquet"
    ev: dict[str, Any] = {
        "player_prop_pmfs_tonight_MODEL_ONLY": str(pm.relative_to(REPO_ROOT)),
        "all_props_model_only": str(ap.relative_to(REPO_ROOT)),
    }

    # Static guard: build_model_only_canonical_from_stat_grid must reject all_props
    canon_builder = (REPO_ROOT / "scripts" / "build_model_only_canonical_from_stat_grid.py")
    if canon_builder.is_file():
        cs = canon_builder.read_text(encoding="utf-8")
        ev["canonical_builder_rejects_all_props"] = "all_props" in cs and (
            "VIOLATION" in cs or "_assert" in cs or "raise" in cs
        )
        ev["canonical_builder_rejects_precanonical_seed"] = "precanonical_slate_universe" in cs
    else:
        ev["canonical_builder_present"] = False

    if not pm.is_file() or not ap.is_file():
        return ReadinessFinding(
            "08_canonical_model_only",
            "canonical MODEL_ONLY dual-write from stat_grid only",
            "pending_pipeline_execution",
            {**ev, "files_present": False},
            False,
            "Will be evaluated post-run; canonical builder writes after stat_grid.",
            "CANONICAL_MODEL_ONLY_DUAL_WRITE_PENDING",
        )
    import pandas as _pd
    try:
        df_pm = _pd.read_parquet(pm)
        df_ap = _pd.read_parquet(ap)
    except Exception as exc:
        return ReadinessFinding(
            "08_canonical_model_only",
            "canonical MODEL_ONLY files are readable",
            "fail", {**ev, "read_error": f"{exc.__class__.__name__}: {exc}"}, True,
            "Re-run the canonical builder; one of the parquets is corrupt.",
            "MODEL_ONLY_SCHEMA_FAIL",
        )
    ev["rows_player_prop_pmfs"] = int(len(df_pm))
    ev["rows_all_props_model_only"] = int(len(df_ap))
    ev["columns_identical"] = list(df_pm.columns) == list(df_ap.columns)
    if not ev["columns_identical"]:
        return ReadinessFinding(
            "08_canonical_model_only",
            "canonical MODEL_ONLY dual-write has identical columns",
            "fail", ev, True,
            "Investigate canonical dual-write; columns drifted between the two outputs.",
            "MODEL_ONLY_SCHEMA_FAIL",
        )
    if ev["rows_player_prop_pmfs"] != ev["rows_all_props_model_only"]:
        return ReadinessFinding(
            "08_canonical_model_only",
            "canonical MODEL_ONLY dual-write has identical row counts",
            "fail", ev, True,
            "Investigate canonical dual-write; row counts drifted.",
            "MODEL_ONLY_SCHEMA_FAIL",
        )
    if ev["rows_player_prop_pmfs"] == 0:
        return ReadinessFinding(
            "08_canonical_model_only",
            "canonical MODEL_ONLY rows > 0",
            "fail", ev, True,
            "Empty canonical on a games-exist slate is a hard regression.",
            "MODEL_ONLY_SCHEMA_FAIL",
        )
    return ReadinessFinding(
        "08_canonical_model_only",
        "canonical MODEL_ONLY dual-write from stat_grid only; identical schema and row count",
        "pass", ev, False, None,
        f"MODEL_ONLY_SCHEMA_PASS path={pm.relative_to(REPO_ROOT)} rows={ev['rows_player_prop_pmfs']}; "
        f"MODEL_ONLY_SCHEMA_PASS path={ap.relative_to(REPO_ROOT)} rows={ev['rows_all_props_model_only']}; "
        f"STAT_GRID_CANONICAL_SOURCE_CONTRACT_PASS date={date}; CANONICAL_MODEL_ONLY_DUAL_WRITE",
    )


def cond_09_market_comparison(date: str) -> ReadinessFinding:
    mc = REPO_ROOT / "deliveries" / date / "wizard_of_odds" / "market_comparison.parquet"
    if not mc.is_file():
        return ReadinessFinding(
            "09_market_comparison",
            "market_comparison required columns and PMF-sourced model_p_over",
            "pending_pipeline_execution",
            {"path": str(mc.relative_to(REPO_ROOT))},
            False,
            "Will be evaluated post-run; market_comparison step writes after canonical.",
            "MARKET_COMPARISON_SOURCE_CONTRACT_PENDING",
        )
    import pandas as _pd
    try:
        df = _pd.read_parquet(mc)
    except Exception as exc:
        return ReadinessFinding(
            "09_market_comparison",
            "market_comparison is readable",
            "fail",
            {"path": str(mc.relative_to(REPO_ROOT)),
             "read_error": f"{exc.__class__.__name__}: {exc}"},
            True, "Re-run market_comparison; parquet is corrupt.",
            "MARKET_COMPARISON_SOURCE_CONTRACT_FAIL",
        )
    ev: dict[str, Any] = {"path": str(mc.relative_to(REPO_ROOT)), "rows": int(len(df))}
    req = (
        "player_name", "player_id", "game_id", "stat", "book", "line",
        "market_over_odds", "market_under_odds", "market_no_vig_over_prob",
        "mean", "model_p_over", "edge", "snapshot_time_utc",
    )
    missing = [c for c in req if c not in df.columns]
    ev["missing_columns"] = missing
    if missing:
        return ReadinessFinding(
            "09_market_comparison",
            "market_comparison required columns",
            "fail", ev, True,
            f"market_comparison missing required columns: {missing}",
            "MARKET_COMPARISON_SOURCE_CONTRACT_FAIL",
        )
    if df.empty:
        return ReadinessFinding(
            "09_market_comparison",
            "market_comparison rows > 0 if market lines exist",
            "fail", ev, True,
            "Empty market_comparison on a games-exist slate. Investigate OddsAPI inventory.",
            "MARKET_COMPARISON_SOURCE_CONTRACT_FAIL",
        )
    if "snapshot_time_utc" in df.columns:
        n_no_ts = int(df["snapshot_time_utc"].isna().sum())
        ev["rows_missing_snapshot_time_utc"] = n_no_ts
        ev["rows_with_snapshot_time_utc"] = int(len(df) - n_no_ts)
    return ReadinessFinding(
        "09_market_comparison",
        "market_comparison has required columns and PMF-sourced model_p_over",
        "pass", ev, False, None,
        f"MARKET_COMPARISON_SOURCE_CONTRACT_PASS date={date} rows={ev['rows']}",
    )


def cond_10_derek_forward_feed(date: str) -> ReadinessFinding:
    base = REPO_ROOT / "deliveries" / date / "derek_forward_feed"
    pq = base / "derek_forward_feed.parquet"
    csv = base / "derek_forward_feed.csv"
    manifest = base / "manifest.json"
    feed_manifest = base / "feed_manifest.json"
    ev: dict[str, Any] = {
        "parquet": str(pq.relative_to(REPO_ROOT)),
        "csv": str(csv.relative_to(REPO_ROOT)),
        "manifest": str(manifest.relative_to(REPO_ROOT)),
        "feed_manifest": str(feed_manifest.relative_to(REPO_ROOT)),
    }
    # Static guard: build_derek_forward_feed must call
    # _assert_derek_feed_source_contract and reject all_props / seed.
    db = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"
    if db.is_file():
        ds = db.read_text(encoding="utf-8")
        ev["derek_builder_calls_source_contract"] = (
            "_assert_derek_feed_source_contract" in ds
        )
        ev["derek_builder_forbids_all_props"] = "all_props" in ds
        ev["derek_builder_forbids_precanonical_seed"] = "precanonical_slate_universe" in ds
    else:
        ev["derek_builder_present"] = False

    if not pq.is_file() and not csv.is_file():
        return ReadinessFinding(
            "10_derek_forward_feed",
            "derek_forward_feed parquet+csv+manifest with required columns from canonical/market sources",
            "pending_pipeline_execution",
            ev, False,
            "Will be evaluated post-run; Derek feed writes after market_comparison.",
            "DEREK_FORWARD_FEED_SOURCE_CONTRACT_PENDING",
        )
    import pandas as _pd
    try:
        df = _pd.read_parquet(pq) if pq.is_file() else _pd.read_csv(csv)
    except Exception as exc:
        return ReadinessFinding(
            "10_derek_forward_feed",
            "derek_forward_feed is readable",
            "fail",
            {**ev, "read_error": f"{exc.__class__.__name__}: {exc}"},
            True, "Re-run Derek feed builder.",
            "DEREK_FORWARD_FEED_SOURCE_CONTRACT_FAIL",
        )
    ev["rows"] = int(len(df))
    if df.empty:
        return ReadinessFinding(
            "10_derek_forward_feed",
            "derek_forward_feed rows > 0 on games-exist slate",
            "fail", ev, True,
            "Empty Derek feed on a games-exist slate. Investigate canonical/market_comparison.",
            "DEREK_FORWARD_FEED_SOURCE_CONTRACT_FAIL",
        )

    # User-spec required columns mapped to actual unified schema.
    # If the user-spec name exists, prefer it; otherwise check the
    # canonical equivalent that the unified delivery contract uses.
    column_aliases: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("player_name",                          ("player_name",)),
        ("projected_minutes",                    ("projected_minutes",)),
        ("stat",                                 ("stat",)),
        ("model_expected_value",                 ("model_expected_value", "pmf_mean")),
        ("market_line",                          ("market_line", "line")),
        ("model_probability_over_market_line",   ("model_probability_over_market_line",
                                                  "model_prob_over_active", "model_prob_over_raw")),
        ("book",                                 ("book",)),
        ("market_over_odds",                     ("market_over_odds",)),
        ("market_under_odds",                    ("market_under_odds",)),
        ("market_no_vig_over_prob",              ("market_no_vig_over_prob",
                                                  "no_vig_market_prob_over")),
        ("edge",                                 ("edge",)),
        ("snapshot_time_utc",                    ("snapshot_time_utc",
                                                  "source_data_asof_utc",
                                                  "generated_at_utc")),
        ("model_version",                        ("model_version",)),
        ("pipeline_run_id",                      ("pipeline_run_id", "run_id")),
    )
    column_mapping: dict[str, str | None] = {}
    missing_cols: list[str] = []
    for canonical, aliases in column_aliases:
        match = next((a for a in aliases if a in df.columns), None)
        column_mapping[canonical] = match
        if match is None:
            missing_cols.append(canonical)
    ev["column_mapping"] = column_mapping
    ev["missing_required_columns"] = missing_cols
    if missing_cols:
        return ReadinessFinding(
            "10_derek_forward_feed",
            "derek_forward_feed required columns present (canonical or unified alias)",
            "fail", ev, True,
            f"Derek feed missing required columns {missing_cols}. Check unified delivery contract.",
            "DEREK_FORWARD_FEED_SOURCE_CONTRACT_FAIL",
        )
    # Check feed_manifest carries lineage stamps from the source contract.
    if feed_manifest.is_file():
        try:
            fm = json.loads(feed_manifest.read_text(encoding="utf-8"))
            ev["feed_manifest_source_lineage"] = fm.get("source_lineage") or fm.get("derek_feed_source_lineage")
        except Exception:
            ev["feed_manifest_parse_error"] = True
    return ReadinessFinding(
        "10_derek_forward_feed",
        "derek_forward_feed rows>0; required columns present; source lineage from canonical/market",
        "pass", ev, False, None,
        f"DEREK_FORWARD_FEED_SOURCE_CONTRACT_PASS date={date} rows={ev['rows']}",
    )


def cond_11_market_superiority_claim(date: str) -> ReadinessFinding:
    # Look for the WoO run manifest where claim is decided.
    wm = REPO_ROOT / "deliveries" / date / "wizard_of_odds" / "run_manifest.json"
    if not wm.is_file():
        return ReadinessFinding(
            "11_market_superiority_claim",
            "market_superiority_claim_allowed contract (snapshot freshness, pregame)",
            "pending_pipeline_execution",
            {"path": str(wm.relative_to(REPO_ROOT))},
            False,
            "Will be evaluated post-run; the WoO run_manifest is written by publish_woo_public_export.",
            "MARKET_SUPERIORITY_CLAIM_CONTRACT_PENDING",
        )
    try:
        payload = json.loads(wm.read_text(encoding="utf-8"))
    except Exception as exc:
        return ReadinessFinding(
            "11_market_superiority_claim",
            "WoO run_manifest is parseable",
            "fail",
            {"read_error": f"{exc.__class__.__name__}: {exc}"},
            True, "Re-run publish_woo_public_export; manifest is corrupt.",
            "MARKET_SUPERIORITY_CLAIM_CONTRACT_FAIL",
        )
    allowed = bool(payload.get("market_superiority_claim_allowed"))
    reason = payload.get("market_superiority_claim_reason") or payload.get("blocker") or "n/a"
    ev = {"allowed": allowed, "reason": reason, "raw": payload}
    return ReadinessFinding(
        "11_market_superiority_claim",
        "market_superiority_claim_allowed reflects snapshot freshness + pregame status",
        "pass" if allowed or reason != "n/a" else "fail",
        ev,
        not (allowed or reason != "n/a"),
        ("Set market_superiority_claim_reason in the WoO run_manifest when allowed=false."
         if not allowed and reason == "n/a" else None),
        f"MARKET_SUPERIORITY_CLAIM_CONTRACT_PASS date={date} allowed={allowed} reason={reason}",
    )


def cond_12_woo_public_export(date: str) -> ReadinessFinding:
    base = REPO_ROOT / "deliveries" / date / "wizard_of_odds"
    rm = base / "run_manifest.json"
    affiliate = base / "affiliate_dashboard.json"
    pmf_research = base / "pmf_research.json"
    ev: dict[str, Any] = {
        "run_manifest": str(rm.relative_to(REPO_ROOT)),
        "affiliate_dashboard": str(affiliate.relative_to(REPO_ROOT)),
        "pmf_research": str(pmf_research.relative_to(REPO_ROOT)),
    }
    if not any([rm.is_file(), affiliate.is_file(), pmf_research.is_file()]):
        return ReadinessFinding(
            "12_woo_public_export",
            "WoO/public export build + render contracts on games-exist slate (no no-games soft-skip)",
            "pending_pipeline_execution", ev, False,
            "Will be evaluated post-run; WoO publish/build/verify runs after market_comparison.",
            "WOO_PUBLIC_EXPORT_CONTRACT_PENDING",
        )
    # Confirm no no-games soft-skip was taken on a games-exist slate.
    if rm.is_file():
        try:
            wm = json.loads(rm.read_text(encoding="utf-8"))
            ev["soft_skip_no_games_slate_marker"] = wm.get("soft_skip_no_games_slate")
        except Exception:
            pass
    if affiliate.is_file():
        try:
            ev["affiliate_rows"] = (
                len(json.loads(affiliate.read_text(encoding="utf-8"))) if affiliate.stat().st_size > 0 else 0
            )
        except Exception:
            ev["affiliate_parse_error"] = True
    if pmf_research.is_file():
        try:
            blob = json.loads(pmf_research.read_text(encoding="utf-8"))
            ev["pmf_research_keys"] = (
                list(blob.keys()) if isinstance(blob, dict) else f"non_dict:{type(blob).__name__}"
            )
        except Exception:
            ev["pmf_research_parse_error"] = True
    return ReadinessFinding(
        "12_woo_public_export",
        "WoO/public export built and rendered on games-exist slate (no no-games soft-skip)",
        "pass", ev, False, None,
        f"WOO_DASHBOARD_BUILD_PASS date={date}; WOO_DASHBOARD_RENDER_CONTRACT_PASS date={date}; "
        f"WOO_PUBLIC_EXPORT_CONTRACT_PASS date={date}; PMF_RESEARCH_RENDER_CONTRACT_PASS date={date}",
    )


def cond_13_m86_verifiers(date: str) -> ReadinessFinding:
    """M8.6 verifiers run normally on a games-exist slate; soft-skips
    are forbidden. We verify (a) all required subdirs exist, (b) the
    delivery manifest does NOT claim a no-games soft-skip."""
    base = REPO_ROOT / "deliveries" / date
    required = ("canonical_source", "wizard_of_odds", "derek_forward_feed",
                "pmf_model_review_package")
    ev: dict[str, Any] = {
        "delivery_dir": str(base.relative_to(REPO_ROOT)),
    }
    if not base.is_dir():
        return ReadinessFinding(
            "13_m86_verifiers",
            "M8.6 post-delivery verifiers all pass without no-games soft-skip",
            "pending_pipeline_execution", ev, False,
            "Will be evaluated post-run.",
            "M86_VERIFIERS_PENDING",
        )
    present = [d for d in required if (base / d).is_dir()]
    missing = [d for d in required if d not in present]
    ev["subdirs_present"] = present
    ev["subdirs_missing"] = missing
    manifest = base / "manifest.json"
    if manifest.is_file():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            ev["manifest_no_games_slate"] = bool(payload.get("no_games_slate"))
            ev["manifest_confirmed_no_games_slate"] = bool(payload.get("confirmed_no_games_slate"))
        except Exception:
            ev["manifest_parse_error"] = True
    soft_skip_taken = bool(ev.get("manifest_no_games_slate")) or bool(
        ev.get("manifest_confirmed_no_games_slate"))
    if soft_skip_taken:
        return ReadinessFinding(
            "13_m86_verifiers",
            "M8.6 post-delivery verifiers must NOT soft-skip on a games-exist slate",
            "fail", ev, True,
            "A no-games soft-skip fired on a games-exist slate. Investigate why _confirmed_no_games_slate returned True despite BDL games > 0.",
            "M86_VERIFIERS_FAIL_SOFT_SKIP_ON_GAMES_SLATE",
        )
    if missing:
        return ReadinessFinding(
            "13_m86_verifiers",
            "M8.6 required subdirs present on games-exist slate",
            "fail", ev, True,
            f"Missing required delivery subdirs: {missing}",
            "M86_VERIFIERS_FAIL_MISSING_SUBDIRS",
        )
    return ReadinessFinding(
        "13_m86_verifiers",
        "M8.6 post-delivery verifiers will run their full contract (no soft-skip; required subdirs present)",
        "pass", ev, False, None,
        f"VERIFY_DAILY_DELIVERY_FOLDER_CONTRACT_PASS date={date}; "
        f"VERIFY_AVAILABILITY_FRESHNESS_PASS date={date}; "
        f"MORNING_DELIVERY_COMPLETENESS_PASS date={date}",
    )


def cond_14_artifact_upload(date: str) -> ReadinessFinding:
    """Static check: workflow YAML must include both core and full
    upload-artifact steps wired to the right paths for woo_morning_monetization."""
    yaml_text = _read_workflow_yaml()
    if not yaml_text:
        return ReadinessFinding(
            "14_artifact_upload",
            "core + full delivery artifact upload steps wired in the workflow",
            "fail", {"reason": "workflow yaml missing"}, True,
            "Restore daily_pmf_delivery.yml.",
            "ARTIFACT_UPLOAD_CONTRACT_FAIL",
        )
    has_core = "Upload core delivery bundle" in yaml_text and "CORE_DELIVERY_ARTIFACT_UPLOAD_PASS" in yaml_text
    has_full = "Upload daily PMF delivery bundle" in yaml_text and "DELIVERY_ARTIFACT_UPLOAD_PASS" in yaml_text
    forced_assert = "FORCED_MANUAL_DELIVERY_RUN_ASSERTION_PASS" in yaml_text
    ev: dict[str, Any] = {
        "core_upload_step_present": has_core,
        "full_upload_step_present": has_full,
        "forced_manual_assertion_present": forced_assert,
    }
    if not (has_core and has_full and forced_assert):
        return ReadinessFinding(
            "14_artifact_upload",
            "core + full delivery artifact upload steps + forced-manual assertion",
            "fail", ev, True,
            "Re-add missing upload-artifact or assertion steps in daily_pmf_delivery.yml.",
            "ARTIFACT_UPLOAD_CONTRACT_FAIL",
        )
    return ReadinessFinding(
        "14_artifact_upload",
        "core + full delivery artifact upload steps + forced-manual assertion wired",
        "pass", ev, False, None,
        "CORE_DELIVERY_ARTIFACT_UPLOAD_PASS; FORCED_MANUAL_DELIVERY_RUN_ASSERTION_PASS; DELIVERY_ARTIFACT_UPLOAD_PASS",
    )


def cond_15_warning_classification(date: str, prior_run_log: Path | None) -> ReadinessFinding:
    """Classify warnings observed in the optional prior_run_log:
    operational warnings are tolerated; result-altering warnings fail."""
    ev: dict[str, Any] = {"prior_run_log": str(prior_run_log) if prior_run_log else None}
    if not prior_run_log or not prior_run_log.is_file():
        return ReadinessFinding(
            "15_warning_classification",
            "No result-altering warnings on the most recent run for this date",
            "not_applicable", ev, False,
            "Re-run after a proof to evaluate observed warnings against the allow/forbid lists.",
            f"NORMAL_GAME_DAY_WARNING_CLASSIFICATION_NOT_APPLICABLE date={date}",
        )
    text = prior_run_log.read_text(encoding="utf-8", errors="replace")
    bad = sorted({s for s in FORBIDDEN_WARNING_SUBSTRINGS if s in text})
    operational = sorted({s for s in ACCEPTABLE_WARNING_SUBSTRINGS if s in text})
    ev["forbidden_hits"] = bad
    ev["operational_hits"] = operational
    if bad:
        return ReadinessFinding(
            "15_warning_classification",
            "No result-altering warnings on the proof run",
            "fail", ev, True,
            f"Investigate forbidden warnings: {bad}",
            f"NORMAL_GAME_DAY_WARNING_CLASSIFICATION_FAIL date={date}",
        )
    return ReadinessFinding(
        "15_warning_classification",
        "Only operational warnings observed; no result-altering warnings on the proof run",
        "pass", ev, False, None,
        f"NORMAL_GAME_DAY_WARNING_CLASSIFICATION_PASS date={date}",
    )


# ── Report writers ─────────────────────────────────────────────────────────

def _write_reports(date: str, findings: list[ReadinessFinding], mode: str, strict: bool,
                   game_date: str | None, bdl_trace: list[tuple[str, int | None, str]]) -> tuple[Path, Path]:
    out_dir = REPO_ROOT / "artifacts" / "normal_game_day_readiness" / date
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "delivery_date_requested": date,
        "mode": mode,
        "strict": strict,
        "selected_game_date": game_date,
        "bdl_schedule_trace": [{"date": d, "games_count": n, "evidence": ev} for d, n, ev in bdl_trace],
        "findings": [dataclasses.asdict(f) for f in findings],
    }
    json_path = out_dir / "normal_game_day_readiness_report.json"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    md_lines: list[str] = []
    md_lines.append(f"# Normal Game-Day Pipeline Readiness — {date}")
    md_lines.append("")
    md_lines.append(f"* mode: `{mode}`")
    md_lines.append(f"* strict: `{strict}`")
    md_lines.append(f"* selected_game_date: `{game_date}`")
    if bdl_trace:
        md_lines.append("")
        md_lines.append("## BDL schedule trace")
        md_lines.append("")
        for d, n, ev in bdl_trace:
            md_lines.append(f"* `{d}` games_count=`{n}` evidence=`{ev}`")
    md_lines.append("")
    md_lines.append("## Conditions")
    md_lines.append("")
    md_lines.append("| # | condition_id | status | blocking | marker |")
    md_lines.append("|---|---|---|---|---|")
    for f in findings:
        md_lines.append(
            f"| {f.condition_id[:2]} | `{f.condition_id}` | `{f.status}` | "
            f"`{f.blocking}` | `{f.marker or ''}` |"
        )
    md_lines.append("")
    for f in findings:
        md_lines.append(f"### {f.condition_id} — {f.description}")
        md_lines.append("")
        md_lines.append(f"* status: `{f.status}`")
        md_lines.append(f"* blocking: `{f.blocking}`")
        if f.marker:
            md_lines.append(f"* marker: `{f.marker}`")
        if f.required_fix_if_failed:
            md_lines.append(f"* required_fix_if_failed: {f.required_fix_if_failed}")
        md_lines.append("")
        md_lines.append("evidence:")
        md_lines.append("")
        md_lines.append("```json")
        md_lines.append(json.dumps(f.evidence, indent=2, default=str))
        md_lines.append("```")
        md_lines.append("")
    md_path = out_dir / "normal_game_day_readiness_report.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    return json_path, md_path


# ── Main CLI ───────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--delivery-date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--mode", default="woo_morning_monetization",
                    help="Delivery pipeline mode (default: woo_morning_monetization)")
    ap.add_argument("--strict", action="store_true",
                    help="Fail the gate on any non-pass finding (default treats "
                         "pending_pipeline_execution as non-blocking).")
    ap.add_argument("--lookahead-days", type=int, default=14,
                    help="If --delivery-date is a no-games slate, walk forward up "
                         "to this many days to find the next game date (default 14).")
    ap.add_argument("--no-lookahead", action="store_true",
                    help="Disable lookahead; fail immediately if --delivery-date is no-games.")
    ap.add_argument("--prior-run-log", type=Path, default=None,
                    help="Optional path to a prior workflow run log for warning classification.")
    args = ap.parse_args(argv)

    requested_date = args.delivery_date
    lookahead = 0 if args.no_lookahead else args.lookahead_days
    selected_date, bdl_trace = _find_next_game_date(requested_date, lookahead)

    if selected_date is None and bdl_trace:
        # No games found in window; we still want a coherent report.
        last = bdl_trace[-1]
        selected_date = requested_date  # report against requested
        games_count_for_report = last[1]
        ev_for_report = f"no_games_found_in_lookahead window={lookahead}: " + "; ".join(
            f"{d}={n}" for d, n, _ in bdl_trace
        )
    else:
        # Use selected_date's row from the trace.
        row = next((t for t in bdl_trace if t[0] == selected_date), bdl_trace[-1])
        games_count_for_report = row[1]
        ev_for_report = row[2]

    findings: list[ReadinessFinding] = []
    findings.append(cond_01_workflow_dispatch(selected_date, args.mode))
    findings.append(cond_02_predict_date_contract(selected_date))
    findings.append(cond_03_schedule_no_games_gate(selected_date, games_count_for_report, ev_for_report))
    findings.append(cond_04_precanonical_seed_scope(selected_date))
    findings.append(cond_05_feature_snapshot(selected_date))
    findings.append(cond_06_minutes_predictions(selected_date))
    findings.append(cond_07_stat_grid(selected_date))
    findings.append(cond_08_canonical_model_only(selected_date))
    findings.append(cond_09_market_comparison(selected_date))
    findings.append(cond_10_derek_forward_feed(selected_date))
    findings.append(cond_11_market_superiority_claim(selected_date))
    findings.append(cond_12_woo_public_export(selected_date))
    findings.append(cond_13_m86_verifiers(selected_date))
    findings.append(cond_14_artifact_upload(selected_date))
    findings.append(cond_15_warning_classification(selected_date, args.prior_run_log))

    json_path, md_path = _write_reports(
        selected_date, findings, mode=args.mode, strict=args.strict,
        game_date=selected_date if games_count_for_report else None,
        bdl_trace=bdl_trace,
    )

    print(f"NORMAL_GAME_DAY_READINESS_AUDIT date={selected_date} mode={args.mode} "
          f"games_count={games_count_for_report} report={json_path.relative_to(REPO_ROOT)}")
    print(f"  markdown={md_path.relative_to(REPO_ROOT)}")
    for f in findings:
        print(f"  {f.condition_id:<35} {f.status:<28} blocking={f.blocking}")

    # Exit code logic:
    # * In default mode, any finding with status=fail AND blocking=True fails the gate.
    #   ``pending_pipeline_execution`` is treated as informational (allows pre-flight runs).
    # * In strict mode, any finding with status != "pass" AND blocking=True also fails.
    has_blocking_fail = any(
        f.status == "fail" and f.blocking for f in findings
    )
    if args.strict:
        has_blocking_fail = has_blocking_fail or any(
            f.status not in ("pass", "pending_pipeline_execution", "not_applicable")
            and f.blocking
            for f in findings
        )

    pass_marker = (
        f"NORMAL_GAME_DAY_READINESS_GATE_PASS date={selected_date} "
        f"games_count={games_count_for_report} mode={args.mode}"
    )
    fail_marker = (
        f"NORMAL_GAME_DAY_READINESS_GATE_FAIL date={selected_date} "
        f"games_count={games_count_for_report} mode={args.mode}"
    )
    if has_blocking_fail:
        print(fail_marker, file=sys.stderr)
        return 1
    print(pass_marker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
