"""Joint sampler — minutes-shared joint samples across NBA Props base stats.

NBA Props Model — Milestone 3 step 2 module.

ADDITIVE: does not modify simulation.py, sparse_hurdle.py, fg3m_hurdle.py,
or any pipeline. Reuses existing primitives.

DESIGN
------
The existing simulate_stat_pmf in nba_props_model.models.simulation re-samples
minutes inside each per-stat call (line 132), so even pts and reb don't share
a minutes draw when called from simulate_all_main_stats. This module fixes
that for combo PMF construction (M5) by:

  1. Drawing minutes ONCE per simulation_id from the same MinutesDistribution.
  2. For pts/reb/ast/tov: sampling per-minute rates given that shared minutes
     vector — sampling method tag: "minutes_shared_rate_quantile_v1".
  3. For fg3m: sampling from fg3m_hurdle_model.pmf via inverse-CDF.
     Independent of minutes — sampling method tag: "independent_hurdle_pmf_v1".
  4. For stl/blk: sampling from sparse_hurdle.hurdle_pmf via inverse-CDF.
     Independent of minutes — sampling method tag: "independent_hurdle_pmf_v1".

LIMITATIONS
-----------
- pts/reb/ast/tov share minutes; given minutes they are conditionally
  independent (matching the existing simulator's implicit assumption).
  Residual stat-stat correlation NOT captured — that is M5 territory
  via the Gaussian-copula path in correlation/sgp_engine.py.
- fg3m/stl/blk samples are drawn from their hurdle PMFs INDEPENDENT of
  the minutes vector AND of each other. Proper minutes-driven stl/blk
  rate models are M4. Until then, downstream consumers (M5 combo PMF
  construction) must NOT treat stl_blk as a production-elite correlated
  combo — see COMBO_READINESS_NOTE.

REGISTRY PARITY
---------------
ALL_BASE_STATS_JOINT is defined explicitly in registry order
(matches nba_props_model.targets.BASE_STATS_FULL) so the dispatcher
manifest's "base_stats" field aligns with the canonical target list.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from nba_props_model.models.minutes import MinutesDistribution
from nba_props_model.models.simulation import (
    DOMAIN_MAX as RATE_DOMAIN_MAX,
    _rate_samples_from_quantiles,
)
from nba_props_model.models.rate_models import rate_quantiles
from nba_props_model.models import sparse_hurdle

logger = logging.getLogger(__name__)

# ── Public version + labeling constants (consumed by the dispatcher) ────

JOINT_SAMPLER_VERSION = "joint_sampler_v1"
RATE_STATS_SAMPLING_METHOD = "minutes_shared_rate_quantile_v1"
HURDLE_STATS_SAMPLING_METHOD = "independent_hurdle_pmf_v1"
COMBO_READINESS_NOTE = (
    "stl_blk correlation is not production-elite until M4 minutes-driven "
    "stl/blk sampling lands."
)

# ── Stat partitions (registry-aligned ordering) ─────────────────────────

# Sampled via minutes × rate (matches simulate_stat_pmf math).
RATE_STATS_JOINT: tuple[str, ...] = ("pts", "reb", "ast", "tov")
# Sampled from per-stat hurdle PMF (independent of minutes in M3).
HURDLE_STATS_JOINT: tuple[str, ...] = ("fg3m", "stl", "blk")
# All 7 base stats persisted — registry order, matching
# nba_props_model.targets.BASE_STATS_FULL exactly.
ALL_BASE_STATS_JOINT: tuple[str, ...] = (
    "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
)


def _sample_from_pmf(
    pmf: Optional[np.ndarray], n_draws: int, rng: np.random.Generator,
) -> np.ndarray:
    """Draw integer samples from a discrete PMF on {0, ..., len(pmf)-1}.

    Returns a (n_draws,) int array. If pmf is None / empty / non-finite
    sum, returns zeros (deterministic graceful fallback so the caller
    can still emit a row rather than dropping the player-game).
    """
    if pmf is None:
        return np.zeros(n_draws, dtype=int)
    arr = np.asarray(pmf, dtype=float).ravel()
    if arr.size == 0:
        return np.zeros(n_draws, dtype=int)
    s = arr.sum()
    if not (np.isfinite(s) and s > 0):
        return np.zeros(n_draws, dtype=int)
    arr = np.clip(arr, 0.0, None)
    arr = arr / arr.sum()
    return rng.choice(len(arr), size=n_draws, p=arr).astype(int)


def simulate_joint_stat_samples(
    minutes_dist: MinutesDistribution,
    feature_row: dict,
    n_draws: int,
    rng: Optional[np.random.Generator] = None,
    fg3m_hurdle_model=None,
) -> Optional[dict[str, np.ndarray]]:
    """Draw n_draws joint samples sharing one minutes vector across stats.

    Returns a dict of equal-length np.ndarray arrays:
        {
            "minutes":       (n_draws,) float
            "inactive_flag": (n_draws,) bool   # True where minutes == 0
            "pts":           (n_draws,) int
            "reb":           (n_draws,) int
            "ast":           (n_draws,) int
            "fg3m":          (n_draws,) int
            "tov":           (n_draws,) int
            "stl":           (n_draws,) int
            "blk":           (n_draws,) int
        }

    Returns None if any RATE stat lacks rate_quantiles() (matching the
    existing simulator's contract: callers fall back to a prior path).

    Sampling structure:
      - minutes is sampled ONCE → shared across pts/reb/ast/tov
      - rates per stat are sampled from per-stat quantile ladders
        (reuses simulation._rate_samples_from_quantiles)
      - integer totals from rng.poisson(mins * rates), clipped to DOMAIN_MAX
      - fg3m: rng.choice(domain, p=fg3m_hurdle.pmf) — independent of minutes
      - stl/blk: rng.choice(domain, p=hurdle_pmf) — independent of minutes

    See module docstring for the LIMITATIONS section.
    """
    if rng is None:
        rng = np.random.default_rng()

    # 1. Sample minutes ONCE — shared driver for all RATE stats.
    mins = minutes_dist.sample(n_draws, rng).astype(float)
    inactive_flag = (mins == 0.0)

    out: dict[str, np.ndarray] = {
        "minutes": mins,
        "inactive_flag": inactive_flag,
    }

    # 2. RATE stats: rates given the SHARED minutes vector.
    for stat in RATE_STATS_JOINT:
        q = rate_quantiles(stat, feature_row)
        if q is None:
            return None  # caller falls back; matches simulate_stat_pmf contract
        rates = _rate_samples_from_quantiles(q, n_draws, rng)
        raw_totals = np.clip(mins * rates, 0.0, RATE_DOMAIN_MAX[stat])
        integer_totals = rng.poisson(raw_totals).astype(int)
        integer_totals = np.clip(integer_totals, 0, RATE_DOMAIN_MAX[stat])
        out[stat] = integer_totals

    # 3. fg3m from fg3m_hurdle_model.pmf if a model is provided, independent.
    if fg3m_hurdle_model is not None:
        try:
            fg3m_pmf = fg3m_hurdle_model.pmf(feature_row)
            out["fg3m"] = _sample_from_pmf(fg3m_pmf, n_draws, rng)
        except Exception as e:
            logger.debug(f"fg3m_hurdle_model.pmf failed: {e}")
            out["fg3m"] = np.zeros(n_draws, dtype=int)
    else:
        out["fg3m"] = np.zeros(n_draws, dtype=int)

    # 4. HURDLE stats: stl/blk from sparse_hurdle.hurdle_pmf, independent.
    for stat in ("stl", "blk"):
        try:
            hpmf = sparse_hurdle.hurdle_pmf(stat, feature_row)
        except Exception as e:
            logger.debug(f"sparse_hurdle.hurdle_pmf failed for {stat}: {e}")
            hpmf = None
        out[stat] = _sample_from_pmf(hpmf, n_draws, rng)

    return out
