#!/usr/bin/env python3
"""
snapshot_closing_lines.py
=========================
Runs at 6 PM ET (23:00 UTC) — after the NBA injury report deadline.

Why 6 PM ET:
  The NBA official injury report deadline is 5:30 PM ET. By 6 PM the
  market has had 30 minutes to fully digest official designations and
  reprice. This is the sharpest point in the market cycle before tipoff
  noise begins. Running at 7 PM risks capturing lines mid-movement as
  books respond to last-minute lineup scratches.

Fetches The Odds API player props, removes vig, stores fair implied
probabilities as the closing line baseline for true CLV calculation.

Output: graded/closing_lines_{YYYY-MM-DD}.json
  {
    "<player_norm>|<stat>|<line>": {
      "player_name":     "LeBron James",
      "stat":            "pts",
      "line":            24.5,
      "fair_over_prob":  0.5312,
      "fair_under_prob": 0.4688,
      "over_odds":       -115,
      "under_odds":      -105,
      "best_over_book":  "draftkings",
      "best_under_book": "fanduel",
      "snapshot_time":   "2026-03-10T00:02:14Z"
    },
    ...
  }
"""

import json
import logging
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

GRADED_DIR = Path("graded")
GRADED_DIR.mkdir(exist_ok=True)

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
REGIONS       = "us,us2"
ODDS_FORMAT   = "american"

# Odds API market key → our internal stat name
MARKET_MAP = {
    "player_points":   "pts",
    "player_rebounds": "reb",
    "player_assists":  "ast",
    "player_threes":   "fg3m",
    "player_steals":   "stl",
    "player_blocks":   "blk",
}

BOOKS = [
    "draftkings", "fanduel", "betmgm", "betrivers",
    "pointsbet_us", "betparx", "bet365_us",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    key = os.environ.get("ODDS_API_KEY", "")
    if not key:
        logger.error("ODDS_API_KEY not set in environment.")
        sys.exit(1)
    return key


def american_to_decimal(american: int) -> float:
    if american > 0:
        return 1.0 + american / 100.0
    return 1.0 + 100.0 / abs(american)


def remove_vig(over_odds: int, under_odds: int) -> tuple[float, float]:
    """Return (fair_over_prob, fair_under_prob) with vig removed."""
    raw_over  = 1.0 / american_to_decimal(over_odds)
    raw_under = 1.0 / american_to_decimal(under_odds)
    total     = raw_over + raw_under
    if total <= 0:
        return 0.5, 0.5
    return round(raw_over / total, 6), round(raw_under / total, 6)


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    name = name.lower().strip()
    name = re.sub(r"[''`]", "", name)   # apostrophes
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def odds_api_get(url: str, api_key: str, retries: int = 3) -> dict | list | None:
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                remaining = r.headers.get("x-requests-remaining", "?")
                logger.debug(f"API requests remaining: {remaining}")
                return r.json()
            elif r.status_code == 429:
                logger.warning(f"Rate limited. Sleeping 10s (attempt {attempt+1})")
                time.sleep(10)
            elif r.status_code == 401:
                logger.error("Invalid ODDS_API_KEY.")
                sys.exit(1)
            else:
                logger.warning(f"HTTP {r.status_code} for {url}")
                return None
        except Exception as e:
            logger.warning(f"Request error: {e} (attempt {attempt+1})")
            time.sleep(3)
    return None


# ── Core snapshot logic ───────────────────────────────────────────────────────

def fetch_closing_lines(api_key: str, target_date: str) -> dict:
    """
    Fetch all NBA player prop odds and return a dict keyed by
    '{player_norm}|{stat}|{line}' with vig-removed probabilities.
    """
    markets_str = ",".join(MARKET_MAP.keys())
    books_str   = ",".join(BOOKS)
    snapshot_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Step 1: get today's events
    events_url = (
        f"{ODDS_API_BASE}/sports/basketball_nba/events"
        f"?apiKey={api_key}&dateFormat=iso"
    )
    events = odds_api_get(events_url, api_key)
    if not events:
        logger.error("No events returned from Odds API.")
        return {}

    # Filter to today's games only
    today_events = []
    for ev in events:
        ct = ev.get("commence_time", "")
        if target_date in ct:
            today_events.append(ev)

    if not today_events:
        logger.warning(f"No NBA events found for {target_date}.")
        return {}

    logger.info(f"Found {len(today_events)} NBA games for {target_date}.")

    closing_lines = {}

    for ev in today_events:
        eid       = ev["id"]
        home_team = ev.get("home_team", "")
        away_team = ev.get("away_team", "")
        game_str  = f"{away_team} @ {home_team}"

        odds_url = (
            f"{ODDS_API_BASE}/sports/basketball_nba/events/{eid}/odds"
            f"?apiKey={api_key}"
            f"&regions={REGIONS}"
            f"&markets={markets_str}"
            f"&oddsFormat={ODDS_FORMAT}"
            f"&bookmakers={books_str}"
        )

        data = odds_api_get(odds_url, api_key)
        if not data or not data.get("bookmakers"):
            logger.warning(f"No odds for game {game_str}")
            continue

        # Collect best odds across all books (best = most favorable to bettor)
        # best_over[key] = {"over_odds": int, "book": str, ...}
        best_over  = {}  # key → best over odds entry
        best_under = {}  # key → best under odds entry

        for bk in data["bookmakers"]:
            book_key = bk["key"]
            for mkt in bk.get("markets", []):
                stat = MARKET_MAP.get(mkt["key"])
                if not stat:
                    continue

                # Group outcomes by player
                by_player: dict[str, dict] = {}
                for outcome in mkt.get("outcomes", []):
                    pname = outcome.get("description", "")
                    side  = outcome.get("name", "")   # "Over" or "Under"
                    if pname and side:
                        by_player.setdefault(pname, {})[side] = outcome

                for pname, sides in by_player.items():
                    if "Over" not in sides or "Under" not in sides:
                        continue

                    over_odds  = int(sides["Over"].get("price", -110))
                    under_odds = int(sides["Under"].get("price", -110))
                    line       = float(sides["Over"].get("point", 0))
                    norm       = normalize_name(pname)
                    key        = f"{norm}|{stat}|{line}"

                    # Best over: highest decimal (most +EV for bettor)
                    if key not in best_over or american_to_decimal(over_odds) > american_to_decimal(best_over[key]["odds"]):
                        best_over[key] = {
                            "odds": over_odds, "book": book_key,
                            "player_name": pname, "stat": stat,
                            "line": line, "game": game_str,
                        }

                    if key not in best_under or american_to_decimal(under_odds) > american_to_decimal(best_under[key]["odds"]):
                        best_under[key] = {
                            "odds": under_odds, "book": book_key,
                        }

        # Build closing line entries from best odds
        for key, over_entry in best_over.items():
            if key not in best_under:
                continue

            oo = over_entry["odds"]
            uo = best_under[key]["odds"]

            fair_over, fair_under = remove_vig(oo, uo)

            closing_lines[key] = {
                "player_name":     over_entry["player_name"],
                "player_norm":     normalize_name(over_entry["player_name"]),
                "stat":            over_entry["stat"],
                "line":            over_entry["line"],
                "game":            over_entry["game"],
                "fair_over_prob":  fair_over,
                "fair_under_prob": fair_under,
                "over_odds":       oo,
                "under_odds":      uo,
                "best_over_book":  over_entry["book"],
                "best_under_book": best_under[key]["book"],
                "snapshot_time":   snapshot_ts,
            }

        logger.info(f"  {game_str}: {len([k for k in closing_lines if closing_lines[k]['game'] == game_str])} player-stat lines captured")

        time.sleep(0.5)  # be kind to the API

    return closing_lines


def main():
    api_key     = get_api_key()
    target_date = date.today().isoformat()
    out_path    = GRADED_DIR / f"closing_lines_{target_date}.json"

    logger.info(f"Snapshotting closing lines for {target_date}...")

    lines = fetch_closing_lines(api_key, target_date)

    if not lines:
        logger.error("No closing lines captured. Exiting without writing file.")
        sys.exit(1)

    with open(out_path, "w") as f:
        json.dump(lines, f, indent=2)

    logger.info(f"Saved {len(lines)} player-stat closing lines → {out_path}")

    # Quick summary
    from collections import Counter
    stat_counts = Counter(v["stat"] for v in lines.values())
    for stat, count in sorted(stat_counts.items()):
        logger.info(f"  {stat}: {count} lines")


if __name__ == "__main__":
    main()
