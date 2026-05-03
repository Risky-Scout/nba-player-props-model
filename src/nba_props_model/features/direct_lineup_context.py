"""Phase 13S — direct lineup context features.

Phase 13R landed an additive contextual challenger that responded to
injury / vacated-opportunity / game-context features but did NOT
respond to direct live BDL ``lineup_confirmed`` / ``current_starter``
flips because those columns weren't trained signals — only the lagged
starter proxy was.

Phase 13S closes that gap by introducing a small set of **direct
lineup features** that occupy the same column slot at training time
(via a no-leakage proxy) and at predict time (via the live BDL
``current_starter`` flag). The model learns a coefficient on each
feature; at predict time the live signal flips it and the trained
model's deltas move accordingly.

No-leakage rule for the historical proxy:

    historical_current_starter = (previous_game_min >= 18.0)

That's a binary flag derived from the player's PREVIOUS game's
minutes. It is strictly pre-game knowable for the row's own game and
captures "this player is in the starter rotation at this point in the
season". The trainer documents the proxy explicitly in the
no_leakage_manifest's ``starter_proxy_used`` and
``starter_proxy_safe_for_training`` flags.

At predict time the same column is populated from the live BDL
lineup flag (or the lagged proxy when BDL is missing). When BDL flips
``current_starter`` from 0 to 1 the trained model's per-target Ridge
``predict()`` output moves by approximately the learned β coefficient.

This module exposes:

    DIRECT_LINEUP_FEATURE_COLUMNS          — single-row direct cols
    LINEUP_COMPOSITION_FEATURE_COLUMNS     — team-aggregate cols
    PLAYER_IN_LINEUP_INTERACTION_COLUMNS   — player×team interaction
    DIRECT_LINEUP_FEATURE_SET_ID           — stable ID
    apply_direct_lineup_overlay(...)       — predict-time helper

Pass token (consumed by verifiers):
    PHASE13S_DIRECT_LINEUP_FEATURE_LAYER_PASS
"""
from __future__ import annotations

from typing import Iterable, Mapping


DIRECT_LINEUP_FEATURE_SET_ID = "phase13s_direct_lineup_injury_pmf_driver_v1"


# ── Single-row direct lineup features (the BDL columns at predict time) ──
DIRECT_LINEUP_FEATURE_COLUMNS = (
    "lineup_confirmed",
    "current_starter",
    "confirmed_starter",
    "confirmed_bench",
    "starter_changed_from_projection",
    "bench_changed_from_projection",
    "role_source_confirmed_lineup",
    "lineup_position_encoded",
    "minutes_projection_conflict",
    "confirmed_starter_low_minutes_flag",
    "confirmed_bench_high_minutes_flag",
    "consecutive_starter_streak",
    "recent_starter_rate_5",
    "lineup_features_missing",
)


# ── Team-aggregate lineup composition features ──────────────────────
LINEUP_COMPOSITION_FEATURE_COLUMNS = (
    "team_confirmed_starters_count",
    "team_confirmed_bench_count",
    "team_lineup_num_guards",
    "team_lineup_num_wings",
    "team_lineup_num_bigs",
    "team_lineup_num_high_usage_players",
    "team_lineup_num_primary_ballhandlers",
    "team_lineup_num_shooters",
    "team_lineup_num_rebounders",
    "team_lineup_usage_competition_proxy",
    "team_lineup_rebound_competition_proxy",
    "team_lineup_assist_creation_proxy",
    "team_lineup_spacing_proxy",
    "team_lineup_turnover_pressure_proxy",
)


# ── Player × lineup interaction features ────────────────────────────
PLAYER_IN_LINEUP_INTERACTION_COLUMNS = (
    "player_confirmed_with_high_usage_count",
    "player_confirmed_with_primary_ballhandler_count",
    "player_confirmed_with_big_count",
    "player_confirmed_with_shooter_count",
    "player_usage_competition_proxy",
    "player_rebound_competition_proxy",
    "player_assist_target_quality_proxy",
    "player_spacing_support_proxy",
    "player_onball_burden_proxy",
)


# Training-time minute thresholds (NBA convention).
STARTER_MIN_THRESHOLD = 18.0   # pre-game knowable proxy via prev-game min
BENCH_MIN_LOWER = 1.0
BENCH_MIN_UPPER = STARTER_MIN_THRESHOLD


# Position encoding (matches live_context.LINEUP_POSITION_ENCODING).
POSITION_ENCODING = {
    None: 0, "": 0, "PG": 1, "G": 1, "SG": 2,
    "SF": 3, "F": 3, "PF": 4, "C": 5,
}

GUARD_POSITIONS = {"PG", "G", "SG"}
WING_POSITIONS = {"SF", "F", "SG"}
BIG_POSITIONS = {"PF", "C", "F-C", "C-F"}


def _safe_float(v, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        return float(v)
    except Exception:
        return default


def apply_direct_lineup_overlay(rows, *,
                                 bdl_lineup_rows=None,
                                 lagged_player_stats=None) -> dict:
    """Phase 13S predict-time overlay.

    Mutates ``rows`` (a list of dicts) by writing the direct lineup
    features. When ``bdl_lineup_rows`` is provided, the BDL-derived
    flags (``lineup_confirmed``, ``current_starter``, ...) win;
    otherwise the lagged-proxy fallback fills them.

    ``lagged_player_stats`` (optional) is a dict keyed by ``player_id``
    carrying the player's most-recent prior-game ``min`` and the
    consecutive-starter streak — those drive the lagged proxy.

    Returns a summary dict for the snapshot manifest.
    """
    summary = {
        "feature_set_id": DIRECT_LINEUP_FEATURE_SET_ID,
        "lineup_rows_joined": 0,
        "starter_flag_changed_count": 0,
        "rows_seen": 0,
        "bdl_supplied": bool(bdl_lineup_rows),
    }

    by_key: dict = {}
    if bdl_lineup_rows:
        for r in bdl_lineup_rows:
            try:
                pid = int(r.get("player_id"))
            except Exception:
                continue
            gid = str(r.get("game_id")) if r.get("game_id") is not None else None
            by_key[(gid, pid)] = r
            by_key[(None, pid)] = r

    lps = lagged_player_stats or {}

    for row in rows:
        summary["rows_seen"] += 1
        try:
            pid = int(row.get("player_id"))
        except Exception:
            pid = None
        gid = str(row.get("game_id")) if row.get("game_id") is not None else None
        match = by_key.get((gid, pid)) or by_key.get((None, pid)) if pid is not None else None

        # Defaults — lagged-proxy fallback when no BDL row.
        prev_min = _safe_float((lps.get(pid) or {}).get("prev_game_min"), 0.0)
        consec_streak = _safe_float(
            (lps.get(pid) or {}).get("consecutive_starter_streak"), 0.0)
        recent_rate_5 = _safe_float(
            (lps.get(pid) or {}).get("recent_starter_rate_5"), 0.0)

        proxy_starter = 1.0 if prev_min >= STARTER_MIN_THRESHOLD else 0.0
        proxy_bench = (
            1.0 if (BENCH_MIN_LOWER <= prev_min < BENCH_MIN_UPPER) else 0.0
        )

        if match is not None:
            starter = bool(match.get("starter"))
            row["lineup_confirmed"] = 1
            row["current_starter"] = 1.0 if starter else 0.0
            row["confirmed_starter"] = 1.0 if starter else 0.0
            row["confirmed_bench"] = 0.0 if starter else 1.0
            row["role_source_confirmed_lineup"] = 1
            row["lineup_position_encoded"] = POSITION_ENCODING.get(
                match.get("lineup_position") or match.get("position"), 0)
            row["lineup_features_missing"] = 0
            summary["lineup_rows_joined"] += 1
            # Live vs lagged conflict counters.
            if (starter and proxy_starter == 0.0) or (not starter and proxy_starter == 1.0):
                summary["starter_flag_changed_count"] += 1
                row["starter_changed_from_projection"] = 1
            else:
                row["starter_changed_from_projection"] = 0
            row["bench_changed_from_projection"] = (
                1 if (not starter and proxy_bench == 0.0) else 0
            )
        else:
            # Lagged-proxy fallback.
            row["lineup_confirmed"] = 0
            row["current_starter"] = proxy_starter
            row["confirmed_starter"] = proxy_starter
            row["confirmed_bench"] = proxy_bench
            row["role_source_confirmed_lineup"] = 0
            row["lineup_position_encoded"] = POSITION_ENCODING.get(
                row.get("position"), 0)
            row["lineup_features_missing"] = 1
            row["starter_changed_from_projection"] = 0
            row["bench_changed_from_projection"] = 0

        row["consecutive_starter_streak"] = consec_streak
        row["recent_starter_rate_5"] = recent_rate_5

        # Minutes-projection conflict heuristic (BDL says starter, exp_mp low).
        emp = _safe_float(row.get("exp_mp"), 0.0)
        if row["confirmed_starter"] >= 0.5 and emp < STARTER_MIN_THRESHOLD:
            row["confirmed_starter_low_minutes_flag"] = 1
            row["minutes_projection_conflict"] = 1
        else:
            row["confirmed_starter_low_minutes_flag"] = 0
            row.setdefault("minutes_projection_conflict", 0)
        if row["confirmed_bench"] >= 0.5 and emp >= 30.0:
            row["confirmed_bench_high_minutes_flag"] = 1
            row["minutes_projection_conflict"] = 1
        else:
            row["confirmed_bench_high_minutes_flag"] = 0

    return summary


def feature_set_id() -> str:
    return DIRECT_LINEUP_FEATURE_SET_ID


def all_columns() -> list[str]:
    return (
        list(DIRECT_LINEUP_FEATURE_COLUMNS)
        + list(LINEUP_COMPOSITION_FEATURE_COLUMNS)
        + list(PLAYER_IN_LINEUP_INTERACTION_COLUMNS)
    )
