import datetime as dt
from pathlib import Path

import pandas as pd

from scripts.verify_phase8_training_table_freshness import verify_training_table


def _write_training_table(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_verify_training_table_passes_when_asof_is_fresh_and_covered(tmp_path: Path) -> None:
    path = tmp_path / "training_table.parquet"
    _write_training_table(
        path,
        [
            {"game_date": "2026-05-19", "prob_active": 0.9},
            {"game_date": "2026-05-20", "prob_active": 0.8},
            {"game_date": "2026-05-20", "prob_active": 0.7},
            {"game_date": "2026-05-20", "prob_active": 0.6},
        ],
    )

    ok, failures = verify_training_table(
        training_table=path,
        as_of_date=dt.date(2026, 5, 20),
        min_prob_active_coverage=0.80,
    )

    assert ok is True
    assert failures == []


def test_verify_training_table_fails_when_table_is_stale(tmp_path: Path) -> None:
    path = tmp_path / "training_table.parquet"
    _write_training_table(
        path,
        [
            {"game_date": "2026-05-18", "prob_active": 0.9},
            {"game_date": "2026-05-19", "prob_active": 0.8},
        ],
    )

    ok, failures = verify_training_table(
        training_table=path,
        as_of_date=dt.date(2026, 5, 20),
        min_prob_active_coverage=0.80,
    )

    assert ok is False
    assert any("stale_max_game_date" in f for f in failures)
    assert any("missing_as_of_rows" in f for f in failures)


def test_verify_training_table_fails_when_asof_coverage_is_too_low(tmp_path: Path) -> None:
    path = tmp_path / "training_table.parquet"
    _write_training_table(
        path,
        [
            {"game_date": "2026-05-20", "prob_active": 0.9},
            {"game_date": "2026-05-20", "prob_active": None},
            {"game_date": "2026-05-20", "prob_active": None},
            {"game_date": "2026-05-20", "prob_active": 0.1},
        ],
    )

    ok, failures = verify_training_table(
        training_table=path,
        as_of_date=dt.date(2026, 5, 20),
        min_prob_active_coverage=0.80,
    )

    assert ok is False
    assert any("low_prob_active_coverage" in f for f in failures)

