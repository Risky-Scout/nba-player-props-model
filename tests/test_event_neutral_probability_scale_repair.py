"""Tests for event-neutral probability scale repair."""
from __future__ import annotations

import numpy as np
import pytest

from nba_props_model.calibration.event_neutral_probability_scale import (
    FORBIDDEN_TRAINING_FEATURE_NAMES,
    apply_logit_ab,
    apply_manifest_to_probability,
    apply_shrink_to_half,
    chronological_date_folds,
)
def test_probs_bounded():
    p = np.array([0.01, 0.5, 0.99])
    o = apply_logit_ab(p, 0.7, -0.05)
    assert np.all(o >= 1e-12) and np.all(o <= 1.0 - 1e-12)


def test_overconfident_moves_toward_half():
    p = np.array([0.95])
    o = apply_shrink_to_half(p, 0.6)
    assert float(o[0]) < float(p[0])


def test_forbidden_training_feature_names_nonempty():
    assert len(FORBIDDEN_TRAINING_FEATURE_NAMES) >= 3


def test_rollback_worse_logloss_detected():
    y = np.array([0.0, 1.0, 0.0, 1.0] * 20)
    p = np.clip(0.2 + 0.6 * y, 0.05, 0.95)
    dates = np.array([f"2024-01-{i+1:02d}" for i in range(len(y))])
    folds = chronological_date_folds(dates, n_folds=3)
    assert len(folds) >= 1


def test_manifest_fallback_raw():
    man = {"version": "1", "segments": {}}
    p, scope, method, ok = apply_manifest_to_probability(0.7, stat="pts", role_bucket="core", manifest=man)
    assert ok is False
    assert abs(p - 0.7) < 1e-9
    assert scope is None


def test_manifest_applies_logit():
    man = {
        "segments": {
            "pts|core": {
                "accepted": True,
                "selected_method": "logit_ab",
                "a": 0.5,
                "b": 0.0,
            }
        }
    }
    p, scope, method, ok = apply_manifest_to_probability(0.9, stat="pts", role_bucket="core", manifest=man)
    assert ok is True
    assert method == "logit_ab"
    assert p < 0.9


def test_date_folds_no_overlap():
    dates = np.array([f"2024-01-{i:02d}" for i in range(1, 10)])
    folds = chronological_date_folds(dates, n_folds=3)
    for tr, va in folds:
        assert len(set(tr.tolist()) & set(va.tolist())) == 0
