from __future__ import annotations

import numpy as np

from nba_props_model.pipelines.pmf_predict import PropPMF


COMBO_COMPONENTS = {
    "pr": ("pts", "reb"),
    "pa": ("pts", "ast"),
    "ra": ("reb", "ast"),
    "pra": ("pts", "reb", "ast"),
    "stocks": ("stl", "blk"),
}


def _mean(pmf: np.ndarray) -> float:
    arr = np.asarray(pmf, dtype=float)
    arr = np.clip(arr, 0.0, None)
    arr = arr / arr.sum()
    return float(np.dot(np.arange(len(arr)), arr))


def test_combo_pmf_means_equal_component_sum_after_rebuild():
    from nba_props_model.pipelines.pmf_predict import _rebuild_mission_combo_pmfs_from_final_components

    out = {
        "pts": PropPMF("pts", np.array([0.0, 0.0, 1.0]), True, "pts_cal"),
        "reb": PropPMF("reb", np.array([0.0, 1.0]), True, "reb_cal"),
        "ast": PropPMF("ast", np.array([0.5, 0.5]), True, "ast_cal"),
        "stl": PropPMF("stl", np.array([0.8, 0.2]), True, "stl_cal"),
        "blk": PropPMF("blk", np.array([0.7, 0.3]), True, "blk_cal"),

        # Deliberately incoherent placeholders. Rebuild should overwrite them.
        "pr": PropPMF("pr", np.array([1.0]), True, "bad_combo"),
        "pa": PropPMF("pa", np.array([1.0]), True, "bad_combo"),
        "ra": PropPMF("ra", np.array([1.0]), True, "bad_combo"),
        "pra": PropPMF("pra", np.array([1.0]), True, "bad_combo"),
        "stocks": PropPMF("stocks", np.array([1.0]), True, "bad_combo"),
    }

    _rebuild_mission_combo_pmfs_from_final_components(out)

    for combo, parts in COMBO_COMPONENTS.items():
        combo_mean = _mean(out[combo].pmf)
        component_sum = sum(_mean(out[p].pmf) for p in parts)
        assert abs(combo_mean - component_sum) < 1e-9, (
            combo,
            combo_mean,
            component_sum,
            out[combo].model_version,
        )


def test_rebuilt_combo_pmfs_are_valid_probability_distributions():
    from nba_props_model.pipelines.pmf_predict import _rebuild_mission_combo_pmfs_from_final_components

    out = {
        "pts": PropPMF("pts", np.array([0.25, 0.75]), True, "pts_cal"),
        "reb": PropPMF("reb", np.array([0.4, 0.6]), True, "reb_cal"),
        "ast": PropPMF("ast", np.array([0.9, 0.1]), True, "ast_cal"),
        "stl": PropPMF("stl", np.array([0.8, 0.2]), True, "stl_cal"),
        "blk": PropPMF("blk", np.array([0.7, 0.3]), True, "blk_cal"),
    }

    _rebuild_mission_combo_pmfs_from_final_components(out)

    for combo in COMBO_COMPONENTS:
        arr = out[combo].pmf
        assert arr.ndim == 1
        assert np.all(np.isfinite(arr))
        assert np.all(arr >= 0.0)
        assert abs(float(arr.sum()) - 1.0) < 1e-12
        assert "component_convolution_mean_coherent_v1" in out[combo].model_version
