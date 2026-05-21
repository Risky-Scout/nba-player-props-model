"""Tests for the hardened merge_injury_sources logic in bdl_client.

Covers:
  * exact full-name match
  * unique first-initial + last-name fallback match
  * ambiguous (initial + last_name) drop with bdl-side preservation
  * full miss (no plausible match anywhere)
  * empty NBA-report path still tags every bdl entry with a source
  * suffix-bearing NBA names never silently bind to bare-name stats rows
"""
from __future__ import annotations

import pandas as pd

from nba_props_model.data.bdl_client import merge_injury_sources


def _stats(df_rows):
    return pd.DataFrame(df_rows, columns=["player_id", "player_name"])


def test_exact_full_name_match_wins_and_tags_nba_official():
    bdl_map = {1: {"status": "GTD", "reason": "knee"}}
    nba_report = {"lebron james": {"status": "OUT", "reason": "ankle"}}
    stats_df = _stats([(1, "LeBron James"), (2, "Stephen Curry")])

    out = merge_injury_sources(bdl_map, nba_report, stats_df)

    assert out[1]["source"] == "nba_official"
    assert out[1]["status"] == "OUT"
    assert out[1]["reason"] == "ankle"


def test_unique_initial_last_name_requires_team_context():
    bdl_map = {}
    nba_report = {"j. tatum": {"status": "OUT", "reason": "wrist"}}
    stats_df = _stats([(101, "Jayson Tatum"), (202, "Kevin Durant")])

    out = merge_injury_sources(bdl_map, nba_report, stats_df)

    assert 101 not in out
    assert not any(v.get("source") == "nba_official" for v in out.values())


def test_ambiguous_initial_last_name_drops_and_preserves_bdl_entries():
    bdl_map = {
        11: {"status": "GTD", "reason": "shoulder"},
        12: {"status": "GTD", "reason": "ankle"},
    }
    nba_report = {"j. smith": {"status": "OUT", "reason": "hamstring"}}
    stats_df = _stats([(11, "Jalen Smith"), (12, "Jason Smith")])

    out = merge_injury_sources(bdl_map, nba_report, stats_df)

    assert out[11]["source"] == "bdl_injuries_api"
    assert out[11]["status"] == "GTD"
    assert out[11]["reason"] == "shoulder"
    assert out[12]["source"] == "bdl_injuries_api"
    assert out[12]["status"] == "GTD"
    assert out[12]["reason"] == "ankle"
    for pid, entry in out.items():
        assert entry.get("source") != "nba_official", (
            f"pid={pid} silently took nba_official on ambiguous J. Smith"
        )


def test_full_miss_is_dropped_without_silent_collision():
    bdl_map = {7: {"status": "GTD", "reason": "rest"}}
    nba_report = {"someone unknown": {"status": "OUT", "reason": "illness"}}
    stats_df = _stats([(7, "Existing Player"), (8, "Other Person")])

    out = merge_injury_sources(bdl_map, nba_report, stats_df)

    assert 7 in out
    assert out[7]["source"] == "bdl_injuries_api"
    assert out[7]["status"] == "GTD"
    for entry in out.values():
        assert entry.get("source") != "nba_official"


def test_empty_nba_report_sets_source_on_every_bdl_entry():
    bdl_map = {
        21: {"status": "GTD", "reason": "knee"},
        22: {"status": "OUT", "reason": "ankle", "source": "bdl_injuries_api"},
        23: {"status": "Q", "reason": "rest", "source": "custom_tag"},
    }
    out = merge_injury_sources(bdl_map, {}, None)

    assert set(out.keys()) == {21, 22, 23}
    for pid, entry in out.items():
        assert "source" in entry, f"pid={pid} missing source"
    assert out[21]["source"] == "bdl_injuries_api"
    assert out[22]["source"] == "bdl_injuries_api"
    assert out[23]["source"] == "custom_tag"
    assert out[21]["status"] == "GTD"
    assert out[21]["reason"] == "knee"


def test_suffix_bearing_nba_name_does_not_silently_match():
    bdl_map = {
        301: {"status": "GTD", "reason": "ankle"},
        302: {"status": "GTD", "reason": "wrist"},
    }
    nba_report = {"j. smith jr": {"status": "OUT", "reason": "hip"}}
    stats_df = _stats([(301, "Dennis Smith Jr"), (302, "Jalen Smith")])

    out = merge_injury_sources(bdl_map, nba_report, stats_df)

    assert out[301]["source"] == "bdl_injuries_api"
    assert out[301]["status"] == "GTD"
    assert out[302]["source"] == "bdl_injuries_api"
    assert out[302]["status"] == "GTD"
    for pid, entry in out.items():
        assert entry.get("source") != "nba_official", (
            f"pid={pid} silently matched suffix-bearing 'j. smith jr'"
        )
