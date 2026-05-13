"""Single source of truth: The Odds API NBA player-prop market keys → canonical stats.

M8.6 production repair — all fetch/compare scripts must import from here.
"""
from __future__ import annotations

ODDSAPI_MARKET_REGISTRY_VERSION = "oddsapi_nba_market_registry_v1_20260513"
ODDSAPI_MARKET_REGISTRY_SOURCE = "src/nba_props_model/markets/oddsapi_markets.py"

ODDSAPI_NBA_REQUIRED_CANONICAL_STATS: tuple[str, ...] = (
    "pts",
    "reb",
    "ast",
    "fg3m",
    "tov",
    "stl",
    "blk",
    "stocks",
    "pa",
    "pr",
    "ra",
    "pra",
)

ODDSAPI_NBA_MAIN_MARKET_TO_STAT: dict[str, str] = {
    "player_points": "pts",
    "player_rebounds": "reb",
    "player_assists": "ast",
    "player_threes": "fg3m",
    "player_turnovers": "tov",
    "player_steals": "stl",
    "player_blocks": "blk",
    "player_blocks_steals": "stocks",
    "player_points_assists": "pa",
    "player_points_rebounds": "pr",
    "player_rebounds_assists": "ra",
    "player_points_rebounds_assists": "pra",
}

ODDSAPI_NBA_ALT_MARKET_TO_STAT: dict[str, str] = {
    "player_points_alternate": "pts",
    "player_rebounds_alternate": "reb",
    "player_assists_alternate": "ast",
    "player_threes_alternate": "fg3m",
    "player_turnovers_alternate": "tov",
    "player_steals_alternate": "stl",
    "player_blocks_alternate": "blk",
    "player_points_assists_alternate": "pa",
    "player_points_rebounds_alternate": "pr",
    "player_rebounds_assists_alternate": "ra",
    "player_points_rebounds_assists_alternate": "pra",
}

ODDSAPI_NBA_MARKET_TO_STAT: dict[str, str] = {
    **ODDSAPI_NBA_MAIN_MARKET_TO_STAT,
    **ODDSAPI_NBA_ALT_MARKET_TO_STAT,
}

ODDSAPI_NBA_MAIN_MARKETS: tuple[str, ...] = tuple(ODDSAPI_NBA_MAIN_MARKET_TO_STAT.keys())
ODDSAPI_NBA_ALT_MARKETS: tuple[str, ...] = tuple(ODDSAPI_NBA_ALT_MARKET_TO_STAT.keys())
ODDSAPI_NBA_DEFAULT_MARKETS: tuple[str, ...] = ODDSAPI_NBA_MAIN_MARKETS + ODDSAPI_NBA_ALT_MARKETS


def canonical_market_key(market_key: str) -> str:
    """Normalize Odds API market key for lookup."""
    return str(market_key or "").strip()


def stat_for_market_key(market_key: str) -> str | None:
    """Return canonical stat for this Odds API market key, or None if unknown."""
    return ODDSAPI_NBA_MARKET_TO_STAT.get(canonical_market_key(market_key))


def is_alternate_market(market_key: str) -> bool:
    return canonical_market_key(market_key) in ODDSAPI_NBA_ALT_MARKET_TO_STAT


def market_keys_for_stat(stat: str, *, include_alternates: bool = True) -> tuple[str, ...]:
    """Return main (then alternate) market keys for a canonical stat."""
    s = str(stat or "").strip().lower()
    mains = [k for k, v in ODDSAPI_NBA_MAIN_MARKET_TO_STAT.items() if v == s]
    if not mains:
        return ()
    main = mains[0]
    if not include_alternates:
        return (main,)
    alts = [k for k, v in ODDSAPI_NBA_ALT_MARKET_TO_STAT.items() if v == s]
    return (main, *tuple(alts))


def validate_market_registry() -> None:
    """Assert internal consistency. Call from CI / verify_oddsapi_market_registry_contract."""
    assert set(ODDSAPI_NBA_REQUIRED_CANONICAL_STATS) == {
        "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
        "stocks", "pa", "pr", "ra", "pra",
    }
    # No None values, no duplicate keys across main+alt
    all_keys: list[str] = []
    for d in (ODDSAPI_NBA_MAIN_MARKET_TO_STAT, ODDSAPI_NBA_ALT_MARKET_TO_STAT):
        for k, v in d.items():
            assert v is not None, k
            assert k not in all_keys, f"duplicate market key: {k}"
            all_keys.append(k)
            assert v in ODDSAPI_NBA_REQUIRED_CANONICAL_STATS, (
                f"non-mission stat {v!r} mapped from {k!r}"
            )

    # Every required stat has ≥1 main market
    for stat in ODDSAPI_NBA_REQUIRED_CANONICAL_STATS:
        mains = [k for k, st in ODDSAPI_NBA_MAIN_MARKET_TO_STAT.items() if st == stat]
        assert mains, f"no main market for stat {stat!r}"

    # Every required stat except stocks has an alternate when listed by Odds API (registry)
    for stat in ODDSAPI_NBA_REQUIRED_CANONICAL_STATS:
        if stat == "stocks":
            continue
        alts = [k for k, st in ODDSAPI_NBA_ALT_MARKET_TO_STAT.items() if st == stat]
        assert alts, f"no alternate market registered for stat {stat!r}"

    # RA wiring
    assert ODDSAPI_NBA_MAIN_MARKET_TO_STAT.get("player_rebounds_assists") == "ra"
    assert ODDSAPI_NBA_ALT_MARKET_TO_STAT.get("player_rebounds_assists_alternate") == "ra"

    assert ODDSAPI_NBA_MAIN_MARKET_TO_STAT.get("player_blocks_steals") == "stocks"
    assert "player_blocks_steals_alternate" not in ODDSAPI_NBA_ALT_MARKET_TO_STAT

    assert ODDSAPI_NBA_MARKET_TO_STAT == {
        **ODDSAPI_NBA_MAIN_MARKET_TO_STAT,
        **ODDSAPI_NBA_ALT_MARKET_TO_STAT,
    }
