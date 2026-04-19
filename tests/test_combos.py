"""Tests for combo-stat PMF derivations."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nba_props_model.models.combos import (
    COMBO_COMPONENTS,
    build_combo_pmf,
    combo_domain_max,
    combo_pmf_copula,
    combo_pmf_independence,
    _psd_project,
)
from nba_props_model.models.simulation import DOMAIN_MAX, StatPMF


def _mk_stat_pmf(stat: str, lam: float) -> StatPMF:
    """Poisson-shaped PMF for a stat, clipped to domain."""
    from scipy.stats import poisson
    k = np.arange(DOMAIN_MAX[stat] + 1)
    pmf = poisson.pmf(k, lam)
    tail = 1.0 - poisson.cdf(DOMAIN_MAX[stat], lam)
    pmf = pmf.copy()
    pmf[-1] += max(0.0, tail)
    pmf = pmf / pmf.sum()
    return StatPMF(stat=stat, pmf=pmf)


def test_combo_components_registry():
    assert COMBO_COMPONENTS["pra"] == ("pts", "reb", "ast")
    assert COMBO_COMPONENTS["pr"] == ("pts", "reb")
    assert COMBO_COMPONENTS["pa"] == ("pts", "ast")
    assert COMBO_COMPONENTS["ra"] == ("reb", "ast")


def test_combo_domain_max_sums_components():
    assert combo_domain_max(("pts", "reb", "ast")) == (
        DOMAIN_MAX["pts"] + DOMAIN_MAX["reb"] + DOMAIN_MAX["ast"]
    )


def test_independence_convolution_preserves_expectation():
    pts = _mk_stat_pmf("pts", lam=18)
    reb = _mk_stat_pmf("reb", lam=7)
    ast = _mk_stat_pmf("ast", lam=5)
    combo = combo_pmf_independence({"pts": pts, "reb": reb, "ast": ast})
    e_pts = pts.mean()
    e_reb = reb.mean()
    e_ast = ast.mean()
    e_combo = combo.mean()
    assert abs(e_combo - (e_pts + e_reb + e_ast)) < 1e-3


def test_independence_convolution_preserves_variance():
    pts = _mk_stat_pmf("pts", lam=18)
    reb = _mk_stat_pmf("reb", lam=7)
    combo = combo_pmf_independence({"pts": pts, "reb": reb})
    v_pts = pts.std() ** 2
    v_reb = reb.std() ** 2
    v_combo = combo.std() ** 2
    # Under independence Var(X+Y) = Var(X)+Var(Y).
    assert abs(v_combo - (v_pts + v_reb)) < 0.25


def test_copula_reduces_to_independence_with_identity():
    pts = _mk_stat_pmf("pts", lam=18)
    reb = _mk_stat_pmf("reb", lam=7)
    combo_ind = combo_pmf_independence({"pts": pts, "reb": reb})
    combo_cop = combo_pmf_copula(
        {"pts": pts, "reb": reb},
        correlation=np.eye(2), n_draws=40_000,
        rng=np.random.default_rng(0),
    )
    # Means should be close (sampling noise is a few tenths).
    assert abs(combo_ind.mean() - combo_cop.mean()) < 0.5


def test_copula_positive_correlation_increases_variance():
    pts = _mk_stat_pmf("pts", lam=18)
    reb = _mk_stat_pmf("reb", lam=7)
    combo_ind = combo_pmf_independence({"pts": pts, "reb": reb})
    corr = np.array([[1.0, 0.5], [0.5, 1.0]])
    combo_cor = combo_pmf_copula(
        {"pts": pts, "reb": reb},
        correlation=corr, n_draws=40_000,
        rng=np.random.default_rng(1),
    )
    assert combo_cor.std() > combo_ind.std()


def test_copula_negative_correlation_decreases_variance():
    pts = _mk_stat_pmf("pts", lam=18)
    ast = _mk_stat_pmf("ast", lam=5)
    combo_ind = combo_pmf_independence({"pts": pts, "ast": ast})
    corr = np.array([[1.0, -0.4], [-0.4, 1.0]])
    combo_cor = combo_pmf_copula(
        {"pts": pts, "ast": ast},
        correlation=corr, n_draws=40_000,
        rng=np.random.default_rng(2),
    )
    assert combo_cor.std() < combo_ind.std()


def test_build_combo_pmf_returns_none_when_component_missing():
    pts = _mk_stat_pmf("pts", lam=18)
    reb = _mk_stat_pmf("reb", lam=7)
    # PRA requires ast too — missing.
    result = build_combo_pmf("pra", {"pts": pts, "reb": reb})
    assert result is None


def test_build_combo_pmf_happy_path():
    pts = _mk_stat_pmf("pts", lam=18)
    reb = _mk_stat_pmf("reb", lam=7)
    ast = _mk_stat_pmf("ast", lam=5)
    result = build_combo_pmf("pra", {"pts": pts, "reb": reb, "ast": ast})
    assert result is not None
    assert result.stat == "pra"
    assert abs(result.pmf.sum() - 1.0) < 1e-6


def test_psd_project_is_idempotent_on_psd_input():
    base = np.array([[1.0, 0.3, 0.1], [0.3, 1.0, 0.2], [0.1, 0.2, 1.0]])
    out = _psd_project(base)
    out2 = _psd_project(out)
    assert np.allclose(out, out2, atol=1e-6)
    # Diagonal must remain 1 after projection.
    assert np.allclose(np.diag(out), 1.0, atol=1e-6)


def test_invalid_correlation_shape_raises():
    pts = _mk_stat_pmf("pts", lam=18)
    reb = _mk_stat_pmf("reb", lam=7)
    with pytest.raises(ValueError):
        combo_pmf_copula({"pts": pts, "reb": reb}, correlation=np.eye(3))


def test_unknown_combo_key_raises():
    pts = _mk_stat_pmf("pts", lam=18)
    with pytest.raises(ValueError):
        build_combo_pmf("pts_plus_sauce", {"pts": pts})
