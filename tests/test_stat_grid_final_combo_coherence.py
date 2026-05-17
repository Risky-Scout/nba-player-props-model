from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


def _load_build_stat_grid_module():
    path = Path("scripts/build_stat_grid_pmfs.py")
    spec = importlib.util.spec_from_file_location("build_stat_grid_pmfs_for_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mean_from_dict_pmf(d: dict[int, float]) -> float:
    max_k = max(d)
    arr = np.zeros(max_k + 1, dtype=float)
    for k, v in d.items():
        arr[int(k)] = float(v)
    arr = arr / arr.sum()
    return float(np.dot(np.arange(len(arr)), arr))


def test_final_stat_grid_combo_pass_rebuilds_after_source_recalibration():
    mod = _load_build_stat_grid_module()

    rows = [
        {"player_id": 1, "game_id": 10, "stat": "pts", "pmf": '{"2": 1.0}', "model_version": "pts_final", "calibrated": True},
        {"player_id": 1, "game_id": 10, "stat": "reb", "pmf": '{"1": 1.0}', "model_version": "reb_final", "calibrated": True},
        {"player_id": 1, "game_id": 10, "stat": "ast", "pmf": '{"0": 0.5, "1": 0.5}', "model_version": "ast_final", "calibrated": True},

        {"player_id": 1, "game_id": 10, "stat": "pr", "pmf": '{"0": 1.0}', "model_version": "bad_pr", "calibrated": False},
        {"player_id": 1, "game_id": 10, "stat": "pa", "pmf": '{"0": 1.0}', "model_version": "bad_pa", "calibrated": False},
        {"player_id": 1, "game_id": 10, "stat": "ra", "pmf": '{"0": 1.0}', "model_version": "bad_ra", "calibrated": False},
        {"player_id": 1, "game_id": 10, "stat": "pra", "pmf": '{"0": 1.0}', "model_version": "bad_pra", "calibrated": False},
    ]

    df = pd.DataFrame(rows)
    for col in ["pmf_summary_mean", "pmf_summary_median", "pmf_summary_mode", "support_max", "pmf_sum_error"]:
        df[col] = np.nan

    out = mod._finalize_combo_coherence_after_source_recalibration(df)

    means = {}
    for _, row in out.iterrows():
        means[row["stat"]] = _mean_from_dict_pmf(
            mod._pmf_to_dict(mod._stat_grid_finalizer_pmf_array(row["pmf"]))
        )

    assert means["pr"] == means["pts"] + means["reb"]
    assert means["pa"] == means["pts"] + means["ast"]
    assert means["ra"] == means["reb"] + means["ast"]
    assert means["pra"] == means["pts"] + means["reb"] + means["ast"]

    for stat in ["pr", "pa", "ra", "pra"]:
        row = out[out["stat"] == stat].iloc[0]
        assert "stat_grid_final_component_convolution_mean_coherent_v1" in row["model_version"]
        assert bool(row["calibrated"]) is True
        assert abs(float(row["pmf_summary_mean"]) - means[stat]) < 1e-12
