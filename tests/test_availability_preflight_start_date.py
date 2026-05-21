from pathlib import Path

import pandas as pd

from scripts.availability_preflight_start_date import compute_start_date


def test_missing_file_prints_target_date(tmp_path: Path):
    assert compute_start_date("2026-05-20", tmp_path / "missing.parquet") == "2026-05-20"


def test_empty_parquet_prints_target_date(tmp_path: Path):
    p = tmp_path / "availability.parquet"
    pd.DataFrame({"game_date": []}).to_parquet(p, index=False)
    assert compute_start_date("2026-05-20", p) == "2026-05-20"


def test_missing_game_date_column_prints_target_date(tmp_path: Path):
    p = tmp_path / "availability.parquet"
    pd.DataFrame({"player_id": [1, 2]}).to_parquet(p, index=False)
    assert compute_start_date("2026-05-20", p) == "2026-05-20"


def test_invalid_game_date_values_print_target_date(tmp_path: Path):
    p = tmp_path / "availability.parquet"
    pd.DataFrame({"game_date": ["not-a-date", None]}).to_parquet(p, index=False)
    assert compute_start_date("2026-05-20", p) == "2026-05-20"


def test_stale_table_prints_next_missing_date(tmp_path: Path):
    p = tmp_path / "availability.parquet"
    pd.DataFrame({"game_date": ["2026-05-17", "2026-05-19"]}).to_parquet(p, index=False)
    assert compute_start_date("2026-05-20", p) == "2026-05-20"


def test_older_stale_table_prints_max_plus_one(tmp_path: Path):
    p = tmp_path / "availability.parquet"
    pd.DataFrame({"game_date": ["2026-05-12", "2026-05-17"]}).to_parquet(p, index=False)
    assert compute_start_date("2026-05-20", p) == "2026-05-18"


def test_current_table_prints_empty_string(tmp_path: Path):
    p = tmp_path / "availability.parquet"
    pd.DataFrame({"game_date": ["2026-05-20"]}).to_parquet(p, index=False)
    assert compute_start_date("2026-05-20", p) == ""


def test_future_covered_table_prints_empty_string(tmp_path: Path):
    p = tmp_path / "availability.parquet"
    pd.DataFrame({"game_date": ["2026-05-21"]}).to_parquet(p, index=False)
    assert compute_start_date("2026-05-20", p) == ""
