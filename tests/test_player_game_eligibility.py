"""Tests for the M8.9 player-game eligibility gate.

Cases enforced:

    1. Deep bench (no market line, low minutes, low rotation/starter
       probability) -> not eligible.
    2. Projected starter (starter_probability >= 0.50) -> eligible by
       starter_probability.
    3. Rotation player (rotation_probability >= 0.50) -> eligible by
       rotation_probability.
    4. Minutes floor (minutes_mean >= 12) -> eligible by minutes_floor.
    5. Market-quoted player (has_current_market_line) -> eligible by
       current_market_line even if minutes are low.
    6. Stale market line (slate_date != target slate) -> filtered out
       by build_current_market_player_signal; does NOT make the
       player eligible.
    7. Empty / whitespace / 'NA' line strings are normalised to NaN
       by normalize_line_column.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.pipelines.player_game_eligibility import (  # noqa: E402
    build_current_market_player_signal,
    build_player_game_eligibility,
    normalize_line_column,
    require_minutes_contract,
)


SLATE_DATE = "2026-05-15"


def _minutes_row(
    *,
    player_id,
    game_id,
    minutes_mean,
    rotation_probability,
    starter_probability,
    p_inactive_used=0.0,
    projected_role="rotation",
):
    return {
        "slate_date": SLATE_DATE,
        "game_id": game_id,
        "player_id": player_id,
        "minutes_mean": minutes_mean,
        "minutes_p10": max(0.0, minutes_mean - 4.0),
        "minutes_p50": minutes_mean,
        "minutes_p90": minutes_mean + 4.0,
        "minutes_std": 3.0,
        "rotation_probability": rotation_probability,
        "starter_probability": starter_probability,
        "projected_role": projected_role,
        "p_inactive_used": p_inactive_used,
        "minutes_source": "minutes_distribution",
        "minutes_model_version": "test-v1",
    }


def _base(player_id, game_id):
    return {"slate_date": SLATE_DATE, "game_id": game_id, "player_id": player_id}


def _build(rows_base, rows_minutes, rows_market):
    base = pd.DataFrame(rows_base)
    minutes = pd.DataFrame(rows_minutes)
    market = pd.DataFrame(rows_market)
    signal = build_current_market_player_signal(market, slate_date=SLATE_DATE)
    return build_player_game_eligibility(
        base, minutes, signal, slate_date=SLATE_DATE
    )


def test_deep_bench_no_line_low_minutes_is_ineligible():
    out = _build(
        rows_base=[_base(101, 9001)],
        rows_minutes=[_minutes_row(
            player_id=101, game_id=9001, minutes_mean=4.0,
            rotation_probability=0.10, starter_probability=0.02,
            p_inactive_used=0.40, projected_role="inactive_risk",
        )],
        rows_market=[],
    )
    assert bool(out["player_game_eligible"].iloc[0]) is False
    assert out["eligibility_reason"].iloc[0] == "not_eligible"


def test_projected_starter_is_eligible_by_starter_probability():
    out = _build(
        rows_base=[_base(102, 9001)],
        rows_minutes=[_minutes_row(
            player_id=102, game_id=9001, minutes_mean=8.0,
            rotation_probability=0.40, starter_probability=0.85,
            projected_role="starter",
        )],
        rows_market=[],
    )
    assert bool(out["player_game_eligible"].iloc[0]) is True
    # current_market_line takes precedence; only starter when no line.
    assert out["eligibility_reason"].iloc[0] == "starter_probability"


def test_rotation_player_is_eligible_by_rotation_probability():
    out = _build(
        rows_base=[_base(103, 9001)],
        rows_minutes=[_minutes_row(
            player_id=103, game_id=9001, minutes_mean=8.0,
            rotation_probability=0.65, starter_probability=0.10,
            projected_role="rotation",
        )],
        rows_market=[],
    )
    assert bool(out["player_game_eligible"].iloc[0]) is True
    assert out["eligibility_reason"].iloc[0] == "rotation_probability"


def test_minutes_floor_makes_player_eligible():
    out = _build(
        rows_base=[_base(104, 9001)],
        rows_minutes=[_minutes_row(
            player_id=104, game_id=9001, minutes_mean=14.0,
            rotation_probability=0.20, starter_probability=0.05,
            projected_role="rotation",
        )],
        rows_market=[],
    )
    assert bool(out["player_game_eligible"].iloc[0]) is True
    assert out["eligibility_reason"].iloc[0] == "minutes_floor"


def test_market_quoted_player_is_eligible_even_with_low_minutes():
    out = _build(
        rows_base=[_base(105, 9001)],
        rows_minutes=[_minutes_row(
            player_id=105, game_id=9001, minutes_mean=3.0,
            rotation_probability=0.05, starter_probability=0.02,
            p_inactive_used=0.30, projected_role="inactive_risk",
        )],
        rows_market=[{
            "slate_date": SLATE_DATE,
            "game_id": 9001,
            "player_id": 105,
            "stat": "points",
            "line": 4.5,
        }],
    )
    assert bool(out["player_game_eligible"].iloc[0]) is True
    assert out["eligibility_reason"].iloc[0] == "current_market_line"


def test_stale_market_line_does_not_make_player_eligible():
    # Player has a market line, but for yesterday's slate.
    out = _build(
        rows_base=[_base(106, 9001)],
        rows_minutes=[_minutes_row(
            player_id=106, game_id=9001, minutes_mean=4.0,
            rotation_probability=0.10, starter_probability=0.02,
            p_inactive_used=0.40, projected_role="inactive_risk",
        )],
        rows_market=[{
            "slate_date": "2026-05-14",  # stale
            "game_id": 9001,
            "player_id": 106,
            "stat": "points",
            "line": 4.5,
        }],
    )
    assert bool(out["player_game_eligible"].iloc[0]) is False
    assert bool(out["has_current_market_line"].iloc[0]) is False


def test_empty_line_strings_are_normalised_to_nan():
    df = pd.DataFrame({
        "line": ["4.5", "", " ", "NA", "N/A", "nan", "None", None, "12.0"],
    })
    out = normalize_line_column(df)
    # 4.5 and 12.0 survive; everything else becomes NaN.
    finite = out["line"].dropna().tolist()
    assert sorted(finite) == [4.5, 12.0]


def test_require_minutes_contract_rejects_missing_columns():
    minutes = pd.DataFrame({
        "slate_date": [SLATE_DATE],
        "game_id": [9001],
        "player_id": [101],
    })
    with pytest.raises(RuntimeError, match="missing required columns"):
        require_minutes_contract(minutes)


def test_require_minutes_contract_rejects_duplicates():
    minutes = pd.DataFrame(
        [_minutes_row(
            player_id=101, game_id=9001, minutes_mean=8.0,
            rotation_probability=0.10, starter_probability=0.10,
        )] * 2
    )
    with pytest.raises(RuntimeError, match="duplicate"):
        require_minutes_contract(minutes)
