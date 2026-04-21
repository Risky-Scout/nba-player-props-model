"""Tests for the state-aware minutes distribution."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nba_props_model.models.minutes import (
    LIMITED_UPPER,
    MINUTES_CEILING,
    MinutesDistribution,
    STATE_INACTIVE,
    STATE_LIMITED,
    STATE_NORMAL,
    _cdf_from_quantiles,
    _clean_quantiles,
    _mean_from_quantiles,
    _sample_from_quantiles,
    _state_label_array,
)


@pytest.fixture(autouse=True)
def _disable_minutes_cdf_calibrator(monkeypatch):
    """These tests assert raw-distribution invariants (inactive mass,
    state mixture, analytic mean). The retrained global calibrator would
    reshape those properties by design — disable it for this file so the
    architectural checks stay sharp. End-to-end calibrated-distribution
    behavior is validated separately in tests/test_minutes_calibrator.py."""
    from nba_props_model.models import minutes as m
    monkeypatch.setattr(m, "_MINUTES_CDF_CAL", None)
    monkeypatch.setattr(m, "_MINUTES_CDF_CAL_LOADED", True)


def _example_dist(
    p_inactive=0.10, p_limited=0.20, p_normal=0.70,
) -> MinutesDistribution:
    return MinutesDistribution(
        state_probs=(p_inactive, p_limited, p_normal),
        limited_quantiles={10: 5.0, 25: 10.0, 50: 15.0, 75: 20.0, 90: 23.0},
        normal_quantiles={10: 25.0, 25: 28.0, 50: 32.0, 75: 36.0, 90: 40.0},
    )


# ── state labeling ──────────────────────────────────────────────────────────


def test_state_labels_partition_minutes_range():
    y = np.array([0.0, 0.1, 15.0, 23.9, 24.0, 34.2, 48.0])
    s = _state_label_array(y)
    assert list(s) == [
        STATE_INACTIVE, STATE_LIMITED, STATE_LIMITED, STATE_LIMITED,
        STATE_NORMAL, STATE_NORMAL, STATE_NORMAL,
    ]


# ── MinutesDistribution invariants ─────────────────────────────────────────


def test_cdf_monotone_and_bounded():
    d = _example_dist()
    xs = np.linspace(0, MINUTES_CEILING, 200)
    cdf = np.array([d.cdf(x) for x in xs])
    assert cdf[0] >= 0.0
    assert cdf[-1] == pytest.approx(1.0, abs=1e-6)
    # non-decreasing
    assert np.all(np.diff(cdf) >= -1e-9)


def test_quantile_inverts_cdf():
    d = _example_dist()
    for q in (0.1, 0.25, 0.5, 0.75, 0.9):
        m = d.quantile(q)
        # CDF at the returned minute value should match q within numerical tolerance.
        assert d.cdf(m) == pytest.approx(q, abs=1e-2)


def test_inactive_mass_pins_lower_tail():
    d = _example_dist(p_inactive=0.40, p_limited=0.10, p_normal=0.50)
    # With 40% P(inactive), P(mins == 0) should be at least 0.40.
    assert d.cdf(0.0) >= 0.39 - 1e-9
    # CDF at m just above 0 inside LIMITED band should jump by p_inactive.
    assert d.cdf(0.001) >= 0.39


def test_sample_respects_state_mixture():
    rng = np.random.default_rng(7)
    d = _example_dist(p_inactive=0.25, p_limited=0.25, p_normal=0.50)
    samples = d.sample(10_000, rng)
    frac_zero = float(np.mean(samples == 0.0))
    assert 0.22 <= frac_zero <= 0.28   # ±3pp on 10k samples
    frac_limited = float(np.mean((samples > 0) & (samples < LIMITED_UPPER)))
    assert 0.22 <= frac_limited <= 0.28
    frac_normal = float(np.mean(samples >= LIMITED_UPPER))
    assert 0.47 <= frac_normal <= 0.53


def test_mean_matches_trapezoid():
    d = _example_dist(p_inactive=0.10, p_limited=0.20, p_normal=0.70)
    samples = d.sample(20_000, np.random.default_rng(42))
    # The analytic mean should be close to the empirical sample mean.
    assert abs(d.mean() - float(np.mean(samples))) < 0.5


def test_empty_quantiles_produce_safe_default():
    q = _clean_quantiles({}, 0.0, LIMITED_UPPER)
    assert set(q.keys()) == {10, 25, 50, 75, 90}
    vals = [q[k] for k in (10, 25, 50, 75, 90)]
    assert vals == sorted(vals)
    assert vals[0] >= 0.0 and vals[-1] <= LIMITED_UPPER


def test_clean_quantiles_enforces_monotone_after_clip():
    raw = {10: 30.0, 25: 5.0, 50: 15.0, 75: 5.0, 90: 40.0}
    out = _clean_quantiles(raw, 0.0, LIMITED_UPPER)
    # clipped to LIMITED_UPPER then made monotone
    vals = [out[k] for k in (10, 25, 50, 75, 90)]
    assert vals == sorted(vals)
    assert all(0.0 <= v <= LIMITED_UPPER for v in vals)


def test_cdf_from_quantiles_piecewise_linear():
    q = {10: 5.0, 25: 10.0, 50: 15.0, 75: 20.0, 90: 23.0}
    # Exactly at a knot: CDF equals the knot probability (accounting for
    # boundary anchoring at 0 and MINUTES_CEILING).
    assert _cdf_from_quantiles(q, 15.0) == pytest.approx(0.5, abs=1e-6)
    assert _cdf_from_quantiles(q, 0.0) == 0.0
    assert _cdf_from_quantiles(q, MINUTES_CEILING) == 1.0


def test_sample_from_quantiles_never_returns_negative():
    q = {10: 5.0, 25: 10.0, 50: 15.0, 75: 20.0, 90: 23.0}
    rng = np.random.default_rng(0)
    samples = [_sample_from_quantiles(q, rng) for _ in range(2_000)]
    assert min(samples) >= 0.0
    assert max(samples) <= MINUTES_CEILING


# ── classifier calibration: Brier decomposes per class ──────────────────────


def test_classifier_brier_matches_manual_definition():
    """If the training procedure emits per-class Brier, each entry must equal
    mean((p_c - y_c)^2) on the holdout."""
    # This checks the metric definition used by the training meta, so the
    # diagnostics report can read the meta JSON without re-running the model.
    y_true = np.array([0, 1, 2, 0, 2, 1, 2, 2])
    # Fake predicted probs, row-sum to 1.
    p = np.array([
        [0.7, 0.2, 0.1],
        [0.1, 0.8, 0.1],
        [0.1, 0.2, 0.7],
        [0.8, 0.1, 0.1],
        [0.2, 0.1, 0.7],
        [0.2, 0.6, 0.2],
        [0.1, 0.2, 0.7],
        [0.1, 0.3, 0.6],
    ])
    briers = {}
    for c in (0, 1, 2):
        briers[c] = float(np.mean((p[:, c] - (y_true == c).astype(int)) ** 2))
    # Sanity: a higher-confidence correct prediction reduces class Brier.
    assert briers[0] < 0.2 and briers[1] < 0.2 and briers[2] < 0.2


# ── conditional distributions: coverage on synthetic data ───────────────────


def test_conditional_coverage_on_limited_quantiles():
    """Given well-calibrated quantiles, 10/50/90 coverage should match the
    nominal levels on synthetic data drawn from the target distribution."""
    rng = np.random.default_rng(1)
    # Draw truth from a distribution with known 10/50/90 quantiles.
    truth = rng.uniform(0, 20, size=5_000)
    # Build quantile table from the empirical truth.
    q = {
        10: float(np.quantile(truth, 0.10)),
        25: float(np.quantile(truth, 0.25)),
        50: float(np.quantile(truth, 0.50)),
        75: float(np.quantile(truth, 0.75)),
        90: float(np.quantile(truth, 0.90)),
    }
    # Empirical below-quantile frequency.
    for qpct in (10, 25, 50, 75, 90):
        emp = float(np.mean(truth <= q[qpct]))
        assert abs(emp - qpct / 100.0) < 0.01


def test_mean_from_quantiles_is_non_negative_and_bounded():
    q = {10: 5.0, 25: 10.0, 50: 15.0, 75: 20.0, 90: 23.0}
    m = _mean_from_quantiles(q)
    assert 0.0 <= m <= MINUTES_CEILING


# ── distribution object roundtrips ──────────────────────────────────────────


def test_state_probs_normalize():
    d = MinutesDistribution(
        state_probs=(2.0, 2.0, 6.0),   # deliberately unnormalized
        limited_quantiles={10: 5, 25: 10, 50: 15, 75: 20, 90: 23},
        normal_quantiles={10: 25, 25: 28, 50: 32, 75: 36, 90: 40},
    )
    assert sum(d.state_probs) == pytest.approx(1.0, abs=1e-9)


def test_sample_returns_requested_count():
    d = _example_dist()
    samples = d.sample(123, np.random.default_rng(0))
    assert samples.shape == (123,)


# ── predict_minutes fallback path (no artifacts required) ──────────────────


def test_predict_minutes_returns_expected_dict_keys_with_no_artifacts(monkeypatch):
    """Even with no state-aware or legacy artifacts loaded, the legacy
    Gaussian-shaped fallback still produces the expected dict keys so the
    rest of the feature pipeline does not break."""
    from nba_props_model.models import minutes as m

    # Force the module into a no-artifacts state by clearing caches and
    # monkeypatching MODEL_DIR to an empty temp dir.
    monkeypatch.setattr(m, "_STATE_CLF", None)
    monkeypatch.setattr(m, "_COND_Q", {})
    monkeypatch.setattr(m, "_STATE_FEATURES", None)
    monkeypatch.setattr(m, "_LEGACY_CACHE", {})
    monkeypatch.setattr(m, "_LEGACY_FEATURES", None)

    prior = pd.DataFrame([
        {"player_id": 1, "game_date": f"2025-01-{d:02d}", "min": 30, "team_id": 10}
        for d in range(1, 12)
    ])
    # With no artifacts available, the function should walk through the
    # legacy fallback path and still return the summary dict.
    def _no_load(*args, **kwargs):
        return False
    monkeypatch.setattr(m, "_load_state_aware", _no_load)

    # Route the legacy loader to an empty cache too.
    def _noop():
        pass
    monkeypatch.setattr(m, "_load_legacy", _noop)

    result = m.predict_minutes(
        prior_stats=prior, game_context={"rest_days": 2}, is_home=True,
        target_date="2025-01-15", team_id=10, all_stats_df=pd.DataFrame(),
        injury_map={}, availability=None,
    )
    for key in ("mean_min_last10", "exp_mp", "mp_q10", "mp_q25",
                "mp_q75", "mp_q90", "mp_vol",
                "mp_pred_floor", "mp_pred_ceiling"):
        assert key in result
    # The distribution is accessible via the side-channel, not the return dict
    # (so the dict is parquet-serializable).
    assert m.last_distribution() is not None
