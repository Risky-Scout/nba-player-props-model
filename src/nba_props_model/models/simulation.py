"""
NBA Props Model — minutes x rate PMF simulation layer.

Combines:
  * MinutesDistribution  from `nba_props_model.models.minutes`
  * per-minute rate quantile ladder from
    `nba_props_model.models.rate_models.rate_quantiles`

to produce a full discrete PMF over non-negative integer stat totals for
{pts, reb, ast, tov}. Used by the prediction pipeline in place of the
direct-total quantile path the old pipeline relied on.

The PMF / CDF produced here is the input to both
`nba_props_model.calibration.pmf_calibration` (for OOF CDF calibration)
and `nba_props_model.pipelines.predict` (for fair probabilities at
offered lines).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from nba_props_model.models.minutes import MinutesDistribution
from nba_props_model.models.rate_models import RATE_STATS, rate_quantiles

logger = logging.getLogger(__name__)

DEFAULT_DRAWS = 5_000
# Hard upper domain for the discrete PMF; sufficient for any NBA stat total.
DOMAIN_MAX = {
    "pts": 80,
    "reb": 30,
    "ast": 25,
    "tov": 12,
}


@dataclass
class StatPMF:
    """Discrete stat PMF over {0, 1, ..., domain_max} with helpers.

    Attributes
    ----------
    stat : str
    pmf : np.ndarray of shape (domain_max + 1,) summing to 1.0
    """
    stat: str
    pmf: np.ndarray

    @property
    def domain(self) -> np.ndarray:
        return np.arange(len(self.pmf))

    def cdf(self, x: float) -> float:
        """P(stat <= x) for an integer-valued stat PMF.

        Discrete step function. For integer NBA stats the CDF jumps at
        each integer atom and is constant between atoms. The previous
        piecewise-linear implementation was incorrect for integer
        outcomes and distorted probabilities at half-point lines.
        """
        if x < 0:
            return 0.0
        k = int(np.floor(x))
        if k >= len(self.pmf) - 1:
            return 1.0
        return float(np.cumsum(self.pmf)[k])

    def prob_over(self, line: float) -> float:
        """Book convention: OVER hits when stat > line (strict)."""
        # For integer stats with .5 lines, this is unambiguous; for whole-
        # number lines it is P(stat > line) = 1 - P(stat <= line).
        return float(1.0 - self.cdf(line))

    def prob_under(self, line: float) -> float:
        return 1.0 - self.prob_over(line)

    def mean(self) -> float:
        return float(np.sum(self.pmf * self.domain))

    def std(self) -> float:
        mu = self.mean()
        return float(np.sqrt(np.sum(self.pmf * (self.domain - mu) ** 2)))


def _rate_samples_from_quantiles(
    q: dict[int, float], n: int, rng: np.random.Generator,
) -> np.ndarray:
    """Inverse-CDF sample from a quantile table (rates >= 0)."""
    sorted_keys = sorted(q.keys())
    xs = [max(0.0, q[k]) for k in sorted_keys]
    ys = [k / 100.0 for k in sorted_keys]
    # Anchor at tails: at q=0 assume zero rate; at q=1 assume 1.2x q90.
    xs = [0.0] + xs + [max(xs[-1] * 1.2, xs[-1] + 0.05)]
    ys = [0.0] + ys + [1.0]

    u = rng.uniform(0, 1, size=n)
    out = np.empty(n, dtype=float)
    xs_a = np.array(xs)
    ys_a = np.array(ys)
    for i, ui in enumerate(u):
        if ui <= ys_a[0]:
            out[i] = xs_a[0]
            continue
        if ui >= ys_a[-1]:
            out[i] = xs_a[-1]
            continue
        idx = int(np.searchsorted(ys_a, ui))
        y0, y1 = ys_a[idx - 1], ys_a[idx]
        x0, x1 = xs_a[idx - 1], xs_a[idx]
        if y1 == y0:
            out[i] = x1
        else:
            out[i] = x0 + (x1 - x0) * (ui - y0) / (y1 - y0)
    return out


def simulate_stat_pmf(
    stat: str,
    minutes_dist: MinutesDistribution,
    feature_row: dict,
    n_draws: int = DEFAULT_DRAWS,
    rng: Optional[np.random.Generator] = None,
    rate_q_override: Optional[dict[int, float]] = None,
) -> Optional[StatPMF]:
    """Simulate the stat PMF via minutes x per-minute rate.

    Returns None if the per-stat rate artifacts are not yet trained —
    callers fall back to their prior direct-total path in that case.
    """
    if stat not in DOMAIN_MAX:
        raise ValueError(f"Unsupported stat for simulation: {stat}")
    if rng is None:
        rng = np.random.default_rng()

    q = rate_q_override or rate_quantiles(stat, feature_row)
    if q is None:
        return None

    mins = minutes_dist.sample(n_draws, rng)
    rates = _rate_samples_from_quantiles(q, n_draws, rng)
    raw_totals = np.clip(mins * rates, 0.0, DOMAIN_MAX[stat])

    # Discretize to integer totals with a Poisson-ish noise layer:
    #   draw from Poisson(lambda = raw_total) to reflect within-minute
    #   arrival noise on top of the rate uncertainty. Keeps tails realistic
    #   without requiring a second parametric assumption.
    integer_totals = rng.poisson(raw_totals).astype(int)
    integer_totals = np.clip(integer_totals, 0, DOMAIN_MAX[stat])

    counts = np.bincount(integer_totals, minlength=DOMAIN_MAX[stat] + 1)
    pmf = counts.astype(float) / counts.sum()
    return StatPMF(stat=stat, pmf=pmf)


def simulate_all_main_stats(
    minutes_dist: MinutesDistribution,
    feature_row: dict,
    n_draws: int = DEFAULT_DRAWS,
    rng: Optional[np.random.Generator] = None,
) -> dict[str, StatPMF]:
    """Run simulate_stat_pmf for each main counting stat with a shared RNG."""
    if rng is None:
        rng = np.random.default_rng()
    out: dict[str, StatPMF] = {}
    for stat in RATE_STATS:
        pmf = simulate_stat_pmf(stat, minutes_dist, feature_row, n_draws, rng)
        if pmf is not None:
            out[stat] = pmf
    return out
