"""Tests for SGP output schema compliance.

Validates that price grids, market comparison, and key output files
contain required columns and correct values.
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

from sgp_engine.bundle import SlateStateBundle


def _load_run_daily():
    spec_path = Path(__file__).resolve().parent.parent / "scripts" / "run_sgp_engine_daily.py"
    spec = importlib.util.spec_from_file_location("run_sgp_engine_daily", spec_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_minimal_bundle(
    n_players: int = 10,
    minutes_per_player: float = 24.0,
    tmp_path: Path | None = None,
) -> "SlateStateBundle":
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n_players):
        team = "T1" if i < n_players // 2 else "T2"
        pmf_vals = rng.dirichlet(np.ones(41) * 2)
        pmf_json = {str(k): float(v) for k, v in enumerate(pmf_vals)}
        rows.append({
            "game_id": "G1", "player_id": f"P{i}", "team_id": team,
            "stat": "pts", "pmf_json": json.dumps(pmf_json),
            "domain_max": 40, "pmf_valid": True,
            "minutes_mean": minutes_per_player, "minutes_std": 5.0,
            "mean": 20.0, "line": 19.5,
        })
    pmf_df = pd.DataFrame(rows)
    bundle_dir = (tmp_path / "bundle") if tmp_path is not None else Path("/tmp/sgp_test_schema_bundle")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    pmf_df.to_parquet(bundle_dir / "player_stat_pmfs.parquet", index=False)
    pd.DataFrame({"game_id": ["G1"]}).to_parquet(bundle_dir / "games.parquet", index=False)
    pd.DataFrame({"player_id": [f"P{i}" for i in range(n_players)]}).to_parquet(
        bundle_dir / "players.parquet", index=False
    )
    manifest = {"bundle_status": "PASS", "slate_date": "2026-05-30"}
    (bundle_dir / "bundle_manifest.json").write_text(json.dumps(manifest))
    return SlateStateBundle(
        root=str(bundle_dir), manifest=manifest,
        games=pd.DataFrame({"game_id": ["G1"]}),
        players=pd.DataFrame({"player_id": [f"P{i}" for i in range(n_players)]}),
        player_stat_pmfs=pmf_df, market_lines=None,
    )


# ── Standardize price grid ────────────────────────────────────────────────────

class TestStandardizePriceGrid:

    def test_required_canonical_columns(self):
        """_standardize_price_grid must add canonical columns from aliases."""
        run_mod = _load_run_daily()
        df = pd.DataFrame({
            "ticket_id": ["t1", "t2"],
            "n_legs": [2, 2],
            "independent_probability_pmf_marginals": [0.25, 0.16],
            "correlation_factor_vs_pmf_independence": [1.1, 0.9],
            "raw_joint_probability": [0.25, 0.15],
            "calibrated_joint_probability": [0.25, 0.15],
            "fair_decimal_odds": [4.0, 6.0],
            "fair_american_odds": [300, 500],
            "model_corr_factor": [1.1, 0.9],
            "tier": ["MODEL_PRICE", "MODEL_PRICE"],
        })
        out = run_mod._standardize_price_grid(df)

        assert "leg_count" in out.columns
        assert "independent_probability" in out.columns
        assert "correlation_factor" in out.columns
        assert "market_corr_factor_source" in out.columns
        assert "actual_sgp_market_odds_available" in out.columns
        assert out["market_corr_factor_source"].iloc[0] == "independence_placeholder"
        assert out["actual_sgp_market_odds_available"].iloc[0] == False

    def test_no_certified_without_backtest(self, tmp_path):
        """After standardization, no CERTIFIED rows should exist without backtest data."""
        run_mod = _load_run_daily()
        # CERTIFIED tier should not be assigned when market_sup_certified=False.
        df = pd.DataFrame({
            "ticket_id": ["t1"],
            "n_legs": [2],
            "raw_joint_probability": [0.25],
            "calibrated_joint_probability": [0.25],
            "fair_decimal_odds": [4.0],
            "fair_american_odds": [300],
            "tier": ["MODEL_PRICE"],  # not CERTIFIED
        })
        out = run_mod._standardize_price_grid(df)
        assert "CERTIFIED" not in out["tier"].values, \
            "Should not have CERTIFIED tier when market superiority not established"

    def test_market_labels_present(self):
        """Price grid must always have market_corr_factor_source and actual_sgp_market_odds_available."""
        run_mod = _load_run_daily()
        df = pd.DataFrame({
            "ticket_id": ["t1"],
            "n_legs": [2],
            "raw_joint_probability": [0.25],
            "calibrated_joint_probability": [0.25],
            "fair_decimal_odds": [4.0],
            "fair_american_odds": [300],
            "tier": ["MODEL_PRICE"],
        })
        out = run_mod._standardize_price_grid(df)
        assert "market_corr_factor_source" in out.columns
        assert "actual_sgp_market_odds_available" in out.columns
        assert out["market_corr_factor_source"].iloc[0] == "independence_placeholder"
        assert bool(out["actual_sgp_market_odds_available"].iloc[0]) == False


# ── Market corr factor baseline ───────────────────────────────────────────────

class TestMarketCorrFactorBaseline:

    def test_market_corr_source_independence_placeholder(self):
        """When no SGP market odds are available, source must be independence_placeholder."""
        run_mod = _load_run_daily()
        df = pd.DataFrame({
            "n_legs": [2],
            "raw_joint_probability": [0.20],
            "calibrated_joint_probability": [0.20],
            "fair_decimal_odds": [5.0],
            "fair_american_odds": [400],
            "tier": ["MODEL_PRICE"],
        })
        out = run_mod._standardize_price_grid(df)
        assert out["market_corr_factor_source"].iloc[0] == "independence_placeholder"

    def test_market_decimal_odds_null_when_no_market(self):
        """market_decimal_odds should be NaN/null when no actual SGP market data."""
        run_mod = _load_run_daily()
        df = pd.DataFrame({
            "n_legs": [2],
            "raw_joint_probability": [0.20],
            "calibrated_joint_probability": [0.20],
            "fair_decimal_odds": [5.0],
            "fair_american_odds": [400],
            "tier": ["MODEL_PRICE"],
        })
        out = run_mod._standardize_price_grid(df)
        if "market_decimal_odds" in out.columns:
            assert pd.isna(out["market_decimal_odds"].iloc[0]), \
                "market_decimal_odds should be NaN when no actual SGP market data"


# ── Dependency diagnostics ─────────────────────────────────────────────────────

class TestDependencyDiagnosticsSchema:

    def test_full_schema_columns(self, tmp_path):
        """_dependency_diagnostics must produce the full §12 schema columns."""
        run_mod = _load_run_daily()

        from sgp_engine.sports.nba.simulator import NBASimulator
        bundle = _make_minimal_bundle(n_players=6, tmp_path=tmp_path)
        sim = NBASimulator(bundle, n_sims=2_000, seed=10)
        tape = sim.run()

        df = run_mod._dependency_diagnostics(tape, bundle.player_stat_pmfs)

        required = {
            "game_id", "player_a", "stat_a", "team_a", "player_b", "stat_b", "team_b",
            "relationship_type", "simulated_pearson_r", "simulated_phi_corr",
            "joint_lift", "explanation", "player_relation",
        }
        if not df.empty:
            missing = required - set(df.columns)
            assert not missing, f"dependency_diagnostics missing columns: {sorted(missing)}"

    def test_relationship_types_are_valid(self, tmp_path):
        """All relationship_type values must be from the spec-defined set."""
        run_mod = _load_run_daily()
        from sgp_engine.sports.nba.simulator import NBASimulator

        bundle = _make_minimal_bundle(n_players=8, tmp_path=tmp_path)
        sim = NBASimulator(bundle, n_sims=2_000, seed=11)
        tape = sim.run()
        df = run_mod._dependency_diagnostics(tape, bundle.player_stat_pmfs)

        valid_types = {
            "same_player_same_stat_overlap", "same_player_combo_overlap", "same_player_cross_stat",
            "same_team_assist_chain", "same_team_usage_competition", "same_team_rebound_competition",
            "same_team_minutes_substitution", "opponent_pace_environment", "opponent_rebound_pool",
            "opponent_turnover_steal_chain", "game_script_close_game", "game_script_blowout",
            "game_script_overtime", "sparse_defensive_activity",
        }
        if not df.empty:
            unknown = set(df["relationship_type"].unique()) - valid_types
            assert not unknown, f"Unknown relationship types found: {unknown}"


# ── Combo coherence report ────────────────────────────────────────────────────

class TestComboCoherenceSchema:

    def test_full_schema_columns(self, tmp_path):
        """_combo_coherence_report must produce the full schema columns."""
        run_mod = _load_run_daily()
        from sgp_engine.sports.nba.simulator import NBASimulator

        rng = np.random.default_rng(99)
        rows = []
        for stat_name in ["pts", "ast", "pa"]:
            pmf_vals = rng.dirichlet(np.ones(41) * 2)
            pmf_json = {str(k): float(v) for k, v in enumerate(pmf_vals)}
            rows.append({
                "game_id": "G1", "player_id": "P1", "team_id": "T1",
                "stat": stat_name, "pmf_json": json.dumps(pmf_json),
                "domain_max": 40, "pmf_valid": True, "mean": 20.0, "line": 19.5,
                "minutes_mean": 24.0, "minutes_std": 5.0,
            })
        # Add a second player so Dirichlet pool works.
        for stat_name in ["pts", "ast"]:
            pmf_vals = rng.dirichlet(np.ones(41) * 2)
            pmf_json = {str(k): float(v) for k, v in enumerate(pmf_vals)}
            rows.append({
                "game_id": "G1", "player_id": "P2", "team_id": "T1",
                "stat": stat_name, "pmf_json": json.dumps(pmf_json),
                "domain_max": 40, "pmf_valid": True, "mean": 18.0, "line": 17.5,
                "minutes_mean": 22.0, "minutes_std": 4.0,
            })

        pmf_df = pd.DataFrame(rows)
        bundle_dir = tmp_path / "combo_bundle"
        bundle_dir.mkdir()
        pmf_df.to_parquet(bundle_dir / "player_stat_pmfs.parquet", index=False)
        pd.DataFrame({"game_id": ["G1"]}).to_parquet(bundle_dir / "games.parquet", index=False)
        pd.DataFrame({"player_id": ["P1", "P2"]}).to_parquet(bundle_dir / "players.parquet", index=False)
        manifest = {"bundle_status": "PASS", "slate_date": "2026-05-30"}
        (bundle_dir / "bundle_manifest.json").write_text(json.dumps(manifest))
        bundle = SlateStateBundle(
            root=str(bundle_dir), manifest=manifest,
            games=pd.DataFrame({"game_id": ["G1"]}),
            players=pd.DataFrame({"player_id": ["P1", "P2"]}),
            player_stat_pmfs=pmf_df, market_lines=None,
        )

        sim = NBASimulator(bundle, n_sims=3_000, seed=12)
        tape = sim.run()

        df = run_mod._combo_coherence_report(tape, bundle.player_stat_pmfs)

        required = {
            "game_id", "player_id", "combo_stat", "component_formula",
            "component_mean", "delivered_combo_mean", "mean_drift",
            "abs_mean_drift", "status",
        }
        if not df.empty:
            missing = required - set(df.columns)
            assert not missing, f"combo_coherence_report missing columns: {sorted(missing)}"
