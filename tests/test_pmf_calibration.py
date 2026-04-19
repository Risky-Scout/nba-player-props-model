"""Tests for the full-PMF calibration layer."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nba_props_model.calibration.pmf_calibration import (
    PMFCalibrator,
    _randomized_pit,
    _walk_forward_folds,
    fit_calibrator,
    fit_all,
)


def _make_pmfs(mu: float, n: int, k: int, sigma: float = 4.0) -> np.ndarray:
    """Make n Gaussian-shaped PMFs of support size k, peaked near mu."""
    x = np.arange(k)
    pmfs = []
    for _ in range(n):
        m = max(0.0, np.random.normal(mu, 2.0))
        pmf = np.exp(-0.5 * ((x - m) / sigma) ** 2)
        pmf = pmf / pmf.sum()
        pmfs.append(pmf)
    return np.array(pmfs)


def _dates_range(n: int, start: str = "2024-10-01") -> np.ndarray:
    return (pd.to_datetime(start) + pd.to_timedelta(np.arange(n), unit="D")).values


def test_randomized_pit_is_uniform_under_perfect_calibration():
    rng = np.random.default_rng(42)
    k = 40
    n = 5_000
    # Sample "true" outcomes from a known distribution.
    true_mu = 18.0
    outcomes = np.clip(
        np.round(rng.normal(true_mu, 4.0, size=n)).astype(int), 0, k - 1,
    )
    # Use well-calibrated PMFs (peaked at the actual outcome's true mu).
    pmfs = np.array([
        np.exp(-0.5 * ((np.arange(k) - true_mu) / 4.0) ** 2) for _ in range(n)
    ])
    pmfs = pmfs / pmfs.sum(axis=1, keepdims=True)
    u = _randomized_pit(pmfs, outcomes, rng)
    assert 0.0 <= u.min()
    assert u.max() <= 1.0
    # Uniformity: mean close to 0.5, KS-ish spread.
    assert abs(float(np.mean(u)) - 0.5) < 0.03
    assert abs(float(np.std(u)) - (1 / np.sqrt(12))) < 0.04


def test_randomized_pit_is_not_uniform_under_miscalibration():
    rng = np.random.default_rng(0)
    k = 40
    n = 5_000
    outcomes = np.clip(
        np.round(rng.normal(18.0, 4.0, size=n)).astype(int), 0, k - 1,
    )
    # Narrow, biased PMFs (underestimating variance and mean).
    pmfs = np.array([
        np.exp(-0.5 * ((np.arange(k) - 14.0) / 1.5) ** 2) for _ in range(n)
    ])
    pmfs = pmfs / pmfs.sum(axis=1, keepdims=True)
    u = _randomized_pit(pmfs, outcomes, rng)
    # Should NOT be uniform: expect high mean (outcomes typically in upper tail).
    assert float(np.mean(u)) > 0.6


def test_walk_forward_folds_respect_date_monotonicity():
    n = 600
    dates = _dates_range(n)
    folds = _walk_forward_folds(dates, fold_days=28, min_train_days=120)
    assert len(folds) > 0
    for train, val in folds:
        assert train.dtype == bool
        assert val.dtype == bool
        # Every val index is strictly after every train index in date.
        train_dates = pd.to_datetime(dates[train])
        val_dates = pd.to_datetime(dates[val])
        assert train_dates.max() < val_dates.min()


def test_fit_calibrator_monotone_and_bounded():
    rng = np.random.default_rng(7)
    k = 40
    n = 2_500
    # Slightly biased PMFs.
    pmfs = np.array([
        np.exp(-0.5 * ((np.arange(k) - 14.0) / 3.0) ** 2) for _ in range(n)
    ])
    pmfs = pmfs / pmfs.sum(axis=1, keepdims=True)
    outcomes = np.clip(
        np.round(rng.normal(18.0, 3.5, size=n)).astype(int), 0, k - 1,
    )
    dates = _dates_range(n)
    cal = fit_calibrator(
        stat="pts", pmfs=pmfs, outcomes=outcomes, dates=dates,
        fold_days=28, min_train_days=180, rng=rng,
    )
    assert cal is not None
    # Isotonic regression is monotone non-decreasing by construction.
    xs = np.linspace(0, 1, 50)
    ys = cal.isotonic.transform(xs)
    assert np.all(np.diff(ys) >= -1e-9)
    assert ys.min() >= 0.0
    assert ys.max() <= 1.0


def test_applied_calibrator_preserves_pmf_sum():
    rng = np.random.default_rng(4)
    n = 1_500
    k = 40
    pmfs = _make_pmfs(mu=18.0, n=n, k=k)
    outcomes = np.clip(np.round(rng.normal(20.0, 3.5, size=n)).astype(int), 0, k - 1)
    dates = _dates_range(n)
    cal = fit_calibrator(
        stat="pts", pmfs=pmfs, outcomes=outcomes, dates=dates,
        fold_days=28, min_train_days=180, rng=rng,
    )
    assert cal is not None
    # Apply to a random raw PMF; sum must stay at 1 and no entries negative.
    raw = pmfs[0]
    calibrated = cal.apply(raw)
    assert abs(calibrated.sum() - 1.0) < 1e-6
    assert calibrated.min() >= -1e-9


def test_applied_calibrator_preserves_cdf_monotonicity():
    rng = np.random.default_rng(13)
    n = 1_500
    k = 40
    pmfs = _make_pmfs(mu=18.0, n=n, k=k)
    outcomes = np.clip(np.round(rng.normal(20.0, 3.5, size=n)).astype(int), 0, k - 1)
    dates = _dates_range(n)
    cal = fit_calibrator(
        stat="pts", pmfs=pmfs, outcomes=outcomes, dates=dates,
        fold_days=28, min_train_days=180, rng=rng,
    )
    assert cal is not None
    raw = pmfs[0]
    calibrated = cal.apply(raw)
    cdf = np.cumsum(calibrated)
    assert np.all(np.diff(cdf) >= -1e-9)
    assert cdf[-1] == pytest.approx(1.0, abs=1e-6)


def test_fit_all_reports_pit_stats_per_stat(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "nba_props_model.calibration.pmf_calibration.CAL_META_PATH",
        tmp_path / "meta.json",
    )
    monkeypatch.setattr(
        "nba_props_model.calibration.pmf_calibration.MODEL_DIR", tmp_path,
    )
    rng = np.random.default_rng(2)
    n = 1_500
    k = 40
    pmfs = _make_pmfs(mu=18.0, n=n, k=k)
    outcomes = np.clip(np.round(rng.normal(20.0, 3.5, size=n)).astype(int), 0, k - 1)
    dates = _dates_range(n)
    meta = fit_all({"pts": (pmfs, outcomes, dates)}, rng=rng)
    assert "pts" in meta["stats"]
    assert meta["stats"]["pts"]["fitted"]
    # Calibration should tighten the PIT toward uniform mean 0.5.
    assert abs(meta["stats"]["pts"]["pit_mean_cal"] - 0.5) <= abs(
        meta["stats"]["pts"]["pit_mean_raw"] - 0.5
    )


def test_fit_all_handles_insufficient_data_gracefully(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "nba_props_model.calibration.pmf_calibration.MODEL_DIR", tmp_path,
    )
    monkeypatch.setattr(
        "nba_props_model.calibration.pmf_calibration.CAL_META_PATH",
        tmp_path / "meta.json",
    )
    pmfs = np.ones((50, 10)) / 10
    outcomes = np.zeros(50, dtype=int)
    dates = _dates_range(50)
    meta = fit_all({"pts": (pmfs, outcomes, dates)})
    assert meta["stats"]["pts"]["fitted"] is False
