#!/usr/bin/env python3
"""
snapshot_opening_lines.py
=========================
Runs at 9 AM ET (14:00 UTC) — before intraday sharp action.

Captures game totals and spreads from The Odds API for all NBA games
scheduled today. These are the "opening" reference prices used to
compute the open-to-close line movement signal (sharp money indicator).

Why 9 AM ET:
  - Books have posted overnight lines by this point
  - Sharp syndicates begin hitting markets ~10 AM–2 PM ET
  - Injury report deadline is 5:30 PM ET
  Capturing at 9 AM gives the cleanest pre-sharp baseline.

Why totals + spreads only (not player props):
  - Featured markets are available across all events in one API call
  - Cost: 2 credits per call (1 per market per region)
  - Player prop opening lines require per-event calls (10 credits each)
    and are not stable enough at 9 AM to be meaningful
  - The total and spread are the primary sharp money signals for
    player prop model context (pace, blowout risk, implied team totals)

Output: data/opening_lines_{YYYY-MM-DD}.json
  {
    "<event_id>": {
      "home_team":        "Boston Celtics",
      "away_team":        "Golden State Warriors",
      "commence_time":    "2026-03-13T00:10:00Z",
      "consensus_total":  224.5,
      "consensus_spread": -6.5,
      "implied_home_total": 115.5,
      "implied_away_total": 109.0,
      "books_total":      {"draftkings": 224.5, "fanduel": 224.0, ...},
      "books_spread":     {"draftkings": -6.5,  "fanduel": -6.5, ...},
      "snapshot_time":    "2026-03-13T14:02:11Z",
      "snapshot_type":    "opening"
    },
    ...
  }

The grader joins this with closing_lines_{date}.json to compute:
  total_move  = closing_total  - opening_total    (sharp steam signal)
  spread_move = closing_spread - opening_spread   (sharp side signal)
"""

import json
import logging
import os
import statistics
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

# ── Constants ──────────────────────────────────────────────────────────────────

DATA_DIR      = Path("data")
DATA_DIR.mkdir(exist_ok=True)

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORT         = "basketball_nba"
REGIONS       = "us"          # us covers DraftKings, FanDuel, BetMGM, BetRivers
ODDS_FORMAT   = "american"
MARKETS       = "totals,spreads"

# Sharp books — Pinnacle unavailable in us region, use consensus across these
BOOKMAKERS    = "draftkings,fanduel,betmgm,betrivers,pointsbet_us"


# ── API helpers ────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    key = os.environ.get("ODDS_API_KEY", "")
    if not key:
        logger.error("ODDS_API_KEY environment variable not set.")
        sys.exit(1)
    return key


def odds_api_get(url: str, retries: int = 3) -> dict | list | None:
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=20)
            remaining = r.headers.get("x-requests-remaining", "?")
            used      = r.headers.get("x-requests-used", "?")
            if r.status_code == 200:
                logger.debug(f"API credits — used: {used}  remaining: {remaining}")
                return r.json()
            elif r.status_code == 429:
                logger.warning(f"Rate limited. Sleeping 15s (attempt {attempt+1})")
                time.sleep(15)
            elif r.status_code == 401:
                logger.error("Invalid ODDS_API_KEY — check GitHub Actions secret.")
                sys.exit(1)
            elif r.status_code == 422:
                logger.error(f"Invalid parameters: {r.text}")
                return None
            else:
                logger.warning(f"HTTP {r.status_code}: {r.text[:200]}")
                return None
        except Exception as exc:
            logger.warning(f"Request error: {exc} (attempt {attempt+1})")
            time.sleep(3)
    return None


# ── Core logic ─────────────────────────────────────────────────────────────────

def fetch_opening_lines(api_key: str, target_date: str) -> dict:
    """
    Fetch today's NBA totals and spreads from The Odds API.
    Returns dict keyed by event_id.
    """
    snapshot_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    url = (
        f"{ODDS_API_BASE}/sports/{SPORT}/odds"
        f"?apiKey={api_key}"
        f"&regions={REGIONS}"
        f"&markets={MARKETS}"
        f"&oddsFormat={ODDS_FORMAT}"
        f"&bookmakers={BOOKMAKERS}"
        f"&commenceTimeFrom={target_date}T00:00:00Z"
        f"&commenceTimeTo={target_date}T23:59:59Z"
        f"&dateFormat=iso"
    )

    data = odds_api_get(url)
    if not data:
        logger.error("No data returned from Odds API.")
        return {}

    logger.info(f"Found {len(data)} NBA events for {target_date}")

    opening_lines = {}

    for event in data:
        eid          = event["id"]
        home_team    = event.get("home_team", "")
        away_team    = event.get("away_team", "")
        commence     = event.get("commence_time", "")
        bookmakers   = event.get("bookmakers", [])

        totals_by_book  = {}
        spreads_by_book = {}

        for bk in bookmakers:
            book = bk["key"]
            for mkt in bk.get("markets", []):
                if mkt["key"] == "totals":
                    for outcome in mkt.get("outcomes", []):
                        if outcome.get("name") == "Over":
                            val = outcome.get("point")
                            if val is not None:
                                totals_by_book[book] = float(val)

                elif mkt["key"] == "spreads":
                    for outcome in mkt.get("outcomes", []):
                        # Home team spread
                        if outcome.get("name") == home_team:
                            val = outcome.get("point")
                            if val is not None:
                                spreads_by_book[book] = float(val)

        if not totals_by_book:
            logger.warning(f"No total found for {away_team} @ {home_team}")
            continue

        consensus_total  = round(statistics.median(totals_by_book.values()), 1)
        consensus_spread = round(statistics.median(spreads_by_book.values()), 1) \
                           if spreads_by_book else 0.0

        # Implied team totals using standard formula:
        # home_total = (total / 2) - (spread / 2)
        # away_total = (total / 2) + (spread / 2)
        implied_home = round((consensus_total / 2) - (consensus_spread / 2), 2)
        implied_away = round((consensus_total / 2) + (consensus_spread / 2), 2)

        opening_lines[eid] = {
            "home_team":          home_team,
            "away_team":          away_team,
            "commence_time":      commence,
            "consensus_total":    consensus_total,
            "consensus_spread":   consensus_spread,
            "implied_home_total": implied_home,
            "implied_away_total": implied_away,
            "books_total":        totals_by_book,
            "books_spread":       spreads_by_book,
            "snapshot_time":      snapshot_ts,
            "snapshot_type":      "opening",
        }

        logger.info(
            f"  {away_team} @ {home_team}: "
            f"total={consensus_total}  spread={consensus_spread:+.1f}  "
            f"({len(totals_by_book)} books)"
        )

    return opening_lines


def main():
    api_key     = get_api_key()
    target_date = date.today().isoformat()
    out_path    = DATA_DIR / f"opening_lines_{target_date}.json"

    logger.info(f"Snapshotting opening lines for {target_date} at 9 AM ET...")

    lines = fetch_opening_lines(api_key, target_date)

    if not lines:
        logger.error("No opening lines captured. Exiting without writing file.")
        sys.exit(1)

    with open(out_path, "w") as f:
        json.dump(lines, f, indent=2)

    logger.info(f"Saved {len(lines)} game opening lines → {out_path}")
    logger.info(
        f"Line movement signal will be computed at inference time by "
        f"joining with closing_lines_{{date}}.json"
    )


if __name__ == "__main__":
    main()
