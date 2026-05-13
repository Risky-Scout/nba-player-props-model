#!/usr/bin/env python3
"""Verify Odds API market registry contract and no stray local registries."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
SCRIPTS = REPO_ROOT / "scripts"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

EXCLUDE_FILES = {
    SRC / "nba_props_model" / "markets" / "oddsapi_markets.py",
    REPO_ROOT / "scripts" / "verify_oddsapi_market_registry_contract.py",
}

FORBIDDEN_ASSIGN_RE = re.compile(
    r"^\s*(MAIN_MARKETS|ALT_MARKETS|DEFAULT_MARKETS|MARKETS|MARKET_TO_STAT|MARKET_KEY_TO_STAT)\s*=",
)


def main() -> int:
    sys.path.insert(0, str(SRC))
    from nba_props_model.markets.oddsapi_markets import (
        ODDSAPI_NBA_ALT_MARKET_TO_STAT,
        ODDSAPI_NBA_ALT_MARKETS,
        ODDSAPI_NBA_DEFAULT_MARKETS,
        ODDSAPI_NBA_MAIN_MARKET_TO_STAT,
        ODDSAPI_NBA_MAIN_MARKETS,
        ODDSAPI_NBA_MARKET_TO_STAT,
        ODDSAPI_NBA_REQUIRED_CANONICAL_STATS,
        validate_market_registry,
    )

    validate_market_registry()

    required_stats = {
        "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
        "stocks", "pa", "pr", "ra", "pra",
    }
    assert set(ODDSAPI_NBA_REQUIRED_CANONICAL_STATS) == required_stats

    assert set(ODDSAPI_NBA_MAIN_MARKETS) == {
        "player_points",
        "player_rebounds",
        "player_assists",
        "player_threes",
        "player_turnovers",
        "player_steals",
        "player_blocks",
        "player_blocks_steals",
        "player_points_assists",
        "player_points_rebounds",
        "player_rebounds_assists",
        "player_points_rebounds_assists",
    }
    assert set(ODDSAPI_NBA_ALT_MARKETS) == {
        "player_points_alternate",
        "player_rebounds_alternate",
        "player_assists_alternate",
        "player_threes_alternate",
        "player_turnovers_alternate",
        "player_steals_alternate",
        "player_blocks_alternate",
        "player_points_assists_alternate",
        "player_points_rebounds_alternate",
        "player_rebounds_assists_alternate",
        "player_points_rebounds_assists_alternate",
    }
    assert "player_blocks_steals_alternate" not in ODDSAPI_NBA_ALT_MARKET_TO_STAT

    expected_map_subset = {
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
        "player_rebounds_assists_alternate": "ra",
    }
    for k, v in expected_map_subset.items():
        assert ODDSAPI_NBA_MARKET_TO_STAT.get(k) == v, (k, ODDSAPI_NBA_MARKET_TO_STAT.get(k))

    offenders: list[str] = []
    for root in (SCRIPTS, SRC, WORKFLOWS):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix not in {".py", ".yml", ".yaml"}:
                continue
            if path.resolve() in {p.resolve() for p in EXCLUDE_FILES}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if FORBIDDEN_ASSIGN_RE.match(line):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{i}:{line.strip()}")
            if path.suffix == ".py" and "test" not in path.parts:
                if '"ra": None' in text or "'ra': None" in text:
                    offenders.append(f"{path}: contains ra=None sentinel")
                if '"reb_ast": None' in text or "'reb_ast': None" in text:
                    offenders.append(f"{path}: contains reb_ast=None sentinel")

    if offenders:
        print("FORBIDDEN_LOCAL_REGISTRY_OR_SENTINEL:", file=sys.stderr)
        for o in offenders:
            print(f"  {o}", file=sys.stderr)
        return 1

    assert len(ODDSAPI_NBA_DEFAULT_MARKETS) == len(ODDSAPI_NBA_MARKET_TO_STAT)
    print("ODDSAPI_MARKET_REGISTRY_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
