from __future__ import annotations

from pathlib import Path

from nba_props_model.features.asof_feature_store import MissingSourceInputsError, build_feature_snapshot
from nba_props_model.features.player_prop_feature_contract import RunMode


REPO = Path(__file__).resolve().parents[1]


def test_snapshot_builds_for_existing_delivery_date():
    result = build_feature_snapshot(REPO, "2026-05-12", RunMode.FINAL_AFTER_GAME)
    assert len(result.snapshot) > 0
    assert "feature_snapshot_id" in result.snapshot.columns
    assert "injury_status_current" in result.snapshot.columns
    assert "official_lineup_status" in result.snapshot.columns


def test_missing_sources_raise_for_nonexistent_date():
    try:
        build_feature_snapshot(REPO, "2099-01-01", RunMode.MORNING_EXPECTED)
        raised = False
    except MissingSourceInputsError:
        raised = True
    assert raised
