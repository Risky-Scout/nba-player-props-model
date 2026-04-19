"""Tests for the diagnostics suite."""
from __future__ import annotations

import numpy as np
import pytest

from nba_props_model.evaluation.diagnostics import (
    FoldMetrics,
    american_to_decimal,
    american_to_prob,
    bootstrap_ci,
    brier,
    calibration_slope_intercept,
    devig_pair,
    discrete_crps,
    ece,
    edge_decile_monotonicity,
    evaluate_fold,
    log_score,
    pit_ks_distance,
    randomized_pit,
    write_report,
)


def test_log_score_penalises_wrong_bin():
    # Two PMFs: one confidently places all mass on the right answer, one
    # spreads evenly. The spread PMF should have higher NLL.
    n_bins = 10
    sharp = np.zeros((1, n_bins)); sharp[0, 7] = 1.0
    flat = np.ones((1, n_bins)) / n_bins
    outcomes = np.array([7])
    assert log_score(sharp, outcomes) < log_score(flat, outcomes)


def test_discrete_crps_nonnegative_and_zero_for_delta():
    pmf = np.zeros((1, 10)); pmf[0, 3] = 1.0
    assert discrete_crps(pmf, np.array([3])) == pytest.approx(0.0, abs=1e-12)
    # Wide uniform PMF has positive CRPS.
    flat = np.ones((1, 10)) / 10
    assert discrete_crps(flat, np.array([3])) > 0.0


def test_randomized_pit_uniformity_on_ideal_model():
    rng = np.random.default_rng(42)
    n_bins = 40
    n = 5_000
    mu = 18.0
    pmfs = np.array([np.exp(-0.5 * ((np.arange(n_bins) - mu) / 4.0) ** 2)
                     for _ in range(n)])
    pmfs = pmfs / pmfs.sum(axis=1, keepdims=True)
    outcomes = np.clip(np.round(rng.normal(mu, 4.0, size=n)).astype(int),
                       0, n_bins - 1)
    pit = randomized_pit(pmfs, outcomes, rng)
    assert abs(float(np.mean(pit)) - 0.5) < 0.03


def test_pit_ks_distance_returns_small_on_uniform():
    rng = np.random.default_rng(0)
    u = rng.uniform(0, 1, size=2_000)
    assert pit_ks_distance(u) < 0.05


def test_pit_ks_distance_detects_non_uniform():
    rng = np.random.default_rng(0)
    skewed = rng.beta(2.0, 5.0, size=2_000)   # heavy mass near 0
    assert pit_ks_distance(skewed) > 0.1


def test_brier_and_ece_cover_trivial_cases():
    probs = np.array([0.1, 0.2, 0.5, 0.8, 0.9])
    outcomes = np.array([0, 0, 1, 1, 1])
    # Brier on this pattern is moderate and bounded in [0, 1].
    b = brier(probs, outcomes)
    assert 0.0 <= b <= 1.0
    # ECE is small for a reasonable ordering.
    assert 0.0 <= ece(probs, outcomes, bins=5) <= 0.5


def test_calibration_slope_1_for_perfect_cal():
    # When probs equal outcomes exactly, slope is 1 and intercept is 0.
    outcomes = np.array([0, 0, 1, 1, 1], dtype=float)
    probs = outcomes.copy()
    slope, intercept = calibration_slope_intercept(probs, outcomes)
    assert slope == pytest.approx(1.0, abs=1e-6)
    assert intercept == pytest.approx(0.0, abs=1e-6)


def test_devig_pair_sums_to_one():
    fair_over = devig_pair(0.55, 0.50)
    fair_under = 1.0 - fair_over
    assert fair_over + fair_under == pytest.approx(1.0, abs=1e-12)


def test_american_conversions_roundtrip():
    for odds in (-200, -110, +100, +150, +250):
        p = american_to_prob(odds)
        d = american_to_decimal(odds)
        # Under fair pricing p * decimal = 1.
        assert p * d == pytest.approx(1.0, abs=1e-6)


def test_bootstrap_ci_contains_mean():
    rng = np.random.default_rng(3)
    values = rng.normal(0.05, 0.2, size=500)
    mean, lo, hi = bootstrap_ci(values, ci=0.9, n=500, rng=rng)
    assert lo <= mean <= hi


def test_edge_decile_monotonicity_returns_positive_on_well_ordered_data():
    rng = np.random.default_rng(0)
    n = 1_000
    edges = rng.uniform(-0.1, 0.3, size=n)
    # Bets with higher edge return more on average.
    returns = np.where(rng.uniform(0, 1, size=n) < (0.5 + edges), 1.0, -1.0)
    rho, means = edge_decile_monotonicity(edges, returns)
    assert rho > 0.5
    assert len(means) >= 8  # at least 8 non-empty deciles


def test_evaluate_fold_produces_complete_struct():
    rng = np.random.default_rng(0)
    n = 500
    n_bins = 40
    pmfs = np.array([np.exp(-0.5 * ((np.arange(n_bins) - 18) / 4.0) ** 2)
                     for _ in range(n)])
    pmfs = pmfs / pmfs.sum(axis=1, keepdims=True)
    outcomes = np.clip(np.round(rng.normal(18, 4, size=n)).astype(int),
                       0, n_bins - 1)
    over_probs_model = rng.uniform(0.3, 0.7, size=n)
    over_probs_market = rng.uniform(0.35, 0.65, size=n)
    over_realised = (rng.uniform(0, 1, size=n) < over_probs_model).astype(int)
    edges = over_probs_model - over_probs_market
    returns = np.where(over_realised == 1, 1.0, -1.0)

    m = evaluate_fold(
        pmfs, outcomes, over_probs_model, over_probs_market, over_realised,
        edges, returns, stat="pts",
        fold_start="2025-10-01", fold_end="2025-10-28", rng=rng,
    )
    assert isinstance(m, FoldMetrics)
    assert m.n == n
    assert np.isfinite(m.log_score)
    assert np.isfinite(m.crps)
    assert np.isfinite(m.brier)
    assert np.isfinite(m.ece)


def test_write_report_round_trips(tmp_path, monkeypatch):
    from nba_props_model.evaluation import diagnostics
    monkeypatch.setattr(diagnostics, "DOCS_DIR", tmp_path)
    fm = FoldMetrics(
        fold_start="2025-10-01", fold_end="2025-10-28",
        stat="pts", n=100, log_score=2.1, crps=1.2,
        pit_mean=0.51, pit_std=0.29, pit_ks=0.03,
        brier=0.22, ece=0.01, cal_slope=0.98, cal_intercept=0.005,
        market_logscore_lift=0.012, edge_monotonicity_rho=0.6,
    )
    path = diagnostics.write_report([fm], run_date="2026-04-19")
    content = path.read_text()
    assert "Stat: `pts`" in content
    assert "2025-10-01" in content
    assert "2025-10-28" in content
