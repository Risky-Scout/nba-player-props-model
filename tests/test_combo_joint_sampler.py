import numpy as np

from nba_props_model.pmf.combo_joint_sampler import sample_combo_joint_pmf


def test_combo_joint_sampler_normalized_pmfs():
    means = {"pts": 22.0, "reb": 7.0, "ast": 5.0}
    cov = np.array([[25.0, 6.0, 5.0], [6.0, 9.0, 3.0], [5.0, 3.0, 8.0]], dtype=float)
    out = sample_combo_joint_pmf(means, cov, n_samples=1500, seed=3)
    assert set(out) == {"pa", "pr", "ra", "pra"}
    for pmf in out.values():
        assert abs(float(pmf.sum()) - 1.0) < 0.05
