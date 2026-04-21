"""De-vigged market baseline reconstruction.

Provides two entry points:

* `devigged_main_line(over_odds, under_odds)`   — two-way de-vig for a posted
  main line. Returns a fair P(over) / P(under) pair summing to 1.

* `market_implied_cdf_from_alt_lines(quotes)`   — monotone CDF reconstruction
  from a ladder of alt-lines. Each quote contributes a point (line, P(over)).
  P(stat <= line) = 1 - P(over at line); we pool these across offered lines
  to fit a monotone non-decreasing CDF via isotonic regression on the
  de-vigged over-probabilities.

Both functions are used by the diagnostics + eval scripts to build a
matched market baseline against which the model is scored. No claims about
"better than market" are permitted without running through these.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


def american_to_implied(odds: float) -> float:
    o = float(odds)
    if o > 0:
        return 100.0 / (o + 100.0)
    return abs(o) / (abs(o) + 100.0)


def devigged_main_line(over_odds: float, under_odds: float) -> tuple[float, float]:
    """Two-way multiplicative de-vig of an over/under pair.

    Returns (p_over_fair, p_under_fair). Both lie in (0, 1) and sum to 1.
    """
    po = american_to_implied(over_odds)
    pu = american_to_implied(under_odds)
    s = po + pu
    if s <= 0:
        return 0.5, 0.5
    return float(po / s), float(pu / s)


@dataclass
class AltQuote:
    """Quote on one offered line for a single player/stat/game."""
    line: float
    over_odds: float
    under_odds: float


def market_implied_cdf_from_alt_lines(
    quotes: Sequence[AltQuote],
    support_max: int,
) -> np.ndarray | None:
    """Reconstruct a monotone non-decreasing market CDF over integer support.

    Algorithm:
      1. For each quote, compute de-vigged p_under.
         p_under = P(stat <= line - 1)  when line is half-integer (line = k + 0.5)
                 = P(stat <  line) + 0.5 * P(stat == line)  when line is integer.
         We treat all lines as half-integer (standard for props) and use
         knots at `floor(line)`.
      2. Collect (knot, p_under) pairs.
      3. Fit isotonic regression on (knot, p_under) to guarantee monotone
         non-decreasing over the support.
      4. Differences give a valid PMF that sums to 1 within numerical error.

    Returns the CDF array of length (support_max + 1), or None when fewer
    than 2 distinct lines are offered (not enough to fit a ladder).
    """
    if len(quotes) < 2:
        return None
    from sklearn.isotonic import IsotonicRegression

    knots: list[tuple[int, float]] = []
    for q in quotes:
        _, pu = devigged_main_line(q.over_odds, q.under_odds)
        # Half-integer lines map to integer knot = floor(line).
        knot = int(np.floor(float(q.line)))
        if 0 <= knot <= support_max:
            knots.append((knot, float(pu)))
    if len(knots) < 2:
        return None

    # If multiple quotes share a knot, average their p_under values.
    from collections import defaultdict
    by_knot: dict[int, list[float]] = defaultdict(list)
    for k, p in knots:
        by_knot[k].append(p)
    xs = sorted(by_knot.keys())
    ys = [float(np.mean(by_knot[k])) for k in xs]
    # Anchor endpoints: CDF at -0.5 = 0, CDF at support_max = 1.
    xs_full = [-1] + xs + [support_max]
    ys_full = [0.0] + ys + [1.0]
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip",
                             increasing=True).fit(xs_full, ys_full)
    grid = np.arange(0, support_max + 1)
    cdf = np.clip(iso.predict(grid), 0.0, 1.0)
    # Enforce CDF = 1 at the final support point.
    if cdf[-1] < 1.0:
        cdf[-1] = 1.0
    return cdf.astype(float)


def market_pmf_from_cdf(cdf: np.ndarray) -> np.ndarray:
    """Convert a monotone CDF over integer support to a valid PMF."""
    pmf = np.diff(np.concatenate([[0.0], cdf]))
    pmf = np.clip(pmf, 0.0, None)
    s = pmf.sum()
    if s > 0:
        pmf = pmf / s
    return pmf


def market_over_prob_at_line(
    over_odds: float, under_odds: float,
) -> float:
    """Convenience: return the de-vigged P(over) at a single posted line."""
    po, _ = devigged_main_line(over_odds, under_odds)
    return po
