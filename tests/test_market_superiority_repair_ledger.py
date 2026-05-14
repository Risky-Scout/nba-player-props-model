"""Tests for market superiority repair ledger."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_market_superiority_repair_ledger as bl


def test_overconfidence_maps_allowed_families():
    allowed, blocked = bl._allowed_blocked_families("model_prob_too_high_or_overconfident_side", [])
    assert "event_neutral_temperature" in allowed
    assert "shrunk_isotonic" in allowed
    assert "hierarchical_logit_shrinkage" in allowed
    assert "pmf_mean_shift" in blocked


def test_mean_too_low_maps_pmf_mean_shift():
    allowed, _ = bl._allowed_blocked_families("mean_too_low", [])
    assert allowed == "pmf_mean_shift"


def test_variance_maps_temperature():
    allowed, _ = bl._allowed_blocked_families("variance_too_narrow", [])
    assert "pmf_variance_temperature" in allowed


def test_passing_but_not_claimable_blocked_calibration(tmp_path: Path, monkeypatch):
    label = "testlabel"
    base = tmp_path / "artifacts" / "model_diagnostics"
    (base / f"event_market_superiority_{label}").mkdir(parents=True)
    sr = pd.DataFrame(
        [
            {
                "stat": "pts",
                "role_bucket": "core",
                "n_rows": 100,
                "n_scored": 100,
                "market_superiority_pass": True,
                "calibration_pass": False,
                "model_better_calibrated": False,
                "model_logloss_avg": 0.5,
                "market_logloss_avg": 0.55,
                "model_brier_avg": 0.2,
                "market_brier_avg": 0.22,
            }
        ]
    )
    sr.to_csv(base / f"event_market_superiority_{label}" / "stat_role_market_superiority.csv", index=False)
    (base / f"market_superiority_failure_modes_{label}").mkdir(parents=True)
    pd.DataFrame(
        [{"stat": "pts", "role_bucket": "core", "dominant_failure_mode": "model_prob_too_high_or_overconfident_side"}]
    ).to_csv(base / f"market_superiority_failure_modes_{label}" / "segment_summary.csv", index=False)
    pd.DataFrame(
        [{"stat": "pts", "role_bucket": "core", "n_rows": 100}]
    ).to_csv(base / f"market_superiority_failure_modes_{label}" / "passing_but_not_claimable.csv", index=False)
    (base / f"market_superiority_math_failure_diag_{label}").mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "stat": "pts",
                "role_bucket": "core",
                "inequality_reason": "bootstrap_ci_not_better",
                "mean_delta_logloss": 0.0,
                "bootstrap_upper95_mean_delta_logloss": 0.01,
            }
        ]
    ).to_csv(base / f"market_superiority_math_failure_diag_{label}" / "math_failure_breakdown.csv", index=False)
    (base / f"market_superiority_math_failure_diag_{label}" / "summary.json").write_text(
        json.dumps({"label": label}), encoding="utf-8"
    )
    (base / f"guarded_event_calibration_{label}").mkdir(parents=True)
    (base / f"guarded_event_calibration_{label}" / "summary.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(bl, "ART", base)
    monkeypatch.setattr(bl, "REPO_ROOT", tmp_path)

    df = bl.build_ledger(label)
    row = df.iloc[0]
    assert "BLOCKED_CALIBRATION" in str(row["claim_status"])
    assert row["bootstrap_ci_pass"] is False or row["bootstrap_ci_pass"] == False


def test_claimable_requires_all_flags(tmp_path: Path, monkeypatch):
    label = "t2"
    base = tmp_path / "artifacts" / "model_diagnostics"
    (base / f"event_market_superiority_{label}").mkdir(parents=True)
    sr = pd.DataFrame(
        [
            {
                "stat": "reb",
                "role_bucket": "bench",
                "n_rows": 200,
                "n_scored": 200,
                "market_superiority_pass": True,
                "calibration_pass": True,
                "model_better_calibrated": True,
                "model_logloss_avg": 0.4,
                "market_logloss_avg": 0.45,
                "model_brier_avg": 0.18,
                "market_brier_avg": 0.2,
            }
        ]
    )
    sr.to_csv(base / f"event_market_superiority_{label}" / "stat_role_market_superiority.csv", index=False)
    (base / f"market_superiority_failure_modes_{label}").mkdir(parents=True)
    pd.DataFrame(
        [{"stat": "reb", "role_bucket": "bench", "dominant_failure_mode": "none"}]
    ).to_csv(base / f"market_superiority_failure_modes_{label}" / "segment_summary.csv", index=False)
    (base / f"market_superiority_math_failure_diag_{label}").mkdir(parents=True)
    (base / f"market_superiority_math_failure_diag_{label}" / "math_failure_breakdown.csv").write_text(
        "stat,role_bucket,inequality_reason\n", encoding="utf-8"
    )
    (base / f"market_superiority_math_failure_diag_{label}" / "summary.json").write_text("{}", encoding="utf-8")
    (base / f"guarded_event_calibration_{label}").mkdir(parents=True)
    (base / f"guarded_event_calibration_{label}" / "summary.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(bl, "ART", base)
    monkeypatch.setattr(bl, "REPO_ROOT", tmp_path)

    df = bl.build_ledger(label)
    assert df.iloc[0]["claim_status"] == "CLAIMABLE"
