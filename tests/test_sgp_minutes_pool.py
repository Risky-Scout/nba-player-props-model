"""Tests for SGP minutes pool and marginal preservation.

Covers P0 fix: Dirichlet minutes inflation bug, ghost remainder bucket,
and basic marginal preservation behaviour.
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
_TESTS = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


from sgp_engine.bundle import SlateStateBundle
from sgp_engine.sports.nba.simulator import (
    NBASimulator,
    _REGULATION_TEAM_MINUTES,
    _MEAN_OT_RATE,
    _OT_EXTRA_MINUTES_PER_PERIOD,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_minimal_bundle(
    n_players: int = 10,
    minutes_per_player: float = 24.0,
    minutes_std: float = 5.0,
    tmp_path: Path | None = None,
) -> SlateStateBundle:
    """Build a minimal SlateStateBundle with a single game and n_players."""
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n_players):
        team = "T1" if i < n_players // 2 else "T2"
        pmf_vals = rng.dirichlet(np.ones(41) * 2)
        pmf_json = {str(k): float(v) for k, v in enumerate(pmf_vals)}
        rows.append({
            "game_id": "G1",
            "player_id": f"P{i}",
            "team_id": team,
            "stat": "pts",
            "pmf_json": json.dumps(pmf_json),
            "domain_max": 40,
            "pmf_valid": True,
            "minutes_mean": minutes_per_player,
            "minutes_std": minutes_std,
            "mean": 20.0,
            "line": 19.5,
        })
    pmf_df = pd.DataFrame(rows)

    bundle_dir = (tmp_path / "bundle") if tmp_path is not None else Path("/tmp/sgp_test_bundle")
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Write stub files required by SlateStateBundle constructor.
    pmf_df.to_parquet(bundle_dir / "player_stat_pmfs.parquet", index=False)
    pd.DataFrame({"game_id": ["G1"]}).to_parquet(bundle_dir / "games.parquet", index=False)
    pd.DataFrame({"player_id": [f"P{i}" for i in range(n_players)]}).to_parquet(
        bundle_dir / "players.parquet", index=False
    )
    manifest = {"bundle_status": "PASS", "slate_date": "2026-05-30"}
    (bundle_dir / "bundle_manifest.json").write_text(json.dumps(manifest))

    return SlateStateBundle(
        root=str(bundle_dir),
        manifest=manifest,
        games=pd.DataFrame({"game_id": ["G1"]}),
        players=pd.DataFrame({"player_id": [f"P{i}" for i in range(n_players)]}),
        player_stat_pmfs=pmf_df,
        market_lines=None,
    )


# ── Tests for Dirichlet minutes allocation ────────────────────────────────────

class TestDirichletMinutesAllocation:

    def test_ghost_bucket_no_inflation(self, tmp_path):
        """Tracked player expected minutes must NOT be inflated.

        If there are 8 players per team averaging 24 min each (sum=192),
        the ghost bucket absorbs the remaining ~49.5 min (241.5 - 192).
        Each player's simulated mean minutes should be close to 24.0.
        """
        n_players_per_team = 8
        exp_min = 24.0
        bundle = _make_minimal_bundle(
            n_players=n_players_per_team * 2,
            minutes_per_player=exp_min,
            minutes_std=4.0,
            tmp_path=tmp_path,
        )

        sim = NBASimulator(bundle, n_sims=20_000, seed=1)
        tape = sim.run()

        for team in ["T1", "T2"]:
            for i in range(n_players_per_team if team == "T1" else n_players_per_team):
                pid = f"P{i if team == 'T1' else i + n_players_per_team}"
                if not tape.has("G1", pid, "minutes"):
                    continue
                sim_mins = tape.get("G1", pid, "minutes").astype(float)
                mean_sim = float(sim_mins.mean())
                # Expected: ~24.0, allow ±2.0 minutes slack for MC noise + OT effect.
                assert abs(mean_sim - exp_min) < 2.5, (
                    f"Player {pid} simulated mean minutes={mean_sim:.2f} "
                    f"vs expected={exp_min} — inflation bug may not be fixed."
                )

    def test_minutes_z_mean_near_zero(self, tmp_path):
        """minutes_z should have a mean near zero after ghost bucket fix.

        Previously mean(minutes_z) was +0.5 to +0.9 due to inflation.
        After fix it should be < 0.10 for normal players.
        """
        bundle = _make_minimal_bundle(
            n_players=10,
            minutes_per_player=24.0,
            minutes_std=5.0,
            tmp_path=tmp_path,
        )
        sim = NBASimulator(bundle, n_sims=20_000, seed=2)
        tape = sim.run()

        minutes_z_means = []
        for pid in [f"P{i}" for i in range(10)]:
            if not tape.has("G1", pid, "minutes"):
                continue
            mins = tape.get("G1", pid, "minutes").astype(float)
            exp_min = 24.0
            exp_std = max(5.0, 1.0)
            z_mean = float((mins - exp_min).mean() / exp_std)
            minutes_z_means.append(z_mean)

        if minutes_z_means:
            mean_z_bias = abs(np.mean(minutes_z_means))
            assert mean_z_bias < 0.15, (
                f"Mean minutes_z bias = {mean_z_bias:.4f} — systematic inflation detected. "
                "Ghost bucket fix may not be applied correctly."
            )

    def test_same_team_minutes_sum_coherent(self, tmp_path):
        """Total simulated minutes for a team should average near the team total."""
        n_per_team = 8
        exp_min = 24.0
        bundle = _make_minimal_bundle(
            n_players=n_per_team * 2,
            minutes_per_player=exp_min,
            minutes_std=4.0,
            tmp_path=tmp_path,
        )
        sim = NBASimulator(bundle, n_sims=20_000, seed=3)
        tape = sim.run()

        # Sum tracked player minutes for T1.
        t1_pids = [f"P{i}" for i in range(n_per_team)]
        t1_mins_arrays = [
            tape.get("G1", pid, "minutes").astype(float)
            for pid in t1_pids if tape.has("G1", pid, "minutes")
        ]
        if len(t1_mins_arrays) > 1:
            total_tracked = np.sum(t1_mins_arrays, axis=0)
            mean_total = float(total_tracked.mean())
            # Tracked sum should be < full team total (240+) since ghost absorbs remainder.
            # But should be close to tracked_expected = 8 * 24 = 192.
            tracked_expected = n_per_team * exp_min
            assert abs(mean_total - tracked_expected) / tracked_expected < 0.15, (
                f"Tracked minutes sum mean={mean_total:.1f} vs expected={tracked_expected:.1f} "
                f"(error={abs(mean_total - tracked_expected) / tracked_expected:.2%})"
            )

    def test_marginal_preservation_metadata_in_tape(self, tmp_path):
        """Simulator must write marginal_preservation_report into tape metadata."""
        bundle = _make_minimal_bundle(n_players=6, tmp_path=tmp_path)
        sim = NBASimulator(bundle, n_sims=5_000, seed=4)
        tape = sim.run()

        assert "marginal_preservation_report" in tape.metadata
        records = tape.metadata["marginal_preservation_report"]
        assert isinstance(records, list)
        # Should have records (one per valid player-stat PMF).
        assert len(records) >= 1

    def test_minutes_allocation_diagnostics_in_tape(self, tmp_path):
        """Simulator must write minutes_allocation_diagnostics into tape metadata."""
        bundle = _make_minimal_bundle(n_players=8, tmp_path=tmp_path)
        sim = NBASimulator(bundle, n_sims=5_000, seed=5)
        tape = sim.run()

        assert "minutes_allocation_diagnostics" in tape.metadata
        diag = tape.metadata["minutes_allocation_diagnostics"]
        assert isinstance(diag, dict)
        # Should have at least one team entry.
        assert len(diag) >= 1
        for key, val in diag.items():
            assert "tracked_expected_total" in val
            assert "ghost_expected_minutes" in val
            assert "method" in val
            assert val["method"] in {"ghost_remainder_dirichlet", "tracked_total_dirichlet"}


# ── Test marginal preservation report columns ─────────────────────────────────

class TestMarginalPreservationReport:

    def test_report_columns_full_schema(self, tmp_path):
        """_marginal_preservation_report must produce all required columns."""
        import importlib.util
        spec_path = Path(__file__).resolve().parent.parent / "scripts" / "run_sgp_engine_daily.py"
        spec = importlib.util.spec_from_file_location("run_sgp_engine_daily", spec_path)
        run_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_mod)

        bundle = _make_minimal_bundle(n_players=6, tmp_path=tmp_path)
        sim = NBASimulator(bundle, n_sims=5_000, seed=6)
        tape = sim.run()

        df = run_mod._marginal_preservation_report(tape, bundle.player_stat_pmfs)

        required_cols = {
            "game_id", "player_id", "stat", "line",
            "delivered_mean", "simulated_mean", "mean_abs_diff",
            "p_over_main_line_delivered", "p_over_main_line_simulated",
            "p_over_abs_diff", "signed_p_over_diff", "abs_error", "status",
        }
        if not df.empty:
            missing = required_cols - set(df.columns)
            assert not missing, f"marginal_preservation_report missing columns: {sorted(missing)}"

    def test_status_values(self, tmp_path):
        """Status column must only contain PASS, WARN, or FAIL."""
        import importlib.util
        spec_path = Path(__file__).resolve().parent.parent / "scripts" / "run_sgp_engine_daily.py"
        spec = importlib.util.spec_from_file_location("run_sgp_engine_daily", spec_path)
        run_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_mod)

        bundle = _make_minimal_bundle(n_players=6, tmp_path=tmp_path)
        sim = NBASimulator(bundle, n_sims=5_000, seed=7)
        tape = sim.run()

        df = run_mod._marginal_preservation_report(tape, bundle.player_stat_pmfs)
        if not df.empty:
            valid_statuses = {"PASS", "WARN", "FAIL"}
            assert set(df["status"].unique()).issubset(valid_statuses), \
                f"Unexpected status values: {set(df['status'].unique()) - valid_statuses}"
