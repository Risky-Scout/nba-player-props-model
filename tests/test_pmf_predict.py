"""Tests for the PMF-first prediction glue."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nba_props_model.models.minutes import MinutesDistribution
from nba_props_model.pipelines.pmf_predict import (
    PropPMF,
    build_prop_pmfs,
    score_full_universe,
    score_prop_line,
)


def _mk_dist() -> MinutesDistribution:
    return MinutesDistribution(
        state_probs=(0.02, 0.10, 0.88),
        limited_quantiles={10: 10.0, 25: 14.0, 50: 18.0, 75: 22.0, 90: 23.5},
        normal_quantiles={10: 26.0, 25: 30.0, 50: 34.0, 75: 38.0, 90: 42.0},
    )


def test_score_prop_line_returns_probabilities_that_sum_to_one():
    pmf = np.exp(-0.5 * ((np.arange(50) - 18) / 4.0) ** 2)
    pmf = pmf / pmf.sum()
    for line in (5.5, 12.5, 18.5, 25.5, 30.5):
        p_over, p_under = score_prop_line(pmf, line)
        assert abs(p_over + p_under - 1.0) < 1e-6
        assert 0 <= p_over <= 1
        assert 0 <= p_under <= 1


def test_score_prop_line_extremes_clamp():
    pmf = np.exp(-0.5 * ((np.arange(50) - 18) / 4.0) ** 2)
    pmf = pmf / pmf.sum()
    # Line below zero: everything above, so p_over ~ 1.
    p_over, p_under = score_prop_line(pmf, -1)
    assert p_over > 0.99
    # Line above domain: nothing above, so p_over == 0.
    p_over, p_under = score_prop_line(pmf, 100)
    assert p_over == 0.0


def test_build_prop_pmfs_returns_no_stats_without_artifacts(tmp_path, monkeypatch):
    """With no trained rate or hurdle artifacts, build_prop_pmfs returns
    an empty dict."""
    from nba_props_model.models import rate_models, sparse_hurdle as sh
    monkeypatch.setattr(rate_models, "_RATE_CACHE", {})
    monkeypatch.setattr(rate_models, "MODEL_DIR", tmp_path)
    monkeypatch.setattr(sh, "_SPARSE_CACHE", {})
    monkeypatch.setattr(sh, "MODEL_DIR", tmp_path)
    from nba_props_model.calibration import pmf_calibration
    monkeypatch.setattr(pmf_calibration, "MODEL_DIR", tmp_path)

    result = build_prop_pmfs(minutes_dist=_mk_dist(), feature_row={},
                             fg3m_hurdle_model=None)
    assert result == {}


def test_score_full_universe_marks_rejected_rows():
    # Hand-build a PMF and construct a universe row with low model edge.
    pmf = np.exp(-0.5 * ((np.arange(80) - 18) / 4.0) ** 2)
    pmf = pmf / pmf.sum()
    pmfs = {1: {"pts": PropPMF(stat="pts", pmf=pmf,
                               calibrated=False, model_version="v")}}
    universe = [{
        "player_id": 1, "player_name": "X", "stat": "pts", "side": "OVER",
        "offered_line": 18.5, "offered_american": -110, "paired_american": -110,
        "books_available": 3,
    }]
    df = score_full_universe(universe, pmfs)
    assert len(df) == 1
    # Model prob at 18.5 sits very close to 50%; edge vs -110 is tiny -> rejected.
    assert bool(df.iloc[0]["selected"]) is False
    assert df.iloc[0]["reject_reason"] == "ev_below_threshold"


def test_score_full_universe_returns_no_pmf_when_unknown_stat():
    universe = [{
        "player_id": 1, "player_name": "Y", "stat": "stocks",
        "side": "OVER", "offered_line": 3.5,
        "offered_american": -120, "paired_american": -110,
        "books_available": 3,
    }]
    df = score_full_universe(universe, prop_pmfs_by_player={})
    assert df.iloc[0]["reject_reason"] == "no_pmf"
    assert bool(df.iloc[0]["selected"]) is False
