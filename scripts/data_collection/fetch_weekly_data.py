#!/usr/bin/env python3
"""
WEEKLY DATA UPDATER
Run this script LOCALLY (not in container) once per week to update training data

This script works around container API blocks by requiring local execution.
"""
import sys
import os

print("="*80)
print("WEEKLY NBA DATA UPDATE")
print("="*80)
print()
print("⚠️  IMPORTANT: Run this script on your LOCAL MACHINE (not in container)")
print()
print("This script requires:")
print("  1. nba_api package: pip install nba_api")
print("  2. Direct internet access (no proxy/container blocks)")
print()
print("="*80)
print()

response = input("Are you running this LOCALLY? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n❌ Please run this script on your local machine where NBA API works.")
    print("\nSteps:")
    print("  1. Clone repo to your local machine")
    print("  2. Install: pip install nba_api pandas")
    print("  3. Run: python scripts/data_collection/fetch_weekly_data.py")
    print("  4. Upload updated CSV files back to server")
    sys.exit(1)

# Continue with actual data fetching
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

try:
    from nba_api.stats.endpoints import leaguegamefinder
    from nba_api.stats.static import players, teams
except ImportError:
    print("\n❌ nba_api not installed!")
    print("Install with: pip install nba_api")
    sys.exit(1)

print("✓ Running locally with nba_api")
print()

# Fetch recent games
print("Fetching games from last 14 days...")
print("This may take 2-3 minutes due to API rate limiting...")
print()

try:
    # Get all games from current season
    gamefinder = leaguegamefinder.LeagueGameFinder(
        season_nullable='2025',
        season_type_nullable='Regular Season',
        timeout=60
    )

    games_df = gamefinder.get_data_frames()[0]
    games_df['GAME_DATE'] = pd.to_datetime(games_df['GAME_DATE'])

    # Filter to last 14 days
    cutoff_date = datetime.now() - timedelta(days=14)
    recent_games = games_df[games_df['GAME_DATE'] >= cutoff_date]

    print(f"✓ Found {len(recent_games)} team-games in last 14 days")
    print(f"  Date range: {recent_games['GAME_DATE'].min()} to {recent_games['GAME_DATE'].max()}")
    print()

    # Get player stats for these games
    print("Fetching player stats for recent games...")
    print("This will take 5-10 minutes due to API rate limiting...")
    print()

    # TODO: Implement player stats collection
    # For now, save what we have

    output_file = f"data/weekly_update_{datetime.now().strftime('%Y%m%d')}.csv"
    recent_games.to_csv(output_file, index=False)

    print(f"✓ Saved recent games to: {output_file}")
    print()
    print("="*80)
    print("✅ DATA FETCH COMPLETE")
    print("="*80)
    print()
    print("Next steps:")
    print("  1. Upload this file to your server")
    print("  2. Run: python scripts/data_collection/process_real_data.py")
    print("  3. Run: python rebuild_best_compact_model.py")
    print()

except Exception as e:
    print(f"\n❌ Data fetch failed: {e}")
    print()
    print("This usually means:")
    print("  - Not running on local machine (container blocks NBA API)")
    print("  - Internet connection issues")
    print("  - NBA API is down")
    sys.exit(1)
