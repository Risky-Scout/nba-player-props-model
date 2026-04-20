"""Guardrail for the isotonic final-fit bug.

IsotonicCalibrator is non-parametric — it has no .slope_ / .intercept_. The
earlier stat×side calibrator code read those attributes and raised on every
run. The fix derives slope/intercept from the calibrated probabilities.
"""
from __future__ import annotations

import numpy as np
import pytest

from nba_props_model.calibration.stat_side_platt import (
    IsotonicCalibrator,
    _calibration_slope,
)


def test_isotonic_calibrator_has_no_platt_attrs():
    cal = IsotonicCalibrator()
    # Deliberately do NOT fit — we want to confirm the class never exposes
    # slope_ / intercept_ at any point.
    assert not hasattr(cal, "slope_"), "IsotonicCalibrator must not expose slope_"
    assert not hasattr(cal, "intercept_"), "IsotonicCalibrator must not expose intercept_"


def test_isotonic_calibration_slope_from_calibrated_probs():
    rng = np.random.default_rng(0)
    raw = rng.uniform(0.01, 0.99, size=500)
    outcomes = (rng.uniform(0, 1, size=500) < raw).astype(int)

    cal = IsotonicCalibrator()
    cal.fit(raw, outcomes)
    cal_probs = cal.predict_proba(raw)

    slope, intercept = _calibration_slope(cal_probs, outcomes)
    assert np.isfinite(slope) and np.isfinite(intercept)
    # A correctly-calibrated isotonic on a well-specified generator should
    # sit near slope ≈ 1 (wide tolerance for sample size).
    assert 0.3 < slope < 3.0, f"slope {slope} far from 1 — suspicious calibration"


def test_isotonic_predict_proba_roundtrip_persistable(tmp_path):
    """The fitted calibrator must be joblib-persistable for the live predict
    path (this was the load-time surface for the original AttributeError)."""
    import joblib

    rng = np.random.default_rng(1)
    raw = rng.uniform(0.01, 0.99, size=200)
    outcomes = (rng.uniform(0, 1, size=200) < raw).astype(int)

    cal = IsotonicCalibrator()
    cal.fit(raw, outcomes)
    path = tmp_path / "iso.pkl"
    joblib.dump(cal, path)
    loaded = joblib.load(path)
    assert np.allclose(cal.predict_proba(raw), loaded.predict_proba(raw))
