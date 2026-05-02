"""Phase 13O — live-context feature builders.

This module is the upstream insertion point that the Phase 13O feature
flow audit identified as missing today. It composes lineup, injury,
availability, and vacated-opportunity features into a single feature row
keyed by (player_id, game_id, game_date).

Critical design rules:

  * **No fabrication.** When a source is unavailable for a row (BDL
    lineups not posted, injury report missing for that timestamp, etc.)
    the feature is NaN/0 with an explicit ``*_missing`` indicator. The
    consumer must know what was observed vs. what was imputed.
  * **Asof join semantics.** Historical training rows MUST not see any
    information timestamped at-or-after game tip. The dataset builder
    enforces this; this module assumes the caller hands it pre-filtered
    inputs.
  * **No coupling to the existing nightly trainer.** A separate Phase
    13O trainer wires these features into a ``challengers/<date>_with_live_context/``
    artifact directory; the existing ``run_nightly_training_and_calibration.py``
    is byte-unchanged.

Pass token (recorded by the dataset builder):
    PHASE13O_LIVE_CONTEXT_FEATURES_PASS
"""
from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import Iterable, Optional


# Stable, deterministic feature column names. Phase 13O training and
# prediction both consume these — DO NOT rename without bumping
# feature_set_id.
LINEUP_FEATURE_COLUMNS = (
    "lineup_confirmed",
    "current_starter",
    "confirmed_starter",
    "confirmed_bench",
    "starter_changed_from_projection",
    "bench_changed_from_projection",
    "role_source_confirmed_lineup",
    "role_bucket_pre_lineup_encoded",
    "role_bucket_post_lineup_encoded",
    "minutes_projection_conflict",
    "confirmed_starter_low_minutes_flag",
    "confirmed_bench_high_minutes_flag",
    "lineup_position_encoded",
    "lineup_features_missing",
)

INJURY_FEATURE_COLUMNS = (
    "is_actionable",
    "is_confirmed_out",
    "is_inactive",
    "is_doubtful",
    "is_questionable",
    "is_probable",
    "injury_status_encoded",
    "availability_status_encoded",
    "injury_lineup_conflict",
    "injury_features_missing",
)

VACATED_OPPORTUNITY_FEATURE_COLUMNS = (
    "num_teammates_out_total",
    "num_teammates_out_guard",
    "num_teammates_out_wing",
    "num_teammates_out_big",
    "vacated_minutes_total",
    "vacated_minutes_guard",
    "vacated_minutes_wing",
    "vacated_minutes_big",
    "vacated_fga_total",
    "vacated_usage_proxy",
    "vacated_reb_chances_proxy",
    "vacated_ast_chances_proxy",
    "vacated_features_missing",
)

# Encodings for ordinal/categorical fields. These are stable across train
# and predict; do not reuse integers for new categories — append.
INJURY_STATUS_ENCODING = {
    "out": 5,
    "inactive": 5,
    "out for season": 5,
    "doubtful": 4,
    "questionable": 3,
    "game time decision": 3,
    "probable": 2,
    "available": 1,
    "active": 1,
    "": 0,
    None: 0,
}
AVAILABILITY_STATUS_ENCODING = INJURY_STATUS_ENCODING  # same scale

LINEUP_POSITION_ENCODING = {
    None: 0,
    "": 0,
    "PG": 1, "G": 1,
    "SG": 2,
    "SF": 3, "F": 3,
    "PF": 4,
    "C": 5,
}

ROLE_BUCKET_ENCODING = {
    None: 0,
    "": 0,
    "low_minutes": 1,
    "medium_minutes": 2,
    "high_minutes": 3,
    "starter": 4,
    "starter_promoted": 5,
    "bench_demoted": 1,
}

# Phase 13O feature-set identifier. Bump when changing the feature set in
# ways that would invalidate trained models.
FEATURE_SET_ID = "phase13o_live_context_v1"


def feature_set_id() -> str:
    return FEATURE_SET_ID


def feature_set_hash(columns: Optional[Iterable[str]] = None) -> str:
    """Stable hash of the live-context feature set's column list."""
    cols = (
        list(columns) if columns is not None
        else (
            list(LINEUP_FEATURE_COLUMNS)
            + list(INJURY_FEATURE_COLUMNS)
            + list(VACATED_OPPORTUNITY_FEATURE_COLUMNS)
        )
    )
    payload = "|".join(sorted(cols))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ── Lineup features ──────────────────────────────────────────────────


def join_lineup_features(prediction_rows, bdl_lineup_rows,
                           projected_minutes_threshold_starter: float = 18.0,
                           projected_minutes_threshold_bench: float = 30.0) -> dict:
    """Join BDL lineup rows into prediction rows in place.

    Mutates ``prediction_rows`` (a list of dicts) by writing every column
    listed in ``LINEUP_FEATURE_COLUMNS``. Returns a summary dict with
    integration counts (``lineup_rows_joined``, ``starter_flag_changed_count``,
    ``role_bucket_changed_count``, ``minutes_projection_conflict_count``).

    Inputs:
      prediction_rows: list of dicts, each with ``player_id``,
        ``game_id``, optional ``role_bucket``, ``exp_mp`` etc.
      bdl_lineup_rows: list of dicts, each with ``player_id``,
        ``game_id``, ``starter`` (bool), optional ``lineup_position``.
        When this list is empty / None, every prediction row gets
        ``lineup_features_missing=1`` and ``lineup_confirmed=False``.

    Returns ``summary`` dict — the same shape Phase 13M-bis produced, so
    the runner's existing manifest plumbing works unchanged.
    """
    summary = {
        "lineup_feature_columns_added": list(LINEUP_FEATURE_COLUMNS),
        "lineup_rows_joined": 0,
        "starter_flag_changed_count": 0,
        "role_bucket_changed_count": 0,
        "minutes_projection_conflict_count": 0,
        "lineup_blocker": "",
    }
    # Index BDL rows by (game_id, player_id).
    by_key = {}
    if bdl_lineup_rows:
        for r in bdl_lineup_rows:
            try:
                pid = int(r.get("player_id"))
            except Exception:
                continue
            gid = str(r.get("game_id")) if r.get("game_id") is not None else None
            by_key[(gid, pid)] = r
            by_key[(None, pid)] = r  # fallback when caller didn't supply gid

    # Initialize defaults on every row.
    for row in prediction_rows:
        row["lineup_confirmed"] = False
        row["current_starter"] = None
        row["confirmed_starter"] = False
        row["confirmed_bench"] = False
        row["starter_changed_from_projection"] = False
        row["bench_changed_from_projection"] = False
        row["role_source_confirmed_lineup"] = False
        pre = row.get("role_bucket")
        row["role_bucket_pre_lineup_encoded"] = ROLE_BUCKET_ENCODING.get(pre, 0)
        row["role_bucket_post_lineup_encoded"] = ROLE_BUCKET_ENCODING.get(pre, 0)
        row["minutes_projection_conflict"] = False
        row["confirmed_starter_low_minutes_flag"] = False
        row["confirmed_bench_high_minutes_flag"] = False
        row["lineup_position_encoded"] = 0
        row["lineup_features_missing"] = 1 if not by_key else 0

    if not by_key:
        summary["lineup_blocker"] = (
            "no BDL lineup rows supplied (lineups not posted, fetch failed, "
            "or backfill mode bypassed predict.py)"
        )
        return summary

    for row in prediction_rows:
        try:
            pid = int(row.get("player_id"))
        except Exception:
            continue
        gid = str(row.get("game_id")) if row.get("game_id") is not None else None
        match = by_key.get((gid, pid)) or by_key.get((None, pid))
        if not match:
            continue
        starter = bool(match.get("starter"))
        row["lineup_features_missing"] = 0
        row["lineup_confirmed"] = True
        row["current_starter"] = starter
        row["confirmed_starter"] = starter
        row["confirmed_bench"] = (not starter)
        row["role_source_confirmed_lineup"] = True
        # Lineup-position encoding.
        row["lineup_position_encoded"] = LINEUP_POSITION_ENCODING.get(
            match.get("lineup_position") or match.get("position"), 0
        )
        # Role-bucket transition rule (conservative documented rule).
        pre_label = row.get("role_bucket")
        if starter and pre_label not in (None, "starter", "starter_promoted"):
            row["role_bucket_post_lineup_encoded"] = ROLE_BUCKET_ENCODING["starter_promoted"]
            summary["role_bucket_changed_count"] += 1
            row["starter_changed_from_projection"] = True
        elif (not starter) and pre_label == "starter":
            row["role_bucket_post_lineup_encoded"] = ROLE_BUCKET_ENCODING["bench_demoted"]
            summary["role_bucket_changed_count"] += 1
            row["bench_changed_from_projection"] = True
        # Minutes-projection conflict heuristic.
        exp_mp = row.get("exp_mp")
        if exp_mp is not None:
            try:
                emp = float(exp_mp)
                if starter and emp < projected_minutes_threshold_starter:
                    row["minutes_projection_conflict"] = True
                    row["confirmed_starter_low_minutes_flag"] = True
                if (not starter) and emp >= projected_minutes_threshold_bench:
                    row["minutes_projection_conflict"] = True
                    row["confirmed_bench_high_minutes_flag"] = True
                if row["minutes_projection_conflict"]:
                    summary["minutes_projection_conflict_count"] += 1
            except Exception:
                pass
        summary["lineup_rows_joined"] += 1
        summary["starter_flag_changed_count"] += 1

    if summary["lineup_rows_joined"] == 0:
        summary["lineup_blocker"] = (
            "lineup parquet had no rows that matched any prediction "
            "(player_id, game_id) — confirmed lineup may not yet be posted"
        )
    return summary


# ── Injury / availability features ──────────────────────────────────


def join_injury_availability_features(prediction_rows, injury_rows,
                                        availability_rows) -> dict:
    """Join injury + availability context into prediction rows in place.

    Inputs may be empty lists; the result records ``injury_features_missing``
    accordingly. Both lists are expected to be already filtered to rows
    timestamped at-or-before tip (no-leakage is the caller's job).
    """
    inj_by_pid = {}
    for r in (injury_rows or []):
        try:
            pid = int(r.get("player_id") or r.get("nba_player_id"))
        except Exception:
            continue
        inj_by_pid[pid] = r
    avl_by_pid = {}
    for r in (availability_rows or []):
        try:
            pid = int(r.get("player_id"))
        except Exception:
            continue
        avl_by_pid[pid] = r

    summary = {
        "injury_feature_columns_added": list(INJURY_FEATURE_COLUMNS),
        "injury_rows_joined": 0,
        "availability_rows_joined": 0,
        "injury_lineup_conflicts": 0,
        "non_actionable_count": 0,
    }

    for row in prediction_rows:
        # Defaults.
        row["is_actionable"] = True
        row["is_confirmed_out"] = False
        row["is_inactive"] = False
        row["is_doubtful"] = False
        row["is_questionable"] = False
        row["is_probable"] = False
        row["injury_status_encoded"] = 0
        row["availability_status_encoded"] = 0
        row["injury_lineup_conflict"] = False
        row["injury_features_missing"] = 1 if not (inj_by_pid or avl_by_pid) else 0

        try:
            pid = int(row.get("player_id"))
        except Exception:
            continue
        inj = inj_by_pid.get(pid)
        avl = avl_by_pid.get(pid)
        if inj:
            summary["injury_rows_joined"] += 1
            status = str(inj.get("current_status") or inj.get("status") or "").lower().strip()
            row["injury_status_encoded"] = INJURY_STATUS_ENCODING.get(status, 0)
            row["is_confirmed_out"] = status in ("out", "out for season", "inactive", "injured")
            row["is_inactive"] = row["is_confirmed_out"]
            row["is_doubtful"] = (status == "doubtful")
            row["is_questionable"] = (status in ("questionable", "game time decision"))
            row["is_probable"] = (status == "probable")
            if row["is_confirmed_out"] or row["is_inactive"]:
                row["is_actionable"] = False
                summary["non_actionable_count"] += 1
        if avl:
            summary["availability_rows_joined"] += 1
            astatus = str(avl.get("availability_status") or "").lower().strip()
            row["availability_status_encoded"] = AVAILABILITY_STATUS_ENCODING.get(astatus, 0)
            # Availability "out" overrides actionability if injury report missing.
            if astatus in ("out", "inactive") and row["is_actionable"]:
                row["is_actionable"] = False
                row["is_confirmed_out"] = True
                summary["non_actionable_count"] += 1

        # Injury/lineup conflict: confirmed_starter=true but injury says out.
        if row.get("confirmed_starter") and row["is_confirmed_out"]:
            row["injury_lineup_conflict"] = True
            summary["injury_lineup_conflicts"] += 1

    return summary


# ── Vacated-opportunity features ────────────────────────────────────


def compute_vacated_opportunity_features(prediction_rows, availability_rows) -> dict:
    """Copy vacated-opportunity columns from availability rows into the
    prediction rows. Availability_asof.parquet already contains computed
    vacated_* features; we just thread them through with stable names.
    """
    avl_by_pid = {}
    for r in (availability_rows or []):
        try:
            pid = int(r.get("player_id"))
        except Exception:
            continue
        avl_by_pid[pid] = r

    fields_map = {
        "num_teammates_out_total": "num_teammates_out_total",
        "num_teammates_out_guard": "teammate_out_count_guard",
        "num_teammates_out_wing": "teammate_out_count_wing",
        "num_teammates_out_big": "teammate_out_count_big",
        "vacated_minutes_total": "vacated_minutes_total",
        "vacated_minutes_guard": "vacated_minutes_guard",
        "vacated_minutes_wing": "vacated_minutes_wing",
        "vacated_minutes_big": "vacated_minutes_big",
        "vacated_fga_total": "vacated_fga_total",
        "vacated_usage_proxy": "vacated_usage_proxy",
        "vacated_reb_chances_proxy": "vacated_reb_chances_proxy",
        "vacated_ast_chances_proxy": "vacated_ast_chances_proxy",
    }

    summary = {
        "vacated_feature_columns_added": list(VACATED_OPPORTUNITY_FEATURE_COLUMNS),
        "vacated_rows_joined": 0,
    }
    for row in prediction_rows:
        # Defaults — zero with missing indicator.
        for tgt in fields_map:
            row.setdefault(tgt, 0.0)
        row["vacated_features_missing"] = 1 if not avl_by_pid else 0
        try:
            pid = int(row.get("player_id"))
        except Exception:
            continue
        avl = avl_by_pid.get(pid)
        if not avl:
            continue
        for tgt, src in fields_map.items():
            v = avl.get(src)
            if v is not None:
                try:
                    row[tgt] = float(v)
                except Exception:
                    pass
        row["vacated_features_missing"] = 0
        summary["vacated_rows_joined"] += 1
    return summary


# ── Combined builder ────────────────────────────────────────────────


def build_live_context_features(prediction_rows, *,
                                  bdl_lineup_rows=None,
                                  injury_rows=None,
                                  availability_rows=None) -> dict:
    """Top-level helper that runs all three joiners in order. Mutates
    ``prediction_rows`` and returns a combined summary."""
    lineup_summary = join_lineup_features(prediction_rows, bdl_lineup_rows or [])
    injury_summary = join_injury_availability_features(
        prediction_rows, injury_rows or [], availability_rows or [],
    )
    vacated_summary = compute_vacated_opportunity_features(
        prediction_rows, availability_rows or [],
    )
    return {
        "feature_set_id": FEATURE_SET_ID,
        "feature_set_hash": feature_set_hash(),
        "lineup": lineup_summary,
        "injury": injury_summary,
        "vacated": vacated_summary,
        "all_columns": (
            list(LINEUP_FEATURE_COLUMNS)
            + list(INJURY_FEATURE_COLUMNS)
            + list(VACATED_OPPORTUNITY_FEATURE_COLUMNS)
        ),
    }


def encode_live_context_features(rows):
    """Final tidy-up step: cast booleans to ints for sklearn-compat
    consumers, leave NaN for genuinely missing numerics. Returns the
    column list actually populated."""
    bool_cols = (
        "lineup_confirmed", "confirmed_starter", "confirmed_bench",
        "starter_changed_from_projection", "bench_changed_from_projection",
        "role_source_confirmed_lineup", "minutes_projection_conflict",
        "confirmed_starter_low_minutes_flag", "confirmed_bench_high_minutes_flag",
        "is_actionable", "is_confirmed_out", "is_inactive", "is_doubtful",
        "is_questionable", "is_probable", "injury_lineup_conflict",
    )
    populated = set()
    for r in rows:
        for c in bool_cols:
            if c in r and isinstance(r[c], bool):
                r[c] = int(r[c])
                populated.add(c)
        for c in r:
            populated.add(c)
    return sorted(populated)
