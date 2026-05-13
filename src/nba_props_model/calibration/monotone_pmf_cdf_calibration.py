"""Monotone PMF adjustment via cumulative binning (lightweight).

Full isotonic on CDF is expensive; this module exposes a hook for future
`sklearn.isotonic.IsotonicRegression` fits. For v0, `apply_identity` returns pmf.
"""
from __future__ import annotations


def apply_identity(pmf: dict[int, float]) -> dict[int, float]:
    return dict(pmf)
