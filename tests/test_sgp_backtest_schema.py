"""Tests for SGP backtest row schema.

Validates that build_sgp_backtest_rows produces all required columns
for hierarchical calibration training.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _load_build_backtest():
    spec_path = Path(__file__).resolve().parent.parent / "scripts" / "build_sgp_backtest_rows.py"
    spec = importlib.util.spec_from_file_location("build_sgp_backtest_rows", spec_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_price_result(pid_a="P1", pid_b="P2", stat_a="pts", stat_b="ast",
                       team_a="T1", team_b="T1", line_a=19.5, line_b=5.5):
    """Build a minimal price_ticket result dict."""
    return {
        "raw_joint_probability": 0.20,
        "calibrated_joint_probability": 0.20,
        "independent_probability_pmf_marginals": 0.22,
        "independent_probability": 0.22,
        "correlation_factor_vs_pmf_independence": 0.20 / 0.22,
        "model_corr_factor": 0.20 / 0.22,
        "fair_decimal_odds": 5.0,
        "fair_american_odds": 400,
        "simulation_count": 10000,
        "legs": [
            {"marginal_probability_pmf": 0.5, "player_id": pid_a, "stat": stat_a, "line": line_a},
            {"marginal_probability_pmf": 0.45, "player_id": pid_b, "stat": stat_b, "line": line_b},
        ],
    }


class TestBacktestRowSchema:

    def test_required_columns_present(self, tmp_path):
        """_price_configs must produce all required schema columns."""
        mod = _load_build_backtest()

        from sgp_engine.simulation import SimulationTape
        from sgp_engine.pricing import price_ticket

        # Build minimal tape and pmf_df.
        n = 5000
        rng = np.random.default_rng(42)
        stats = {
            ("G1", "P1", "pts"): (rng.normal(20, 5, n)).clip(0).astype(np.float32),
            ("G1", "P2", "ast"): (rng.normal(5, 2, n)).clip(0).astype(np.float32),
        }
        tape = SimulationTape(n_sims=n, stats=stats, factors={}, metadata={})

        pmf_vals_pts = rng.dirichlet(np.ones(41) * 2)
        pmf_vals_ast = rng.dirichlet(np.ones(15) * 2)
        pmf_df = pd.DataFrame([
            {"game_id": "G1", "player_id": "P1", "stat": "pts", "team_id": "T1",
             "pmf_json": json.dumps({str(k): float(v) for k, v in enumerate(pmf_vals_pts)}),
             "domain_max": 40, "pmf_valid": True, "mean": 20.0, "line": 19.5},
            {"game_id": "G1", "player_id": "P2", "stat": "ast", "team_id": "T2",
             "pmf_json": json.dumps({str(k): float(v) for k, v in enumerate(pmf_vals_ast)}),
             "domain_max": 14, "pmf_valid": True, "mean": 5.0, "line": 4.5},
        ])

        configs = [{
            "game_id": "G1",
            "leg_a": {"player_id": "P1", "stat": "pts", "line": 19.5, "side": "over",
                      "mean": 20.0, "team_id": "T1"},
            "leg_b": {"player_id": "P2", "stat": "ast", "line": 4.5, "side": "over",
                      "mean": 5.0, "team_id": "T2"},
        }]

        rows = mod._price_configs(configs, tape, pmf_df, "2026-05-25", as_of_date="2026-05-25")
        assert len(rows) == 1
        row = rows[0]

        required_cols = [
            "prediction_date", "as_of_date", "game_id", "sgp_id", "ticket_id",
            "leg_count", "n_legs", "legs_json", "relationship_type",
            "stat_mix", "role_mix", "same_player_count", "same_team_count",
            "opponent_count", "contains_combo_overlap", "contains_sparse_stat",
            "contains_alt_line", "line_percentile_bucket", "lineup_status",
            "raw_joint_probability", "calibrated_joint_probability",
            "independent_probability", "correlation_factor",
            "model_corr_factor", "market_sgp_probability", "market_sgp_odds",
            "market_corr_factor", "market_corr_factor_source",
            "corr_factor_delta_vs_market", "actual_hit", "hit_result",
            "model_logloss", "model_brier",
            "logloss_delta_vs_independence", "brier_delta_vs_independence",
        ]
        missing = [c for c in required_cols if c not in row]
        assert not missing, f"Backtest row missing required columns: {missing}"

    def test_actual_hit_null_before_outcome_linking(self, tmp_path):
        """actual_hit must be null before outcome linking."""
        mod = _load_build_backtest()

        from sgp_engine.simulation import SimulationTape
        n = 2000
        rng = np.random.default_rng(99)
        stats = {
            ("G1", "P1", "pts"): rng.normal(20, 5, n).clip(0).astype(np.float32),
            ("G1", "P2", "ast"): rng.normal(5, 2, n).clip(0).astype(np.float32),
        }
        tape = SimulationTape(n_sims=n, stats=stats, factors={}, metadata={})
        pmf_vals = rng.dirichlet(np.ones(41) * 2)
        pmf_df = pd.DataFrame([
            {"game_id": "G1", "player_id": "P1", "stat": "pts", "team_id": "T1",
             "pmf_json": json.dumps({str(k): float(v) for k, v in enumerate(pmf_vals)}),
             "domain_max": 40, "pmf_valid": True, "mean": 20.0, "line": 19.5},
            {"game_id": "G1", "player_id": "P2", "stat": "ast", "team_id": "T2",
             "pmf_json": json.dumps({str(k): float(v) for k, v in enumerate(pmf_vals[:15])}),
             "domain_max": 14, "pmf_valid": True, "mean": 5.0, "line": 4.5},
        ])
        configs = [{
            "game_id": "G1",
            "leg_a": {"player_id": "P1", "stat": "pts", "line": 19.5, "side": "over",
                      "mean": 20.0, "team_id": "T1"},
            "leg_b": {"player_id": "P2", "stat": "ast", "line": 4.5, "side": "over",
                      "mean": 5.0, "team_id": "T2"},
        }]
        rows = mod._price_configs(configs, tape, pmf_df, "2026-05-25")
        assert rows[0]["actual_hit"] is None

    def test_link_outcomes_populates_losses(self):
        """_link_outcomes must compute model_logloss and brier after linking."""
        mod = _load_build_backtest()

        row = {
            "game_id": "G1",
            "leg_1_player_id": "P1", "leg_1_stat": "pts",
            "leg_1_line": 19.5, "leg_1_side": "over",
            "leg_2_player_id": "P2", "leg_2_stat": "ast",
            "leg_2_line": 4.5, "leg_2_side": "over",
            "calibrated_joint_probability": 0.22,
            "independent_probability": 0.25,
            "market_sgp_probability": float("nan"),
            "actual_hit": None, "hit_result": None,
            "model_logloss": float("nan"), "model_brier": float("nan"),
            "independence_logloss": float("nan"), "independence_brier": float("nan"),
            "logloss_delta_vs_independence": float("nan"), "brier_delta_vs_independence": float("nan"),
            "market_logloss": float("nan"), "market_brier": float("nan"),
            "logloss_delta_vs_market": float("nan"), "brier_delta_vs_market": float("nan"),
        }

        # Simulate: both legs hit.
        lookup = {("G1", "P1", "pts"): 25.0, ("G1", "P2", "ast"): 6.0}
        linked = mod._link_outcomes([row], lookup)
        r = linked[0]

        assert r["actual_hit"] == 1
        assert np.isfinite(r["model_logloss"])
        assert np.isfinite(r["model_brier"])
        assert np.isfinite(r["logloss_delta_vs_independence"])
        # Model brier should equal (0.22 - 1.0)^2 = 0.6084
        expected_brier = (0.22 - 1.0) ** 2
        assert abs(r["model_brier"] - expected_brier) < 1e-6

    def test_market_corr_source_placeholder(self):
        """Backtest rows must have market_corr_factor_source=independence_placeholder."""
        mod = _load_build_backtest()
        from sgp_engine.simulation import SimulationTape
        n = 500
        rng = np.random.default_rng(77)
        stats = {
            ("G1", "P1", "pts"): rng.normal(20, 5, n).clip(0).astype(np.float32),
            ("G1", "P2", "ast"): rng.normal(5, 2, n).clip(0).astype(np.float32),
        }
        tape = SimulationTape(n_sims=n, stats=stats, factors={}, metadata={})
        pmf_vals = rng.dirichlet(np.ones(41) * 2)
        pmf_df = pd.DataFrame([
            {"game_id": "G1", "player_id": "P1", "stat": "pts", "team_id": "T1",
             "pmf_json": json.dumps({str(k): float(v) for k, v in enumerate(pmf_vals)}),
             "domain_max": 40, "pmf_valid": True, "mean": 20.0, "line": 19.5},
            {"game_id": "G1", "player_id": "P2", "stat": "ast", "team_id": "T2",
             "pmf_json": json.dumps({str(k): float(v) for k, v in enumerate(pmf_vals[:15])}),
             "domain_max": 14, "pmf_valid": True, "mean": 5.0, "line": 4.5},
        ])
        configs = [{
            "game_id": "G1",
            "leg_a": {"player_id": "P1", "stat": "pts", "line": 19.5, "side": "over",
                      "mean": 20.0, "team_id": "T1"},
            "leg_b": {"player_id": "P2", "stat": "ast", "line": 4.5, "side": "over",
                      "mean": 5.0, "team_id": "T2"},
        }]
        rows = mod._price_configs(configs, tape, pmf_df, "2026-05-25")
        assert rows[0]["market_corr_factor_source"] == "independence_placeholder"
