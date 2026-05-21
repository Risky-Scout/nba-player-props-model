from pathlib import Path

import pandas as pd

from scripts import resolve_previous_day_et_target as resolver


def _write_rows(path: Path, game_date: str, rows: int) -> None:
    pd.DataFrame({"game_date": [game_date] * rows}).to_parquet(path, index=False)


def test_playoff_low_volume_complete_night_meets_adaptive_floor(tmp_path: Path, monkeypatch) -> None:
    parquet_path = tmp_path / "player_game_stats.parquet"
    _write_rows(parquet_path, "2026-05-03", 22)
    monkeypatch.setattr(resolver, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(resolver, "PLAYER_GAME_STATS", parquet_path)
    monkeypatch.setattr(resolver, "FRESHNESS_MANIFEST_DIR", tmp_path / "freshness_manifest")

    findings = resolver._check_completeness(target=resolver.dt.date(2026, 5, 3))

    assert findings["rows_floor_for_target"] == 20
    assert findings["rows_for_target"] == 22
    assert findings["rows_for_target_meets_floor"] is True
    assert findings["data_complete_for_target_date"] is True


def test_playoff_incomplete_night_still_fail_closed(tmp_path: Path, monkeypatch) -> None:
    parquet_path = tmp_path / "player_game_stats.parquet"
    _write_rows(parquet_path, "2026-05-04", 17)
    monkeypatch.setattr(resolver, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(resolver, "PLAYER_GAME_STATS", parquet_path)
    monkeypatch.setattr(resolver, "FRESHNESS_MANIFEST_DIR", tmp_path / "freshness_manifest")

    findings = resolver._check_completeness(target=resolver.dt.date(2026, 5, 4))

    assert findings["rows_floor_for_target"] == 20
    assert findings["rows_for_target"] == 17
    assert findings["rows_for_target_meets_floor"] is False
    assert findings["data_complete_for_target_date"] is False

