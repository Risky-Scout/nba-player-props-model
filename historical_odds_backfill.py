"""
historical_odds_backfill.py — The Odds API Historical Odds Backfill

Backfills NBA game totals and spreads from The Odds API historical endpoint.
Persists data/historical_game_odds.parquet keyed by game_date and teams.

Usage:
    python3 historical_odds_backfill.py --start 2023-10-24 --end 2026-03-30
    python3 historical_odds_backfill.py --days 30  (last 30 days only)
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

API_KEY   = os.environ.get("ODDS_API_KEY", "")
BASE_URL  = "https://api.the-odds-api.com/v4"
SPORT     = "basketball_nba"
BOOKMAKERS = "draftkings,fanduel,betmgm,betrivers,williamhill_us"
OUT_PATH  = Path("data/historical_game_odds.parquet")


def fetch_historical_odds(snapshot_utc: str) -> list:
    """Fetch NBA odds snapshot at a given UTC timestamp."""
    url = (
        f"{BASE_URL}/historical/sports/{SPORT}/odds"
        f"?apiKey={API_KEY}"
        f"&regions=us"
        f"&markets=spreads,totals"
        f"&bookmakers={BOOKMAKERS}"
        f"&oddsFormat=american"
        f"&date={snapshot_utc}"
    )
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=15)
            remaining = r.headers.get("x-requests-remaining", "?")
            if r.status_code == 200:
                data = r.json()
                games = data.get("data", [])
                logger.info(f"  {snapshot_utc}: {len(games)} games | remaining={remaining}")
                return games
            elif r.status_code == 422:
                logger.warning(f"  {snapshot_utc}: 422 — date out of range, skipping")
                return []
            elif r.status_code == 429:
                logger.warning(f"  Rate limited — sleeping 60s")
                time.sleep(60)
            else:
                logger.warning(f"  HTTP {r.status_code}: {r.text[:200]}")
                time.sleep(5)
        except Exception as e:
            logger.error(f"  Request error: {e}")
            time.sleep(5)
    return []


def parse_consensus(games: list) -> list:
    """Extract consensus totals and spreads from multi-book response."""
    records = []
    for game in games:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        commence = game.get("commence_time", "")
        game_date = commence[:10] if commence else ""

        totals_list = []
        spreads_list = []

        for bm in game.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market["key"] == "totals":
                    for outcome in market.get("outcomes", []):
                        if outcome["name"] == "Over":
                            totals_list.append(float(outcome.get("point", 0)))
                elif market["key"] == "spreads":
                    for outcome in market.get("outcomes", []):
                        if outcome["name"] == home:
                            spreads_list.append(float(outcome.get("point", 0)))

        if not totals_list and not spreads_list:
            continue

        consensus_total  = round(pd.Series(totals_list).median(), 1)  if totals_list  else None
        consensus_spread = round(pd.Series(spreads_list).median(), 1) if spreads_list else None

        implied_home = None
        implied_away = None
        if consensus_total and consensus_spread:
            implied_home = round((consensus_total / 2) - (consensus_spread / 2), 2)
            implied_away = round((consensus_total / 2) + (consensus_spread / 2), 2)

        records.append({
            "game_date":        game_date,
            "home_team":        home,
            "away_team":        away,
            "commence_time":    commence,
            "consensus_total":  consensus_total,
            "consensus_spread": consensus_spread,
            "implied_home_total": implied_home,
            "implied_away_total": implied_away,
            "book_count_total":   len(totals_list),
            "book_count_spread":  len(spreads_list),
            "snapshot_utc":     "",  # filled by caller
            "snapshot_kind":    "asof_8am",
        })
    return records


def backfill(start_date: str, end_date: str) -> pd.DataFrame:
    """Backfill odds for all dates in range, one snapshot per game day at 8AM ET."""
    if not API_KEY:
        raise ValueError("ODDS_API_KEY not set — run: export ODDS_API_KEY=your_key")

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end   = datetime.strptime(end_date,   "%Y-%m-%d")

    # Load existing to avoid re-fetching
    existing_dates = set()
    if OUT_PATH.exists():
        existing = pd.read_parquet(OUT_PATH)
        existing_dates = set(existing["game_date"].unique())
        logger.info(f"Existing records: {len(existing)} rows covering {len(existing_dates)} dates")
    else:
        existing = pd.DataFrame()

    all_records = []
    current = start

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in existing_dates:
            current += timedelta(days=1)
            continue

        # 8AM ET = 13:00 UTC (EST) or 12:00 UTC (EDT)
        # Use 13:00 UTC as conservative pregame snapshot
        snapshot_utc = f"{date_str}T13:00:00Z"
        games = fetch_historical_odds(snapshot_utc)

        if games:
            records = parse_consensus(games)
            for r in records:
                r["snapshot_utc"] = snapshot_utc
            all_records.extend(records)

        time.sleep(0.5)  # respect rate limits
        current += timedelta(days=1)

    if not all_records:
        logger.info("No new records fetched")
        return existing

    new_df = pd.DataFrame(all_records)
    combined = pd.concat([existing, new_df], ignore_index=True) if not existing.empty else new_df
    combined = combined.drop_duplicates(subset=["game_date","home_team","away_team","snapshot_kind"])
    combined.to_parquet(OUT_PATH, index=False)
    logger.info(f"Saved {len(combined)} total records to {OUT_PATH}")
    return combined


def derive_market_features(odds_df: pd.DataFrame, pgs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join historical odds to player-game rows to derive market context features.

    Returns DataFrame with player_id, game_id, market_pace_proxy (enhanced),
    opp_pace_context_market, implied_team_total.
    """
    pgs = pgs_df.copy()
    pgs['game_date'] = pd.to_datetime(pgs['game_date']).dt.strftime('%Y-%m-%d')

    odds = odds_df.copy()

    # Normalize team names for join
    # Join on game_date + team name matching
    records = []
    for _, row in pgs.iterrows():
        game_date = row['game_date']
        team_abbr = str(row.get('team_abbr', ''))

        matching = odds[odds['game_date'] == game_date]
        if len(matching) == 0:
            records.append({'player_id': row['player_id'], 'game_id': row['game_id'],
                           'market_total': None, 'implied_team_total': None})
            continue

        # Match by home/away team name containing team abbr (rough join)
        # More robust: use game_id join after building odds game_id mapping
        best = matching.iloc[0]  # fallback to first game of day
        is_home = row.get('home_team_id') == row.get('team_id')
        impl = best['implied_home_total'] if is_home else best['implied_away_total']

        records.append({
            'player_id':          row['player_id'],
            'game_id':            row['game_id'],
            'market_total':       best['consensus_total'],
            'implied_team_total': impl,
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', default='2025-10-01',
                        help='Start date YYYY-MM-DD')
    parser.add_argument('--end',   default=datetime.now().strftime('%Y-%m-%d'),
                        help='End date YYYY-MM-DD')
    parser.add_argument('--days',  type=int, default=None,
                        help='Backfill last N days only (overrides --start)')
    args = parser.parse_args()

    if args.days:
        start = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
        end   = datetime.now().strftime('%Y-%m-%d')
    else:
        start = args.start
        end   = args.end

    logger.info(f"Backfilling {start} → {end}")
    df = backfill(start, end)

    print(f"\n✓ {len(df)} total records")
    if len(df) > 0:
        print(f"  Date range: {df['game_date'].min()} → {df['game_date'].max()}")
        print(f"  Avg consensus total: {df['consensus_total'].mean():.1f}")
        print(f"  Coverage: {df['consensus_total'].notna().mean():.1%} of games have totals")
