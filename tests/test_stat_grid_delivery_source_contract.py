"""Stat-grid delivery source graph contract (feature snapshot → stat_grid only)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

pd = pytest.importorskip("pandas")

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_aborts_stat_grid_missing_output_without_all_props_canonical(monkeypatch):
    """1) STAT_GRID_BUILD_MISSING_OUTPUT; canonical not invoked with all_props path."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import run_daily_delivery_pipeline as rdp

    fake_sg = REPO_ROOT / "scripts" / "build_stat_grid_pmfs.py"
    calls: list[list[str]] = []

    def capture_run(cmd, **kwargs):
        calls.append(list(cmd))
        if "build_stat_grid_pmfs.py" in cmd[1]:
            # Simulate successful subprocess but omit writing stat_grid parquet.
            return 0
        return 0

    monkeypatch.setattr(rdp, "_run", capture_run)
    monkeypatch.setattr(rdp, "STAT_GRID", fake_sg)
    sg_path = REPO_ROOT / "predictions" / "stat_grid_2099-01-01.parquet"
    if sg_path.exists():
        sg_path.unlink()

    with pytest.raises(SystemExit) as exc:
        rdp._run_mission_stat_grid_and_canonical("2099-01-01", None)
    assert "STAT_GRID_BUILD_MISSING_OUTPUT" in str(exc.value)

    assert any("build_stat_grid_pmfs.py" in str(c) for c in calls)
    assert not any(
        "build_model_only_canonical_from_stat_grid.py" in str(c) for c in calls
    )


def test_canonical_rejects_all_props_path_via_cli(tmp_path):
    """2) all_props path → CANONICAL_SOURCE_CONTRACT_VIOLATION."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import build_model_only_canonical_from_stat_grid as canon

    bad = tmp_path / "predictions" / "all_props_2026-01-01.parquet"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"")

    rc = canon.main(
        [
            "--date",
            "2026-01-01",
            "--stat-grid-path",
            str(bad),
        ]
    )
    assert rc == 1


def test_build_stat_grid_writes_parquet_with_fixture_features(tmp_path, monkeypatch):
    """3–4) Feature snapshot rows → stat_grid parquet includes all 12 mission stats."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    sys.path.insert(0, str(REPO_ROOT / "src"))

    import build_stat_grid_pmfs as bsg
    from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL

    monkeypatch.setenv("BDL_API_KEY", "test-key-for-stat-grid-contract")

    feat = tmp_path / "player_prop_features_2026-01-20_morning_expected.parquet"
    rows = []
    for sid, stat in enumerate(MISSION_REQUIRED_TARGETS_CANONICAL):
        rows.append({"player_id": 42, "game_id": 9001 + sid % 2, "stat": stat})
    pd.DataFrame(rows).to_parquet(feat)

    out_pq = tmp_path / "stat_grid_2026-01-20.parquet"

    def fake_state(_date):
        return {
            "stats_df": pd.DataFrame(),
            "adv_by_player": {},
            "games_by_id": {
                9001: {
                    "id": 9001,
                    "home_team": {"id": 10, "full_name": "Home"},
                    "visitor_team": {"id": 20, "full_name": "Vis"},
                },
            },
            "ctx_map": {},
            "injury_map": {},
            "inactive_player_ids": set(),
            "availability_lookup": {},
            "availability_builder": None,
            "injury_freshness_status": "ok",
            "injury_context_source": "test",
            "injury_report_fetched_at_utc": "Z",
            "suppress_inactive_risk": True,
            "availability_table_freshness": "missing",
            "availability_table_age_hours": None,
        }

    def fake_eligibility(_root, _date, keys):
        return {(k[0], k[1]): {"player_game_eligible": True} for k in keys}

    base_row = {
        "player_name": "X",
        "team_id": 10,
        "game": "Vis @ Home",
        "is_home": True,
        "opp_team_id": 20,
        "role_bucket": "core",
        "role_source": "test",
        "mp_bucket": 1,
        "usage_bucket": 1,
        "slate_date": "2026-01-20",
        "minutes_mean": 20.0,
        "minutes_q50": 20.0,
        "minutes_p10": None,
        "minutes_p50": 20.0,
        "minutes_p90": None,
        "minutes_std": None,
        "p_inactive_used": 0.05,
        "rotation_probability": None,
        "starter_probability": None,
        "projected_role": None,
        "player_game_eligible": True,
        "eligibility_reason": None,
        "has_current_market_line": False,
        "minutes_source": None,
        "minutes_model_version": None,
        "injury_freshness_status": None,
        "injury_context_source": None,
        "injury_report_fetched_at_utc": None,
        "availability_table_freshness": None,
        "availability_table_age_hours": None,
        "suppress_inactive_risk": False,
        "availability_blocks_market_superiority": False,
        "side": "MODEL_ONLY",
        "line": None,
        "odds": None,
        "model_version": "test",
        "calibrated": False,
        "source_recalibration_applied": False,
        "source_recalibration_version": None,
        "source_recalibration_stage": None,
        "source_recalibration_role_bucket": None,
        "pmf_summary_mean": 1.0,
        "pmf_summary_median": 1,
        "pmf_summary_mode": 0,
        "support_max": 5,
        "pmf_sum_error": 0.0,
        "tov_status": None,
        "tov_status_reason": None,
        "line_is_real": False,
        "scored_at_utc": "Z",
    }

    def fake_row(pid, gid, *, target_date, state, fg3m_model, stats, recalibrator=None,
                 eligibility_row=None):
        out_l = []
        for stat in stats:
            r = dict(base_row)
            r["player_id"] = pid
            r["game_id"] = gid
            r["stat"] = stat
            r["pmf"] = json.dumps({0: 0.2, 1: 0.8})
            out_l.append(r)
        return out_l

    class _Rec:
        enabled = False
        version = None

    monkeypatch.setattr(bsg, "_build_pipeline_state", fake_state)
    monkeypatch.setattr(bsg, "build_eligibility_map", fake_eligibility)
    monkeypatch.setattr(bsg, "_row_for_player_game", fake_row)
    monkeypatch.setattr(bsg, "load_stat_grid_delivery_recalibrator", lambda: _Rec())
    monkeypatch.setattr(bsg, "_fg3m_hurdle_model", lambda **kwargs: None)
    monkeypatch.setattr(bsg, "assert_no_ineligible_pmfs", lambda df, label: None)

    argv = [
        "--date",
        "2026-01-20",
        "--slate-source",
        "feature_snapshot_morning_expected",
        "--feature-snapshot",
        str(feat),
        "--stats",
        *MISSION_REQUIRED_TARGETS_CANONICAL,
        "--out",
        str(out_pq),
    ]
    rc = bsg.main(argv)
    assert rc == 0
    assert out_pq.is_file()
    df = pd.read_parquet(out_pq, columns=["stat"])
    present = set(df["stat"].astype(str).unique())
    assert present == set(MISSION_REQUIRED_TARGETS_CANONICAL)


def test_tov_error_token_not_rectangularize():
    """5) TOV path surfaces TOV_MISSING_FROM_STAT_GRID_SOURCE."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from nba_props_model.models import simulation as simulation_mod
    from nba_props_model.models.simulation import StatPMF
    from nba_props_model.models.minutes import MinutesDistribution
    from nba_props_model.pipelines.pmf_predict import build_prop_pmfs

    md = MinutesDistribution(
        state_probs=(0.02, 0.10, 0.88),
        limited_quantiles={10: 10.0, 25: 14.0, 50: 18.0, 75: 22.0, 90: 23.5},
        normal_quantiles={10: 26.0, 25: 30.0, 50: 34.0, 75: 38.0, 90: 42.0},
    )

    def fake_main(*a, **k):
        p = __import__("numpy").ones(5) / 5.0
        return {
            "pts": StatPMF(stat="pts", pmf=p.copy()),
            "reb": StatPMF(stat="reb", pmf=p.copy()),
        }

    with patch.object(simulation_mod, "simulate_all_main_stats", fake_main):
        with pytest.raises(RuntimeError) as exc:
            build_prop_pmfs(md, {}, fg3m_hurdle_model=None, stat_grid_mode=True)
    msg = str(exc.value)
    assert "TOV_MISSING_FROM_STAT_GRID_SOURCE" in msg
    assert "STAT_GRID_RECTANGULARIZE_FAILED" not in msg


def test_combo_synthesis_failure_token():
    """6) Missing joint / components → COMBO_PMF_SYNTHESIS_FAILED."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import numpy as np
    from nba_props_model.models import simulation as simulation_mod
    from nba_props_model.models.simulation import StatPMF
    from nba_props_model.models.minutes import MinutesDistribution
    from nba_props_model.pipelines import pmf_predict as pp
    from nba_props_model.pipelines.pmf_predict import build_prop_pmfs

    md = MinutesDistribution(
        state_probs=(0.02, 0.10, 0.88),
        limited_quantiles={10: 10.0, 25: 14.0, 50: 18.0, 75: 22.0, 90: 23.5},
        normal_quantiles={10: 26.0, 25: 30.0, 50: 34.0, 75: 38.0, 90: 42.0},
    )
    p = np.ones(8, dtype=float) / 8.0

    def fake_main(*a, **k):
        return {
            "pts": StatPMF(stat="pts", pmf=p.copy()),
            "reb": StatPMF(stat="reb", pmf=p.copy()),
            "ast": StatPMF(stat="ast", pmf=p.copy()),
            "tov": StatPMF(stat="tov", pmf=p.copy()),
        }

    with patch.object(simulation_mod, "simulate_all_main_stats", fake_main):
        with patch.object(pp, "simulate_joint_stat_samples", lambda *a, **k: None):
            with pytest.raises(RuntimeError) as exc:
                build_prop_pmfs(
                    md,
                    {"x": 1},
                    fg3m_hurdle_model=None,
                    stat_grid_mode=True,
                )
    assert "COMBO_PMF_SYNTHESIS_FAILED" in str(exc.value)

