"""Unit tests for repair active scoring contract helpers."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]


def _load_verify():
    p = REPO / "scripts" / "verify_repair_active_scoring_contract.py"
    spec = importlib.util.spec_from_file_location("verify_repair_active_scoring_contract", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_compare_strict_matches_stored_row_metrics():
    v = _load_verify()
    combo = pd.DataFrame(
        {
            "stat": ["pts", "pts"],
            "role_bucket": ["starter", "starter"],
            "hit_result": [1.0, 0.0],
            "model_prob_over_raw": [0.4, 0.4],
            "model_prob_over_active": [0.55, 0.45],
            "model_event_logloss": [np.nan, np.nan],
            "market_event_logloss": [0.5, 0.5],
            "model_brier": [np.nan, np.nan],
            "market_brier": [0.25, 0.25],
        }
    )
    ll0 = v._ll(0.55, 1.0)
    ll1 = v._ll(0.45, 0.0)
    br0 = v._brier(0.55, 1.0)
    br1 = v._brier(0.45, 0.0)
    combo["model_event_logloss"] = [ll0, ll1]
    combo["model_brier"] = [br0, br1]

    sr = pd.DataFrame(
        {
            "stat": ["pts"],
            "role_bucket": ["starter"],
            "model_logloss_avg": [float(np.mean([ll0, ll1]))],
            "model_brier_avg": [float(np.mean([br0, br1]))],
        }
    )
    mm, rt = v.compare_strict_report_to_active_probs(combo, sr)
    assert mm == []
    assert rt == []


def test_raw_trap_detected_when_csv_aligns_raw_not_active():
    v = _load_verify()
    combo = pd.DataFrame(
        {
            "stat": ["pts", "pts"],
            "role_bucket": ["starter", "starter"],
            "hit_result": [1.0, 0.0],
            "model_prob_over_raw": [0.5, 0.5],
            "model_prob_over_active": [0.7, 0.3],
            "market_event_logloss": [0.5, 0.5],
            "market_brier": [0.25, 0.25],
        }
    )
    ll_act0 = v._ll(0.7, 1.0)
    ll_act1 = v._ll(0.3, 0.0)
    ll_raw0 = v._ll(0.5, 1.0)
    ll_raw1 = v._ll(0.5, 0.0)
    combo["model_event_logloss"] = [ll_raw0, ll_raw1]
    combo["model_brier"] = [v._brier(0.5, 1.0), v._brier(0.5, 0.0)]

    csv_ll = float(np.mean([ll_raw0, ll_raw1]))
    sr = pd.DataFrame(
        {
            "stat": ["pts"],
            "role_bucket": ["starter"],
            "model_logloss_avg": [csv_ll],
            "model_brier_avg": [0.25],
        }
    )
    _, rt = v.compare_strict_report_to_active_probs(combo, sr)
    assert len(rt) == 1


def test_build_script_has_manifest_flags():
    v = _load_verify()
    ok, msg = v._build_script_has_flags()
    assert ok, msg


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
