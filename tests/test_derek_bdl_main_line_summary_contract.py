import importlib.util
from pathlib import Path

import pandas as pd


def _load_mod():
    path = Path("scripts/build_derek_forward_feed.py")
    spec = importlib.util.spec_from_file_location("build_derek_forward_feed_for_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_derek_unique_summary_columns_constant():
    mod = _load_mod()
    assert mod.DEREK_UNIQUE_SUMMARY_COLS == [
        "player_name",
        "projected_minutes",
        "stat",
        "pmf_mean",
        "market_line",
        "p_over",
    ]


def test_direct_pmf_math_for_summary_fields():
    mod = _load_mod()
    pmf = {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}
    arr = mod._pmf_array_from_jsonish(pmf)
    assert abs(mod._pmf_direct_mean(arr) - 2.0) < 1e-12
    assert abs(mod._pmf_direct_p_over(arr, 1.5) - 0.7) < 1e-12


def test_summary_contract_no_quarantined_fields_in_constant():
    mod = _load_mod()
    banned = {
        "model_projected_mean",
        "model_probability_over_market_line",
        "model_prob_over_raw",
        "model_prob_over_active",
        "model_p_over",
    }
    assert not banned.intersection(set(mod.DEREK_UNIQUE_SUMMARY_COLS))
