"""Phase 13S — lineup-composition / player×lineup interaction helpers.

Provides leakage-safe construction of team-aggregate lineup
composition features and player×lineup interaction features. The
helpers operate on **lagged** per-player stats — never same-game
production — so they are pre-game knowable for the row's own game.

Definitions:

  * "Expected to play tonight" = a teammate whose most-recent prior
    game's ``min`` >= 1. This is the leakage-safe approximation of the
    BDL active list. At predict time the caller can replace this with
    the BDL-confirmed active list.
  * "High usage" = teammate whose lag-10 ``usage_proxy`` (computed as
    ``(fga + 0.44 * fta + tov) / max(min, 0.5)``) is >= 0.6.
  * "Primary ballhandler" = teammate whose lag-10 ``ast_per_min`` is
    >= 0.18.
  * "Shooter" = teammate whose lag-10 ``fg3_attempt_rate`` is >= 0.25.
  * "Rebounder" = teammate whose lag-10 ``reb_per_min`` is >= 0.25.
  * "Big" = teammate listed at position in {C, PF, F-C, C-F}.
  * "Guard" / "Wing" — by position.

For each row (player, game) we compute team-aggregate counts,
competition proxies (sum of teammates' usage / rebound), and the
player×lineup interaction columns (``player_*_count``,
``player_*_competition_proxy``).

These columns are stable feature-list members of the Phase 13S
trained models, so the model learns coefficients on them.
"""
from __future__ import annotations

from typing import Iterable

USAGE_HIGH_THRESHOLD = 0.6
PRIMARY_BH_THRESHOLD = 0.18
SHOOTER_FG3_RATE_THRESHOLD = 0.25
REBOUNDER_REB_PER_MIN_THRESHOLD = 0.25


GUARD_POSITIONS = {"PG", "G", "SG"}
WING_POSITIONS = {"SF", "F"}
BIG_POSITIONS = {"PF", "C", "F-C", "C-F"}


def classify_role(*, position, usage_proxy: float, ast_per_min: float,
                    fg3_rate: float, reb_per_min: float) -> dict[str, bool]:
    """Return a dict of role flags for a teammate's lagged profile."""
    if position is None:
        pos = ""
    elif isinstance(position, str):
        pos = position.upper()
    else:
        try:
            pos = str(position).upper()
        except Exception:
            pos = ""
        if pos in ("NAN", "NONE"):
            pos = ""
    return {
        "is_guard": pos in GUARD_POSITIONS,
        "is_wing": pos in WING_POSITIONS,
        "is_big": pos in BIG_POSITIONS,
        "is_high_usage": float(usage_proxy or 0.0) >= USAGE_HIGH_THRESHOLD,
        "is_primary_ballhandler": float(ast_per_min or 0.0) >= PRIMARY_BH_THRESHOLD,
        "is_shooter": float(fg3_rate or 0.0) >= SHOOTER_FG3_RATE_THRESHOLD,
        "is_rebounder": float(reb_per_min or 0.0) >= REBOUNDER_REB_PER_MIN_THRESHOLD,
    }


def aggregate_team_lineup(teammates: Iterable[dict]) -> dict[str, float]:
    """Aggregate role classifications across teammates expected to play.

    Each teammate dict must carry pre-game knowable lagged stats:
    ``position``, ``usage_proxy_lagged``, ``ast_per_min_lagged``,
    ``fg3_attempt_rate_lagged``, ``reb_per_min_lagged``,
    ``starter_proxy_lagged`` (binary), ``mp_mean_last10`` (minutes),
    ``expected_to_play`` (binary).
    """
    counts = {
        "team_confirmed_starters_count": 0.0,
        "team_confirmed_bench_count": 0.0,
        "team_lineup_num_guards": 0.0,
        "team_lineup_num_wings": 0.0,
        "team_lineup_num_bigs": 0.0,
        "team_lineup_num_high_usage_players": 0.0,
        "team_lineup_num_primary_ballhandlers": 0.0,
        "team_lineup_num_shooters": 0.0,
        "team_lineup_num_rebounders": 0.0,
        "team_lineup_usage_competition_proxy": 0.0,
        "team_lineup_rebound_competition_proxy": 0.0,
        "team_lineup_assist_creation_proxy": 0.0,
        "team_lineup_spacing_proxy": 0.0,
        "team_lineup_turnover_pressure_proxy": 0.0,
    }
    for tm in teammates:
        if not tm.get("expected_to_play"):
            continue
        roles = classify_role(
            position=tm.get("position"),
            usage_proxy=tm.get("usage_proxy_lagged") or 0.0,
            ast_per_min=tm.get("ast_per_min_lagged") or 0.0,
            fg3_rate=tm.get("fg3_attempt_rate_lagged") or 0.0,
            reb_per_min=tm.get("reb_per_min_lagged") or 0.0,
        )
        if tm.get("starter_proxy_lagged"):
            counts["team_confirmed_starters_count"] += 1.0
        else:
            counts["team_confirmed_bench_count"] += 1.0
        if roles["is_guard"]:
            counts["team_lineup_num_guards"] += 1.0
        if roles["is_wing"]:
            counts["team_lineup_num_wings"] += 1.0
        if roles["is_big"]:
            counts["team_lineup_num_bigs"] += 1.0
        if roles["is_high_usage"]:
            counts["team_lineup_num_high_usage_players"] += 1.0
        if roles["is_primary_ballhandler"]:
            counts["team_lineup_num_primary_ballhandlers"] += 1.0
        if roles["is_shooter"]:
            counts["team_lineup_num_shooters"] += 1.0
        if roles["is_rebounder"]:
            counts["team_lineup_num_rebounders"] += 1.0
        counts["team_lineup_usage_competition_proxy"] += float(
            tm.get("usage_proxy_lagged") or 0.0)
        counts["team_lineup_rebound_competition_proxy"] += float(
            tm.get("reb_per_min_lagged") or 0.0)
        counts["team_lineup_assist_creation_proxy"] += float(
            tm.get("ast_per_min_lagged") or 0.0)
        counts["team_lineup_spacing_proxy"] += float(
            tm.get("fg3_attempt_rate_lagged") or 0.0)
        counts["team_lineup_turnover_pressure_proxy"] += float(
            tm.get("tov_per_min_lagged") or 0.0)
    return counts


def player_in_lineup_interactions(*, player_row: dict,
                                    teammates: Iterable[dict]) -> dict[str, float]:
    """Compute the player × lineup-composition interaction features.

    These are the features the trained model uses to learn how the
    player's PMF shifts as a function of who they share the floor with.
    """
    own_usage = float(player_row.get("usage_proxy_lagged") or 0.0)
    own_reb = float(player_row.get("reb_per_min_lagged") or 0.0)
    own_ast = float(player_row.get("ast_per_min_lagged") or 0.0)
    own_3p = float(player_row.get("fg3_attempt_rate_lagged") or 0.0)
    out = {
        "player_confirmed_with_high_usage_count": 0.0,
        "player_confirmed_with_primary_ballhandler_count": 0.0,
        "player_confirmed_with_big_count": 0.0,
        "player_confirmed_with_shooter_count": 0.0,
        "player_usage_competition_proxy": 0.0,
        "player_rebound_competition_proxy": 0.0,
        "player_assist_target_quality_proxy": 0.0,
        "player_spacing_support_proxy": 0.0,
        "player_onball_burden_proxy": 0.0,
    }
    n_teammates_playing = 0
    for tm in teammates:
        if not tm.get("expected_to_play"):
            continue
        n_teammates_playing += 1
        roles = classify_role(
            position=tm.get("position"),
            usage_proxy=tm.get("usage_proxy_lagged") or 0.0,
            ast_per_min=tm.get("ast_per_min_lagged") or 0.0,
            fg3_rate=tm.get("fg3_attempt_rate_lagged") or 0.0,
            reb_per_min=tm.get("reb_per_min_lagged") or 0.0,
        )
        if roles["is_high_usage"]:
            out["player_confirmed_with_high_usage_count"] += 1.0
        if roles["is_primary_ballhandler"]:
            out["player_confirmed_with_primary_ballhandler_count"] += 1.0
        if roles["is_big"]:
            out["player_confirmed_with_big_count"] += 1.0
        if roles["is_shooter"]:
            out["player_confirmed_with_shooter_count"] += 1.0
        out["player_usage_competition_proxy"] += float(tm.get("usage_proxy_lagged") or 0.0)
        out["player_rebound_competition_proxy"] += float(tm.get("reb_per_min_lagged") or 0.0)
        # assist creation by teammates → assist-target quality for this player.
        out["player_assist_target_quality_proxy"] += float(tm.get("ast_per_min_lagged") or 0.0)
        out["player_spacing_support_proxy"] += float(tm.get("fg3_attempt_rate_lagged") or 0.0)

    # On-ball burden: low primary-ballhandler count + own ast usage.
    out["player_onball_burden_proxy"] = (
        own_ast / (out["player_confirmed_with_primary_ballhandler_count"] + 1.0)
    )
    # Net usage room = own usage - share of competition normalized.
    if n_teammates_playing > 0:
        out["player_usage_competition_proxy"] = (
            out["player_usage_competition_proxy"] / max(1, n_teammates_playing)
        )
        out["player_rebound_competition_proxy"] = (
            out["player_rebound_competition_proxy"] / max(1, n_teammates_playing)
        )
        out["player_assist_target_quality_proxy"] = (
            out["player_assist_target_quality_proxy"] / max(1, n_teammates_playing)
        )
        out["player_spacing_support_proxy"] = (
            out["player_spacing_support_proxy"] / max(1, n_teammates_playing)
        )
    return out
