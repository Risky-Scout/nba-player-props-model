"""NBA Props Model — combo PMFs derived from joint samples (M5A).

For each (player_id, game_id) group in a joint stat samples table, sum
the component stat columns within the SAME simulation_id and histogram
the resulting outcomes into an empirical PMF. This preserves the
within-game correlation structure that np.convolve / independence loses.

Mission-required combos:
    stocks  (mission: stl_blk)     = stl + blk
    pa      (mission: pts_ast)     = pts + ast
    pr      (mission: pts_reb)     = pts + reb
    pra     (mission: pts_reb_ast) = pts + reb + ast

Optional non-mission combo:
    ra      (mission: reb_ast)     = reb + ast

This module is the M5A foundation. It is consumed by
scripts/build_combo_pmfs_from_joint_samples.py. M5A does NOT wire combo
PMFs into production delivery — that is M5B/later. M6 handles
calibration of combo PMFs across stat x role cells.
"""
from __future__ import annotations

import logging
from typing import Iterable

import numpy as np
import pandas as pd

from nba_props_model.targets import (
    COMBO_COMPONENTS,
    CANONICAL_TO_MISSION,
    MISSION_TO_CANONICAL,
)

logger = logging.getLogger(__name__)


# ── Versions and labels ────────────────────────────────────────────────────

JOINT_COMBO_PMF_VERSION = "joint_combo_pmf_v1"
MODEL_VERSION_TAG = "joint_combo_pmf_v1"
CALIBRATION_STATUS_PENDING_M6 = "pending_m6_stat_role_calibration"

# Mission-required combos per acceptance section 1 + master prompt section 5.
DEFAULT_MISSION_COMBOS: tuple[str, ...] = ("stocks", "pa", "pr", "pra")
# All combos this module knows how to build (canonical names).
ALL_KNOWN_COMBOS: tuple[str, ...] = ("stocks", "pa", "pr", "pra", "ra")


# ── Component domain bounds ────────────────────────────────────────────────

# Pull authoritative values from existing modules where available; provide
# fallbacks only for any component not defined upstream so this module is
# self-contained.
try:
    from nba_props_model.models.simulation import DOMAIN_MAX as _MAIN_DM
except ImportError:  # pragma: no cover
    _MAIN_DM = {}
try:
    from nba_props_model.models.sparse_hurdle import DOMAIN_MAX as _SPARSE_DM
except ImportError:  # pragma: no cover
    _SPARSE_DM = {}

_FALLBACK_DOMAIN_MAX: dict[str, int] = {
    "pts": 80, "reb": 30, "ast": 25, "tov": 12, "fg3m": 14, "stl": 10, "blk": 10,
}

COMPONENT_DOMAIN_MAX: dict[str, int] = {}
for _s in ("pts", "reb", "ast", "tov", "fg3m", "stl", "blk"):
    if _s in _SPARSE_DM:
        COMPONENT_DOMAIN_MAX[_s] = int(_SPARSE_DM[_s])
    elif _s in _MAIN_DM:
        COMPONENT_DOMAIN_MAX[_s] = int(_MAIN_DM[_s])
    else:
        COMPONENT_DOMAIN_MAX[_s] = int(_FALLBACK_DOMAIN_MAX[_s])


def combo_domain_max(canonical_combo: str) -> int:
    """Maximum possible value for a canonical combo stat = sum of component maxes."""
    if canonical_combo not in COMBO_COMPONENTS:
        raise ValueError(f"unknown canonical combo: {canonical_combo!r}")
    components = COMBO_COMPONENTS[canonical_combo]
    return int(sum(COMPONENT_DOMAIN_MAX[c] for c in components))


# ── Name resolution (canonical <-> mission alias) ──────────────────────────


def normalize_combo_name(name: str) -> str:
    """Resolve any combo name (canonical OR mission alias) to canonical form.

    Examples:
        normalize_combo_name("stocks")       -> "stocks"
        normalize_combo_name("stl_blk")      -> "stocks"
        normalize_combo_name("pts_reb_ast")  -> "pra"
    """
    if name in COMBO_COMPONENTS:
        return name
    if name in MISSION_TO_CANONICAL:
        return MISSION_TO_CANONICAL[name]
    raise ValueError(f"unknown combo name: {name!r}")


def mission_alias_for(canonical_combo: str) -> str:
    """Return mission-style alias for a canonical combo (or input if no alias)."""
    return CANONICAL_TO_MISSION.get(canonical_combo, canonical_combo)


# ── Empirical PMF construction ─────────────────────────────────────────────


def empirical_combo_pmf_from_samples(
    samples: pd.DataFrame,
    canonical_combo: str,
) -> np.ndarray:
    """Build empirical PMF for ``canonical_combo`` from one (player, game) group.

    Each row of ``samples`` must correspond to one simulation_id and contain
    the component columns for the requested combo. Components are summed
    ROW-WISE (preserving within-simulation correlation), then the integer
    outcomes are histogrammed across simulations into a normalized PMF.

    Args:
        samples: DataFrame for a single (player_id, game_id) group; must
                 contain all component columns for ``canonical_combo``.
        canonical_combo: One of COMBO_COMPONENTS keys.

    Returns:
        np.ndarray of length combo_domain_max(canonical_combo) + 1, summing
        to ~1.0 (within float64 precision).
    """
    if canonical_combo not in COMBO_COMPONENTS:
        raise ValueError(f"unknown canonical combo: {canonical_combo!r}")
    if len(samples) == 0:
        raise ValueError("samples is empty")
    components = COMBO_COMPONENTS[canonical_combo]
    missing = [c for c in components if c not in samples.columns]
    if missing:
        raise ValueError(
            f"samples missing component columns for {canonical_combo}: {missing}"
        )

    # Sum components ROW-WISE: each row is one simulation_id; row-wise sum
    # preserves within-sim correlation across components.
    combo_values = samples[list(components)].to_numpy(dtype=np.int64).sum(axis=1)

    support_max = combo_domain_max(canonical_combo)
    n_over = int((combo_values > support_max).sum())
    n_neg = int((combo_values < 0).sum())
    if n_over > 0:
        logger.warning(
            f"{n_over}/{len(combo_values)} samples exceed support_max={support_max} "
            f"for {canonical_combo} -- clipping"
        )
    if n_neg > 0:
        logger.warning(
            f"{n_neg}/{len(combo_values)} samples are negative for {canonical_combo} "
            f"-- clipping to 0"
        )
    combo_int = np.clip(combo_values, 0, support_max).astype(np.int64)

    counts = np.bincount(combo_int, minlength=support_max + 1).astype(np.float64)
    total = counts.sum()
    if total <= 0:
        # Degenerate; should not happen for valid input
        pmf = np.zeros_like(counts)
        pmf[0] = 1.0
        return pmf
    pmf = counts / total
    return pmf


def build_combo_pmfs_for_group(
    group: pd.DataFrame,
    combos: Iterable[str] = DEFAULT_MISSION_COMBOS,
) -> dict:
    """Build empirical PMFs for all requested combos in one (player, game) group.

    Args:
        group: DataFrame for one (player_id, game_id) group.
        combos: Iterable of combo names; canonical names are used as keys
                in the returned dict. Mission aliases on input are resolved.

    Returns:
        dict mapping canonical_combo_name -> np.ndarray PMF
    """
    out: dict = {}
    for c in combos:
        canonical = normalize_combo_name(c)
        out[canonical] = empirical_combo_pmf_from_samples(group, canonical)
    return out
