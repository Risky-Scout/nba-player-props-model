"""
NBA Props Model — derived combo-stat PMFs.

Markets covered: pra (pts+reb+ast), pr (pts+reb), pa (pts+ast), ra (reb+ast).

Each combo is DERIVED from the calibrated component PMFs of its
constituents — never trained as an independent direct-total model. Two
derivation modes are supported:

  independence_convolution   pure within-game independence assumption.
  gaussian_copula_simulation uses the within-player residual correlation
                              matrix from `nba_props_model.correlation.sgp_engine`
                              to induce realistic within-game dependence.

At predict time the caller picks the mode. Default is Gaussian copula
when the correlation artifact is loadable; independence otherwise.
"""
from __future__ import annotations

import logging
from typing import Iterable, Optional

import numpy as np

from nba_props_model.models.simulation import DOMAIN_MAX as MAIN_DOMAIN_MAX
from nba_props_model.models.simulation import StatPMF

logger = logging.getLogger(__name__)


COMBO_COMPONENTS: dict[str, tuple[str, ...]] = {
    "pra": ("pts", "reb", "ast"),
    "pr":  ("pts", "reb"),
    "pa":  ("pts", "ast"),
    "ra":  ("reb", "ast"),
}


def combo_domain_max(components: Iterable[str]) -> int:
    return int(sum(MAIN_DOMAIN_MAX[s] for s in components))


# ── Independence convolution ─────────────────────────────────────────────────


def _convolve_pmfs(pmfs: list[np.ndarray]) -> np.ndarray:
    out = pmfs[0].copy()
    for p in pmfs[1:]:
        out = np.convolve(out, p)
    s = out.sum()
    if s > 0:
        out = out / s
    return out


def combo_pmf_independence(components_pmf: dict[str, StatPMF]) -> StatPMF:
    """Combine component PMFs assuming within-game independence."""
    keys = list(components_pmf.keys())
    arr = [components_pmf[k].pmf for k in keys]
    pmf = _convolve_pmfs(arr)
    combo_key = _combo_key_for_components(keys)
    return StatPMF(stat=combo_key, pmf=pmf)


# ── Gaussian copula derivation ───────────────────────────────────────────────


def _cdf(pmf: np.ndarray) -> np.ndarray:
    c = np.cumsum(pmf)
    # Clamp to [0, 1] to guard against tiny float drift.
    return np.clip(c, 0.0, 1.0)


def _inverse_cdf(pmf: np.ndarray, u: np.ndarray) -> np.ndarray:
    """For each u in [0,1], return the smallest integer k with CDF[k] >= u."""
    c = _cdf(pmf)
    # searchsorted(c, u) returns the insertion index; integer values map
    # directly to the discrete support {0, ..., len(pmf)-1}.
    idx = np.searchsorted(c, u, side="left")
    idx = np.clip(idx, 0, len(pmf) - 1)
    return idx


def combo_pmf_copula(
    components_pmf: dict[str, StatPMF],
    correlation: Optional[np.ndarray] = None,
    n_draws: int = 20_000,
    rng: Optional[np.random.Generator] = None,
) -> StatPMF:
    """Combine component PMFs with Gaussian-copula-induced correlation.

    Parameters
    ----------
    components_pmf : ordered dict-like {stat: StatPMF}
    correlation : square matrix of shape (len(components_pmf),) or None.
        If None, identity is used -> falls back to independence.
        Off-diagonal entries must lie in (-1, 1); diagonal must be 1.0.
    n_draws : Monte Carlo sample count.
    rng : optional Generator for reproducibility.

    The correlation argument is typically the within-player residual-z
    correlation between stats at a matched usage bucket, sourced from
    the correlation engine. We apply it in standard-normal space then
    map back through each component's discrete CDF to produce a joint
    sample, then sum component draws to get the combo total.
    """
    if rng is None:
        rng = np.random.default_rng()
    keys = list(components_pmf.keys())
    pmfs = [components_pmf[k].pmf for k in keys]
    k_count = len(keys)

    if correlation is None:
        correlation = np.eye(k_count)
    else:
        correlation = np.array(correlation, dtype=float)
        if correlation.shape != (k_count, k_count):
            raise ValueError(
                f"correlation shape {correlation.shape} != expected ({k_count},{k_count})"
            )
        # Symmetrize and PSD-project defensively.
        correlation = 0.5 * (correlation + correlation.T)
        correlation = _psd_project(correlation)

    # Draw (n_draws, k_count) correlated standard normals.
    L = np.linalg.cholesky(correlation + 1e-9 * np.eye(k_count))
    z = rng.standard_normal(size=(n_draws, k_count)) @ L.T
    # To uniforms via the normal CDF.
    from scipy.stats import norm
    u = norm.cdf(z)

    # Inverse CDF per component (operating column-wise).
    samples = np.zeros((n_draws, k_count), dtype=int)
    for j, pmf in enumerate(pmfs):
        samples[:, j] = _inverse_cdf(pmf, u[:, j])

    totals = samples.sum(axis=1)
    max_total = combo_domain_max(keys)
    totals = np.clip(totals, 0, max_total)
    counts = np.bincount(totals, minlength=max_total + 1)
    out_pmf = counts.astype(float) / counts.sum()
    combo_key = _combo_key_for_components(keys)
    return StatPMF(stat=combo_key, pmf=out_pmf)


def _psd_project(mat: np.ndarray) -> np.ndarray:
    """Clip eigenvalues at a small epsilon to guarantee PSD."""
    eigvals, eigvecs = np.linalg.eigh(mat)
    eigvals = np.clip(eigvals, 1e-6, None)
    out = (eigvecs * eigvals) @ eigvecs.T
    # Renormalize diagonal to 1.
    d = np.sqrt(np.clip(np.diag(out), 1e-9, None))
    out = out / np.outer(d, d)
    return out


def _combo_key_for_components(keys: list[str]) -> str:
    key_set = set(keys)
    for combo_key, comps in COMBO_COMPONENTS.items():
        if set(comps) == key_set:
            return combo_key
    return "+".join(sorted(keys))


# ── Convenience entry point ──────────────────────────────────────────────────


def build_combo_pmf(
    combo: str,
    components_pmf: dict[str, StatPMF],
    correlation: Optional[np.ndarray] = None,
    n_draws: int = 20_000,
    rng: Optional[np.random.Generator] = None,
) -> Optional[StatPMF]:
    """Top-level helper: return combo PMF if all components are present."""
    expected = COMBO_COMPONENTS.get(combo)
    if expected is None:
        raise ValueError(f"Unknown combo: {combo}")
    if any(e not in components_pmf for e in expected):
        return None
    ordered = {e: components_pmf[e] for e in expected}
    if correlation is None:
        return combo_pmf_independence(ordered)
    return combo_pmf_copula(ordered, correlation=correlation, n_draws=n_draws, rng=rng)
