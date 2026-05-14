"""Unit tests for post-repair failure ledger mapping."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load_ledger():
    p = REPO / "scripts" / "build_post_repair_failure_ledger.py"
    spec = importlib.util.spec_from_file_location("build_post_repair_failure_ledger", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_next_family_mapping():
    m = _load_ledger()
    assert m._next_family("active_prob_not_used") == "integration_fix"
    assert m._next_family("variance_too_narrow") == "pmf_variance_temperature"
    assert m._next_family("bootstrap_ci_not_better") == "needs_more_data_or_more_stable_edges"


def test_primary_blocker_insufficient_sample():
    m = _load_ledger()
    pb = m._primary_blocker(
        n_scored=50,
        n_joined=500,
        failure_reason="ok",
        cal_pass=True,
        ms_pass=False,
        boot_fail=False,
        mean_fail=False,
        delta_ll=-0.1,
        delta_br=-0.1,
        dom="",
    )
    assert pb == "insufficient_sample"


def test_primary_blocker_low_coverage():
    m = _load_ledger()
    pb = m._primary_blocker(
        n_scored=200,
        n_joined=50,
        failure_reason="ok",
        cal_pass=True,
        ms_pass=False,
        boot_fail=False,
        mean_fail=False,
        delta_ll=None,
        delta_br=None,
        dom="",
    )
    assert pb == "low_market_coverage"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
