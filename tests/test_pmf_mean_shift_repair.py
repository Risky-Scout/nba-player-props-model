"""Unit tests for PMF mean-shift repair library."""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from nba_props_model.calibration.event_neutral_probability_scale import chronological_date_folds
from nba_props_model.calibration.pmf_mean_shift_repair import (
    apply_mean_shift_manifest_to_pmf,
    assert_fit_columns_allowed,
    eval_candidate_on_rows,
    is_valid_pmf,
    normalize_pmf,
    passes_rollback,
    pmf_mean,
    scale_pmf_mean_multiplicative,
    shift_pmf_additive,
)


def test_normalize_sums_to_one():
    p = normalize_pmf({0: 0.3, 1: 0.7})
    assert abs(sum(p.values()) - 1.0) < 1e-9
    assert is_valid_pmf(p)


def test_additive_shift_increases_mean_for_positive_delta():
    raw = normalize_pmf({0: 0.5, 1: 0.3, 2: 0.2})
    m0 = pmf_mean(raw)
    rep = shift_pmf_additive(raw, 0.5)
    assert pmf_mean(rep) > m0 + 1e-6


def test_multiplicative_scale_increases_mean():
    raw = normalize_pmf({0: 0.4, 1: 0.35, 2: 0.25})
    m0 = pmf_mean(raw)
    rep = scale_pmf_mean_multiplicative(raw, 1.08)
    assert rep is not None
    assert pmf_mean(rep) > m0 + 1e-6


def test_rollback_rejects_worse_nll():
    raw_m = {
        "mean_bias": -2.0,
        "mean_abs_error": 2.0,
        "mean_nll": 0.5,
        "mean_rps": 0.2,
        "mean_event_ll": 0.6,
        "mean_event_brier": 0.25,
    }
    bad = {
        **raw_m,
        "mean_bias": -0.5,
        "mean_abs_error": 0.6,
        "mean_nll": 0.52,
    }
    ok, reason = passes_rollback(raw_m, bad, require_bias_improve=True)
    assert not ok
    assert "nll" in reason


def test_date_folds_no_overlap():
    dates = np.array([f"2024-01-{i:02d}" for i in range(1, 20)])
    folds = chronological_date_folds(dates, n_folds=3)
    assert len(folds) >= 1
    for tr, va in folds:
        assert not set(tr.tolist()) & set(va.tolist())


def test_forbidden_training_column_raises():
    with pytest.raises(SystemExit):
        assert_fit_columns_allowed(["stat", "game_date", "no_vig"])


def test_apply_additive_manifest():
    raw = normalize_pmf({0: 0.5, 1: 0.3, 2: 0.2})
    man = {
        "segments": {
            "pts|core": {
                "accepted": True,
                "selected_method": "additive",
                "delta": 0.5,
            }
        }
    }
    out, scope, method, applied, rr = apply_mean_shift_manifest_to_pmf(
        raw, stat="pts", role_bucket="core", manifest=man
    )
    assert applied
    assert scope == "pts|core"
    assert method == "additive"
    assert rr is None
    assert is_valid_pmf(out)
    assert pmf_mean(out) > pmf_mean(raw) + 1e-6


def test_apply_unknown_method_rolls_back():
    raw = normalize_pmf({0: 0.5, 1: 0.5})
    man = {
        "segments": {
            "pts|core": {"accepted": True, "selected_method": "not_a_method", "delta": 0.5}
        }
    }
    out, _k, _m, applied, rr = apply_mean_shift_manifest_to_pmf(
        raw, stat="pts", role_bucket="core", manifest=man
    )
    assert not applied
    assert rr == "unknown_method"
    assert pmf_mean(out) == pytest.approx(pmf_mean(raw))


def test_eval_candidate_runs_on_rows():
    pmfs = [normalize_pmf({0: 0.5, 1: 0.3, 2: 0.2})] * 5
    acts = [1, 0, 2, 1, 0]
    lines = [0.5] * 5
    overs = [1, 0, 1, 0, 1]
    m = eval_candidate_on_rows(
        pmfs, acts, lines, overs, method="additive", delta=0.25, gamma=None, alpha=None, d_stat=None
    )
    assert m is not None
    assert "mean_bias" in m


def test_no_market_in_eval_signature():
    """eval_candidate_on_rows has no market-probability parameters."""
    sig = inspect.signature(eval_candidate_on_rows)
    names = set(sig.parameters)
    for bad in ("market_prob", "no_vig", "book_prob"):
        assert bad not in names


def test_rollback_blocks_bias_not_improved():
    raw_m = {
        "mean_bias": -2.0,
        "mean_abs_error": 2.0,
        "mean_nll": 1.0,
        "mean_rps": 0.3,
        "mean_event_ll": 0.7,
        "mean_event_brier": 0.25,
    }
    worse_bias = {**raw_m, "mean_bias": -2.5, "mean_nll": 0.9}
    ok, reason = passes_rollback(raw_m, worse_bias, require_bias_improve=True)
    assert not ok
    assert "bias" in reason
