import numpy as np
from sklearn.isotonic import IsotonicRegression

from nba_props_model.calibration.pmf_calibration import (
    PMFCalibrator,
    _repair_basketball_tail_shape,
)


def test_pmf_calibrator_does_not_dump_residual_into_fg3m_terminal_bucket():
    raw = np.zeros(16, dtype=float)
    raw[0] = 0.3544
    raw[1] = 0.3470
    raw[2] = 0.1883
    raw[3] = 0.0870
    raw[4] = 0.0233
    raw = raw / raw.sum()

    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    iso.fit(
        np.asarray([0.0, 0.50, 0.98, 1.0], dtype=float),
        np.asarray([0.0, 0.50, 0.9767, 0.9767], dtype=float),
    )

    cal = PMFCalibrator(
        stat="fg3m",
        isotonic=iso,
        n_train=4,
        fold_spans=[],
    ).apply(raw)

    assert np.isclose(cal.sum(), 1.0)
    assert np.all(cal >= 0.0)
    assert cal[-1] <= 1e-5


def test_tail_repair_spreads_isolated_remote_pts_atom():
    k = np.arange(81, dtype=float)
    raw = np.exp(-0.5 * ((k - 24.0) / 6.0) ** 2)
    raw[45:] = 0.0
    raw = raw / raw.sum()

    cal = raw.copy()
    cal[60] = 0.003
    cal = cal / cal.sum()

    repaired = _repair_basketball_tail_shape(raw, cal, "pts")

    assert np.isclose(repaired.sum(), 1.0)
    assert np.all(repaired >= 0.0)
    assert repaired[60] < 0.001
    assert repaired[59] > 0.0
    assert repaired[61] > 0.0
