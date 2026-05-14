"""Simple correlated sampler for combo stat PMFs."""
from __future__ import annotations

import numpy as np
import pandas as pd


def sample_combo_joint_pmf(
    means: dict[str, float],
    covariance: np.ndarray,
    *,
    n_samples: int = 5000,
    seed: int = 7,
) -> dict[str, np.ndarray]:
    order = ("pts", "reb", "ast")
    mu = np.array([float(means.get(k, 0.0)) for k in order], dtype=float)
    cov = np.asarray(covariance, dtype=float)
    draws = np.random.default_rng(seed).multivariate_normal(mu, cov, size=n_samples)
    draws = np.clip(np.round(draws), 0, None).astype(int)
    pts, reb, ast = draws[:, 0], draws[:, 1], draws[:, 2]
    combos = {
        "pa": pts + ast,
        "pr": pts + reb,
        "ra": reb + ast,
        "pra": pts + reb + ast,
    }
    out: dict[str, np.ndarray] = {}
    for k, v in combos.items():
        vc = pd.Series(v).value_counts(normalize=True).sort_index()
        pmf = np.zeros(int(vc.index.max()) + 1, dtype=float)
        pmf[vc.index.astype(int)] = vc.values
        out[k] = pmf
    return out
