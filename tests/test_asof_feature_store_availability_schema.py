"""Regression: ``_populate_availability`` no-KeyError contract."""

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")

from nba_props_model.features.asof_feature_store import (
    AVAILABILITY_CONFIDENCE_ALIASES,
    _coalesce_availability_confidence,
    _populate_availability,
)


def _snapshot_with_placeholder_confidence(player_ids):
    """Mirror what ``_add_family_placeholders`` produces — a snapshot
    that already carries ``availability_confidence`` as a pd.NA column.
    The function under test must not KeyError or duplicate this column
    when avail also has a confidence column, and must default when avail
    does not have one.
    """
    df = pd.DataFrame({"player_id": player_ids})
    df["availability_confidence"] = pd.NA
    return df


def test_coalesce_aliases_supports_each_known_name():
    for alias in AVAILABILITY_CONFIDENCE_ALIASES[1:]:
        df = pd.DataFrame({"player_id": [1], alias: [0.9]})
        out = _coalesce_availability_confidence(df)
        assert "availability_confidence" in out.columns
        assert "availability_confidence" in out.columns
        assert out["availability_confidence"].iloc[0] == pytest.approx(0.9)


def test_canonical_name_wins_over_alias():
    df = pd.DataFrame(
        {"player_id": [1], "availability_confidence": [0.7], "confidence_score": [0.2]}
    )
    out = _coalesce_availability_confidence(df)
    assert out["availability_confidence"].iloc[0] == pytest.approx(0.7)


def test_populate_availability_defaults_confidence_when_missing(capsys):
    snap = _snapshot_with_placeholder_confidence([1, 2, 3])
    avail = pd.DataFrame(
        {
            "player_id": [1, 2, 3],
            "availability_status": ["fresh", "fresh", "fresh"],
            "prob_active": [0.9, 0.8, 0.7],
        }
    )
    out = _populate_availability(snap, avail)
    assert "availability_confidence" in out.columns
    assert out["availability_confidence"].notna().all()
    assert (out["availability_confidence"] == 0.5).all()
    text = capsys.readouterr().out
    assert "AVAILABILITY_CONFIDENCE_DEFAULTED" in text
    assert "rows=3" in text
    assert "reason=column_missing_after_merge" in text


def test_populate_availability_maps_confidence_alias():
    snap = _snapshot_with_placeholder_confidence([1, 2])
    avail = pd.DataFrame(
        {
            "player_id": [1, 2],
            "availability_status": ["fresh", "fresh"],
            "prob_active": [0.9, 0.8],
            "confidence_score": [0.95, 0.91],
        }
    )
    out = _populate_availability(snap, avail)
    assert "availability_confidence" in out.columns
    assert out.set_index("player_id")["availability_confidence"].loc[1] == pytest.approx(
        0.95
    )
    assert out.set_index("player_id")["availability_confidence"].loc[2] == pytest.approx(
        0.91
    )


def test_populate_availability_does_not_keyerror_on_empty_avail():
    snap = _snapshot_with_placeholder_confidence([10, 11])
    out = _populate_availability(snap, pd.DataFrame())
    assert "availability_confidence" in out.columns
    assert (out["availability_confidence"] == 0.5).all()
    assert "injury_status_current" in out.columns


def test_populate_availability_handles_merge_overlap_without_suffix_collision():
    """The bug that took down run 25949963791: ``avail`` and ``snap`` both
    carry ``availability_confidence``, so an unguarded merge produced
    ``..._x`` / ``..._y`` and the next line KeyError'd."""
    snap = _snapshot_with_placeholder_confidence([7])
    avail = pd.DataFrame(
        {
            "player_id": [7],
            "availability_status": ["questionable"],
            "prob_active": [0.42],
            "availability_confidence": [0.88],
            "availability_source": ["nba_official"],
        }
    )
    out = _populate_availability(snap, avail)
    assert "availability_confidence_x" not in out.columns
    assert "availability_confidence_y" not in out.columns
    assert out["availability_confidence"].iloc[0] == pytest.approx(0.88)
    assert out["injury_status_current"].iloc[0] == "questionable"
