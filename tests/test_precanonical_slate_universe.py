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
    NoGamesSlateSoftSkip,
    PrecanonicalSlateUniverseError,
    build_precanonical_slate_universe,
    materialize_precanonical_slate_universe,
    precanonical_seed_path,
    predictions_all_props_path,
    predictions_singles_path,
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


def _write_no_games_signal(repo_root: Path, date: str) -> Path:
    """Mirror predict.py's write_no_game_outputs side-effect — just the
    singles_<date>.json with reason=no_games_slate signal."""
    import json
    p = predictions_singles_path(repo_root, date)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            {
                "date": date,
                "version": "test",
                "total_picks": 0,
                "picks": [],
                "reason": "no_games_slate",
            }
        ),
        encoding="utf-8",
    )
    return p


def test_materialize_soft_skips_on_no_games_signal_with_empty_parquet(tmp_path):
    """predict.py's no-games path writes an empty all_props parquet AND
    a singles_<date>.json with reason=no_games_slate. The seed builder
    must soft-skip in that case rather than hard-fail."""
    repo_root = tmp_path
    pred_dir = repo_root / "predictions"
    pred_dir.mkdir()
    empty = pd.DataFrame(columns=["slate_date", "player_id", "game_id", "stat", "line", "model_prob", "pmf"])
    empty.to_parquet(pred_dir / "all_props_2026-05-16.parquet", index=False)
    _write_no_games_signal(repo_root, "2026-05-16")

    with pytest.raises(NoGamesSlateSoftSkip) as exc:
        materialize_precanonical_slate_universe(
            repo_root, date="2026-05-16", run_mode="morning_expected"
        )
    msg = str(exc.value)
    assert "PRECANNONICAL_SLATE_UNIVERSE_SOFT_SKIP_NO_GAMES" in msg
    assert "date=2026-05-16" in msg
    assert "upstream_signal=predictions/singles_2026-05-16.json" in msg


def test_materialize_soft_skips_when_all_props_missing_but_signal_present(tmp_path):
    """Some predict no-games paths may delete the all_props file rather
    than write an empty one. Soft-skip still applies when the explicit
    upstream signal is on disk."""
    repo_root = tmp_path
    (repo_root / "predictions").mkdir()
    _write_no_games_signal(repo_root, "2026-05-16")
    with pytest.raises(NoGamesSlateSoftSkip) as exc:
        materialize_precanonical_slate_universe(
            repo_root, date="2026-05-16", run_mode="morning_expected"
        )
    assert "PRECANNONICAL_SLATE_UNIVERSE_SOFT_SKIP_NO_GAMES" in str(exc.value)


def test_empty_parquet_without_no_games_signal_still_hard_fails(tmp_path):
    """No upstream no-games signal means an empty all_props parquet is
    a regression (predict ran but produced no rows for a games-bearing
    slate). Must remain a hard fail."""
    repo_root = tmp_path
    pred_dir = repo_root / "predictions"
    pred_dir.mkdir()
    empty = pd.DataFrame(columns=["slate_date", "player_id", "game_id", "stat", "line"])
    empty.to_parquet(pred_dir / "all_props_2026-05-16.parquet", index=False)
    with pytest.raises(PrecanonicalSlateUniverseError) as exc:
        materialize_precanonical_slate_universe(
            repo_root, date="2026-05-16", run_mode="morning_expected"
        )
    assert "PRECANNONICAL_SLATE_UNIVERSE_EMPTY" in str(exc.value)


def test_no_games_signal_with_other_reason_does_not_soft_skip(tmp_path):
    """A singles_<date>.json with a different reason field must NOT
    trigger soft-skip — only ``reason == "no_games_slate"`` is the
    legitimate upstream signal."""
    import json
    repo_root = tmp_path
    pred_dir = repo_root / "predictions"
    pred_dir.mkdir()
    empty = pd.DataFrame(columns=["slate_date", "player_id", "game_id", "stat", "line"])
    empty.to_parquet(pred_dir / "all_props_2026-05-16.parquet", index=False)
    (pred_dir / "singles_2026-05-16.json").write_text(
        json.dumps({"date": "2026-05-16", "reason": "odds_api_offline", "picks": []}),
        encoding="utf-8",
    )
    with pytest.raises(PrecanonicalSlateUniverseError) as exc:
        materialize_precanonical_slate_universe(
            repo_root, date="2026-05-16", run_mode="morning_expected"
        )
    assert "PRECANNONICAL_SLATE_UNIVERSE_EMPTY" in str(exc.value)
