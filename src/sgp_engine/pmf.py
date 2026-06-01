from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np


EPS = 1e-12


def parse_pmf(value: Any, *, domain_max: int | None = None) -> np.ndarray:
    """Parse a PMF from JSON/dict/list/array and return a normalized numpy array.

    Accepts:
      - JSON string like {"0": 0.1, "1": 0.2}
      - dict with int/string keys
      - list/array of probabilities
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        raise ValueError("Missing PMF")

    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError("Empty PMF string")
        value = json.loads(value)

    if isinstance(value, Mapping):
        items = {}
        max_k = -1
        for k, p in value.items():
            try:
                kk = int(float(k))
            except Exception as exc:
                raise ValueError(f"Invalid PMF key {k!r}") from exc
            pp = float(p)
            if kk < 0:
                continue
            items[kk] = pp
            max_k = max(max_k, kk)
        if domain_max is not None:
            max_k = max(max_k, int(domain_max))
        arr = np.zeros(max_k + 1, dtype=float)
        for k, p in items.items():
            if k < len(arr):
                arr[k] = p
    else:
        arr = np.asarray(value, dtype=float).copy()
        if domain_max is not None and len(arr) <= domain_max:
            out = np.zeros(domain_max + 1, dtype=float)
            out[: len(arr)] = arr
            arr = out

    if arr.ndim != 1 or len(arr) == 0:
        raise ValueError("PMF must be a 1D non-empty array")
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    arr[arr < 0] = 0.0
    total = arr.sum()
    if total <= EPS:
        raise ValueError("PMF has no positive probability mass")
    return arr / total


def pmf_to_json(pmf: np.ndarray, *, min_prob: float = 0.0) -> str:
    arr = parse_pmf(pmf)
    return json.dumps({int(k): float(p) for k, p in enumerate(arr) if p > min_prob}, sort_keys=True)


def cdf_from_pmf(pmf: np.ndarray) -> np.ndarray:
    return np.cumsum(parse_pmf(pmf))


def quantile_int_from_u(pmf: np.ndarray, u: np.ndarray | float) -> np.ndarray:
    """Inverse CDF sample for integer PMF. u is clipped to (0, 1)."""
    arr = parse_pmf(pmf)
    cdf = np.cumsum(arr)
    uu = np.clip(u, EPS, 1.0 - EPS)
    return np.searchsorted(cdf, uu, side="left").astype(np.int16)


def event_probability(pmf: np.ndarray, line: float, side: str) -> float:
    """Return P(stat > line) for over and P(stat < line) for under.

    Push is excluded only naturally by integer comparison: integer outcome equal to integer line
    is neither over nor under.
    """
    arr = parse_pmf(pmf)
    ks = np.arange(len(arr), dtype=float)
    side_l = side.lower()
    if side_l in {"over", "o", ">" , "gt"}:
        return float(arr[ks > float(line)].sum())
    if side_l in {"under", "u", "<", "lt"}:
        return float(arr[ks < float(line)].sum())
    if side_l in {"ge", ">="}:
        return float(arr[ks >= float(line)].sum())
    if side_l in {"le", "<="}:
        return float(arr[ks <= float(line)].sum())
    raise ValueError(f"Unknown side {side!r}")


def validate_pmf(pmf: np.ndarray, *, tolerance: float = 1e-6) -> dict[str, Any]:
    arr = np.asarray(pmf, dtype=float)
    return {
        "valid": bool(arr.ndim == 1 and len(arr) > 0 and np.all(np.isfinite(arr)) and np.all(arr >= -tolerance) and abs(arr.sum() - 1.0) <= tolerance),
        "sum": float(np.nansum(arr)),
        "min": float(np.nanmin(arr)) if len(arr) else np.nan,
        "max": float(np.nanmax(arr)) if len(arr) else np.nan,
        "domain_max": int(len(arr) - 1) if len(arr) else None,
    }


def rank_to_uniform(values: np.ndarray) -> np.ndarray:
    """Stable rank transform to approximately uniform(0,1)."""
    x = np.asarray(values)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    ranks[order] = np.arange(len(x), dtype=float)
    return (ranks + 0.5) / max(len(x), 1)


def push_mass(pmf_array: np.ndarray, line: float) -> float:
    """Return probability mass exactly at line; 0.0 if line is not an exact integer."""
    arr = parse_pmf(pmf_array)
    line_f = float(line)
    if line_f == float(int(line_f)):
        idx = int(line_f)
        if 0 <= idx < len(arr):
            return float(arr[idx])
    return 0.0


def inverse_cdf_from_pmf(pmf_array: np.ndarray, domain_min: int = 0) -> np.ndarray:
    """Return the integer outcome array [domain_min, domain_min+1, ...] for CDF lookup.

    Each index i maps to the outcome domain_min+i, which pairs with cumsum(pmf)[i]
    to form a complete inverse-CDF table.
    """
    arr = parse_pmf(pmf_array)
    return np.arange(domain_min, domain_min + len(arr), dtype=np.int64)


def rank_remap_samples_to_pmf(
    raw_samples: np.ndarray,
    pmf_array: np.ndarray,
    domain_min: int = 0,
) -> np.ndarray:
    """Rank-remap raw_samples onto the PMF's inverse-CDF to produce anchored integer outcomes.

    Takes a 1D int/float array of raw simulation samples, converts them to pseudo-uniform
    ranks, then maps through the PMF's inverse-CDF to produce marginal-anchored outcomes.
    Preserves rank order of raw_samples while matching the delivered PMF distribution.
    """
    arr = parse_pmf(pmf_array)
    u = rank_to_uniform(np.asarray(raw_samples, dtype=float))
    return (quantile_int_from_u(arr, u).astype(np.int64) + int(domain_min)).astype(np.int64)


@dataclass(frozen=True)
class PMFEvent:
    player_id: str
    stat: str
    line: float
    side: str

    def probability(self, pmf: np.ndarray) -> float:
        return event_probability(pmf, self.line, self.side)
