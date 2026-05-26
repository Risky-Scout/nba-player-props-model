"""tests/test_sparse_hurdle_tail_shape.py

Tests that the sparse hurdle PMF builder produces well-shaped distributions:
  - No non-monotone tail spikes after the plausible region.
  - PMF sums to approximately 1.0.
  - No negative probabilities.
  - q99 at low values (2-3) does not create mass spikes at k=7-10.

These tests exercise the internal helpers directly (no model artifacts needed).
"""

from __future__ import annotations

import numpy as np
import pytest

from nba_props_model.models.sparse_hurdle import (
    _enforce_monotone_positive_tail,
    _sample_from_quantile_table,
    DOMAIN_MAX,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_q_table_with_low_q90(q90_val: float = 2.0) -> dict[int, float]:
    """A realistic stl/blk quantile table where q90 is low (typical case)."""
    return {
        10: 1.0,
        25: 1.0,
        50: 1.0,
        75: 2.0,
        90: q90_val,
    }


def _build_pos_pmf_via_sampling(
    q_table: dict[int, float], stat: str = "stl"
) -> np.ndarray:
    """Replicate the hurdle_pmf positive-distribution build path."""
    lo = 0.5
    hi_buffer = 1.5
    q_max_val = max(
        float(max(lo, min(DOMAIN_MAX[stat] + 0.5, q_table[k])))
        for k in q_table
    )
    hi_dynamic = min(
        max(q_max_val + hi_buffer, lo + 1.0),
        DOMAIN_MAX[stat] + 0.5,
    )
    rng = np.random.default_rng(0)
    samples = _sample_from_quantile_table(q_table, 4_000, rng, lo=0.5, hi=hi_dynamic)
    integers = np.clip(np.rint(samples).astype(int), 1, DOMAIN_MAX[stat])
    pos_counts = np.bincount(integers, minlength=DOMAIN_MAX[stat] + 1)
    pos_pmf = pos_counts.astype(float) / max(pos_counts.sum(), 1)
    pos_pmf = _enforce_monotone_positive_tail(pos_pmf, start_k=2)
    return pos_pmf


# ---------------------------------------------------------------------------
# Tests: _enforce_monotone_positive_tail
# ---------------------------------------------------------------------------

class TestEnforceMonotonePositiveTail:
    def test_already_monotone_unchanged_structure(self):
        """A well-behaved monotone array passes through cleanly."""
        arr = np.array([0.0, 0.5, 0.3, 0.1, 0.05, 0.03, 0.01, 0.005, 0.003, 0.001, 0.001])
        result = _enforce_monotone_positive_tail(arr, start_k=2)
        assert result.sum() == pytest.approx(1.0, abs=1e-6)
        assert np.all(result >= 0)
        # The enforced tail must be non-increasing from k=2 onward.
        for k in range(2, len(result) - 1):
            assert result[k] >= result[k + 1] - 1e-9, (
                f"Non-monotone at k={k}: P({k})={result[k]:.6f} < P({k+1})={result[k+1]:.6f}"
            )

    def test_spike_at_k7_is_removed(self):
        """Classic failure: P(7) >> P(3-5) — must be repaired."""
        arr = np.zeros(11)
        arr[0] = 0.666
        arr[1] = 0.215
        arr[2] = 0.105
        arr[3] = 0.0008
        arr[4] = 0.0001
        arr[5] = 0.00004
        arr[6] = 0.0009
        arr[7] = 0.0033   # spike
        arr[8] = 0.0031
        arr[9] = 0.0021
        arr[10] = 0.0039  # spike at terminal
        arr = arr / arr.sum()

        # Only repair the positive tail (k>=2); k=0 and k=1 are left as-is.
        result = _enforce_monotone_positive_tail(arr, start_k=2)

        assert result.sum() == pytest.approx(1.0, abs=1e-6)
        assert np.all(result >= -1e-9)
        # After repair, tail must be non-increasing from k=2.
        for k in range(2, len(result) - 1):
            assert result[k] >= result[k + 1] - 1e-9, (
                f"Spike not removed at k={k+1}: P({k})={result[k]:.6f}"
                f" < P({k+1})={result[k+1]:.6f}"
            )
        # In particular, P(7) must not exceed P(3).
        assert result[7] <= result[3] + 1e-9, (
            f"P(7)={result[7]:.6f} > P(3)={result[3]:.6f} — spike not removed"
        )

    def test_total_mass_preserved(self):
        """Mass is neither created nor destroyed during repair."""
        rng = np.random.default_rng(42)
        for _ in range(20):
            arr = np.abs(rng.normal(0, 0.1, 11))
            arr = arr / arr.sum()
            result = _enforce_monotone_positive_tail(arr, start_k=2)
            assert result.sum() == pytest.approx(1.0, abs=1e-5)

    def test_no_negative_probabilities(self):
        """Result never contains negative probabilities."""
        arr = np.array([0.0, 0.0, 0.0, 0.0, 0.001, 0.5, 0.3, 0.1, 0.05, 0.02, 0.029])
        arr = arr / arr.sum()
        result = _enforce_monotone_positive_tail(arr, start_k=2)
        assert np.all(result >= -1e-9)


# ---------------------------------------------------------------------------
# Tests: full positive-PMF build path (dynamic hi + monotone repair)
# ---------------------------------------------------------------------------

class TestPositivePMFBuildPath:
    @pytest.mark.parametrize("stat", ["stl", "blk"])
    def test_low_q90_no_spike_after_plausible_region(self, stat: str):
        """
        When q90 ≈ 2, the old code spread mass uniformly to DOMAIN_MAX=10,
        creating P(7) > P(3). The new dynamic-hi + monotone repair must
        prevent this.
        """
        q_table = _make_q_table_with_low_q90(q90_val=2.0)
        pos_pmf = _build_pos_pmf_via_sampling(q_table, stat=stat)

        # Normalise including k=0 (which is zero in pos_pmf).
        assert pos_pmf.sum() == pytest.approx(1.0, abs=1e-5)
        assert np.all(pos_pmf >= -1e-9)

        # After k=2, tail must be non-increasing.
        for k in range(2, len(pos_pmf) - 1):
            assert pos_pmf[k] >= pos_pmf[k + 1] - 1e-9, (
                f"{stat}: pos_pmf[{k}]={pos_pmf[k]:.6f} < pos_pmf[{k+1}]={pos_pmf[k+1]:.6f}"
            )

        # Specifically: P(7 steals) must not exceed P(3 steals).
        assert pos_pmf[7] <= pos_pmf[3] + 1e-9, (
            f"{stat}: P(7)={pos_pmf[7]:.6f} > P(3)={pos_pmf[3]:.6f} — spike exists"
        )

    @pytest.mark.parametrize("stat", ["stl", "blk"])
    def test_dynamic_hi_stays_within_domain(self, stat: str):
        """The dynamic hi must not exceed DOMAIN_MAX + 0.5."""
        q_table = {10: 1.0, 25: 2.0, 50: 3.0, 75: 5.0, 90: 8.0}
        lo = 0.5
        hi_buffer = 1.5
        q_max_val = max(
            float(max(lo, min(DOMAIN_MAX[stat] + 0.5, q_table[k])))
            for k in q_table
        )
        hi_dynamic = min(
            max(q_max_val + hi_buffer, lo + 1.0),
            DOMAIN_MAX[stat] + 0.5,
        )
        assert hi_dynamic <= DOMAIN_MAX[stat] + 0.5 + 1e-9

    @pytest.mark.parametrize("stat", ["stl", "blk"])
    def test_pmf_sums_to_one(self, stat: str):
        """Full PMF (pos_pmf) sums to 1 for multiple q_table inputs."""
        for q90_val in [1.0, 1.5, 2.0, 3.0, 5.0]:
            q_table = _make_q_table_with_low_q90(q90_val=q90_val)
            pos_pmf = _build_pos_pmf_via_sampling(q_table, stat=stat)
            assert pos_pmf.sum() == pytest.approx(1.0, abs=1e-4), (
                f"{stat} q90={q90_val}: sum={pos_pmf.sum():.6f}"
            )

    @pytest.mark.parametrize("stat", ["stl", "blk"])
    def test_no_negative_probs(self, stat: str):
        """All probabilities in the positive PMF are >= 0."""
        q_table = _make_q_table_with_low_q90(q90_val=2.0)
        pos_pmf = _build_pos_pmf_via_sampling(q_table, stat=stat)
        assert np.all(pos_pmf >= -1e-9), (
            f"{stat}: negative probability found: {pos_pmf.min():.8f}"
        )

    def test_stocks_tail_does_not_spike(self):
        """stocks = conv(stl, blk); ensure the result is not spiky in the tail."""
        from nba_props_model.models.sparse_hurdle import stocks_pmf

        stl_q = _make_q_table_with_low_q90(q90_val=2.0)
        blk_q = _make_q_table_with_low_q90(q90_val=2.0)
        p_zero_stl, p_zero_blk = 0.65, 0.72

        stl_pos = _build_pos_pmf_via_sampling(stl_q, stat="stl")
        blk_pos = _build_pos_pmf_via_sampling(blk_q, stat="blk")

        stl_arr = np.zeros(DOMAIN_MAX["stl"] + 1)
        stl_arr[0] = p_zero_stl
        stl_arr[1:] = (1 - p_zero_stl) * stl_pos[1:]
        stl_arr /= stl_arr.sum()

        blk_arr = np.zeros(DOMAIN_MAX["blk"] + 1)
        blk_arr[0] = p_zero_blk
        blk_arr[1:] = (1 - p_zero_blk) * blk_pos[1:]
        blk_arr /= blk_arr.sum()

        stocks = stocks_pmf(stl_arr, blk_arr)
        assert stocks is not None
        assert stocks.sum() == pytest.approx(1.0, abs=1e-5)
        assert np.all(stocks >= -1e-9)

        # After k=3, the stocks tail should not spike.
        SPIKE_REL = 0.25
        SPIKE_ABS = 0.00025
        for k in range(4, len(stocks)):
            p_prev = stocks[k - 1]
            p_curr = stocks[k]
            if p_prev > 0:
                rel = (p_curr - p_prev) / p_prev
                assert not (rel > SPIKE_REL and p_curr > SPIKE_ABS), (
                    f"stocks spike at k={k}: P({k-1})={p_prev:.6f} P({k})={p_curr:.6f}"
                )
