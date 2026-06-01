"""Tests for SGP PMF utilities — parse, validate, stats, probability functions."""
from __future__ import annotations

import json

import numpy as np
import pytest

try:
    from sgp_engine.pmf import (
        cdf_from_pmf,
        event_probability,
        parse_pmf,
        quantile_int_from_u,
        rank_to_uniform,
        validate_pmf,
    )
except ImportError as exc:
    pytest.skip(f"sgp_engine.pmf not available: {exc}", allow_module_level=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uniform_pmf(n: int) -> np.ndarray:
    return np.full(n, 1.0 / n)


def _push_mass(pmf_arr: np.ndarray, line: float) -> float:
    """P(k == line) for integer line, 0.0 for any non-integer line.

    This is the "push" probability that is excluded from both over and under
    when the line is exactly an integer.
    """
    if float(line) != float(int(line)):
        return 0.0
    k = int(line)
    arr = np.asarray(pmf_arr, dtype=float)
    if k < 0 or k >= len(arr):
        return 0.0
    return float(arr[k])


# ---------------------------------------------------------------------------
# 1 · parse_pmf input formats
# ---------------------------------------------------------------------------

class TestParsePMF:
    def test_parse_pmf_string_keys(self):
        pmf = parse_pmf({"0": 0.3, "1": 0.5, "2": 0.2})
        assert abs(pmf.sum() - 1.0) < 1e-9
        assert abs(pmf[0] - 0.3) < 1e-9
        assert abs(pmf[1] - 0.5) < 1e-9
        assert abs(pmf[2] - 0.2) < 1e-9

    def test_parse_pmf_dict_input(self):
        pmf = parse_pmf({0: 0.4, 1: 0.6})
        assert abs(pmf.sum() - 1.0) < 1e-9
        assert abs(pmf[0] - 0.4) < 1e-9
        assert abs(pmf[1] - 0.6) < 1e-9

    def test_parse_pmf_list_input(self):
        pmf = parse_pmf([0.25, 0.25, 0.25, 0.25])
        assert len(pmf) == 4
        assert abs(pmf.sum() - 1.0) < 1e-9
        for v in pmf:
            assert abs(v - 0.25) < 1e-9

    def test_parse_pmf_normalizes_sum_1001(self):
        # Sums to ≈1.001 — normalizes without error.
        pmf = parse_pmf([0.3, 0.5, 0.201])
        assert abs(pmf.sum() - 1.0) < 1e-9

    def test_parse_pmf_rejects_negative(self):
        """All-negative input has no positive mass → raises ValueError."""
        with pytest.raises(ValueError):
            parse_pmf([-0.5, -0.3, -0.2])

    def test_parse_pmf_rejects_zero_total(self):
        with pytest.raises(ValueError):
            parse_pmf([0.0, 0.0, 0.0])


# ---------------------------------------------------------------------------
# 2 · event_probability — over / under at half-lines and integer lines
# ---------------------------------------------------------------------------

class TestEventProbability:
    def test_prob_over_half_line(self):
        # P(k > 1.5) = P(k >= 2) = 0.3 + 0.2 = 0.5
        pmf = parse_pmf({"0": 0.2, "1": 0.3, "2": 0.3, "3": 0.2})
        assert abs(event_probability(pmf, 1.5, "over") - 0.5) < 1e-9

    def test_prob_under_half_line(self):
        # P(k < 1.5) = P(k <= 1) = 0.2 + 0.3 = 0.5
        pmf = parse_pmf({"0": 0.2, "1": 0.3, "2": 0.3, "3": 0.2})
        assert abs(event_probability(pmf, 1.5, "under") - 0.5) < 1e-9

    def test_push_mass_integer_line(self):
        # push_mass(pmf, 1) == pmf[1]
        pmf = parse_pmf([0.2, 0.3, 0.3, 0.2])
        push = _push_mass(pmf, 1)
        assert abs(push - float(pmf[1])) < 1e-9

    def test_push_mass_non_integer_line(self):
        # Non-integer line → push = 0 (no integer outcome equals 1.5)
        pmf = parse_pmf([0.2, 0.3, 0.3, 0.2])
        assert _push_mass(pmf, 1.5) == 0.0

    def test_event_probability_over_under_sum(self):
        # P(over L) + P(under L) + push_mass(L) must exactly cover the whole PMF.
        pmf = parse_pmf([0.2, 0.3, 0.3, 0.2])
        line = 1  # integer
        p_over = event_probability(pmf, line, "over")
        p_under = event_probability(pmf, line, "under")
        push = _push_mass(pmf, line)
        assert abs(p_over + p_under + push - 1.0) < 1e-9, (
            f"over={p_over:.4f} under={p_under:.4f} push={push:.4f} total={p_over+p_under+push:.4f}"
        )


# ---------------------------------------------------------------------------
# 3 · Inverse-CDF and rank-remap utilities
# ---------------------------------------------------------------------------

def test_inverse_cdf_from_pmf_basic():
    """Uniform PMF of size 10: quantile at u=0.5 maps to outcome 4."""
    pmf = _uniform_pmf(10)
    # CDF: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    # searchsorted(cdf, 0.5, side='left') returns 4
    result = quantile_int_from_u(pmf, np.array([0.5]))
    assert int(result[0]) == 4


def test_inverse_cdf_degenerate_pmf():
    """Degenerate PMF (all mass at k=7) → every u maps to 7."""
    pmf = np.zeros(20)
    pmf[7] = 1.0
    u = np.linspace(0.01, 0.99, 50)
    outcomes = quantile_int_from_u(pmf, u)
    assert (outcomes == 7).all()


def test_rank_remap_samples_preserves_pmf_marginal():
    """Rank-remap 10k N(0,1) samples through uniform-10 PMF.

    After the transform each bucket should appear within ±5 ppts of 10%.
    """
    rng = np.random.default_rng(42)
    n = 10_000
    normal_samples = rng.normal(size=n)
    target_pmf = _uniform_pmf(10)
    u = rank_to_uniform(normal_samples)
    outcomes = quantile_int_from_u(target_pmf, u)
    for k in range(10):
        frac = float((outcomes == k).mean())
        assert 0.05 < frac < 0.15, (
            f"Bucket {k}: fraction={frac:.4f} is outside the tolerance [0.05, 0.15]"
        )


def test_cdf_from_pmf_monotone_and_bounded():
    pmf = parse_pmf([0.1, 0.2, 0.4, 0.3])
    cdf = cdf_from_pmf(pmf)
    assert len(cdf) == 4
    assert abs(cdf[-1] - 1.0) < 1e-9
    for i in range(len(cdf) - 1):
        assert cdf[i] <= cdf[i + 1], f"CDF not monotone at index {i}"


def test_validate_pmf_valid():
    result = validate_pmf(_uniform_pmf(10))
    assert result["valid"] is True
    assert abs(result["sum"] - 1.0) < 1e-6


def test_validate_pmf_invalid_sum():
    arr = np.array([0.3, 0.3, 0.3])
    result = validate_pmf(arr)
    assert result["valid"] is False
