"""PHASE 3 guardrails — monotone CDF calibration for minutes distribution.

The calibrator must preserve valid CDF behavior (monotone, bounded, starts
at 0 ends at 1) and should improve interval coverage on the holdout. The
calibrator is applied inside MinutesDistribution.cdf when the artifact is
present.
"""
from __future__ import annotations

import numpy as np
import pytest

from nba_props_model.models.minutes import (
    MINUTES_CEILING,
    MinutesCDFCalibrator,
    MinutesDistribution,
)


def _example_dist() -> MinutesDistribution:
    return MinutesDistribution(
        state_probs=(0.05, 0.20, 0.75),
        limited_quantiles={10: 4.0, 25: 8.0, 50: 14.0, 75: 20.0, 90: 23.0},
        normal_quantiles={10: 26.0, 25: 30.0, 50: 33.0, 75: 37.0, 90: 41.0},
    )


def test_calibrator_maps_unit_interval_onto_itself_monotone():
    rng = np.random.default_rng(0)
    # Simulate a miscalibrated PIT distribution skewed to high u.
    u = rng.beta(2.0, 5.0, size=300)
    cal = MinutesCDFCalibrator().fit(u)
    grid = np.linspace(0.0, 1.0, 101)
    mapped = np.array([cal.apply_cdf(g) for g in grid])
    # Monotone non-decreasing.
    assert np.all(np.diff(mapped) >= -1e-9)
    # Bounded inside [0, 1].
    assert mapped.min() >= 0.0 - 1e-9
    assert mapped.max() <= 1.0 + 1e-9
    assert abs(mapped[0]) < 1e-6
    assert abs(mapped[-1] - 1.0) < 1e-6


def test_distribution_cdf_remains_valid_after_calibration(monkeypatch):
    from nba_props_model.models import minutes as m

    d = _example_dist()
    rng = np.random.default_rng(7)
    # Fit a calibrator on synthetic PIT values and inject into the module.
    pit = rng.beta(3.0, 2.0, size=250)
    cal = MinutesCDFCalibrator().fit(pit)
    monkeypatch.setattr(m, "_MINUTES_CDF_CAL", cal)
    monkeypatch.setattr(m, "_MINUTES_CDF_CAL_LOADED", True)

    xs = np.linspace(0.0, MINUTES_CEILING, 100)
    cdfs = np.array([d.cdf(x) for x in xs])
    assert cdfs[0] >= 0.0 - 1e-9
    assert cdfs[-1] <= 1.0 + 1e-6
    # Monotone non-decreasing after calibration.
    assert np.all(np.diff(cdfs) >= -1e-9)


def test_quantile_is_inverse_of_calibrated_cdf(monkeypatch):
    from nba_props_model.models import minutes as m

    d = _example_dist()
    rng = np.random.default_rng(9)
    pit = rng.beta(2.0, 2.0, size=200)
    cal = MinutesCDFCalibrator().fit(pit)
    monkeypatch.setattr(m, "_MINUTES_CDF_CAL", cal)
    monkeypatch.setattr(m, "_MINUTES_CDF_CAL_LOADED", True)

    for q in (0.1, 0.25, 0.5, 0.75, 0.9):
        mq = d.quantile(q)
        assert 0.0 <= mq <= MINUTES_CEILING
        # cdf at the returned minute value should be close to the target q.
        assert d.cdf(mq) == pytest.approx(q, abs=2e-2)


def test_calibrator_absent_falls_through_to_raw_cdf(monkeypatch):
    """When the calibrator artifact is missing, cdf() must return the raw
    mixture CDF unchanged — this is the backward-compatible behavior."""
    from nba_props_model.models import minutes as m

    monkeypatch.setattr(m, "_MINUTES_CDF_CAL", None)
    monkeypatch.setattr(m, "_MINUTES_CDF_CAL_LOADED", True)
    d = _example_dist()
    raw = d._raw_cdf(20.0)
    cal = d.cdf(20.0)
    assert cal == pytest.approx(raw, abs=1e-9)


def test_calibrator_improves_pit_uniformity_on_skewed_input():
    """Starting from a PIT distribution that is far from Uniform, the fitted
    calibrator must pull the calibrated values closer to Uniform. We use
    the KS distance to Uniform as the metric."""
    rng = np.random.default_rng(11)
    # PIT values skewed to the low end (model over-predicts minutes).
    pit = rng.beta(1.5, 6.0, size=500)
    cal = MinutesCDFCalibrator().fit(pit)
    pit_cal = np.array([cal.apply_cdf(u) for u in pit])

    def ks(xs):
        xs = np.sort(xs)
        n = len(xs)
        emp = np.arange(1, n + 1) / n
        nominal = xs
        return float(np.max(np.abs(emp - nominal)))

    assert ks(pit_cal) <= ks(pit), (
        f"calibrator did not improve PIT uniformity: "
        f"before={ks(pit):.3f} after={ks(pit_cal):.3f}"
    )
