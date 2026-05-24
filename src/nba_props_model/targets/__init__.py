"""Centralized target-stat registry for the NBA Props Model.

Single source of truth for the target universe (base + combo stats),
their components, and the mapping between internal canonical names
and external mission-spec alias names.

This module is ADDITIVE. Existing constants in:
  - src/nba_props_model/training_automation.py (SUPPORTED_STATS, full 7-stat)
  - src/nba_props_model/correlation/sgp_engine.py (COMBO_STATS, COMBO_COMPONENTS — full 5-combo)
  - src/nba_props_model/features/engineering.py  (COMBO_STATS duplicate of sgp_engine)
  - src/nba_props_model/models/combos.py         (COMBO_COMPONENTS — partial: 4 combos, missing "stocks")
  - src/nba_props_model/pipelines/pmf_predict.py (COMBO_STATS derived from combos.py — also partial)
remain in place unchanged. New code SHOULD prefer importing from this
module. Migration of existing call sites is OUT OF SCOPE for this commit.

Naming convention:
  - "canonical" name: the internal short name used by the codebase
    (e.g., "pra", "stocks").
  - "mission" name:   the external descriptive name from the mission
    spec (e.g., "pts_reb_ast", "stl_blk").
Helper functions accept either form and return the requested form.

Cross-source consistency invariants (verified by smoke check):
  - BASE_STATS_FULL == tuple(training_automation.SUPPORTED_STATS)
  - models.combos.COMBO_COMPONENTS is a subset of registry COMBO_COMPONENTS
    (missing only "stocks"); for shared keys the values match
  - sgp_engine.COMBO_STATS == COMBO_STATS_CANONICAL (same order)
  - sgp_engine.COMBO_COMPONENTS keys == registry COMBO_COMPONENTS keys
    (full 5-combo universe); for all keys the values match

Note on 5-stat scattered hardcoded literals (out of M2 scope):
  scripts/build_daily_pmf_delivery.py:86
  scripts/refresh_daily_inputs.py:77
  scripts/verify_woo_dashboard_render_contract.py:56
  These three files have local 5-stat literals that diverge from the
  canonical 7-stat training_automation.SUPPORTED_STATS. Reconciling them
  is deferred to a later milestone (likely after M4 ships stl/blk PMFs).
"""
from __future__ import annotations

from typing import Iterable

# ── Base stats ───────────────────────────────────────────────────────────
# Mission spec requires 7 base stats. training_automation.SUPPORTED_STATS
# already exposes all 7. PMF role-aware calibrators currently exist for
# the 5-stat subset (pts/reb/ast/fg3m/tov); stl/blk role-aware PMFs are
# scheduled for Milestone 4 (hurdle models for stl/blk DO exist in
# artifacts/models/ but are not yet plumbed through role-aware PMF
# calibration end-to-end).

BASE_STATS_FULL: tuple[str, ...] = (
    "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
)
BASE_STATS_PMF_TRAINED: tuple[str, ...] = (
    "pts", "reb", "ast", "fg3m", "tov",
)
BASE_STATS_PMF_PENDING: tuple[str, ...] = (
    "stl", "blk",
)

# ── Combo stats (canonical names match the codebase) ─────────────────────

COMBO_STATS_CANONICAL: tuple[str, ...] = (
    "pra",     # pts + reb + ast
    "pr",      # pts + reb
    "pa",      # pts + ast
    "ra",      # reb + ast
    "stocks",  # stl + blk
)

COMBO_COMPONENTS: dict[str, tuple[str, ...]] = {
    "pra":    ("pts", "reb", "ast"),
    "pr":     ("pts", "reb"),
    "pa":     ("pts", "ast"),
    "ra":     ("reb", "ast"),
    "stocks": ("stl", "blk"),
}

# ── Bidirectional alias mapping ──────────────────────────────────────────

CANONICAL_TO_MISSION: dict[str, str] = {
    "pra":    "pts_reb_ast",
    "pr":     "pts_reb",
    "pa":     "pts_ast",
    "ra":     "reb_ast",
    "stocks": "stl_blk",
}
MISSION_TO_CANONICAL: dict[str, str] = {v: k for k, v in CANONICAL_TO_MISSION.items()}

# ── Mission-required subset: 7 base + 5 combo = 12 (includes RA / reb_ast) ──

MISSION_REQUIRED_BASE: tuple[str, ...] = BASE_STATS_FULL  # all 7
MISSION_REQUIRED_COMBOS_CANONICAL: tuple[str, ...] = (
    "stocks", "pa", "pr", "ra", "pra",
)
MISSION_REQUIRED_COMBOS_MISSION: tuple[str, ...] = (
    "stl_blk", "pts_ast", "pts_reb", "reb_ast", "pts_reb_ast",
)
MISSION_REQUIRED_TARGETS_CANONICAL: tuple[str, ...] = (
    MISSION_REQUIRED_BASE + MISSION_REQUIRED_COMBOS_CANONICAL
)
MISSION_REQUIRED_TARGETS_MISSION: tuple[str, ...] = (
    MISSION_REQUIRED_BASE + MISSION_REQUIRED_COMBOS_MISSION
)

# ── Delivery-required canonical stat list (authoritative 12-stat set) ────
# Every delivery output, PMF prediction, stat-role matrix, market comparison,
# calibration report, and dashboard export MUST include all 12 of these stats.
# Use this constant instead of hardcoded stat lists anywhere stats are iterated.
DELIVERY_REQUIRED_TARGETS_CANONICAL: tuple[str, ...] = (
    "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
    "stocks", "pa", "pr", "ra", "pra",
)

# ── Full codebase target universe (12 = 7 base + 5 combo, includes "ra") ─

ALL_TARGETS_CANONICAL: tuple[str, ...] = BASE_STATS_FULL + COMBO_STATS_CANONICAL
ALL_TARGETS_MISSION: tuple[str, ...] = BASE_STATS_FULL + tuple(
    CANONICAL_TO_MISSION[c] for c in COMBO_STATS_CANONICAL
)
ALL_KNOWN_NAMES: frozenset[str] = frozenset(
    list(ALL_TARGETS_CANONICAL) + list(ALL_TARGETS_MISSION)
)


# ── Helpers ──────────────────────────────────────────────────────────────


_EXTRA_ALIASES: dict[str, str] = {
    # All known surface forms for ra (rebounds + assists)
    "reb_ast":           "ra",
    "reb+ast":           "ra",
    "rebounds_assists":  "ra",
    "r+a":               "ra",
}


def canonical(stat: str) -> str:
    """Return the internal canonical name (accepts canonical, mission, or extended alias).

    >>> canonical("pra")
    'pra'
    >>> canonical("pts_reb_ast")
    'pra'
    >>> canonical("stl_blk")
    'stocks'
    >>> canonical("pts")
    'pts'
    >>> canonical("reb_ast")
    'ra'
    >>> canonical("rebounds_assists")
    'ra'
    >>> canonical("reb+ast")
    'ra'
    """
    if stat in MISSION_TO_CANONICAL:
        return MISSION_TO_CANONICAL[stat]
    if stat in _EXTRA_ALIASES:
        return _EXTRA_ALIASES[stat]
    return stat


def mission_name(stat: str) -> str:
    """Return the mission-spec alias (accepts canonical or mission).

    Base stats (no alias) return themselves.

    >>> mission_name("pra")
    'pts_reb_ast'
    >>> mission_name("pts_reb_ast")
    'pts_reb_ast'
    >>> mission_name("stocks")
    'stl_blk'
    >>> mission_name("pts")
    'pts'
    """
    s = canonical(stat)
    return CANONICAL_TO_MISSION.get(s, s)


def is_combo(stat: str) -> bool:
    """True if stat is a multi-component combo."""
    return canonical(stat) in COMBO_COMPONENTS


def is_base(stat: str) -> bool:
    """True if stat is a single base count stat."""
    return canonical(stat) in BASE_STATS_FULL


def components_of(stat: str) -> tuple[str, ...]:
    """Return base-stat components.

    For a base stat, returns a single-element tuple.
    Raises ValueError for unknown names.
    """
    s = canonical(stat)
    if s in COMBO_COMPONENTS:
        return COMBO_COMPONENTS[s]
    if s in BASE_STATS_FULL:
        return (s,)
    raise ValueError(f"Unknown stat: {stat!r}")


def is_known(stat: str) -> bool:
    """True if stat is a recognized name (canonical or mission alias)."""
    return stat in ALL_KNOWN_NAMES


def normalize(stats: Iterable[str]) -> tuple[str, ...]:
    """Return canonical names for an iterable of stat names.

    Filters out unknown names. Useful when accepting input that may mix
    canonical and mission-alias names.
    """
    return tuple(canonical(s) for s in stats if is_known(s))


# ── Self-test (callable via import) ──────────────────────────────────────


def _self_test() -> None:
    """Verify registry invariants. Raises AssertionError on violation.

    Validate by importing this function and calling it:

        from nba_props_model.targets import _self_test
        _self_test()

    This module is a package without __main__.py, so `python -m
    nba_props_model.targets` does NOT work. Call _self_test() via import.
    """
    # Round-trip canonical <-> mission
    for c in COMBO_STATS_CANONICAL:
        m = CANONICAL_TO_MISSION[c]
        assert canonical(m) == c, f"canonical({m!r}) failed round-trip"
        assert mission_name(c) == m, f"mission_name({c!r}) failed round-trip"
        assert canonical(c) == c, f"canonical({c!r}) idempotent"
        assert mission_name(m) == m, f"mission_name({m!r}) idempotent"
    # Components consistency
    for c in COMBO_STATS_CANONICAL:
        comps = COMBO_COMPONENTS[c]
        assert len(comps) >= 2
        for comp in comps:
            assert comp in BASE_STATS_FULL, (
                f"component {comp!r} of {c!r} not in BASE_STATS_FULL")
        assert components_of(c) == comps
        assert components_of(CANONICAL_TO_MISSION[c]) == comps
    # Base stat self-component + classifiers
    for b in BASE_STATS_FULL:
        assert components_of(b) == (b,)
        assert is_base(b)
        assert not is_combo(b)
    # Combo classifiers
    for c in COMBO_STATS_CANONICAL:
        assert is_combo(c)
        assert is_combo(CANONICAL_TO_MISSION[c])
        assert not is_base(c)
    # Counts
    assert len(BASE_STATS_FULL) == 7
    assert len(COMBO_STATS_CANONICAL) == 5
    assert len(ALL_TARGETS_CANONICAL) == 12
    assert len(ALL_TARGETS_MISSION) == 12
    assert len(MISSION_REQUIRED_TARGETS_CANONICAL) == 12
    assert len(MISSION_REQUIRED_TARGETS_MISSION) == 12
    # Known-name closure
    for s in ALL_TARGETS_CANONICAL:
        assert is_known(s)
    for s in ALL_TARGETS_MISSION:
        assert is_known(s)
    # PMF subsets partition base stats
    assert set(BASE_STATS_PMF_TRAINED + BASE_STATS_PMF_PENDING) == set(BASE_STATS_FULL)
    assert set(MISSION_REQUIRED_COMBOS_CANONICAL) == set(COMBO_STATS_CANONICAL)
    # normalize() round-trips canonical
    assert normalize(COMBO_STATS_CANONICAL) == COMBO_STATS_CANONICAL
    # normalize() converts mission to canonical
    assert normalize(("pts_reb_ast", "stl_blk", "pts")) == ("pra", "stocks", "pts")
    # normalize() filters unknowns
    assert normalize(("pra", "totally_fake_stat", "stl_blk")) == ("pra", "stocks")

    print("nba_props_model.targets self-test PASS")
    print(f"  BASE_STATS_FULL ({len(BASE_STATS_FULL)}): {BASE_STATS_FULL}")
    print(f"  COMBO_STATS_CANONICAL ({len(COMBO_STATS_CANONICAL)}): {COMBO_STATS_CANONICAL}")
    print(f"  ALL_TARGETS_CANONICAL ({len(ALL_TARGETS_CANONICAL)}): {ALL_TARGETS_CANONICAL}")
    print(f"  ALL_TARGETS_MISSION   ({len(ALL_TARGETS_MISSION)}): {ALL_TARGETS_MISSION}")
    print(f"  MISSION_REQUIRED_TARGETS_CANONICAL ({len(MISSION_REQUIRED_TARGETS_CANONICAL)}): {MISSION_REQUIRED_TARGETS_CANONICAL}")
    print(f"  MISSION_REQUIRED_TARGETS_MISSION   ({len(MISSION_REQUIRED_TARGETS_MISSION)}): {MISSION_REQUIRED_TARGETS_MISSION}")
