"""Pre-canonical slate universe seed contract tests.

These tests pin down the narrow scope of the seed:

  * Identity-only columns. No PMFs / model probabilities / market
    edges / Derek-feed fields / canonical delivery outputs.
  * Strict validation (rows > 0, non-null player_id / game_id,
    slate_date matches delivery date, deduped).
  * Structured failure markers on every contract violation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nba_props_model.features.precanonical_slate_universe import (  # noqa: E402
    OPTIONAL_IDENTITY_COLUMNS,
    REQUIRED_IDENTITY_COLUMNS,
    PrecanonicalSlateUniverseError,
    build_precanonical_slate_universe,
    materialize_precanonical_slate_universe,
    precanonical_seed_path,
    predictions_all_props_path,
)


FORBIDDEN_SEED_COLUMNS = (
    "pmf",
    "pmf_json",
    "model_prob",
    "model_p_over",
    "model_p_under",
    "model_expected_value",
    "mean",
    "median",
    "edge",
    "edge_over",
    "edge_under",
    "fair_over_odds_american",
    "fair_under_odds_american",
    "market_no_vig_over_prob",
    "market_no_vig_under_prob",
)


def _all_props_like(rows: list[dict]) -> pd.DataFrame:
    """Build a fixture frame shaped like predictions/all_props_<date>.parquet."""
    return pd.DataFrame(rows)


def test_basic_dedup_and_keep_identity_columns():
    df = _all_props_like(
        [
            {
                "slate_date": "2026-05-16",
                "player_id": 100,
                "game_id": 21,
                "stat": "pts",
                "line": 21.5,
                "model_prob": 0.55,
                "pmf": "{}",
                "team_abbr": "BOS",
                "opponent": "NYK",
                "is_home": True,
                "player_name": "Player A",
            },
            {
                "slate_date": "2026-05-16",
                "player_id": 100,
                "game_id": 21,
                "stat": "reb",
                "line": 7.5,
                "model_prob": 0.48,
                "pmf": "{}",
                "team_abbr": "BOS",
                "opponent": "NYK",
                "is_home": True,
                "player_name": "Player A",
            },
            {
                "slate_date": "2026-05-16",
                "player_id": 200,
                "game_id": 22,
                "stat": "pts",
                "line": 17.5,
                "model_prob": 0.6,
                "pmf": "{}",
                "team_abbr": "NYK",
                "opponent": "BOS",
                "is_home": False,
                "player_name": "Player B",
            },
        ]
    )
    seed = build_precanonical_slate_universe(df, "2026-05-16")
    assert len(seed) == 2
    assert set(seed["player_id"].tolist()) == {100, 200}
    for col in REQUIRED_IDENTITY_COLUMNS:
        assert col in seed.columns
    for col in FORBIDDEN_SEED_COLUMNS:
        assert col not in seed.columns, f"forbidden model/market column leaked into seed: {col}"
    assert seed["slate_date"].astype(str).unique().tolist() == ["2026-05-16"]


def test_seed_columns_are_identity_only():
    seed_cols = {*REQUIRED_IDENTITY_COLUMNS, *OPTIONAL_IDENTITY_COLUMNS}
    for forbidden in FORBIDDEN_SEED_COLUMNS:
        assert forbidden not in seed_cols, (
            f"seed schema must not declare {forbidden!r} as a kept column"
        )


def test_empty_input_hard_fails():
    with pytest.raises(PrecanonicalSlateUniverseError) as exc:
        build_precanonical_slate_universe(pd.DataFrame(), "2026-05-16")
    assert "PRECANNONICAL_SLATE_UNIVERSE_EMPTY" in str(exc.value)


def test_missing_required_keys_hard_fails():
    df = _all_props_like(
        [{"slate_date": "2026-05-16", "player_id": 1, "stat": "pts", "line": 10.5}]
    )
    with pytest.raises(PrecanonicalSlateUniverseError) as exc:
        build_precanonical_slate_universe(df, "2026-05-16")
    s = str(exc.value)
    assert "PRECANNONICAL_SLATE_UNIVERSE_KEYS_MISSING" in s
    assert "game_id" in s


def test_null_player_id_or_game_id_hard_fails():
    df = _all_props_like(
        [
            {"slate_date": "2026-05-16", "player_id": None, "game_id": 21, "stat": "pts", "line": 21.5},
            {"slate_date": "2026-05-16", "player_id": 100, "game_id": None, "stat": "reb", "line": 7.5},
        ]
    )
    with pytest.raises(PrecanonicalSlateUniverseError) as exc:
        build_precanonical_slate_universe(df, "2026-05-16")
    assert "PRECANNONICAL_SLATE_UNIVERSE_KEYS_MISSING" in str(exc.value)


def test_slate_date_mismatch_hard_fails():
    df = _all_props_like(
        [
            {"slate_date": "2026-05-15", "player_id": 100, "game_id": 21, "stat": "pts", "line": 21.5},
            {"slate_date": "2026-05-16", "player_id": 200, "game_id": 22, "stat": "pts", "line": 19.5},
        ]
    )
    with pytest.raises(PrecanonicalSlateUniverseError) as exc:
        build_precanonical_slate_universe(df, "2026-05-16")
    msg = str(exc.value)
    assert "PRECANNONICAL_SLATE_UNIVERSE_DATE_MISMATCH" in msg
    assert "2026-05-15" in msg


def test_blank_slate_date_is_tolerated_and_stamped():
    df = _all_props_like(
        [
            {"slate_date": "", "player_id": 100, "game_id": 21, "stat": "pts", "line": 21.5},
            {"slate_date": None, "player_id": 200, "game_id": 22, "stat": "pts", "line": 19.5},
        ]
    )
    seed = build_precanonical_slate_universe(df, "2026-05-16")
    assert len(seed) == 2
    assert (seed["slate_date"].astype(str) == "2026-05-16").all()


def test_non_numeric_keys_dropped_or_hard_fail():
    df = _all_props_like(
        [
            {"slate_date": "2026-05-16", "player_id": "abc", "game_id": "xyz", "stat": "pts", "line": 1.5},
        ]
    )
    with pytest.raises(PrecanonicalSlateUniverseError) as exc:
        build_precanonical_slate_universe(df, "2026-05-16")
    assert "PRECANNONICAL_SLATE_UNIVERSE_KEYS_MISSING" in str(exc.value)


def test_materialize_writes_to_named_seed_path(tmp_path):
    repo_root = tmp_path
    pred_dir = repo_root / "predictions"
    pred_dir.mkdir()
    src = pred_dir / "all_props_2026-05-16.parquet"
    df = _all_props_like(
        [
            {"slate_date": "2026-05-16", "player_id": 100, "game_id": 21, "stat": "pts", "line": 21.5, "model_prob": 0.55},
            {"slate_date": "2026-05-16", "player_id": 200, "game_id": 22, "stat": "pts", "line": 19.5, "model_prob": 0.5},
        ]
    )
    df.to_parquet(src, index=False)
    out = materialize_precanonical_slate_universe(
        repo_root, date="2026-05-16", run_mode="morning_expected"
    )
    expected = precanonical_seed_path(repo_root, "2026-05-16", "morning_expected")
    assert out == expected
    # Path must be clearly named so callers cannot confuse it with canonical output.
    assert "precanonical_slate_universe_" in out.name
    assert "MODEL_ONLY" not in out.name
    written = pd.read_parquet(out)
    assert "model_prob" not in written.columns
    assert set(written.columns) >= {"player_id", "game_id", "slate_date"}


def test_materialize_missing_input_hard_fails(tmp_path):
    repo_root = tmp_path
    (repo_root / "predictions").mkdir()
    with pytest.raises(PrecanonicalSlateUniverseError) as exc:
        materialize_precanonical_slate_universe(
            repo_root, date="2026-05-16", run_mode="morning_expected"
        )
    assert "PRECANNONICAL_SLATE_UNIVERSE_MISSING" in str(exc.value)


def test_seed_path_helper_uses_data_features_directory(tmp_path):
    p = precanonical_seed_path(tmp_path, "2026-05-16", "morning_expected")
    assert p.parts[-2:] == ("features", "precanonical_slate_universe_2026-05-16_morning_expected.parquet")


def test_predictions_all_props_path_helper(tmp_path):
    p = predictions_all_props_path(tmp_path, "2026-05-16")
    assert p.name == "all_props_2026-05-16.parquet"
    assert p.parent.name == "predictions"
