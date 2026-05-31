"""Comprehensive SGP Engine test suite.

Covers: PMF utilities, schema/odds, SimulationTape round-trip,
NBASimulator marginal anchoring, combo algebraic consistency,
pricing pipeline, calibration, and bundle write/load round-trip.

All tests that need filesystem access use pytest's tmp_path fixture
and operate entirely in temporary directories — no delivery files
are read or modified.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sgp_engine.bundle import SlateStateBundle, BUNDLE_VERSION
from sgp_engine.calibration import (
    JointProbabilityCalibrator,
    fit_global_joint_calibrator,
    reliability_table,
    expected_calibration_error,
)
from sgp_engine.pmf import (
    cdf_from_pmf,
    event_probability,
    parse_pmf,
    pmf_to_json,
    quantile_int_from_u,
    rank_to_uniform,
    validate_pmf,
)
from sgp_engine.pricing import price_ticket, price_tickets_to_frame
from sgp_engine.schema import (
    SGPLeg,
    SGPTicket,
    american_to_decimal,
    calculate_ev,
    decimal_to_american,
    prob_to_american,
    prob_to_decimal,
)
from sgp_engine.simulation import SimulationTape
from sgp_engine.sports.nba.simulator import NBASimulator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uniform_pmf(n: int) -> np.ndarray:
    return np.full(n, 1.0 / n)


def _degenerate_pmf(k: int, domain: int = 60) -> np.ndarray:
    """PMF with all mass at outcome k."""
    arr = np.zeros(domain + 1)
    arr[k] = 1.0
    return arr


def _make_minimal_bundle(
    tmp_path: Path,
    player_stat_rows: list[dict],
    game_id: str = "G1",
    team_a: str = "TEA",
    team_b: str = "TEB",
    slate_date: str = "2026-01-01",
) -> SlateStateBundle:
    """Build a minimal SlateStateBundle inside tmp_path for testing."""
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
            "minutes_mean": r.get("minutes_mean", 28.0),
            "minutes_std": r.get("minutes_std", 6.0),
            "p_inactive_used": r.get("p_inactive_used", 0.0),
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
# 1 · PMF utilities
# ---------------------------------------------------------------------------

class TestParsePMF:
    def test_dict_input(self):
        pmf = parse_pmf({"0": 0.2, "1": 0.5, "2": 0.3})
        assert abs(pmf.sum() - 1.0) < 1e-9
        assert abs(pmf[1] - 0.5) < 1e-9

    def test_list_input(self):
        pmf = parse_pmf([0.1, 0.4, 0.3, 0.2])
        assert len(pmf) == 4
        assert abs(pmf.sum() - 1.0) < 1e-9

    def test_json_string_input(self):
        pmf = parse_pmf('{"0": 0.4, "1": 0.6}')
        assert abs(pmf[0] - 0.4) < 1e-9
        assert abs(pmf[1] - 0.6) < 1e-9

    def test_normalizes_unnormalized(self):
        pmf = parse_pmf([2.0, 3.0, 5.0])
        assert abs(pmf.sum() - 1.0) < 1e-9
        assert abs(pmf[2] - 0.5) < 1e-9

    def test_rejects_empty(self):
        with pytest.raises((ValueError, Exception)):
            parse_pmf([])

    def test_rejects_zero_mass(self):
        with pytest.raises(ValueError, match="no positive probability"):
            parse_pmf([0.0, 0.0, 0.0])

    def test_skips_negative_keys(self):
        pmf = parse_pmf({"-1": 0.5, "0": 0.3, "1": 0.7})
        assert len(pmf) == 2

    def test_domain_max_extends_array(self):
        pmf = parse_pmf({"0": 0.5, "1": 0.5}, domain_max=5)
        assert len(pmf) == 6

    def test_nan_values_treated_as_zero(self):
        pmf = parse_pmf([float("nan"), 0.5, 0.5])
        assert abs(pmf[0]) < 1e-9
        assert abs(pmf.sum() - 1.0) < 1e-9


class TestEventProbability:
    def test_over(self):
        pmf = parse_pmf({"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4})
        assert abs(event_probability(pmf, 1.5, "over") - 0.7) < 1e-9

    def test_under(self):
        pmf = parse_pmf({"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4})
        assert abs(event_probability(pmf, 1.5, "under") - 0.3) < 1e-9

    def test_ge(self):
        pmf = parse_pmf({"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25})
        assert abs(event_probability(pmf, 2.0, ">=") - 0.5) < 1e-9

    def test_le(self):
        pmf = parse_pmf({"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25})
        assert abs(event_probability(pmf, 1.0, "<=") - 0.5) < 1e-9

    def test_integer_line_push_excluded(self):
        pmf = parse_pmf({"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25})
        over_prob = event_probability(pmf, 2.0, "over")
        under_prob = event_probability(pmf, 2.0, "under")
        assert abs(over_prob - 0.25) < 1e-9
        assert abs(under_prob - 0.50) < 1e-9

    def test_unknown_side_raises(self):
        pmf = _uniform_pmf(5)
        with pytest.raises(ValueError):
            event_probability(pmf, 2.0, "sideways")


class TestValidatePMF:
    def test_valid_pmf(self):
        r = validate_pmf(_uniform_pmf(10))
        assert r["valid"] is True
        assert abs(r["sum"] - 1.0) < 1e-6

    def test_invalid_pmf_sum(self):
        arr = np.array([0.3, 0.3, 0.3])
        r = validate_pmf(arr)
        assert r["valid"] is False


def test_pmf_to_json_round_trips():
    pmf = _uniform_pmf(5)
    s = pmf_to_json(pmf)
    recovered = parse_pmf(json.loads(s))
    assert abs(recovered.sum() - 1.0) < 1e-9
    assert len(recovered) == 5


def test_cdf_from_pmf_monotone():
    pmf = parse_pmf([0.1, 0.2, 0.3, 0.4])
    cdf = cdf_from_pmf(pmf)
    assert len(cdf) == 4
    assert cdf[-1] == pytest.approx(1.0, abs=1e-9)
    assert all(cdf[i] <= cdf[i + 1] for i in range(len(cdf) - 1))


def test_quantile_int_from_u_degenerate():
    pmf = _degenerate_pmf(7, domain=10)
    u = np.linspace(0.01, 0.99, 100)
    outcomes = quantile_int_from_u(pmf, u)
    assert (outcomes == 7).all()


def test_quantile_int_from_u_uniform_coverage():
    pmf = _uniform_pmf(10)
    rng = np.random.default_rng(0)
    u = rng.uniform(0, 1, size=100_000)
    outcomes = quantile_int_from_u(pmf, u)
    for k in range(10):
        frac = float((outcomes == k).mean())
        assert 0.08 < frac < 0.12, f"k={k}: frac={frac:.4f}"


def test_rank_to_uniform_is_approximately_uniform():
    rng = np.random.default_rng(0)
    x = rng.normal(size=10_000)
    u = rank_to_uniform(x)
    assert abs(u.mean() - 0.5) < 0.01
    assert u.min() > 0
    assert u.max() < 1


# ---------------------------------------------------------------------------
# 2 · Schema + odds conversions
# ---------------------------------------------------------------------------

class TestSGPLeg:
    def test_from_dict_basic(self):
        leg = SGPLeg.from_dict({"player_id": "P1", "stat": "PTS", "line": 24.5, "side": "over", "game_id": "G1"})
        assert leg.player_id == "P1"
        assert leg.stat == "pts"
        assert leg.side == "over"

    def test_from_dict_camel_case_player_id(self):
        leg = SGPLeg.from_dict({"playerId": "P2", "stat": "reb", "line": 6.5, "side": "under"})
        assert leg.player_id == "P2"

    def test_from_dict_invalid_side_raises(self):
        with pytest.raises(ValueError, match="Invalid SGP leg side"):
            SGPLeg.from_dict({"player_id": "P1", "stat": "pts", "line": 10, "side": "push"})


class TestSGPTicket:
    def test_from_dict_explicit_game_id(self):
        t = SGPTicket.from_dict({
            "game_id": "G1",
            "legs": [{"player_id": "P1", "stat": "pts", "line": 20, "side": "over"}],
        })
        assert t.game_id == "G1"

    def test_from_dict_infers_game_id_from_legs(self):
        t = SGPTicket.from_dict({
            "legs": [
                {"player_id": "P1", "stat": "pts", "line": 20, "side": "over", "game_id": "G5"},
                {"player_id": "P2", "stat": "ast", "line": 5, "side": "over", "game_id": "G5"},
            ],
        })
        assert t.game_id == "G5"

    def test_asdict_round_trip(self):
        t = SGPTicket.from_dict({
            "game_id": "G1",
            "ticket_id": "T1",
            "legs": [{"player_id": "P1", "stat": "pts", "line": 20, "side": "over"}],
        })
        d = t.asdict()
        assert d["ticket_id"] == "T1"
        assert len(d["legs"]) == 1


class TestOddsConversions:
    def test_american_to_decimal_positive(self):
        assert abs(american_to_decimal(100) - 2.0) < 1e-9

    def test_american_to_decimal_negative(self):
        assert abs(american_to_decimal(-110) - 1.9091) < 1e-3

    def test_decimal_to_american_positive(self):
        assert decimal_to_american(3.0) == 200

    def test_decimal_to_american_negative(self):
        assert decimal_to_american(1.5) == -200

    def test_prob_to_decimal_and_back(self):
        p = 0.4
        d = prob_to_decimal(p)
        assert abs(d - 2.5) < 1e-9

    def test_prob_to_american_favourite(self):
        assert prob_to_american(0.6) < 0

    def test_prob_to_american_underdog(self):
        assert prob_to_american(0.4) > 0

    def test_calculate_ev_positive(self):
        ev = calculate_ev(0.5, 2.5)
        assert abs(ev - 0.25) < 1e-9

    def test_calculate_ev_zero(self):
        assert abs(calculate_ev(0.5, 2.0)) < 1e-9


# ---------------------------------------------------------------------------
# 3 · SimulationTape round-trip
# ---------------------------------------------------------------------------

def _make_tape(n: int = 1000) -> SimulationTape:
    rng = np.random.default_rng(0)
    stats = {
        ("G", "P1", "pts"): rng.integers(0, 40, size=n).astype(np.int16),
        ("G", "P1", "ast"): rng.integers(0, 15, size=n).astype(np.int16),
        ("G", "P2", "reb"): rng.integers(0, 20, size=n).astype(np.int16),
    }
    return SimulationTape(n_sims=n, stats=stats, factors={"pace_z": rng.normal(size=n).astype(np.float32)}, metadata={"test": True})


def test_simulation_tape_round_trip(tmp_path):
    tape = _make_tape(2000)
    path = tmp_path / "tape.npz"
    tape.save_npz(path)
    loaded = SimulationTape.load_npz(path)
    assert loaded.n_sims == tape.n_sims
    for key, arr in tape.stats.items():
        assert loaded.has(*key)
        np.testing.assert_array_equal(arr, loaded.get(*key))


def test_simulation_tape_get_missing_raises():
    tape = _make_tape()
    with pytest.raises(KeyError):
        tape.get("GAME_X", "NO_PLAYER", "pts")


def test_simulation_tape_has_false():
    tape = _make_tape()
    assert tape.has("G", "P1", "pts") is True
    assert tape.has("G", "P1", "tov") is False


# ---------------------------------------------------------------------------
# 4 · NBASimulator — marginal anchoring and combo consistency
# ---------------------------------------------------------------------------

def test_nba_simulator_degenerate_pmf_anchoring(tmp_path):
    """Degenerate PMF → every simulated outcome equals the modal value."""
    TARGET = 22
    rows = [
        {"player_id": "A1", "team_id": "TEA", "opponent_id": "TEB", "stat": "pts",
         "pmf": _degenerate_pmf(TARGET, domain=60)},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=5_000, seed=42).run()
    outcomes = tape.get("G1", "A1", "pts")
    assert (outcomes == TARGET).all(), f"Expected all {TARGET}, got {np.unique(outcomes)}"


def test_nba_simulator_uniform_pmf_marginal(tmp_path):
    """Uniform PMF → simulated distribution is approximately uniform."""
    N = 10
    rows = [
        {"player_id": "B1", "team_id": "TEA", "opponent_id": "TEB", "stat": "ast",
         "pmf": _uniform_pmf(N)},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=50_000, seed=7).run()
    outcomes = tape.get("G1", "B1", "ast")
    for k in range(N):
        frac = float((outcomes == k).mean())
        assert 0.07 < frac < 0.13, f"bucket {k}: fraction={frac:.4f} outside [0.07, 0.13]"


def test_nba_simulator_combo_algebraic_consistency(tmp_path):
    """Simulated pra == pts + reb + ast component-by-component."""
    pts_pmf = _uniform_pmf(40)
    reb_pmf = _uniform_pmf(20)
    ast_pmf = _uniform_pmf(15)
    pra_pmf = _uniform_pmf(70)
    rows = [
        {"player_id": "C1", "team_id": "TEA", "opponent_id": "TEB", "stat": "pts", "pmf": pts_pmf},
        {"player_id": "C1", "team_id": "TEA", "opponent_id": "TEB", "stat": "reb", "pmf": reb_pmf},
        {"player_id": "C1", "team_id": "TEA", "opponent_id": "TEB", "stat": "ast", "pmf": ast_pmf},
        {"player_id": "C1", "team_id": "TEA", "opponent_id": "TEB", "stat": "pra", "pmf": pra_pmf},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=10_000, seed=0).run()
    pts = tape.get("G1", "C1", "pts").astype(int)
    reb = tape.get("G1", "C1", "reb").astype(int)
    ast = tape.get("G1", "C1", "ast").astype(int)
    pra = tape.get("G1", "C1", "pra").astype(int)
    np.testing.assert_array_equal(pra, pts + reb + ast)


def test_nba_simulator_pa_combo_consistency(tmp_path):
    """Simulated pa == pts + ast."""
    rows = [
        {"player_id": "D1", "team_id": "TEA", "opponent_id": "TEB", "stat": "pts", "pmf": _uniform_pmf(40)},
        {"player_id": "D1", "team_id": "TEA", "opponent_id": "TEB", "stat": "ast", "pmf": _uniform_pmf(15)},
        {"player_id": "D1", "team_id": "TEA", "opponent_id": "TEB", "stat": "pa", "pmf": _uniform_pmf(50)},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=5_000, seed=1).run()
    np.testing.assert_array_equal(
        tape.get("G1", "D1", "pa").astype(int),
        tape.get("G1", "D1", "pts").astype(int) + tape.get("G1", "D1", "ast").astype(int),
    )


def test_nba_simulator_all_stats_simulated(tmp_path):
    """All 7 DIRECT_STATS are produced for a player that has them."""
    from sgp_engine.sports.nba.simulator import DIRECT_STATS
    rows = [
        {"player_id": "E1", "team_id": "TEA", "opponent_id": "TEB", "stat": s, "pmf": _uniform_pmf(20)}
        for s in DIRECT_STATS
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    tape = NBASimulator(bundle, n_sims=1_000, seed=99).run()
    for s in DIRECT_STATS:
        assert tape.has("G1", "E1", s), f"Missing stat {s}"


# ---------------------------------------------------------------------------
# 5 · Pricing
# ---------------------------------------------------------------------------

def _make_pmf_df(*rows) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "game_id": r["game_id"],
            "player_id": r["player_id"],
            "stat": r["stat"],
            "pmf_json": json.dumps({str(k): float(p) for k, p in enumerate(r["pmf"]) if p > 1e-15}),
            "domain_max": len(r["pmf"]) - 1,
        }
        for r in rows
    ])


def _make_tape_from_pmf_rows(rows, n_sims=20_000, seed=0):
    rng = np.random.default_rng(seed)
    stats = {}
    for r in rows:
        pmf = parse_pmf(r["pmf"])
        u = rng.uniform(0, 1, n_sims)
        key = (r["game_id"], r["player_id"], r["stat"])
        stats[key] = quantile_int_from_u(pmf, u)
    return SimulationTape(n_sims=n_sims, stats=stats, factors={}, metadata={})


def test_price_ticket_both_legs_always_hit():
    """When PMFs are degenerate and lines are set so legs always hit, joint = 1."""
    rows = [
        {"game_id": "G", "player_id": "P1", "stat": "pts", "pmf": _degenerate_pmf(30, 60)},
        {"game_id": "G", "player_id": "P2", "stat": "ast", "pmf": _degenerate_pmf(10, 20)},
    ]
    tape = _make_tape_from_pmf_rows(rows, n_sims=5_000)
    pmf_df = _make_pmf_df(*rows)
    ticket = SGPTicket.from_dict({
        "game_id": "G",
        "legs": [
            {"player_id": "P1", "stat": "pts", "line": 29.5, "side": "over"},
            {"player_id": "P2", "stat": "ast", "line": 9.5, "side": "over"},
        ],
    })
    result = price_ticket(ticket, tape, pmf_df)
    assert abs(result["calibrated_joint_probability"] - 1.0) < 1e-6
    assert result["n_legs"] == 2


def test_price_ticket_one_leg_never_hits():
    """When one leg never hits (degenerate PMF below line), joint = 0."""
    rows = [
        {"game_id": "G", "player_id": "P1", "stat": "pts", "pmf": _degenerate_pmf(10, 60)},
        {"game_id": "G", "player_id": "P2", "stat": "ast", "pmf": _degenerate_pmf(10, 20)},
    ]
    tape = _make_tape_from_pmf_rows(rows, n_sims=5_000)
    pmf_df = _make_pmf_df(*rows)
    ticket = SGPTicket.from_dict({
        "game_id": "G",
        "legs": [
            {"player_id": "P1", "stat": "pts", "line": 20.5, "side": "over"},  # never hits
            {"player_id": "P2", "stat": "ast", "line": 9.5, "side": "over"},   # always hits
        ],
    })
    result = price_ticket(ticket, tape, pmf_df)
    assert result["calibrated_joint_probability"] < 1e-6


def test_price_ticket_marginal_gap_diagnostic():
    """Marginal gaps (sim - PMF) should be small when PMF anchoring is respected."""
    rows = [
        {"game_id": "G", "player_id": "P1", "stat": "pts", "pmf": _uniform_pmf(40)},
        {"game_id": "G", "player_id": "P2", "stat": "reb", "pmf": _uniform_pmf(20)},
    ]
    tape = _make_tape_from_pmf_rows(rows, n_sims=20_000, seed=77)
    pmf_df = _make_pmf_df(*rows)
    ticket = SGPTicket.from_dict({
        "game_id": "G",
        "legs": [
            {"player_id": "P1", "stat": "pts", "line": 19.5, "side": "over"},
            {"player_id": "P2", "stat": "reb", "line": 9.5, "side": "over"},
        ],
    })
    result = price_ticket(ticket, tape, pmf_df)
    for leg in result["legs"]:
        gap = abs(leg["marginal_gap_sim_minus_pmf"])
        assert gap < 0.04, f"Large marginal gap for {leg['stat']}: {gap:.4f}"


def test_price_ticket_with_calibrator():
    """Calibrator is applied and calibrator_id is recorded."""
    from sklearn.isotonic import IsotonicRegression
    ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    x = np.linspace(0, 1, 100)
    ir.fit(x, x * 0.9)  # slight downward shift calibrator
    cal = JointProbabilityCalibrator(calibrator_id="test_cal", model=ir, n_train=100)

    rows = [
        {"game_id": "G", "player_id": "P1", "stat": "pts", "pmf": _uniform_pmf(40)},
        {"game_id": "G", "player_id": "P2", "stat": "ast", "pmf": _uniform_pmf(15)},
    ]
    tape = _make_tape_from_pmf_rows(rows, n_sims=5_000, seed=3)
    pmf_df = _make_pmf_df(*rows)
    ticket = SGPTicket.from_dict({
        "game_id": "G",
        "legs": [
            {"player_id": "P1", "stat": "pts", "line": 19.5, "side": "over"},
            {"player_id": "P2", "stat": "ast", "line": 7.5, "side": "over"},
        ],
    })
    result = price_ticket(ticket, tape, pmf_df, joint_calibrator=cal)
    assert result["calibration"]["applied"] is True
    assert result["calibration"]["calibrator_id"] == "test_cal"


def test_price_tickets_to_frame_columns():
    rows = [
        {"game_id": "G", "player_id": "P1", "stat": "pts", "pmf": _uniform_pmf(40)},
        {"game_id": "G", "player_id": "P2", "stat": "ast", "pmf": _uniform_pmf(15)},
    ]
    tape = _make_tape_from_pmf_rows(rows, n_sims=5_000)
    pmf_df = _make_pmf_df(*rows)
    tickets = [
        SGPTicket.from_dict({"game_id": "G", "ticket_id": f"T{i}", "legs": [
            {"player_id": "P1", "stat": "pts", "line": 19.5, "side": "over"},
            {"player_id": "P2", "stat": "ast", "line": 7.5, "side": "over"},
        ]}) for i in range(3)
    ]
    df = price_tickets_to_frame(tickets, tape, pmf_df)
    assert len(df) == 3
    assert "calibrated_joint_probability" in df.columns
    assert "fair_american_odds" in df.columns
    assert "legs_json" in df.columns


def test_price_ticket_ev_when_offered_american_provided():
    rows = [{"game_id": "G", "player_id": "P1", "stat": "pts", "pmf": _degenerate_pmf(30, 60)}]
    tape = _make_tape_from_pmf_rows(rows, n_sims=1_000)
    pmf_df = _make_pmf_df(*rows)
    ticket = SGPTicket.from_dict({
        "game_id": "G",
        "offered_american_odds": 200,
        "legs": [{"player_id": "P1", "stat": "pts", "line": 29.5, "side": "over"}],
    })
    result = price_ticket(ticket, tape, pmf_df)
    assert "ev" in result
    assert result["ev"] == pytest.approx(3.0 * 1.0 - 1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# 6 · Calibration pipeline
# ---------------------------------------------------------------------------

def _make_calibration_rows(n=1000, seed=0):
    rng = np.random.default_rng(seed)
    pred = rng.uniform(0, 1, n)
    hit = (rng.uniform(0, 1, n) < pred).astype(int)
    return pd.DataFrame({"raw_joint_probability": pred, "hit_result": hit})


def test_fit_global_joint_calibrator(tmp_path):
    df = _make_calibration_rows(n=500)
    cal = fit_global_joint_calibrator(df, min_n=300)
    assert cal.n_train == 500
    preds = cal.predict(np.array([0.1, 0.5, 0.9]))
    assert all(0 <= p <= 1 for p in preds)


def test_fit_global_joint_calibrator_saves_and_loads(tmp_path):
    df = _make_calibration_rows(n=400)
    path = tmp_path / "cal.joblib"
    cal = fit_global_joint_calibrator(df, min_n=300, out_path=path)
    loaded = JointProbabilityCalibrator.load(path)
    np.testing.assert_array_almost_equal(
        cal.predict(np.linspace(0.1, 0.9, 5)),
        loaded.predict(np.linspace(0.1, 0.9, 5)),
    )


def test_fit_global_joint_calibrator_insufficient_n():
    df = _make_calibration_rows(n=50)
    with pytest.raises(ValueError, match="Insufficient rows"):
        fit_global_joint_calibrator(df, min_n=300)


def test_reliability_table_shape():
    df = _make_calibration_rows(n=2000)
    df["calibrated_joint_probability"] = df["raw_joint_probability"]
    tab = reliability_table(df, pred_col="calibrated_joint_probability", y_col="hit_result", bins=10)
    assert len(tab) == 10
    assert "abs_calibration_error" in tab.columns
    assert "weighted_abs_calibration_error" in tab.columns


def test_expected_calibration_error_bounded():
    df = _make_calibration_rows(n=5000)
    df["calibrated_joint_probability"] = df["raw_joint_probability"]
    ece = expected_calibration_error(df, pred_col="calibrated_joint_probability", y_col="hit_result")
    assert 0.0 <= ece <= 1.0


def test_calibrator_predict_clamps():
    df = _make_calibration_rows(n=400)
    cal = fit_global_joint_calibrator(df, min_n=300)
    edge = cal.predict(np.array([0.0, 1.0, -0.5, 1.5]))
    assert all(1e-9 <= p <= 1 - 1e-9 for p in edge)


# ---------------------------------------------------------------------------
# 7 · Bundle write/load round-trip
# ---------------------------------------------------------------------------

def test_bundle_write_load_round_trip(tmp_path):
    rows = [
        {"player_id": "X1", "stat": "pts", "pmf": _uniform_pmf(40)},
        {"player_id": "X1", "stat": "ast", "pmf": _uniform_pmf(15)},
        {"player_id": "X2", "stat": "reb", "pmf": _uniform_pmf(20)},
    ]
    bundle = _make_minimal_bundle(tmp_path, rows)
    bundle.write()

    loaded = SlateStateBundle.load(bundle.root)
    assert loaded.status == "PASS"
    assert loaded.slate_date == "2026-01-01"
    assert len(loaded.player_stat_pmfs) == 3
    assert len(loaded.games) == 1
    assert set(loaded.player_stat_pmfs["player_id"]) == {"X1", "X2"}


def test_bundle_assert_pass_raises_on_fail(tmp_path):
    rows = [{"player_id": "Y1", "stat": "pts", "pmf": _uniform_pmf(40)}]
    bundle = _make_minimal_bundle(tmp_path, rows)
    bundle.manifest["bundle_status"] = "FAIL"
    with pytest.raises(RuntimeError, match="refusing to price"):
        bundle.assert_pass()


def test_bundle_assert_pass_ok(tmp_path):
    rows = [{"player_id": "Z1", "stat": "pts", "pmf": _uniform_pmf(40)}]
    bundle = _make_minimal_bundle(tmp_path, rows)
    bundle.assert_pass()  # should not raise


# ---------------------------------------------------------------------------
# 8 · Full adapter + build from fake delivery
# ---------------------------------------------------------------------------

def _write_fake_delivery(delivery_root: Path, slate_date: str, pmf_rows: list[dict]) -> None:
    """Write a minimal canonical_source PMF parquet for adapter testing."""
    df = pd.DataFrame(pmf_rows)
    src = delivery_root / slate_date / "canonical_source"
    src.mkdir(parents=True, exist_ok=True)
    df.to_parquet(src / "player_prop_pmfs_tonight_MODEL_ONLY.parquet", index=False)

    trained_through = (pd.Timestamp(slate_date) - pd.Timedelta(days=1)).date().isoformat()
    manifest = {
        "trained_through_date": trained_through,
        "calibrated_through_date": trained_through,
    }
    (delivery_root / slate_date).mkdir(parents=True, exist_ok=True)
    (delivery_root / slate_date / "run_manifest.json").write_text(json.dumps(manifest))


def test_build_nba_bundle_from_fake_delivery(tmp_path):
    from sgp_engine.sports.nba.adapter import build_nba_slate_state_bundle

    slate_date = "2026-03-01"
    pmf_rows = []
    uniform40 = {str(k): 1 / 40 for k in range(40)}
    uniform15 = {str(k): 1 / 15 for k in range(15)}
    for pid, team, opp, stat, pmf_d in [
        ("P1", "LAL", "BOS", "pts", uniform40),
        ("P1", "LAL", "BOS", "ast", uniform15),
        ("P2", "BOS", "LAL", "reb", {str(k): 1 / 20 for k in range(20)}),
    ]:
        pmf_rows.append({
            "game_id": "LAL_BOS_20260301",
            "player_id": pid,
            "team_id": team,
            "opponent_id": opp,
            "stat": stat,
            "pmf_json": json.dumps(pmf_d),
        })

    repo_root = tmp_path / "repo"
    _write_fake_delivery(repo_root / "deliveries", slate_date, pmf_rows)

    bundle = build_nba_slate_state_bundle(
        repo_root,
        slate_date,
        allow_missing_asof_metadata=True,
        strict=False,
    )
    assert bundle is not None
    assert len(bundle.player_stat_pmfs) == 3
    assert set(bundle.player_stat_pmfs["player_id"]) == {"P1", "P2"}
    dq_path = bundle.root / "data_quality_report.json"
    assert dq_path.exists()


def test_full_pipeline_bundle_to_price(tmp_path):
    """Full pipeline: fake delivery → bundle → simulate → price ticket."""
    from sgp_engine.sports.nba.adapter import build_nba_slate_state_bundle

    slate_date = "2026-03-15"
    uniform40 = {str(k): 1 / 40 for k in range(40)}
    uniform15 = {str(k): 1 / 15 for k in range(15)}
    pmf_rows = [
        {"game_id": "G_TEST", "player_id": "PA", "team_id": "T1", "opponent_id": "T2",
         "stat": "pts", "pmf_json": json.dumps(uniform40)},
        {"game_id": "G_TEST", "player_id": "PB", "team_id": "T1", "opponent_id": "T2",
         "stat": "ast", "pmf_json": json.dumps(uniform15)},
    ]

    repo_root = tmp_path / "repo"
    _write_fake_delivery(repo_root / "deliveries", slate_date, pmf_rows)

    bundle = build_nba_slate_state_bundle(
        repo_root, slate_date,
        allow_missing_asof_metadata=True, strict=False,
    )
    tape = NBASimulator(bundle, n_sims=20_000, seed=0).run()
    assert tape.has("G_TEST", "PA", "pts")
    assert tape.has("G_TEST", "PB", "ast")

    ticket = SGPTicket.from_dict({
        "game_id": "G_TEST",
        "ticket_id": "PIPELINE_TEST",
        "legs": [
            {"player_id": "PA", "stat": "pts", "line": 19.5, "side": "over"},
            {"player_id": "PB", "stat": "ast", "line": 7.5, "side": "over"},
        ],
    })
    result = price_ticket(ticket, tape, bundle.player_stat_pmfs)
    assert 0 < result["calibrated_joint_probability"] < 1
    assert result["n_legs"] == 2
    assert result["simulation_count"] == 20_000


def test_combo_standalone_leg_anchored_marginal(tmp_path):
    """Standalone combo leg uses anchored tape → simulated marginal ≈ PMF marginal.

    Build a bundle where component means (pts=19.5 + reb=9.5 + ast=7.0 = 36.0)
    intentionally differ from the delivered pra PMF mean (34.5).  For a standalone
    PRA ticket leg the pricing layer must select the rank-anchored tape values so
    that the simulated marginal probability tracks the delivered PMF — not the
    algebraic sum distribution.
    """
    from sgp_engine.sports.nba.adapter import build_nba_slate_state_bundle

    slate_date = "2026-02-01"
    u40  = {str(k): 1 / 40 for k in range(40)}  # pts  mean=19.5
    u20  = {str(k): 1 / 20 for k in range(20)}  # reb  mean=9.5
    u15  = {str(k): 1 / 15 for k in range(15)}  # ast  mean=7.0
    # Delivered combo PMF has mean=34.5 (intentionally different from sum 36.0)
    u70  = {str(k): 1 / 70 for k in range(70)}  # pra  mean=34.5
    pmf_rows = [
        {"game_id": "G1", "player_id": "P1", "team_id": "T1", "opponent_id": "T2",
         "stat": "pts", "pmf_json": json.dumps(u40)},
        {"game_id": "G1", "player_id": "P1", "team_id": "T1", "opponent_id": "T2",
         "stat": "reb", "pmf_json": json.dumps(u20)},
        {"game_id": "G1", "player_id": "P1", "team_id": "T1", "opponent_id": "T2",
         "stat": "ast", "pmf_json": json.dumps(u15)},
        {"game_id": "G1", "player_id": "P1", "team_id": "T1", "opponent_id": "T2",
         "stat": "pra", "pmf_json": json.dumps(u70)},
    ]
    repo_root = tmp_path / "repo"
    _write_fake_delivery(repo_root / "deliveries", slate_date, pmf_rows)
    bundle = build_nba_slate_state_bundle(
        repo_root, slate_date,
        allow_missing_asof_metadata=True, strict=False,
    )
    tape = NBASimulator(bundle, n_sims=50_000, seed=0).run()

    # Anchored variant must exist in the tape
    assert tape.has("G1", "P1", "pra_anchored"), "Anchored pra key must be stored in tape"

    # Algebraic combo should preserve pts+reb+ast identity
    pra_alg  = tape.get("G1", "P1", "pra").astype(int)
    pts      = tape.get("G1", "P1", "pts").astype(int)
    reb      = tape.get("G1", "P1", "reb").astype(int)
    ast      = tape.get("G1", "P1", "ast").astype(int)
    np.testing.assert_array_equal(pra_alg, pts + reb + ast)

    # Anchored variant should have mean ≈ delivered PMF mean (34.5), not 36.0
    pra_anch = tape.get("G1", "P1", "pra_anchored").astype(float)
    assert abs(pra_anch.mean() - 34.5) < 0.5, (
        f"Anchored pra mean {pra_anch.mean():.2f} should be near 34.5 (PMF mean)"
    )

    # Price a standalone PRA leg — simulated marginal should track PMF marginal
    pra_pmf_prob = event_probability(parse_pmf(u70), 34.5, "over")  # ≈ 0.5
    ticket = SGPTicket.from_dict({
        "game_id": "G1",
        "legs": [{"player_id": "P1", "stat": "pra", "line": 34.5, "side": "over"}],
    })
    result = price_ticket(ticket, tape, bundle.player_stat_pmfs)
    sim_marginal = result["legs"][0]["marginal_probability_simulated"]
    # Anchored sim marginal must be close to the PMF marginal, not the algebraic sim
    assert abs(sim_marginal - pra_pmf_prob) < 0.04, (
        f"Standalone PRA marginal gap too large: sim={sim_marginal:.3f} pmf={pra_pmf_prob:.3f}"
    )
