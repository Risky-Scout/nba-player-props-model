"""Stat-grid mission 12-stat synthesis and TOV contract (M8.6)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from nba_props_model.models.minutes import MinutesDistribution  # noqa: E402
from nba_props_model.models.simulation import StatPMF  # noqa: E402
from nba_props_model.pipelines import pmf_predict as pmf_predict_mod  # noqa: E402
from nba_props_model.pipelines.pmf_predict import (  # noqa: E402
    PropPMF,
    build_prop_pmfs,
    ensure_mission_combos_present,
)
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402

import build_stat_grid_pmfs as build_stat_grid_pmfs_mod  # noqa: E402


def _minutes_dist() -> MinutesDistribution:
    return MinutesDistribution(
        state_probs=(0.02, 0.10, 0.88),
        limited_quantiles={10: 10.0, 25: 14.0, 50: 18.0, 75: 22.0, 90: 23.5},
        normal_quantiles={10: 26.0, 25: 30.0, 50: 34.0, 75: 38.0, 90: 42.0},
    )


def test_stat_grid_emission_order_base_before_combos():
    req = list(MISSION_REQUIRED_TARGETS_CANONICAL)
    ordered = build_stat_grid_pmfs_mod._stat_grid_emission_order(req)
    assert set(ordered) == set(req)
    assert ordered.index("blk") < ordered.index("stocks")
    assert ordered.index("tov") < ordered.index("pa")


def test_ensure_mission_combos_joint_synthesis_adds_five_combos(monkeypatch):
    """Seven base PMFs only → mission combo keys appear after joint synthesis."""
    n = 400
    rng = np.random.default_rng(0)

    def _fake_joint(*args, **kwargs):
        return {
            "pts": rng.integers(0, 25, size=n),
            "reb": rng.integers(0, 12, size=n),
            "ast": rng.integers(0, 12, size=n),
            "tov": rng.integers(0, 6, size=n),
            "fg3m": rng.integers(0, 8, size=n),
            "stl": rng.integers(0, 5, size=n),
            "blk": rng.integers(0, 5, size=n),
        }

    monkeypatch.setattr(pmf_predict_mod, "simulate_joint_stat_samples", _fake_joint)
    monkeypatch.setattr(pmf_predict_mod, "_apply_pmf_calibrators", lambda *a, **k: None)

    K = 31
    uniform = np.ones(K, dtype=float) / K
    pack: dict[str, PropPMF] = {
        "pts": PropPMF("pts", uniform.copy(), False, "t"),
        "reb": PropPMF("reb", uniform.copy(), False, "t"),
        "ast": PropPMF("ast", uniform.copy(), False, "t"),
        "fg3m": PropPMF("fg3m", uniform.copy(), False, "t"),
        "tov": PropPMF("tov", uniform.copy(), False, "t"),
        "stl": PropPMF("stl", uniform.copy(), False, "t"),
        "blk": PropPMF("blk", uniform.copy(), False, "t"),
    }

    ensure_mission_combos_present(
        pack,
        minutes_dist=_minutes_dist(),
        feature_row={"player_id": 1},
        fg3m_hurdle_model=None,
        rng=np.random.default_rng(1),
    )

    mission = {
        "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
        "stocks", "pa", "pr", "ra", "pra",
    }
    assert mission.issubset(pack.keys())
    for stat in ("stocks", "pa", "pr", "ra", "pra"):
        assert pack[stat].pmf is not None
        assert float(np.asarray(pack[stat].pmf).sum()) == pytest.approx(1.0)


def test_stat_grid_mode_surfaces_tov_missing_token_not_rectangularize(monkeypatch):
    def fake_main(*args, **kwargs):
        p = np.ones(8, dtype=float) / 8.0
        return {
            "pts": StatPMF(stat="pts", pmf=p.copy()),
            "reb": StatPMF(stat="reb", pmf=p.copy()),
            "ast": StatPMF(stat="ast", pmf=p.copy()),
        }

    from nba_props_model.models import simulation as simulation_mod

    monkeypatch.setattr(simulation_mod, "simulate_all_main_stats", fake_main)

    with pytest.raises(RuntimeError) as excinfo:
        build_prop_pmfs(
            _minutes_dist(),
            {"player_id": 42},
            fg3m_hurdle_model=None,
            stat_grid_mode=True,
        )
    msg = str(excinfo.value)
    assert "TOV_MISSING_FROM_STAT_GRID_SOURCE" in msg
    assert "STAT_GRID_RECTANGULARIZE_FAILED" not in msg
