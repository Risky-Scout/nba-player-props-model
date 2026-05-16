"""Tests for the daily minutes predictions artifact contract.

Cases:

    1. ``REQUIRED_OUTPUT_COLUMNS`` matches the spec verbatim.
    2. ``validate_minutes_artifact`` rejects missing required columns.
    3. ``validate_minutes_artifact`` rejects duplicate
       (slate_date, game_id, player_id) rows.
    4. ``validate_minutes_artifact`` rejects null minutes_mean /
       null minutes_p10/p50/p90 / null rotation/starter probabilities.
    5. ``validate_minutes_artifact`` rejects minutes outside [0, 60].
    6. ``validate_minutes_artifact`` rejects probabilities outside
       [0, 1].
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load_minutes_predictions_module():
    import importlib.util
    script_path = REPO_ROOT / "scripts" / "build_minutes_predictions.py"
    spec = importlib.util.spec_from_file_location(
        "build_minutes_predictions", script_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build_minutes_predictions = _load_minutes_predictions_module()

REQUIRED_OUTPUT_COLUMNS = build_minutes_predictions.REQUIRED_OUTPUT_COLUMNS
validate_minutes_artifact = build_minutes_predictions.validate_minutes_artifact


SLATE_DATE = "2026-05-15"


def _good_row(player_id, game_id, **overrides):
    base = {
        "slate_date": SLATE_DATE,
        "game_id": game_id,
        "player_id": player_id,
        "player_name": f"Player_{player_id}",
        "team": "LAL",
        "opponent": "BOS",
        "is_home": True,
        "rotation_probability": 0.80,
        "starter_probability": 0.60,
        "projected_role": "starter",
        "minutes_mean": 30.0,
        "minutes_p10": 24.0,
        "minutes_p50": 30.0,
        "minutes_p90": 36.0,
        "minutes_std": 3.5,
        "p_inactive_used": 0.02,
        "minutes_source": "state_aware_minutes_model",
        "minutes_model_version": "state_aware_v1",
        "feature_snapshot_id": "abc123",
        "lineup_snapshot_id": None,
        "injury_freshness_status": "fresh",
        "lineup_freshness_status": "projected",
        "inferred_at_utc": "2026-05-15T13:00:00Z",
    }
    base.update(overrides)
    return base


def _good_df(rows=None):
    rows = rows or [_good_row(101, 9001), _good_row(102, 9001)]
    return pd.DataFrame(rows, columns=REQUIRED_OUTPUT_COLUMNS)


def test_required_columns_match_spec_verbatim():
    assert REQUIRED_OUTPUT_COLUMNS == [
        "slate_date",
        "game_id",
        "player_id",
        "player_name",
        "team",
        "opponent",
        "is_home",
        "rotation_probability",
        "starter_probability",
        "projected_role",
        "minutes_mean",
        "minutes_p10",
        "minutes_p50",
        "minutes_p90",
        "minutes_std",
        "p_inactive_used",
        "minutes_source",
        "minutes_model_version",
        "feature_snapshot_id",
        "lineup_snapshot_id",
        "injury_freshness_status",
        "lineup_freshness_status",
        "inferred_at_utc",
    ]


def test_validator_passes_well_formed_artifact():
    validate_minutes_artifact(_good_df(), slate_date=SLATE_DATE)


def test_validator_rejects_missing_required_columns():
    df = _good_df().drop(columns=["minutes_mean"])
    with pytest.raises(SystemExit, match="missing required columns"):
        validate_minutes_artifact(df, slate_date=SLATE_DATE)


def test_validator_rejects_duplicate_keys():
    df = _good_df([_good_row(101, 9001), _good_row(101, 9001)])
    with pytest.raises(SystemExit, match="duplicate"):
        validate_minutes_artifact(df, slate_date=SLATE_DATE)


def test_validator_rejects_null_minutes_mean():
    df = _good_df([_good_row(101, 9001, minutes_mean=None)])
    with pytest.raises(SystemExit, match="minutes_mean"):
        validate_minutes_artifact(df, slate_date=SLATE_DATE)


def test_validator_rejects_null_quantile():
    df = _good_df([_good_row(101, 9001, minutes_p50=None)])
    with pytest.raises(SystemExit, match="minutes_p50"):
        validate_minutes_artifact(df, slate_date=SLATE_DATE)


def test_validator_rejects_null_probabilities():
    df = _good_df([_good_row(101, 9001, rotation_probability=None)])
    with pytest.raises(SystemExit, match="rotation_probability"):
        validate_minutes_artifact(df, slate_date=SLATE_DATE)


def test_validator_rejects_minutes_out_of_range():
    df = _good_df([_good_row(101, 9001, minutes_mean=75.0)])
    with pytest.raises(SystemExit, match=r"outside \[0, 60\]"):
        validate_minutes_artifact(df, slate_date=SLATE_DATE)


def test_validator_rejects_probability_out_of_range():
    df = _good_df([_good_row(101, 9001, starter_probability=1.5)])
    with pytest.raises(SystemExit, match=r"outside \[0, 1\]"):
        validate_minutes_artifact(df, slate_date=SLATE_DATE)


def _deep_bench_row(player_id, game_id, **overrides):
    return _good_row(
        player_id,
        game_id,
        rotation_probability=0.10,
        starter_probability=0.05,
        projected_role="deep_bench",
        minutes_mean=4.0,
        minutes_p10=0.0,
        minutes_p50=3.0,
        minutes_p90=9.0,
        minutes_std=2.5,
        p_inactive_used=0.40,
        **overrides,
    )


def test_eligible_view_excludes_deep_bench_when_no_market_line():
    """Q1 contract: universe artifact INCLUDES deep-bench rows by design,
    eligible artifact EXCLUDES them when none of the four floors
    (market line / starter / rotation / minutes) clears."""
    build_eligible_view = build_minutes_predictions.build_eligible_view

    universe = _good_df(
        [
            _good_row(101, 9001),
            _deep_bench_row(102, 9001),
            _good_row(103, 9001, rotation_probability=0.20, starter_probability=0.10,
                      minutes_mean=20.0),
            _good_row(104, 9001, rotation_probability=0.20, starter_probability=0.80,
                      minutes_mean=8.0),
        ]
    )
    # Empty market frame -> no current_market_line signal.
    empty_market = pd.DataFrame(columns=["slate_date", "game_id", "player_id", "line", "stat"])

    eligible = build_eligible_view(universe, slate_date=SLATE_DATE, market_df=empty_market)

    universe_ids = set(universe["player_id"].tolist())
    eligible_ids = set(eligible["player_id"].tolist())
    assert 102 in universe_ids, "universe must include the deep-bench row"
    assert 102 not in eligible_ids, "eligible view must drop deep-bench rows"
    assert 101 in eligible_ids, "starter (>=0.50) must remain eligible"
    assert 103 in eligible_ids, "minutes_mean>=12 must remain eligible"
    assert 104 in eligible_ids, "starter_probability>=0.50 must remain eligible"

    assert "has_current_market_line" in eligible.columns
    assert "eligibility_reason" in eligible.columns
    valid = {
        "current_market_line",
        "starter_probability",
        "rotation_probability",
        "minutes_floor",
    }
    assert set(eligible["eligibility_reason"].astype(str).tolist()).issubset(valid)


def test_eligible_view_keeps_deep_bench_with_market_line():
    """Same deep-bench row becomes eligible when a current market line
    exists for it (current_market_line floor)."""
    build_eligible_view = build_minutes_predictions.build_eligible_view

    universe = _good_df([_deep_bench_row(202, 9002)])
    market = pd.DataFrame(
        [
            {
                "slate_date": SLATE_DATE,
                "game_id": 9002,
                "player_id": 202,
                "line": 4.5,
                "stat": "points",
            }
        ]
    )

    eligible = build_eligible_view(universe, slate_date=SLATE_DATE, market_df=market)
    assert len(eligible) == 1
    row = eligible.iloc[0].to_dict()
    assert row["player_id"] == 202
    assert bool(row["has_current_market_line"]) is True
    assert row["eligibility_reason"] == "current_market_line"
