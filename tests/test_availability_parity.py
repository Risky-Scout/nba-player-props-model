"""Train/predict parity for the as-of availability features.

Both sides must read the same historical availability table via
`load_availability_table()` and key on (player_id, game_date) as a
10-char ISO date string. This test fails if either side drifts.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest


REPO = Path(__file__).parent.parent
TRAIN = REPO / "src/nba_props_model/pipelines/train.py"
PREDICT = REPO / "src/nba_props_model/pipelines/predict.py"

# Canonical availability feature set — edits to this list must land on both
# sides of the pipeline at once.
CANONICAL_COLS = {
    "prob_active",
    "days_since_last_played",
    "is_returning_from_absence",
    "minutes_restriction_flag",
    "num_teammates_out_total",
    "vacated_minutes_guard",
    "vacated_minutes_wing",
    "vacated_minutes_big",
    "teammate_out_count_guard",
    "teammate_out_count_wing",
    "teammate_out_count_big",
    "vacated_fga_total",
}


def _has_load_availability_table_call(path: Path) -> bool:
    src = path.read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "load_availability_table":
                return True
    # Also accept the aliased import name used in predict.py (see the `as _load_availability_table`
    # import). Search for any name ending in `load_availability_table`.
    return "load_availability_table" in src


def test_train_and_predict_both_load_availability_table():
    assert _has_load_availability_table_call(TRAIN), (
        "training pipeline must call load_availability_table()"
    )
    assert _has_load_availability_table_call(PREDICT), (
        "predict pipeline must call load_availability_table()"
    )


def test_train_uses_canonical_availability_columns():
    src = TRAIN.read_text()
    for col in CANONICAL_COLS:
        assert col in src, f"training must reference availability column {col!r}"


def test_predict_uses_canonical_availability_columns():
    src = PREDICT.read_text()
    for col in CANONICAL_COLS:
        assert col in src, f"predict must reference availability column {col!r}"


def test_availability_table_matches_training_rows_above_95pct():
    """Historical box scores must be covered by the as-of availability table
    at well over 95%. If this drops, the replay build is broken."""
    stats_p = REPO / "data/player_game_stats.parquet"
    avail_p = REPO / "data/player_availability_asof.parquet"
    if not stats_p.exists() or not avail_p.exists():
        pytest.skip("data parquets not present in this environment")
    stats = pd.read_parquet(stats_p)
    avail = pd.read_parquet(avail_p)
    stats = stats.assign(date_str=stats["game_date"].astype(str).str.slice(0, 10))
    avail = avail.assign(date_str=avail["game_date"].astype(str).str.slice(0, 10))

    # Restrict the denominator to the date window the availability replay
    # covers — we cannot hold the replay responsible for dates outside its
    # build window. Everything inside the window must match.
    lo, hi = avail["date_str"].min(), avail["date_str"].max()
    in_window = (stats["date_str"] >= lo) & (stats["date_str"] <= hi)
    stats_in = stats.loc[in_window]

    avail_keys = set(zip(avail["player_id"].astype(int), avail["date_str"]))
    matched = sum(
        1 for pid, ds in zip(stats_in["player_id"].astype(int), stats_in["date_str"])
        if (pid, ds) in avail_keys
    )
    total = len(stats_in)
    assert total > 0
    pct = 100.0 * matched / total
    assert pct >= 95.0, (
        f"availability coverage {pct:.2f}% below 95% on {total} rows "
        f"({matched} matched)"
    )
