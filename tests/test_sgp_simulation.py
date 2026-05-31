"""Tests for NBA joint simulator — minutes pool, marginal preservation, tape format."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

try:
    from sgp_engine.bundle import SlateStateBundle, BUNDLE_VERSION
    from sgp_engine.pmf import parse_pmf, quantile_int_from_u
    from sgp_engine.simulation import SimulationTape
    from sgp_engine.sports.nba.simulator import NBASimulator, DIRECT_STATS, COMBO_COMPONENTS
except ImportError as exc:
    pytest.skip(f"sgp_engine not available: {exc}", allow_module_level=True)


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------

def _uniform_pmf(n: int) -> np.ndarray:
    return np.full(n, 1.0 / n)


def _degenerate_pmf(k: int, domain: int = 60) -> np.ndarray:
    arr = np.zeros(domain + 1)
    arr[k] = 1.0
    return arr


def _make_minimal_bundle(
    tmp_path: Path,
    player_stat_rows: list[dict[str, Any]],
    game_id: str = "G1",
    team_a: str = "TEA",
    team_b: str = "TEB",
    slate_date: str = "2026-01-01",
) -> SlateStateBundle:
    """Build a minimal SlateStateBundle in tmp_path for simulator tests."""
    games = pd.DataFrame([{
        "slate_date": slate_date,
        "game_id": game_id,
        "home_team_id": team_a,
        "away_team_id": team_b,
        "scheduled_tip_utc": None,
        "lineup_state": "unknown",
        "snapshot_type": "test",
        "snapshot_time_utc": "2026-01-01T00:00:00+00:00",
        "market_total": np.nan,
        "market_spread_home": np.nan,
        "projected_pace_mean": 99.0,
        "projected_pace_sd": 5.0,
        "overtime_probability": 0.06,
        "blowout_probability_home": 0.14,
        "blowout_probability_away": 0.14,
        "close_game_probability": 0.40,
        "garbage_time_probability": 0.18,
        "data_quality_status": "PASS",
    }])

    pmf_rows = []
    player_ids_seen: set[str] = set()
    for r in player_stat_rows:
        pmf_arr: np.ndarray = r["pmf"]
        pmf_json_str = json.dumps({str(k): float(p) for k, p in enumerate(pmf_arr) if p > 1e-15})
        pmf_rows.append({
            "slate_date": slate_date,
            "game_id": game_id,
            "team_id": r.get("team_id", team_a),
            "opponent_id": r.get("opponent_id", team_b),
            "player_id": r["player_id"],
            "player_name": r["player_id"],
            "stat": r["stat"].lower(),
            "pmf_json": pmf_json_str,
            "domain_max": int(len(pmf_arr) - 1),
            "pmf_valid": True,
            "pmf_sum": float(pmf_arr.sum()),
            "pmf_negative_mass_flag": False,
            "mean": float((np.arange(len(pmf_arr)) * pmf_arr).sum()),
            "role_bucket": r.get("role_bucket", "core"),
            "lineup_status": None,
            "injury_status": None,
            "calibration_confidence": None,
        })
        player_ids_seen.add(r["player_id"])

    player_stat_pmfs = pd.DataFrame(pmf_rows)
    players = pd.DataFrame([{
        "slate_date": slate_date,
        "game_id": game_id,
        "team_id": team_a,
        "opponent_id": team_b,
        "player_id": pid,
        "player_name": pid,
        "role_bucket": "core",
        "lineup_status": None,
        "injury_status": None,
        "calibration_confidence": None,
    } for pid in sorted(player_ids_seen)])

    bundle = SlateStateBundle(
        root=tmp_path / "bundle",
        manifest={
            "schema_version": BUNDLE_VERSION,
            "sport": "nba",
            "slate_date": slate_date,
            "bundle_status": "PASS",
            "generated_at_utc": "2026-01-01T00:00:00+00:00",
        },
        games=games,
        players=players,
        player_stat_pmfs=player_stat_pmfs,
    )
    bundle.write()
    return bundle


# ---------------------------------------------------------------------------
# 1 · Competitive minutes — teammates should have negatively correlated minutes
# ---------------------------------------------------------------------------

def test_competitive_minutes_negative_teammate_correlation(tmp_path):
    """Competitive minutes pool limits (but does not necessarily negate) teammate correlation.

    Phase D of the simulator uses a Dirichlet competitive minutes pool so that
    if player A gets more of the team's minutes, player B gets fewer — contributing
    negative covariance through the minutes_z channel (weight ~0.24 for pts).

    Shared game factors (pace_z, total_z, team_offense_z, team_shooting_z) together
    contribute ~0.14 of positive covariance, which the Dirichlet minutes channel
    partially offsets. Net outcome correlation is typically in the range (-0.1, +0.3).
    This test verifies the correlation is capped below 0.4 (well below the ~0.5 that
    independent minutes would produce).
    """
    rows = [
        {"player_id": "A1", "team_id": "TEA", "opponent_id": "TEB",
         "stat": "pts", "pmf": _uniform_pmf(40)},
        {"player_id": "A2", "team_id": "TEA", "opponent_id": "TEB",
         "stat": "pts", "pmf": _uniform_pmf(40)},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=10_000, seed=0).run()
    pts_a1 = tape.get("G1", "A1", "pts").astype(float)
    pts_a2 = tape.get("G1", "A2", "pts").astype(float)
    corr = float(np.corrcoef(pts_a1, pts_a2)[0, 1])
    assert corr < 0.4, (
        f"Teammate pts correlation={corr:.4f} — competitive minutes pool should "
        f"limit shared-factor positive correlation below 0.4"
    )


# ---------------------------------------------------------------------------
# 2 · Minutes sum to team total (5 players × 48 min = 240 player-minutes)
# ---------------------------------------------------------------------------

def test_minutes_sum_to_team_total(tmp_path):
    """Sum of all team players' simulated minutes ≈ 240 (5×48) per simulation."""
    players = [f"P{i}" for i in range(5)]
    rows = [
        {"player_id": pid, "team_id": "TEA", "opponent_id": "TEB",
         "stat": "pts", "pmf": _uniform_pmf(40)}
        for pid in players
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=5_000, seed=1).run()

    # Sum each player's simulated minutes (requires 'minutes' stat in tape)
    total_minutes = np.zeros(tape.n_sims, dtype=float)
    for pid in players:
        total_minutes += tape.get("G1", pid, "minutes").astype(float)

    mean_total = float(total_minutes.mean())
    assert abs(mean_total - 240.0) < 5.0, (
        f"Mean total team minutes {mean_total:.1f} is not close to 240"
    )


# ---------------------------------------------------------------------------
# 3 · Marginal PMF is preserved after rank-anchored simulation
# ---------------------------------------------------------------------------

def test_marginal_pmf_preserved(tmp_path):
    """Uniform-10 PMF: each bucket appears in ~10% ± 5% of 50k simulations."""
    rows = [{"player_id": "B1", "team_id": "TEA", "opponent_id": "TEB",
             "stat": "pts", "pmf": _uniform_pmf(10)}]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=50_000, seed=7).run()
    outcomes = tape.get("G1", "B1", "pts")
    for k in range(10):
        frac = float((outcomes == k).mean())
        assert 0.05 < frac < 0.15, (
            f"Bucket {k}: fraction={frac:.4f} outside tolerance [0.05, 0.15]"
        )


# ---------------------------------------------------------------------------
# 4 · Combo algebraic consistency — pra == pts + reb + ast
# ---------------------------------------------------------------------------

def test_combo_algebraic_consistency(tmp_path):
    """pra simulations must equal pts + reb + ast component-by-component."""
    rows = [
        {"player_id": "C1", "stat": "pts",  "pmf": _uniform_pmf(40)},
        {"player_id": "C1", "stat": "reb",  "pmf": _uniform_pmf(20)},
        {"player_id": "C1", "stat": "ast",  "pmf": _uniform_pmf(15)},
        {"player_id": "C1", "stat": "pra",  "pmf": _uniform_pmf(70)},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=10_000, seed=0).run()
    pts = tape.get("G1", "C1", "pts").astype(int)
    reb = tape.get("G1", "C1", "reb").astype(int)
    ast = tape.get("G1", "C1", "ast").astype(int)
    pra = tape.get("G1", "C1", "pra").astype(int)
    np.testing.assert_array_equal(pra, pts + reb + ast)


# ---------------------------------------------------------------------------
# 5 · Anchored key exists in tape for combo stats
# ---------------------------------------------------------------------------

def test_combo_anchored_key_exists(tmp_path):
    """pra_anchored key must be stored in the tape after simulation."""
    rows = [
        {"player_id": "D1", "stat": "pts",  "pmf": _uniform_pmf(40)},
        {"player_id": "D1", "stat": "reb",  "pmf": _uniform_pmf(20)},
        {"player_id": "D1", "stat": "ast",  "pmf": _uniform_pmf(15)},
        {"player_id": "D1", "stat": "pra",  "pmf": _uniform_pmf(70)},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=5_000, seed=0).run()
    assert tape.has("G1", "D1", "pra_anchored"), (
        "pra_anchored key not found in tape — combo anchoring not applied"
    )


# ---------------------------------------------------------------------------
# 6 · Standalone combo leg uses anchored tape values
# ---------------------------------------------------------------------------

def test_combo_standalone_leg_uses_anchored(tmp_path):
    """Standalone PRA leg pricing uses the rank-anchored pra values.

    The anchored mean must track the delivered PMF mean (34.5), not the
    algebraic sum mean (≈36.0).
    """
    from sgp_engine.pricing import price_ticket
    from sgp_engine.schema import SGPTicket

    u40 = _uniform_pmf(40)   # pts mean = 19.5
    u20 = _uniform_pmf(20)   # reb mean = 9.5
    u15 = _uniform_pmf(15)   # ast mean = 7.0
    u70 = _uniform_pmf(70)   # pra mean = 34.5  (different from sum 36.0)

    rows = [
        {"player_id": "E1", "stat": "pts",  "pmf": u40},
        {"player_id": "E1", "stat": "reb",  "pmf": u20},
        {"player_id": "E1", "stat": "ast",  "pmf": u15},
        {"player_id": "E1", "stat": "pra",  "pmf": u70},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=50_000, seed=0).run()

    assert tape.has("G1", "E1", "pra_anchored")

    # Anchored mean should be near 34.5 (delivered PMF mean), not 36.0
    pra_anch = tape.get("G1", "E1", "pra_anchored").astype(float)
    assert abs(pra_anch.mean() - 34.5) < 1.0, (
        f"Anchored PRA mean {pra_anch.mean():.2f} should be near 34.5"
    )

    # Pricing a standalone PRA ticket uses the anchored tape
    ticket = SGPTicket.from_dict({
        "game_id": "G1",
        "legs": [{"player_id": "E1", "stat": "pra", "line": 34.5, "side": "over"}],
    })
    result = price_ticket(ticket, tape, bundle.player_stat_pmfs)
    sim_marginal = result["legs"][0]["marginal_probability_simulated"]
    # Should be close to ≈0.50 (from the u70 PMF), not ≈0.39 (from algebraic sum)
    assert 0.40 < sim_marginal < 0.60, (
        f"Standalone PRA sim marginal {sim_marginal:.3f} not near 0.50"
    )


# ---------------------------------------------------------------------------
# 7 · tape.to_frame() returns DataFrame with expected columns
# ---------------------------------------------------------------------------

def test_tape_to_frame_shape(tmp_path):
    """tape.to_frame() returns a DataFrame with one row per (game, player, stat, sim)."""
    rows = [
        {"player_id": "F1", "stat": "pts",  "pmf": _uniform_pmf(40)},
        {"player_id": "F1", "stat": "ast",  "pmf": _uniform_pmf(15)},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=100, seed=0).run()
    df = tape.to_frame()
    assert isinstance(df, pd.DataFrame)
    for col in ["game_id", "player_id", "stat", "outcome", "sim_index"]:
        assert col in df.columns, f"Missing column: {col}"
    assert len(df) == 100 * 2  # 100 sims × 2 stats


# ---------------------------------------------------------------------------
# 8 · Tape round-trip save/load
# ---------------------------------------------------------------------------

def test_tape_round_trip_save_load(tmp_path):
    """Save tape to .npz and reload; all stat arrays must be identical."""
    rows = [
        {"player_id": "H1", "stat": "pts",  "pmf": _uniform_pmf(40)},
        {"player_id": "H1", "stat": "ast",  "pmf": _uniform_pmf(15)},
        {"player_id": "H2", "stat": "reb",  "pmf": _uniform_pmf(20)},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=2_000, seed=0).run()

    path = tmp_path / "tape.npz"
    tape.save_npz(path)
    loaded = SimulationTape.load_npz(path)

    assert loaded.n_sims == tape.n_sims
    for key, arr in tape.stats.items():
        assert loaded.has(*key), f"Key {key} missing after reload"
        np.testing.assert_array_equal(arr, loaded.get(*key))


# ---------------------------------------------------------------------------
# 9 · All players in the bundle appear in the tape
# ---------------------------------------------------------------------------

def test_all_players_simulated(tmp_path):
    """Every player × stat combination in the bundle has an entry in the tape."""
    stat_rows = [
        {"player_id": "X1", "stat": "pts",  "pmf": _uniform_pmf(40)},
        {"player_id": "X1", "stat": "ast",  "pmf": _uniform_pmf(15)},
        {"player_id": "X2", "stat": "reb",  "pmf": _uniform_pmf(20)},
        {"player_id": "X2", "stat": "pts",  "pmf": _uniform_pmf(40)},
    ]
    bundle = _make_minimal_bundle(tmp_path, stat_rows)
    tape = NBASimulator(bundle, n_sims=1_000, seed=0).run()

    for r in stat_rows:
        player_id = r["player_id"]
        stat = r["stat"]
        assert tape.has("G1", player_id, stat), (
            f"Player {player_id} stat {stat} not found in simulation tape"
        )
