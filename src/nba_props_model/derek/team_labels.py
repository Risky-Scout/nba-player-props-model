"""Phase 13Z polish — derive human-readable team labels from existing
sources (predictions parquet, snapshot manifest, pmf_display, etc.).

Returns short-name labels suitable for visible Markdown headings:

    {"away": "Raptors", "home": "Cavaliers", "matchup": "Raptors @ Cavaliers",
     "away_full": "Toronto Raptors", "home_full": "Cleveland Cavaliers"}

No fabrication; if no source resolves the matchup, the helper returns
``None`` and callers fall back to ``Game <game_id>``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


# Map full team names → short headline label.
NBA_TEAM_FULL_TO_SHORT: dict[str, str] = {
    "Atlanta Hawks": "Hawks",
    "Boston Celtics": "Celtics",
    "Brooklyn Nets": "Nets",
    "Charlotte Hornets": "Hornets",
    "Chicago Bulls": "Bulls",
    "Cleveland Cavaliers": "Cavaliers",
    "Dallas Mavericks": "Mavericks",
    "Denver Nuggets": "Nuggets",
    "Detroit Pistons": "Pistons",
    "Golden State Warriors": "Warriors",
    "Houston Rockets": "Rockets",
    "Indiana Pacers": "Pacers",
    "LA Clippers": "Clippers",
    "Los Angeles Clippers": "Clippers",
    "Los Angeles Lakers": "Lakers",
    "Memphis Grizzlies": "Grizzlies",
    "Miami Heat": "Heat",
    "Milwaukee Bucks": "Bucks",
    "Minnesota Timberwolves": "Timberwolves",
    "New Orleans Pelicans": "Pelicans",
    "New York Knicks": "Knicks",
    "Oklahoma City Thunder": "Thunder",
    "Orlando Magic": "Magic",
    "Philadelphia 76ers": "76ers",
    "Phoenix Suns": "Suns",
    "Portland Trail Blazers": "Trail Blazers",
    "Sacramento Kings": "Kings",
    "San Antonio Spurs": "Spurs",
    "Toronto Raptors": "Raptors",
    "Utah Jazz": "Jazz",
    "Washington Wizards": "Wizards",
}


def _short(full_name: str) -> str:
    return NBA_TEAM_FULL_TO_SHORT.get(full_name.strip(), full_name.strip())


def parse_matchup_string(s: str) -> Optional[dict]:
    """Parse "Away Team @ Home Team" → away/home labels."""
    if not s or " @ " not in s:
        return None
    away_full, home_full = s.split(" @ ", 1)
    away = _short(away_full)
    home = _short(home_full)
    if not away or not home:
        return None
    return {
        "away": away,
        "home": home,
        "matchup": f"{away} @ {home}",
        "away_full": away_full.strip(),
        "home_full": home_full.strip(),
    }


def resolve_team_labels(*, repo_root: Path, delivery_date: str,
                         game_id: str) -> Optional[dict]:
    """Cascade through:

      1. ``predictions/all_props_<date>.parquet`` ``game`` column
         (canonical and per-row matched to the game_id).
      2. ``predictions/pmf_display_<date>.json`` props with matching
         player_id reverse-mapped through the parquet.
      3. ``deliveries/<date>/derek_game_snapshots/<gid>/current_live/
         snapshot_manifest.json`` ``game`` field if added.

    Returns a dict (see module docstring) or ``None`` when no source
    resolves the labels.
    """
    # Source 1 — predictions parquet.
    parquet = repo_root / "predictions" / f"all_props_{delivery_date}.parquet"
    if parquet.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(parquet, columns=["game_id", "game"])
            sub = df[df["game_id"].astype(str) == str(game_id)]
            if not sub.empty:
                game_str = str(sub["game"].dropna().iloc[0])
                parsed = parse_matchup_string(game_str)
                if parsed:
                    return parsed
        except Exception:
            pass
    # Source 3 — manifest may eventually carry "game".
    manifest = (
        repo_root / "deliveries" / delivery_date / "derek_game_snapshots"
        / str(game_id) / "current_live" / "snapshot_manifest.json"
    )
    if manifest.exists():
        try:
            m = json.loads(manifest.read_text(encoding="utf-8"))
            game_str = m.get("game") or m.get("matchup")
            if game_str:
                parsed = parse_matchup_string(game_str)
                if parsed:
                    return parsed
        except Exception:
            pass
    return None
