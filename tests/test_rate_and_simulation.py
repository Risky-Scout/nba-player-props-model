"""Tests for rate quantile inference + minutes x rate simulation."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nba_props_model.models.minutes import MinutesDistribution
from nba_props_model.models.rate_models import (
    MIN_MINUTES_FOR_RATE,
    RATE_CLIP,
    RATE_QUANTILES,
    RATE_STATS,
    _rate_feature_cols,
)
from nba_props_model.models.simulation import (
    DOMAIN_MAX,
    StatPMF,
    _rate_samples_from_quantiles,
    simulate_stat_pmf,
)


def _mk_dist(p=(0.05, 0.15, 0.80)) -> MinutesDistribution:
    return MinutesDistribution(
        state_probs=p,
        limited_quantiles={10: 4.0, 25: 10.0, 50: 15.0, 75: 20.0, 90: 23.0},
        normal_quantiles={10: 25.0, 25: 28.0, 50: 32.0, 75: 36.0, 90: 40.0},
    )


def test_rate_feature_cols_excludes_targets_and_keys():
    df = pd.DataFrame({
        "player_id": [1, 2], "game_id": [1, 2], "team_id": [1, 1],
        "game_date": ["2024-01-01", "2024-01-02"],
        "min": [30, 28], "pts": [10, 12], "reb": [4, 5], "ast": [3, 2],
        "usage_proxy": [0.25, 0.3], "mp_ewma": [28.0, 27.0],
    })
    feats = _rate_feature_cols(df, "pts")
    assert "usage_proxy" in feats
    assert "mp_ewma" in feats
    for bad in ("pts", "reb", "ast", "min", "player_id", "game_id", "game_date"):
        assert bad not in feats


def test_rate_clip_values_sane():
    for s in RATE_STATS:
        assert 0.2 <= RATE_CLIP[s] <= 2.0


def test_stat_pmf_cdf_monotone_and_bounded():
    # Hand-built PMF peaked around 10.
    pmf = np.exp(-0.5 * ((np.arange(30) - 10) / 3.0) ** 2)
    pmf = pmf / pmf.sum()
    p = StatPMF(stat="pts", pmf=pmf)
    cdf = np.array([p.cdf(x) for x in range(30)])
    assert cdf[0] >= 0.0
    assert cdf[-1] == pytest.approx(1.0, abs=1e-6)
    assert np.all(np.diff(cdf) >= -1e-9)


def test_stat_pmf_prob_over_inverse_of_prob_under():
    pmf = np.exp(-0.5 * ((np.arange(20) - 8) / 2.0) ** 2)
    pmf = pmf / pmf.sum()
    p = StatPMF(stat="ast", pmf=pmf)
    for line in (3.5, 5.5, 7.5, 10.5):
        assert p.prob_over(line) + p.prob_under(line) == pytest.approx(1.0, abs=1e-6)


def test_rate_samples_never_negative_and_bounded():
    q = {10: 0.1, 25: 0.2, 50: 0.35, 75: 0.5, 90: 0.7}
    rng = np.random.default_rng(0)
    samples = _rate_samples_from_quantiles(q, 5_000, rng)
    assert samples.min() >= 0.0
    # Upper anchor: 1.2 * q90 = 0.84
    assert samples.max() <= 0.84 + 1e-9


def test_rate_samples_calibrate_to_quantile_table():
    q = {10: 0.1, 25: 0.2, 50: 0.35, 75: 0.5, 90: 0.7}
    rng = np.random.default_rng(1)
    samples = _rate_samples_from_quantiles(q, 50_000, rng)
    for qpct, expected in q.items():
        emp = float(np.mean(samples <= expected))
        assert abs(emp - qpct / 100.0) < 0.02


def test_simulate_stat_pmf_returns_none_when_no_artifacts(tmp_path, monkeypatch):
    """Without trained rate artifacts the simulator returns None so callers
    can fall back to the old path without crashing."""
    from nba_props_model.models import rate_models

    monkeypatch.setattr(rate_models, "_RATE_CACHE", {})
    monkeypatch.setattr(rate_models, "MODEL_DIR", tmp_path)

    dist = _mk_dist()
    result = simulate_stat_pmf("pts", dist, feature_row={"usage_proxy": 0.3})
    assert result is None


def test_simulate_stat_pmf_with_override_produces_valid_pmf():
    """Caller can inject an explicit rate quantile table for testing and
    get back a valid discrete PMF."""
    dist = _mk_dist(p=(0.05, 0.10, 0.85))
    rate_q = {10: 0.3, 25: 0.45, 50: 0.6, 75: 0.75, 90: 0.95}
    pmf = simulate_stat_pmf(
        stat="pts", minutes_dist=dist, feature_row={},
        n_draws=8_000, rng=np.random.default_rng(0),
        rate_q_override=rate_q,
    )
    assert pmf is not None
    assert pmf.stat == "pts"
    assert len(pmf.pmf) == DOMAIN_MAX["pts"] + 1
    # Must sum to 1
    assert pmf.pmf.sum() == pytest.approx(1.0, abs=1e-6)
    # Most mass between ~5 and ~40 for these numbers
    assert pmf.mean() > 5
    assert pmf.mean() < 40


def test_simulate_pmf_reflects_minutes_inactive_mass():
    """When P(INACTIVE) is large, the simulator must place mass at zero."""
    dist = _mk_dist(p=(0.50, 0.10, 0.40))
    rate_q = {10: 0.4, 25: 0.5, 50: 0.6, 75: 0.7, 90: 0.8}
    pmf = simulate_stat_pmf(
        stat="pts", minutes_dist=dist, feature_row={},
        n_draws=10_000, rng=np.random.default_rng(0),
        rate_q_override=rate_q,
    )
    # At 50% inactive, at least ~40% of total probability should sit at 0 pts.
    assert pmf.pmf[0] >= 0.40


def test_simulate_all_stats_returns_dict_only_for_available_rate_models(monkeypatch, tmp_path):
    """If no rate artifacts exist for any stat, simulate_all_main_stats is empty."""
    from nba_props_model.models import rate_models, simulation

    monkeypatch.setattr(rate_models, "_RATE_CACHE", {})
    monkeypatch.setattr(rate_models, "MODEL_DIR", tmp_path)

    result = simulation.simulate_all_main_stats(_mk_dist(), feature_row={})
    assert result == {}


def test_quantile_ladder_monotone_invariant_on_override():
    """Overrides that pass in a monotone table still produce a sensible PMF."""
    dist = _mk_dist()
    rate_q = {10: 0.1, 25: 0.2, 50: 0.3, 75: 0.4, 90: 0.5}
    pmf = simulate_stat_pmf(
        "ast", dist, {}, n_draws=5_000,
        rng=np.random.default_rng(0), rate_q_override=rate_q,
    )
    assert pmf is not None
    # CDF monotone
    cdf = np.array([pmf.cdf(x) for x in range(DOMAIN_MAX["ast"] + 1)])
    assert np.all(np.diff(cdf) >= -1e-9)
