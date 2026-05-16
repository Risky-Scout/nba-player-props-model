"""Regression: ``_populate_availability`` no-KeyError contract."""

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")

from nba_props_model.features.asof_feature_store import (
    AVAILABILITY_CONFIDENCE_ALIASES,
    AVAILABILITY_CONFIDENCE_TIER_MAP,
    _coalesce_availability_confidence,
    _coerce_availability_confidence_to_numeric,
    _populate_availability,
    assert_availability_confidence_is_numeric,
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


# ── tier-string coercion (run 25950902639) ────────────────────────────


def test_generic_confidence_tier_is_preserved_and_mapped_to_numeric():
    """The exact regression in run 25950902639: source feed ships a
    ``confidence`` column with categorical tier labels like ``HIGH``.
    The tier label must survive in ``availability_confidence_tier`` and
    the numeric value must end up in ``availability_confidence``."""
    snap = _snapshot_with_placeholder_confidence([42])
    avail = pd.DataFrame(
        {
            "player_id": [42],
            "availability_status": ["fresh"],
            "prob_active": [0.9],
            "confidence": ["HIGH"],
        }
    )
    out = _populate_availability(snap, avail)
    row = out.set_index("player_id").loc[42]
    assert row["availability_confidence"] == pytest.approx(0.9)
    assert row["availability_confidence_tier"] == "HIGH"
    assert pd.api.types.is_numeric_dtype(out["availability_confidence"])


def test_availability_confidence_with_tier_strings_does_not_crash():
    """If ``availability_confidence`` itself is shipped as tier strings
    (legacy producers), the function maps them to numeric without
    raising. Required because pyarrow refuses ``object`` columns mixing
    str and float when writing parquet."""
    snap = _snapshot_with_placeholder_confidence([1, 2])
    avail = pd.DataFrame(
        {
            "player_id": [1, 2],
            "availability_status": ["fresh", "questionable"],
            "prob_active": [0.9, 0.5],
            "availability_confidence": ["HIGH", "LOW"],
        }
    )
    out = _populate_availability(snap, avail)
    rows = out.set_index("player_id")
    assert rows["availability_confidence"].loc[1] == pytest.approx(0.9)
    assert rows["availability_confidence"].loc[2] == pytest.approx(0.5)
    assert rows["availability_confidence_tier"].loc[1] == "HIGH"
    assert rows["availability_confidence_tier"].loc[2] == "LOW"
    assert pd.api.types.is_numeric_dtype(out["availability_confidence"])


def test_mixed_numeric_and_tier_values_collapse_to_float64():
    snap = _snapshot_with_placeholder_confidence([10, 11, 12, 13])
    avail = pd.DataFrame(
        {
            "player_id": [10, 11, 12, 13],
            "availability_status": ["fresh", "fresh", "fresh", "fresh"],
            "prob_active": [0.95, 0.9, 0.7, 0.5],
            "availability_confidence": [0.95, "HIGH", "MEDIUM", None],
        }
    )
    out = _populate_availability(snap, avail)
    rows = out.set_index("player_id")["availability_confidence"]
    assert rows.loc[10] == pytest.approx(0.95)
    assert rows.loc[11] == pytest.approx(AVAILABILITY_CONFIDENCE_TIER_MAP["HIGH"])
    assert rows.loc[12] == pytest.approx(AVAILABILITY_CONFIDENCE_TIER_MAP["MEDIUM"])
    assert rows.loc[13] == pytest.approx(0.5)
    assert out["availability_confidence"].dtype.name == "float64"


def test_snapshot_with_tier_strings_round_trips_through_parquet(tmp_path):
    """Pyarrow ArrowInvalid no longer surfaces because the dtype is
    float64 at write time."""
    snap = _snapshot_with_placeholder_confidence([1, 2, 3])
    avail = pd.DataFrame(
        {
            "player_id": [1, 2, 3],
            "availability_status": ["fresh", "questionable", "out"],
            "prob_active": [0.9, 0.55, 0.0],
            "confidence": ["HIGH", "MEDIUM", "LOW"],
        }
    )
    out = _populate_availability(snap, avail)
    p = tmp_path / "feature_snapshot.parquet"
    out.to_parquet(p, index=False)
    reread = pd.read_parquet(p)
    rows = reread.set_index("player_id")["availability_confidence"]
    assert rows.loc[1] == pytest.approx(AVAILABILITY_CONFIDENCE_TIER_MAP["HIGH"])
    assert rows.loc[2] == pytest.approx(AVAILABILITY_CONFIDENCE_TIER_MAP["MEDIUM"])
    assert rows.loc[3] == pytest.approx(AVAILABILITY_CONFIDENCE_TIER_MAP["LOW"])


def test_assert_availability_confidence_is_numeric_passes_for_float_column():
    df = pd.DataFrame({"availability_confidence": [0.1, 0.2, 0.3]})
    assert_availability_confidence_is_numeric(df)


def test_assert_availability_confidence_is_numeric_fails_on_unmappable_strings():
    df = pd.DataFrame({"availability_confidence": ["not_a_number", "another_bad"]})
    with pytest.raises(RuntimeError) as excinfo:
        assert_availability_confidence_is_numeric(df)
    msg = str(excinfo.value)
    assert "AVAILABILITY_CONFIDENCE_NON_NUMERIC" in msg
    assert "not_a_number" in msg


def test_coerce_helper_preserves_caller_supplied_tier():
    """If a caller already populated ``availability_confidence_tier``,
    that value wins over the auto-inferred upper-case label."""
    df = pd.DataFrame(
        {
            "availability_confidence": ["HIGH", "LOW"],
            "availability_confidence_tier": ["UPSTREAM_HIGH", None],
        }
    )
    _coerce_availability_confidence_to_numeric(df)
    assert df["availability_confidence_tier"].iloc[0] == "UPSTREAM_HIGH"
    assert df["availability_confidence_tier"].iloc[1] == "LOW"
    assert df["availability_confidence"].iloc[0] == pytest.approx(
        AVAILABILITY_CONFIDENCE_TIER_MAP["HIGH"]
    )
