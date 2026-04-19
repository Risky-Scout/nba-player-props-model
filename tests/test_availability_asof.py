"""Tests for the as-of availability feature builder.

The central guarantee is strict as-of correctness: a feature row dated D
may only use raw data with timestamp strictly before D. Any leak of
post-game information would make historical training distribution
different from inference distribution and undo the Phase 2 rebuild.
"""
from __future__ import annotations

import pandas as pd
import pytest

from nba_props_model.features.availability_asof import (
    ARCHETYPES,
    AvailabilityBuilder,
    CONF_HIGH,
    CONF_LOW,
    CONF_MEDIUM,
    STATUS_ACTIVE,
    STATUS_OUT,
    STATUS_QUESTIONABLE,
    STATUS_UNKNOWN,
    _normalize_name,
    archetype_from_position,
    normalize_status,
)


# ─── helpers ──────────────────────────────────────────────────────────────────


def _make_builder() -> AvailabilityBuilder:
    injury_reports = pd.DataFrame([
        # 2024-11-10 — Team Alpha: two OUT (one guard, one big) + one QUESTIONABLE
        {"report_date": "2024-11-10", "report_hour": 8, "game_date": "11/10/2024",
         "matchup": "ALPHA @ BETA", "team": "Alpha Team",
         "player_name_raw": "Guard, Absent", "current_status": "Out",
         "reason": "injury", "dnp_injury": 1, "dnp_rest": 0, "dnp_coach_decision": 0},
        {"report_date": "2024-11-10", "report_hour": 8, "game_date": "11/10/2024",
         "matchup": "ALPHA @ BETA", "team": "Alpha Team",
         "player_name_raw": "Big, Absent", "current_status": "Out",
         "reason": "injury", "dnp_injury": 1, "dnp_rest": 0, "dnp_coach_decision": 0},
        {"report_date": "2024-11-10", "report_hour": 8, "game_date": "11/10/2024",
         "matchup": "ALPHA @ BETA", "team": "Alpha Team",
         "player_name_raw": "Starter, Question", "current_status": "Questionable",
         "reason": "soreness", "dnp_injury": 0, "dnp_rest": 0, "dnp_coach_decision": 0},
        # Later report date, must NOT leak backward.
        {"report_date": "2024-11-15", "report_hour": 8, "game_date": "11/15/2024",
         "matchup": "ALPHA @ GAMMA", "team": "Alpha Team",
         "player_name_raw": "Starter, Question", "current_status": "Out",
         "reason": "back", "dnp_injury": 1, "dnp_rest": 0, "dnp_coach_decision": 0},
    ])

    # Game history: enough rows to exercise the 10-game rolling window.
    rows = []
    for d in [f"2024-11-{day:02d}" for day in (1, 3, 5, 7, 9)]:
        rows.extend([
            {"player_id": 1, "player_name": "Absent Guard",    "game_id": d,
             "game_date": d, "season": 2024, "team_id": 10, "team_abbr": "ALP",
             "min": 30, "pts": 12, "reb": 3, "ast": 6, "fg3m": 2, "stl": 1, "blk": 0,
             "fga": 12, "fg3a": 5, "fta": 2, "ftm": 2,
             "fg_pct": 0.5, "fg3_pct": 0.4, "ft_pct": 1.0,
             "oreb": 1, "dreb": 2, "turnover": 2, "pf": 1, "plus_minus": 0,
             "position": "G",
             "home_team_id": 10, "visitor_team_id": 20},
            {"player_id": 2, "player_name": "Absent Big",      "game_id": d,
             "game_date": d, "season": 2024, "team_id": 10, "team_abbr": "ALP",
             "min": 28, "pts": 14, "reb": 9, "ast": 1, "fg3m": 0, "stl": 0, "blk": 2,
             "fga": 10, "fg3a": 0, "fta": 4, "ftm": 4,
             "fg_pct": 0.5, "fg3_pct": 0.0, "ft_pct": 1.0,
             "oreb": 3, "dreb": 6, "turnover": 1, "pf": 2, "plus_minus": 0,
             "position": "C",
             "home_team_id": 10, "visitor_team_id": 20},
            {"player_id": 3, "player_name": "Question Starter", "game_id": d,
             "game_date": d, "season": 2024, "team_id": 10, "team_abbr": "ALP",
             "min": 32, "pts": 20, "reb": 4, "ast": 5, "fg3m": 3, "stl": 1, "blk": 1,
             "fga": 15, "fg3a": 6, "fta": 3, "ftm": 3,
             "fg_pct": 0.5, "fg3_pct": 0.5, "ft_pct": 1.0,
             "oreb": 1, "dreb": 3, "turnover": 2, "pf": 2, "plus_minus": 0,
             "position": "F",
             "home_team_id": 10, "visitor_team_id": 20},
            {"player_id": 4, "player_name": "Healthy Wing",    "game_id": d,
             "game_date": d, "season": 2024, "team_id": 10, "team_abbr": "ALP",
             "min": 24, "pts": 10, "reb": 5, "ast": 3, "fg3m": 1, "stl": 1, "blk": 0,
             "fga": 8, "fg3a": 3, "fta": 2, "ftm": 2,
             "fg_pct": 0.5, "fg3_pct": 0.33, "ft_pct": 1.0,
             "oreb": 1, "dreb": 4, "turnover": 1, "pf": 1, "plus_minus": 0,
             "position": "F",
             "home_team_id": 10, "visitor_team_id": 20},
        ])
    # The player of interest: played only 3 of 5 games, absent the last two.
    # Let's say player 5 is the one we query.
    for d in ["2024-11-01", "2024-11-03", "2024-11-05"]:
        rows.append({
            "player_id": 5, "player_name": "Query Player", "game_id": d,
            "game_date": d, "season": 2024, "team_id": 10, "team_abbr": "ALP",
            "min": 28, "pts": 18, "reb": 4, "ast": 6, "fg3m": 2, "stl": 1, "blk": 0,
            "fga": 12, "fg3a": 5, "fta": 2, "ftm": 2,
            "fg_pct": 0.5, "fg3_pct": 0.4, "ft_pct": 1.0,
            "oreb": 1, "dreb": 3, "turnover": 2, "pf": 1, "plus_minus": 0,
            "position": "G",
            "home_team_id": 10, "visitor_team_id": 20,
        })
    game_stats = pd.DataFrame(rows)

    positions = pd.DataFrame([
        {"player_id": 1, "position": "G"},
        {"player_id": 2, "position": "C"},
        {"player_id": 3, "position": "F"},
        {"player_id": 4, "position": "F"},
        {"player_id": 5, "position": "G"},
    ])

    return AvailabilityBuilder(
        injury_reports=injury_reports,
        game_stats=game_stats,
        positions=positions,
    )


# ─── normalization ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("raw, expected", [
    ("Clarke, Brandon",     "brandon clarke"),
    ("Brandon Clarke",      "brandon clarke"),
    ("Pippen Jr., Scotty",  "scotty pippen"),
    ("Scotty Pippen Jr.",   "scotty pippen"),
    ("O'Neal, Shaquille",   "shaquille oneal"),
    ("Luka Dončić",         "luka dončić"),   # unicode preserved
    (None,                  ""),
    ("",                    ""),
])
def test_normalize_name_roundtrips_both_formats(raw, expected):
    assert _normalize_name(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("Out",           STATUS_OUT),
    ("OUT",           STATUS_OUT),
    ("Out for Season", STATUS_OUT),
    ("Doubtful",      "DOUBTFUL"),
    ("Questionable",  STATUS_QUESTIONABLE),
    ("Probable",      "PROBABLE"),
    ("Available",     STATUS_ACTIVE),
    ("Active",        STATUS_ACTIVE),
    ("",              STATUS_UNKNOWN),
    (None,            STATUS_UNKNOWN),
    ("   ",           STATUS_UNKNOWN),
])
def test_normalize_status_collapses_variants(raw, expected):
    assert normalize_status(raw) == expected


@pytest.mark.parametrize("position, expected", [
    ("G",    "guard"),
    ("PG",   "guard"),
    ("F",    "wing"),
    ("SF",   "wing"),
    ("G-F",  "wing"),
    ("C",    "big"),
    ("F-C",  "big"),
    ("",     "wing"),     # default
    (None,   "wing"),
])
def test_archetype_bucketing(position, expected):
    assert archetype_from_position(position) == expected


# ─── core feature build ──────────────────────────────────────────────────────


def test_day_reports_resolve_to_features_for_query_player():
    """Player with a game on 11-10-2024 inherits team's absences as teammate_*."""
    builder = _make_builder()
    pairs = pd.DataFrame([{
        "player_id": 5, "team_id": 10, "game_date": "2024-11-10",
    }])
    feats = builder.features_for(pairs).iloc[0]

    # Player 5 has no injury report → implicit active (HIGH confidence since
    # we are in the injury-report coverage window).
    assert feats["availability_status"] == STATUS_ACTIVE
    assert feats["availability_confidence"] == CONF_HIGH
    assert feats["availability_source"] == "implicit_active"

    # Teammates 1 (guard) and 2 (big) are OUT, 3 (wing) is QUESTIONABLE.
    assert feats["teammate_out_count_guard"] == 1
    assert feats["teammate_out_count_big"] == 1
    assert feats["teammate_out_count_wing"] == 0
    assert feats["teammate_questionable_count_wing"] == 1
    assert feats["num_teammates_out_total"] == 2
    # Vacated minutes pulled from the absent teammates' rolling averages.
    assert feats["vacated_minutes_guard"] > 0
    assert feats["vacated_minutes_big"] > 0
    assert feats["vacated_minutes_wing"] == 0


# ─── leakage guarantees ──────────────────────────────────────────────────────


def test_no_future_injury_report_leaks_into_earlier_row():
    """The 11-15 OUT flip for Question Starter must not affect the 11-10 row."""
    builder = _make_builder()
    pairs = pd.DataFrame([{
        "player_id": 3, "team_id": 10, "game_date": "2024-11-10",
    }])
    feats = builder.features_for(pairs).iloc[0]
    # On 11-10 the report said QUESTIONABLE, not OUT.
    assert feats["availability_status"] == STATUS_QUESTIONABLE


def test_no_future_game_leaks_into_teammate_rolling():
    """If a teammate's stat row falls on or after the query date it must not
    contribute to vacated_minutes / vacated_fga."""
    builder = _make_builder()
    # Inject a *post-date* game for player 1 with extreme minutes.
    cheat_row = pd.DataFrame([{
        "player_id": 1, "player_name": "Absent Guard", "game_id": "future",
        "game_date": "2024-11-20", "season": 2024, "team_id": 10, "team_abbr": "ALP",
        "min": 99, "fga": 99, "pts": 0, "reb": 0, "ast": 0, "fg3m": 0,
        "stl": 0, "blk": 0, "fg3a": 0, "fta": 0, "ftm": 0,
        "fg_pct": 0, "fg3_pct": 0, "ft_pct": 0,
        "oreb": 0, "dreb": 0, "turnover": 0, "pf": 0, "plus_minus": 0,
        "position": "G",
        "home_team_id": 10, "visitor_team_id": 20,
    }])
    poisoned = pd.concat([builder.game_stats, cheat_row], ignore_index=True)
    poisoned_builder = AvailabilityBuilder(
        injury_reports=builder.injury_reports,
        game_stats=poisoned.drop(columns=["name_norm"], errors="ignore"),
        positions=builder.positions.drop(columns=["archetype"], errors="ignore"),
    )

    clean = builder.features_for(pd.DataFrame([{
        "player_id": 5, "team_id": 10, "game_date": "2024-11-10",
    }])).iloc[0]
    post = poisoned_builder.features_for(pd.DataFrame([{
        "player_id": 5, "team_id": 10, "game_date": "2024-11-10",
    }])).iloc[0]

    assert clean["vacated_minutes_guard"] == post["vacated_minutes_guard"]
    assert clean["vacated_fga_total"] == post["vacated_fga_total"]


def test_determinism_same_input_same_output():
    """Two identical calls to features_for on the same builder yield equal rows."""
    builder = _make_builder()
    pairs = pd.DataFrame([{
        "player_id": 5, "team_id": 10, "game_date": "2024-11-10",
    }])
    a = builder.features_for(pairs)
    b = builder.features_for(pairs)
    pd.testing.assert_frame_equal(a, b)


def test_empty_history_emits_low_confidence_unknown_row():
    """A player with no prior games gets STATUS_UNKNOWN + CONF_LOW, no NaN floods."""
    builder = _make_builder()
    pairs = pd.DataFrame([{
        "player_id": 999, "team_id": 10, "game_date": "2024-11-10",
    }])
    feats = builder.features_for(pairs).iloc[0]
    assert feats["availability_status"] == STATUS_UNKNOWN
    assert feats["availability_confidence"] == CONF_LOW
    # Timeline features should be None/False, not NaN.
    assert feats["games_since_last_played"] is None
    assert bool(feats["is_returning_from_absence"]) is False


# ─── schema invariants ────────────────────────────────────────────────────────


def test_features_for_emits_expected_columns():
    builder = _make_builder()
    pairs = pd.DataFrame([{
        "player_id": 5, "team_id": 10, "game_date": "2024-11-10",
    }])
    cols = set(builder.features_for(pairs).columns)
    required = {
        "player_id", "game_date", "team_id",
        "availability_status", "prob_active",
        "availability_confidence", "availability_source",
        "games_since_last_played", "days_since_last_played",
        "is_returning_from_absence", "minutes_restriction_flag",
        "num_teammates_out_total", "vacated_fga_total",
    }
    for arch in ARCHETYPES:
        required.add(f"teammate_out_count_{arch}")
        required.add(f"teammate_questionable_count_{arch}")
        required.add(f"vacated_minutes_{arch}")
    missing = required - cols
    assert not missing, f"missing columns: {missing}"


def test_prob_active_in_unit_interval():
    builder = _make_builder()
    pairs = pd.DataFrame([
        {"player_id": 1, "team_id": 10, "game_date": "2024-11-10"},
        {"player_id": 3, "team_id": 10, "game_date": "2024-11-10"},
        {"player_id": 5, "team_id": 10, "game_date": "2024-11-10"},
    ])
    feats = builder.features_for(pairs)
    assert (feats["prob_active"] >= 0).all()
    assert (feats["prob_active"] <= 1).all()
