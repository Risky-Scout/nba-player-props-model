"""Tests that --start-date/--end-date range mode merges into an existing file.

Root-cause guard for the bug where range mode overwrote the output file
entirely, destroying historical rows and dropping availability coverage to ~8%.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_mock_builder(new_rows: pd.DataFrame) -> MagicMock:
    """Return a mock AvailabilityBuilder whose features_for returns new_rows."""
    builder = MagicMock()
    builder.game_stats = new_rows[["player_id", "team_id", "game_date"]].copy()
    builder.injury_reports = pd.DataFrame()
    builder.features_for.return_value = new_rows.copy()
    return builder


def _availability_columns() -> list[str]:
    return [
        "player_id", "team_id", "game_date",
        "availability_status", "availability_confidence",
    ]


def _make_rows(dates: list[str], player_start: int = 1) -> pd.DataFrame:
    rows = []
    for i, d in enumerate(dates):
        rows.append({
            "player_id": player_start + i,
            "team_id": 10,
            "game_date": d,
            "availability_status": "ACTIVE",
            "availability_confidence": "HIGH",
        })
    return pd.DataFrame(rows, columns=_availability_columns())


# ---------------------------------------------------------------------------
# Core merge regression test
# ---------------------------------------------------------------------------


def test_range_mode_merges_preserving_outside_rows(tmp_path: Path):
    """Range mode must keep rows outside [start, end] from the existing file."""
    out_file = tmp_path / "availability.parquet"

    # Pre-existing file: dates 2026-05-01 through 2026-05-15
    old_dates = [f"2026-05-{d:02d}" for d in range(1, 16)]
    existing = _make_rows(old_dates)
    existing.to_parquet(out_file, index=False)
    assert len(pd.read_parquet(out_file)) == 15

    # New rows computed for range 2026-05-13 → 2026-05-15 (overlapping update)
    new_dates = ["2026-05-13", "2026-05-14", "2026-05-15"]
    new_feats = _make_rows(new_dates, player_start=100)

    mock_builder = _make_mock_builder(new_feats)

    with patch(
        "scripts.build_availability_table.AvailabilityBuilder.from_data_dir",
        return_value=mock_builder,
    ):
        import importlib
        import scripts.build_availability_table as bat
        importlib.reload(bat)

        with patch(
            "sys.argv",
            [
                "build_availability_table.py",
                "--start-date", "2026-05-13",
                "--end-date", "2026-05-15",
                "--out", str(out_file),
            ],
        ):
            bat.main()

    result = pd.read_parquet(out_file)

    # Rows for 2026-05-01 through 2026-05-12 (12 rows) must be preserved
    result_norm = pd.to_datetime(result["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    outside = result.loc[result_norm < "2026-05-13"]
    assert len(outside) == 12, (
        f"Expected 12 outside-range rows to be preserved, got {len(outside)}. "
        f"Total rows in file: {len(result)}"
    )

    # Rows for 2026-05-13 → 2026-05-15 must be the NEW ones (player_id >= 100)
    inside = result.loc[(result_norm >= "2026-05-13") & (result_norm <= "2026-05-15")]
    assert len(inside) == 3
    assert set(inside["player_id"]) == {100, 101, 102}, (
        "Inside-range rows should be the new rows, not the old ones"
    )

    # Total should be 12 preserved + 3 new = 15
    assert len(result) == 15


def test_range_mode_no_existing_file_writes_directly(tmp_path: Path):
    """Without an existing file, range mode must write new rows directly."""
    out_file = tmp_path / "availability.parquet"
    assert not out_file.exists()

    new_dates = ["2026-05-13", "2026-05-14"]
    new_feats = _make_rows(new_dates)
    mock_builder = _make_mock_builder(new_feats)

    with patch(
        "scripts.build_availability_table.AvailabilityBuilder.from_data_dir",
        return_value=mock_builder,
    ):
        import importlib
        import scripts.build_availability_table as bat
        importlib.reload(bat)

        with patch(
            "sys.argv",
            [
                "build_availability_table.py",
                "--start-date", "2026-05-13",
                "--end-date", "2026-05-14",
                "--out", str(out_file),
            ],
        ):
            bat.main()

    result = pd.read_parquet(out_file)
    assert len(result) == 2


def test_range_mode_start_date_only_merges(tmp_path: Path):
    """--start-date without --end-date must still trigger merge, not overwrite."""
    out_file = tmp_path / "availability.parquet"

    old_dates = ["2026-05-01", "2026-05-02", "2026-05-10"]
    existing = _make_rows(old_dates)
    existing.to_parquet(out_file, index=False)

    new_dates = ["2026-05-10", "2026-05-11"]
    new_feats = _make_rows(new_dates, player_start=200)
    mock_builder = _make_mock_builder(new_feats)

    with patch(
        "scripts.build_availability_table.AvailabilityBuilder.from_data_dir",
        return_value=mock_builder,
    ):
        import importlib
        import scripts.build_availability_table as bat
        importlib.reload(bat)

        with patch(
            "sys.argv",
            [
                "build_availability_table.py",
                "--start-date", "2026-05-10",
                "--out", str(out_file),
            ],
        ):
            bat.main()

    result = pd.read_parquet(out_file)
    result_norm = pd.to_datetime(result["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    # 2026-05-01 and 2026-05-02 must be preserved
    outside = result.loc[result_norm < "2026-05-10"]
    assert len(outside) == 2, f"Expected 2 preserved rows before start_date, got {len(outside)}"

    # 2026-05-10 row must be the new one (player_id 200), not old (player_id 3)
    on_date = result.loc[result_norm == "2026-05-10"]
    assert len(on_date) == 1
    assert on_date.iloc[0]["player_id"] == 200


def test_range_mode_end_date_only_merges(tmp_path: Path):
    """--end-date without --start-date must still trigger merge, not overwrite."""
    out_file = tmp_path / "availability.parquet"

    old_dates = ["2026-05-05", "2026-05-10", "2026-05-15"]
    existing = _make_rows(old_dates)
    existing.to_parquet(out_file, index=False)

    new_dates = ["2026-05-05", "2026-05-10"]
    new_feats = _make_rows(new_dates, player_start=300)
    mock_builder = _make_mock_builder(new_feats)

    with patch(
        "scripts.build_availability_table.AvailabilityBuilder.from_data_dir",
        return_value=mock_builder,
    ):
        import importlib
        import scripts.build_availability_table as bat
        importlib.reload(bat)

        with patch(
            "sys.argv",
            [
                "build_availability_table.py",
                "--end-date", "2026-05-10",
                "--out", str(out_file),
            ],
        ):
            bat.main()

    result = pd.read_parquet(out_file)
    result_norm = pd.to_datetime(result["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    # 2026-05-15 must be preserved (outside range)
    outside = result.loc[result_norm > "2026-05-10"]
    assert len(outside) == 1

    # New rows inside range (player_id >= 300)
    inside = result.loc[result_norm <= "2026-05-10"]
    assert set(inside["player_id"]) == {300, 301}
