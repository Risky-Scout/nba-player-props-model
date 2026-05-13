"""Odds API and sportsbook market registries (single sources of truth)."""

from nba_props_model.markets.oddsapi_markets import (
    ODDSAPI_NBA_ALT_MARKETS,
    ODDSAPI_NBA_ALT_MARKET_TO_STAT,
    ODDSAPI_NBA_DEFAULT_MARKETS,
    ODDSAPI_NBA_MAIN_MARKETS,
    ODDSAPI_NBA_MAIN_MARKET_TO_STAT,
    ODDSAPI_NBA_MARKET_TO_STAT,
    ODDSAPI_NBA_REQUIRED_CANONICAL_STATS,
    canonical_market_key,
    is_alternate_market,
    market_keys_for_stat,
    stat_for_market_key,
    validate_market_registry,
)

__all__ = [
    "ODDSAPI_NBA_ALT_MARKETS",
    "ODDSAPI_NBA_ALT_MARKET_TO_STAT",
    "ODDSAPI_NBA_DEFAULT_MARKETS",
    "ODDSAPI_NBA_MAIN_MARKETS",
    "ODDSAPI_NBA_MAIN_MARKET_TO_STAT",
    "ODDSAPI_NBA_MARKET_TO_STAT",
    "ODDSAPI_NBA_REQUIRED_CANONICAL_STATS",
    "canonical_market_key",
    "is_alternate_market",
    "market_keys_for_stat",
    "stat_for_market_key",
    "validate_market_registry",
]
