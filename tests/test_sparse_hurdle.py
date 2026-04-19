"""Tests for the hurdle / zero-inflated sparse-stat models."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nba_props_model.models.sparse_hurdle import (
    DOMAIN_MAX,
    STOCKS_DOMAIN_MAX,
    SPARSE_QUANTILES,
    SPARSE_STATS,
    _feature_cols,
    _sample_from_quantile_table,
    hurdle_pmf,
    stocks_pmf,
)


def test_feature_cols_excludes_targets_and_keys():
    df = pd.DataFrame({
        "player_id": [1, 2], "game_date": ["2024-01-01", "2024-01-02"],
        "team_id": [1, 1], "game_id": [1, 2],
        "stl": [1, 0], "blk": [0, 2], "min": [28, 30],
        "usage_proxy": [0.18, 0.2], "opp_pace": [99, 101],
    })
    feats = _feature_cols(df)
    assert "usage_proxy" in feats
    assert "opp_pace" in feats
    for bad in ("stl", "blk", "min", "player_id", "game_id", "game_date"):
        assert bad not in feats


def test_sample_from_quantile_table_bounded():
    q = {10: 1.0, 25: 1.3, 50: 1.8, 75: 2.5, 90: 3.2}
    rng = np.random.default_rng(0)
    samples = _sample_from_quantile_table(q, 5_000, rng, lo=0.5, hi=10.5)
    assert samples.min() >= 0.5
    assert samples.max() <= 10.5


def test_sample_from_quantile_table_matches_target_quantiles():
    q = {10: 1.0, 25: 1.3, 50: 1.8, 75: 2.5, 90: 3.2}
    rng = np.random.default_rng(1)
    samples = _sample_from_quantile_table(q, 50_000, rng, lo=0.5, hi=10.5)
    for qpct, expected in q.items():
        emp = float(np.mean(samples <= expected))
        assert abs(emp - qpct / 100.0) < 0.02


def test_hurdle_pmf_returns_none_when_no_artifacts(tmp_path, monkeypatch):
    from nba_props_model.models import sparse_hurdle as sh
    monkeypatch.setattr(sh, "_SPARSE_CACHE", {})
    monkeypatch.setattr(sh, "MODEL_DIR", tmp_path)
    assert hurdle_pmf("stl", feature_row={"usage_proxy": 0.3}) is None


def test_stocks_pmf_sums_to_one_and_preserves_domain():
    # Hand-built component PMFs
    stl = np.array([0.6, 0.25, 0.1, 0.04, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    blk = np.array([0.7, 0.2, 0.07, 0.02, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    combined = stocks_pmf(stl, blk)
    assert combined is not None
    assert combined.shape == (STOCKS_DOMAIN_MAX + 1,)
    assert combined.sum() == pytest.approx(1.0, abs=1e-6)
    # Combined expectation equals sum of component expectations (independence).
    e_stl = float(np.sum(stl * np.arange(len(stl))))
    e_blk = float(np.sum(blk * np.arange(len(blk))))
    e_sum = float(np.sum(combined * np.arange(len(combined))))
    assert abs(e_sum - (e_stl + e_blk)) < 1e-3


def test_stocks_pmf_zero_mass_is_product_of_components():
    stl = np.zeros(11); stl[0] = 0.5; stl[1] = 0.5
    blk = np.zeros(11); blk[0] = 0.3; blk[1] = 0.7
    combined = stocks_pmf(stl, blk)
    # P(stocks=0) should equal P(stl=0) * P(blk=0) = 0.15
    assert combined[0] == pytest.approx(0.15, abs=1e-6)


def test_stocks_pmf_with_missing_component_returns_none():
    stl = np.array([0.6, 0.25, 0.1, 0.04, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert stocks_pmf(stl, None) is None
    assert stocks_pmf(None, stl) is None


def test_quantiles_constant_respects_ladder():
    assert SPARSE_QUANTILES == (0.10, 0.25, 0.50, 0.75, 0.90)
    assert set(SPARSE_STATS) == {"stl", "blk"}


def test_domain_max_sane():
    # A seven-block game is once-a-decade; we set 10 as a hard ceiling.
    assert DOMAIN_MAX["stl"] == 10
    assert DOMAIN_MAX["blk"] == 10
    assert STOCKS_DOMAIN_MAX == 20
