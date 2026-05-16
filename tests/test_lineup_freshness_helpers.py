"""Unit tests for :mod:`nba_props_model.data.lineup_freshness`."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from nba_props_model.data.lineup_freshness import (
    LINEUP_SOURCE_DEFAULT,
    LineupFreshnessSnapshot,
    compute_lineup_freshness_status,
    derive_lineup_metadata_for_row,
    load_bdl_lineup_freshness_snapshot,
)


def test_load_returns_empty_snapshot_when_directory_missing(tmp_path: Path) -> None:
    snap = load_bdl_lineup_freshness_snapshot(tmp_path, "2026-05-17")
    assert snap.has_any_rows is False
    assert snap.manifest_last_updated_utc is None
    assert snap.player_lookup == {}
    assert snap.game_lookup == {}


def test_load_records_fetched_at_and_per_game_player(tmp_path: Path) -> None:
    gdir = tmp_path / "artifacts" / "live_lineups" / "2026-05-17" / "21712345"
    gdir.mkdir(parents=True)
    (gdir / "lineup_status.json").write_text(
        json.dumps(
            {
                "lineup_confirmed": False,
                "total_rows": 5,
                "source": "balldontlie_v1_lineups",
                "fetched_at_utc": "2026-05-16T20:14:00Z",
            }
        )
    )
    pd.DataFrame(
        [
            {
                "player_id": 100,
                "starter": True,
                "lineup_position": "PG",
                "source": "balldontlie_v1_lineups",
            },
            {
                "player_id": 200,
                "starter": False,
                "lineup_position": "BENCH",
                "source": "balldontlie_v1_lineups",
            },
        ]
    ).to_parquet(gdir / "bdl_lineups_normalized.parquet", index=False)

    snap = load_bdl_lineup_freshness_snapshot(tmp_path, "2026-05-17")
    assert snap.has_any_rows is True
    assert snap.manifest_last_updated_utc == "2026-05-16T20:14:00Z"
    assert "21712345" in snap.game_lookup
    assert snap.player_lookup[("21712345", 100)]["starter"] is True
    assert snap.player_lookup[("21712345", 200)]["starter"] is False


def test_derive_morning_defaults_when_snapshot_absent() -> None:
    snap = LineupFreshnessSnapshot({}, {}, None)
    meta = derive_lineup_metadata_for_row(
        game_id=42,
        player_id=99,
        role_source="derived_from_projected_minutes",
        snapshot=snap,
        allow_official_confirmation=False,
    )
    assert meta["expected_lineup_status"] == "projected"
    assert meta["official_lineup_status"] == "not_available_yet"
    assert meta["lineup_source"] == LINEUP_SOURCE_DEFAULT
    assert meta["lineup_last_updated_utc"] is None
    assert meta["lineup_freshness_status"] == "projected"


def test_derive_morning_refuses_to_promote_confirmed_lineup() -> None:
    snap = LineupFreshnessSnapshot(
        player_lookup={("21712345", 100): {"starter": True, "lineup_position": "PG"}},
        game_lookup={
            "21712345": {
                "confirmed": True,
                "has_rows": True,
                "source": "balldontlie_v1_lineups",
                "fetched_at_utc": "2026-05-17T00:00:00Z",
            }
        },
        manifest_last_updated_utc="2026-05-17T00:00:00Z",
    )
    meta = derive_lineup_metadata_for_row(
        game_id=21712345,
        player_id=100,
        role_source="derived_from_projected_minutes",
        snapshot=snap,
        allow_official_confirmation=False,
    )
    assert meta["official_lineup_status"] == "projected"
    assert meta["expected_lineup_status"] == "projected"
    assert meta["lineup_last_updated_utc"] == "2026-05-17T00:00:00Z"


def test_derive_pretipoff_promotes_confirmed_lineup() -> None:
    snap = LineupFreshnessSnapshot(
        player_lookup={("21712345", 100): {"starter": True, "lineup_position": "PG"}},
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
        player_id=100,
        role_source="derived_from_projected_minutes",
        snapshot=snap,
        allow_official_confirmation=True,
    )
    assert meta["official_lineup_status"] == "confirmed"
    assert meta["role_source"] == "confirmed_bdl_lineup"
    assert meta["lineup_freshness_status"] == "confirmed"


def test_compute_lineup_freshness_status_branches() -> None:
    assert (
        compute_lineup_freshness_status(
            official_lineup_status="confirmed",
            expected_lineup_status="projected",
            role_source="any",
        )
        == "confirmed"
    )
    assert (
        compute_lineup_freshness_status(
            official_lineup_status="not_available_yet",
            expected_lineup_status="projected",
            role_source="derived_from_projected_minutes",
        )
        == "projected"
    )
    assert (
        compute_lineup_freshness_status(
            official_lineup_status=None,
            expected_lineup_status=None,
            role_source="unknown",
        )
        == "unknown"
    )
