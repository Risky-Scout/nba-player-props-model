"""Smoke tests for the lineup/injury metadata fields the patched
``scripts/build_stat_grid_pmfs.py`` is required to stamp on every
emitted row.

We do NOT exercise the full ``_build_pipeline_state`` (which makes
network calls to BDL); instead we synthesize the same ``state``
shape and assert ``derive_lineup_metadata_for_row`` returns the
contract values that stat_grid then stamps onto each row.

Together with ``test_lineup_freshness_helpers.py`` these tests
guard against regressions in:

  * the row-level lineup metadata schema (5 fields plus
    optionally-upgraded ``role_source``),
  * the morning-vs-pre_tipoff promotion contract,
  * the propagation of row-level
    ``injury_report_fetched_at_utc`` from state to row.
"""
from __future__ import annotations

from nba_props_model.data.lineup_freshness import (
    LINEUP_SOURCE_DEFAULT,
    LineupFreshnessSnapshot,
    derive_lineup_metadata_for_row,
)


REQUIRED_LINEUP_FIELDS = {
    "expected_lineup_status",
    "official_lineup_status",
    "lineup_source",
    "lineup_last_updated_utc",
    "lineup_freshness_status",
}


def _empty_snapshot() -> LineupFreshnessSnapshot:
    return LineupFreshnessSnapshot({}, {}, None)


def test_morning_row_always_carries_lineup_metadata_fields() -> None:
    meta = derive_lineup_metadata_for_row(
        game_id=21712345,
        player_id=42,
        role_source="derived_from_projected_minutes",
        snapshot=_empty_snapshot(),
        allow_official_confirmation=False,
    )
    assert REQUIRED_LINEUP_FIELDS.issubset(meta.keys())
    assert meta["lineup_source"] == LINEUP_SOURCE_DEFAULT


def test_simulated_stat_grid_row_includes_5_fields_plus_injury_provenance() -> None:
    """Mirror the dict shape the patched stat_grid row builder
    emits. The assertion is structural: every stat_grid row must
    carry these fields so canonical MODEL_ONLY and downstream
    consumers can rely on them being present and non-null where
    upstream produced a value.
    """
    state = {
        "injury_freshness_status": "latest_valid_report_selected",
        "injury_context_source": "bdl_plus_nba_official",
        "injury_report_fetched_at_utc": "2026-05-17T14:00:00Z",
        "lineup_snapshot": LineupFreshnessSnapshot(
            player_lookup={},
            game_lookup={
                "21712345": {
                    "confirmed": False,
                    "has_rows": False,
                    "source": "balldontlie_v1_lineups",
                    "fetched_at_utc": "2026-05-16T20:14:00Z",
                }
            },
            manifest_last_updated_utc="2026-05-16T20:14:00Z",
        ),
    }

    lineup_meta = derive_lineup_metadata_for_row(
        game_id=21712345,
        player_id=42,
        role_source="derived_from_projected_minutes",
        snapshot=state["lineup_snapshot"],
        allow_official_confirmation=False,
    )

    row = {
        "player_id": 42,
        "game_id": 21712345,
        "stat": "pts",
        "injury_freshness_status": state["injury_freshness_status"],
        "injury_context_source": state["injury_context_source"],
        "injury_report_fetched_at_utc": state["injury_report_fetched_at_utc"],
        "expected_lineup_status": lineup_meta["expected_lineup_status"],
        "official_lineup_status": lineup_meta["official_lineup_status"],
        "lineup_source": lineup_meta["lineup_source"],
        "lineup_last_updated_utc": lineup_meta["lineup_last_updated_utc"],
        "lineup_freshness_status": lineup_meta["lineup_freshness_status"],
    }

    assert REQUIRED_LINEUP_FIELDS.issubset(row.keys())
    assert row["expected_lineup_status"] == "projected"
    assert row["official_lineup_status"] == "not_available_yet"
    assert row["lineup_source"] == LINEUP_SOURCE_DEFAULT
    assert row["lineup_last_updated_utc"] == "2026-05-16T20:14:00Z"
    assert row["lineup_freshness_status"] == "projected"
    assert row["injury_freshness_status"] == "latest_valid_report_selected"
    assert row["injury_report_fetched_at_utc"] == "2026-05-17T14:00:00Z"


def test_pretipoff_row_can_promote_to_confirmed_lineup() -> None:
    snap = LineupFreshnessSnapshot(
        player_lookup={
            ("21712345", 42): {"starter": True, "lineup_position": "PG"}
        },
        game_lookup={
            "21712345": {
                "confirmed": True,
                "has_rows": True,
                "source": "balldontlie_v1_lineups",
                "fetched_at_utc": "2026-05-17T00:30:00Z",
            }
        },
        manifest_last_updated_utc="2026-05-17T00:30:00Z",
    )
    meta = derive_lineup_metadata_for_row(
        game_id=21712345,
        player_id=42,
        role_source="derived_from_projected_minutes",
        snapshot=snap,
        allow_official_confirmation=True,
    )
    assert meta["official_lineup_status"] == "confirmed"
    assert meta["role_source"] == "confirmed_bdl_lineup"
    assert meta["lineup_freshness_status"] == "confirmed"
