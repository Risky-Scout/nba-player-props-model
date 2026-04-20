"""Tests for the sparse-data shrinkage fallback in residual centering.

Previously a stat with < 30 graded rows emitted a WARNING and used the raw
stat median. The fix shrinks toward a family/global median via
delta = w * stat_median + (1-w) * global_median, w = n / (n + k).
No WARNING should fire on sparse data; abstention is normal behavior.
"""
from __future__ import annotations

import logging

import pytest

from nba_props_model.calibration import residual_centering as rc


def _rows(stat: str, n: int, residual: float = 0.5, q50: float = 1.0):
    return [{"stat": stat, "actual": q50 + residual, "q50": q50} for _ in range(n)]


def test_sparse_stat_uses_shrinkage_fallback(monkeypatch, tmp_path, caplog):
    graded = _rows("fg3m", 5, residual=2.0, q50=1.0) + _rows("pts", 200, residual=0.1, q50=20.0)

    centerer = rc.ResidualCenterer()
    monkeypatch.setattr(centerer, "_load_graded", lambda _dir: graded)
    caplog.set_level(logging.INFO, logger=rc.logger.name)

    centerer.train(graded_dir=tmp_path)

    assert "fg3m" in centerer.fallback, "sparse fallback must populate self.fallback"
    assert centerer.meta["fg3m"]["model_type"] == "shrinkage_fallback"
    # The shrinkage mix must sit strictly between stat_median and global_median.
    stat_med = centerer.meta["fg3m"]["stat_median"]
    glob_med = centerer.meta["fg3m"]["global_median"]
    delta = centerer.fallback["fg3m"]
    lo, hi = sorted((stat_med, glob_med))
    assert lo - 1e-9 <= delta <= hi + 1e-9, (
        f"shrinkage result {delta} outside [{lo}, {hi}]"
    )

    # No WARNING should have fired for the sparse stat.
    warn_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
    offenders = [r.getMessage() for r in warn_records if "fg3m" in r.getMessage()]
    assert not offenders, f"unexpected WARNING: {offenders}"


def test_shrinkage_weight_grows_with_n():
    rc_ = rc.ResidualCenterer()
    small = _rows("fg3m", 1, residual=0.0, q50=1.0) + _rows("pts", 100, residual=0.5, q50=20.0)
    med = _rows("fg3m", 25, residual=0.0, q50=1.0) + _rows("pts", 100, residual=0.5, q50=20.0)

    import types
    rc_._load_graded = types.MethodType(lambda self, _d: small, rc_)
    rc_.train(graded_dir=".")
    w_small = rc_.meta["fg3m"]["shrinkage_w"]

    rc2 = rc.ResidualCenterer()
    rc2._load_graded = types.MethodType(lambda self, _d: med, rc2)
    rc2.train(graded_dir=".")
    w_med = rc2.meta["fg3m"]["shrinkage_w"]

    assert w_med > w_small, f"w must grow with n: got {w_small} and {w_med}"
