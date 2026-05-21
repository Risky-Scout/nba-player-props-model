"""Canonical injury identity + availability propagation regression tests."""
from __future__ import annotations

import logging

import pandas as pd
import pytest

from nba_props_model.data.bdl_client import merge_injury_sources
from nba_props_model.data.injury_player_identity import (
    InjuryPlayerIdentityIndex,
    injury_report_team_to_abbr,
    parse_injury_name,
    resolve_injury_report_name,
)
from nba_props_model.delivery.delivery_contract import DEREK_UNIFIED_REQUIRED_COLUMNS
from nba_props_model.features.asof_feature_store import _populate_availability


def _stats(rows):
    return pd.DataFrame(
        rows,
        columns=["player_id", "player_name", "team_abbr", "game_date"],
    )


def _merge(bdl_map, nba_report, stats_df, *, slate_date="2026-05-20"):
    report: dict = {}
    out = merge_injury_sources(
        bdl_map,
        nba_report,
        stats_df,
        slate_date=slate_date,
        merge_report_out=report,
    )
    return out, report


AMBIGUOUS_INITIAL_FIXTURES: dict[str, list[tuple[str, str]]] = {
    "j. green": [("Jaylen Green", "HOU"), ("Josh Green", "CHA")],
    "j. williams": [("Jaylen Williams", "OKC"), ("Jalen Williams", "CHA")],
    "d. smith": [("Dennis Smith", "DAL"), ("Dorian Smith", "MIA")],
    "k. johnson": [("Keldon Johnson", "SAS"), ("Keshad Johnson", "MIA")],
    "d. jones": [("Derrick Jones", "LAC"), ("Damian Jones", "CLE")],
    "m. morris": [("Markieff Morris", "DAL"), ("Monte Morris", "PHX")],
    "m. bridges": [("Mikal Bridges", "NYK"), ("Miles Bridges", "CHA")],
    "a. wiggins": [("Andrew Wiggins", "GSW"), ("Aaron Wiggins", "OKC")],
    "t. jones": [("Tre Jones", "SAS"), ("Tyus Jones", "WAS")],
}


@pytest.mark.parametrize("injury_key", list(AMBIGUOUS_INITIAL_FIXTURES))
def test_ambiguous_initial_last_without_team_stays_unresolved(injury_key):
    """Test B: unmapped team + initial+last with multiple candidates stays unresolved."""
    players = AMBIGUOUS_INITIAL_FIXTURES[injury_key]
    stats = _stats(
        [(100 + i, name, team, "2026-05-18") for i, (name, team) in enumerate(players)]
    )
    nba = {injury_key: {"status": "OUT", "reason": "ankle"}}
    out, report = _merge({}, nba, stats)
    assert report["ambiguous_dropped"] == 0
    assert report["unmapped_team_initial_last_blocked"] == 1
    assert injury_key in report["unmapped_team_initial_last_names"]
    assert not any(v.get("source") == "nba_official" for v in out.values())


def test_unmapped_team_unique_initial_last_stays_unresolved():
    """Test A: unmapped team + globally unique initial+last must not resolve."""
    stats = _stats([(11, "Jalen Smith", "CHI", "2026-05-18")])
    nba = {"j. smith": {"status": "OUT", "reason": "hamstring"}}
    out, report = _merge({}, nba, stats)
    assert 11 not in out
    assert report["unmapped_team_initial_last_blocked"] == 1
    assert report["matched_initial_last_name"] == 0
    assert report["ambiguous_dropped"] == 0


def test_unmapped_team_with_bad_team_label_blocks_initial_last():
    """Test A variant: unmapped team label + unique initial+last stays unresolved."""
    stats = _stats([(11, "Jalen Smith", "CHI", "2026-05-18")])
    nba = {"j. smith": {"status": "OUT", "reason": "hamstring", "team": "Alpha Team"}}
    out, report = _merge({}, nba, stats)
    assert 11 not in out
    assert report["unmapped_team_initial_last_blocked"] == 1


def test_j_green_resolves_with_team_context():
    """Test C: mapped team + initial+last with one team candidate resolves."""
    stats = _stats(
        [
            (101, "Jaylen Green", "HOU", "2026-05-18"),
            (102, "Josh Green", "CHA", "2026-05-18"),
        ]
    )
    nba = {"j. green": {"status": "OUT", "reason": "ankle", "team": "Houston Rockets"}}
    out, report = _merge({}, nba, stats)
    assert 101 in out
    assert out[101]["source"] == "nba_official"
    assert report["matched_initial_last_name"] == 1


def test_j_smith_resolves_with_team_when_unique_on_roster():
    stats = _stats(
        [
            (11, "Jalen Smith", "CHI", "2026-05-18"),
            (12, "Jason Smith", "POR", "2026-05-18"),
        ]
    )
    nba = {"j. smith": {"status": "OUT", "reason": "hamstring", "team": "Chicago Bulls"}}
    out, report = _merge({}, nba, stats)
    assert 11 in out
    assert out[11]["status"] == "OUT"
    assert report["ambiguous_dropped"] == 0


def test_exact_full_name_unique_resolves_without_team():
    """Test D: unmapped team + exact full name unique globally resolves."""
    stats = _stats([(1, "LeBron James", "LAL", "2026-05-18")])
    nba = {"lebron james": {"status": "OUT", "reason": "ankle"}}
    out, report = _merge({}, nba, stats)
    assert out[1]["source"] == "nba_official"
    assert report["matched_exact"] == 1


def test_exact_full_name_duplicate_without_team_is_ambiguous():
    """Test E: unmapped team + exact full name duplicated globally is ambiguous."""
    stats = _stats(
        [
            (501, "Chris Smith", "MIA", "2026-05-18"),
            (502, "Chris Smith", "DAL", "2026-05-18"),
        ]
    )
    nba = {"chris smith": {"status": "OUT", "reason": "rest"}}
    out, report = _merge({}, nba, stats)
    assert report["ambiguous_dropped"] == 1
    assert 501 not in out or out[501].get("source") != "nba_official"


def test_exact_full_name_duplicate_with_team_resolves():
    stats = _stats(
        [
            (501, "Chris Smith", "MIA", "2026-05-18"),
            (502, "Chris Smith", "DAL", "2026-05-18"),
        ]
    )
    nba = {"chris smith": {"status": "OUT", "reason": "rest", "team": "Miami Heat"}}
    out, report = _merge({}, nba, stats)
    assert out[501]["source"] == "nba_official"
    assert report["matched_exact"] == 1


def test_suffix_name_never_initial_last_matches():
    """Test F: suffix names never fall through to initial+last."""
    stats = _stats(
        [
            (301, "Dennis Smith Jr", "DAL", "2026-05-18"),
            (302, "Jalen Smith", "CHI", "2026-05-18"),
        ]
    )
    nba = {"j. smith jr": {"status": "OUT", "reason": "hip"}}
    out, report = _merge({}, nba, stats)
    assert report["unmatched"] == 1
    assert all(v.get("source") != "nba_official" for v in out.values())


def test_unmatched_logs_separate_from_ambiguous(caplog):
    stats = _stats([(7, "Existing Player", "BOS", "2026-05-18")])
    nba = {
        "j. smith": {"status": "OUT", "reason": "hamstring"},
        "someone unknown": {"status": "OUT", "reason": "illness"},
    }
    with caplog.at_level(logging.WARNING):
        _, report = _merge({}, nba, stats)
    assert report["unmatched"] == 2
    assert report["unmapped_team_initial_last_blocked"] == 2
    assert report["ambiguous_dropped"] == 0
    assert any("injury_merge_unmatched" in r.message for r in caplog.records)
    assert not any("injury_merge_ambiguous" in r.message for r in caplog.records)


def test_alias_map_ambiguity_logged_separately_from_report_ambiguity(caplog):
    """Test G: alias-map ambiguity warnings separate from active injury-report ambiguous."""
    stats = _stats(
        [
            (11, "Jalen Smith", "CHI", "2026-05-18"),
            (12, "Jason Smith", "CHI", "2026-05-18"),
        ]
    )
    with caplog.at_level(logging.WARNING):
        _, report = _merge(
            {},
            {"j. smith": {"status": "OUT", "reason": "x", "team": "Chicago Bulls"}},
            stats,
        )
    assert report["alias_map_ambiguous_keys"]
    assert any("injury_merge_alias_ambiguous" in r.message for r in caplog.records)
    assert report["ambiguous_dropped"] == 1
    assert any("injury_merge_ambiguous" in r.message for r in caplog.records)


def test_bdl_entries_preserved_on_ambiguous_drop():
    bdl = {11: {"status": "GTD", "reason": "shoulder"}, 12: {"status": "GTD", "reason": "ankle"}}
    stats = _stats(
        [
            (11, "Jalen Smith", "CHI", "2026-05-18"),
            (12, "Jason Smith", "POR", "2026-05-18"),
        ]
    )
    out, _ = _merge(bdl, {"j. smith": {"status": "OUT", "reason": "hamstring"}}, stats)
    assert out[11]["source"] == "bdl_injuries_api"
    assert out[12]["source"] == "bdl_injuries_api"


def test_populate_availability_survives_merge_with_confidence_alias():
    snap = pd.DataFrame({"player_id": [1]})
    avail = pd.DataFrame(
        {
            "player_id": [1],
            "availability_status": ["questionable"],
            "prob_active": [0.55],
            "availability_confidence": [0.88],
            "availability_source": ["injury_report"],
            "minutes_restriction_flag": [False],
            "is_returning_from_absence": [False],
            "num_teammates_out_total": [1],
            "teammate_out_count_guard": [0],
            "teammate_out_count_wing": [1],
            "teammate_out_count_big": [0],
        }
    )
    out = _populate_availability(snap, avail)
    assert out.loc[0, "availability_status"] == "questionable"
    assert out.loc[0, "prob_active"] == pytest.approx(0.55)
    assert out.loc[0, "availability_confidence"] == pytest.approx(0.88)
    assert out.loc[0, "injury_status_current"] == "questionable"


def test_populate_availability_schema_missing_emits_explicit_report(capsys):
    snap = pd.DataFrame({"player_id": [1, 2]})
    out = _populate_availability(snap, pd.DataFrame())
    text = capsys.readouterr().out
    assert "AVAILABILITY_FEATURE_SCHEMA_MISSING" in text
    assert "rows=2" in text
    assert "availability_status" in out.columns
    assert out.loc[0, "availability_status"] == "source_unavailable"


def test_populate_availability_confidence_default_has_counted_reason(capsys):
    snap = pd.DataFrame({"player_id": [1]})
    avail = pd.DataFrame(
        {
            "player_id": [1],
            "availability_status": ["fresh"],
            "prob_active": [0.9],
        }
    )
    _populate_availability(snap, avail)
    text = capsys.readouterr().out
    assert "AVAILABILITY_CONFIDENCE_DEFAULTED" in text
    assert "defaulted_rows=1" in text


def test_derek_feed_contract_includes_injury_availability_surface_columns():
    required = set(DEREK_UNIFIED_REQUIRED_COLUMNS)
    assert {"injury_status", "injury_source", "inactive_risk", "stale_injury_flag"} <= required


def test_injury_report_team_to_abbr_maps_full_name():
    abbr, mapped = injury_report_team_to_abbr("Boston Celtics")
    assert abbr == "BOS"
    assert mapped is True
    abbr, mapped = injury_report_team_to_abbr("BOS")
    assert abbr == "BOS"
    assert mapped is True


def test_unmapped_team_does_not_force_scoped_resolution():
    abbr, mapped = injury_report_team_to_abbr("Alpha Team")
    assert mapped is False


def test_identity_index_respects_slate_date_roster():
    stats = _stats(
        [
            (900, "Old Roster Guy", "LAL", "2026-05-01"),
            (901, "New Roster Guy", "LAL", "2026-05-19"),
        ]
    )
    idx_early = InjuryPlayerIdentityIndex(stats, slate_date="2026-05-10")
    idx_late = InjuryPlayerIdentityIndex(stats, slate_date="2026-05-20")
    assert idx_late.resolve("old roster guy").player_id == 900
    assert idx_late.resolve("new roster guy").player_id == 901
    assert idx_early.resolve("new roster guy").outcome == "unmatched"


def test_parse_injury_name_detects_suffix():
    assert parse_injury_name("j. smith jr")[2] is True
    assert parse_injury_name("j. smith")[2] is False


def test_resolve_forbids_global_initial_last_without_team():
    stats = _stats([(101, "Jayson Tatum", "BOS", "2026-05-18")])
    index = InjuryPlayerIdentityIndex(stats, slate_date="2026-05-20")
    result = index.resolve("j. tatum")
    assert result.outcome == "unmatched"
    assert result.strategy == "unmapped_team_initial_last_not_allowed"
    assert result.player_id is None


def test_resolve_injury_report_name_uses_team_field():
    stats = _stats(
        [
            (201, "Tre Jones", "SAS", "2026-05-18"),
            (202, "Tyus Jones", "WAS", "2026-05-18"),
        ]
    )
    index = InjuryPlayerIdentityIndex(stats, slate_date="2026-05-20")
    result = resolve_injury_report_name(
        index,
        "t. jones",
        {"status": "OUT", "reason": "ankle", "team": "San Antonio Spurs"},
    )
    assert result.player_id == 201
    assert result.outcome == "resolved"
