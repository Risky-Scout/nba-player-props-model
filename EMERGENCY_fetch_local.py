#!/usr/bin/env python3
"""
EMERGENCY DATA UPDATE - Run this on YOUR LOCAL MACHINE
This MUST be run outside the container where APIs work.

This will fetch Nov 4-12 games in 5 minutes.
"""
import sys
import os

print("="*80)
print("EMERGENCY NBA DATA UPDATE - Nov 4-12")
print("="*80)
print()

# Check if running locally
try:
    import requests
    response = requests.get("https://www.nba.com", timeout=5)
    if response.status_code != 200:
        print("⚠️  Warning: NBA.com not accessible")
except:
    print("❌ Internet/NBA.com not accessible")
    print()
    print("This script MUST run on your LOCAL machine, not in container!")
    sys.exit(1)

try:
    from nba_api.stats.endpoints import leaguegamefinder
    from nba_api.stats.static import players
except ImportError:
    print("❌ nba_api not installed!")
    print()
    print("Install it:")
    print("  pip install nba_api")
    sys.exit(1)

import pandas as pd
import time
from datetime import datetime

print("✓ Running locally with internet access")
print("✓ nba_api installed")
print()
print("Fetching Nov 4-12, 2025 games...")
print("This will take 3-5 minutes due to API rate limiting...")
print()

try:
    # Get all games from 2025 season
    gamefinder = leaguegamefinder.LeagueGameFinder(
        season_nullable='2025',
        season_type_nullable='Regular Season',
        timeout=120
    )

    all_games = gamefinder.get_data_frames()[0]
    all_games['GAME_DATE'] = pd.to_datetime(all_games['GAME_DATE'])

    print(f"✓ Found {len(all_games)} total team-games in 2025 season")

    # Filter to Nov 4-12
    nov_games = all_games[
        (all_games['GAME_DATE'] >= '2025-11-04') &
        (all_games['GAME_DATE'] <= '2025-11-12')
    ]

    print(f"✓ Filtered to {len(nov_games)} team-games in Nov 4-12")
    print()

    # Save
    output_file = 'emergency_update_nov4_12.csv'
    nov_games.to_csv(output_file, index=False)

    print("="*80)
    print("✅ SUCCESS!")
    print("="*80)
    print(f"Saved: {output_file}")
    print(f"Games: {len(nov_games)} team-games")
    print()
    print("NEXT STEPS:")
    print("1. Upload this CSV to your server:")
    print(f"   scp {output_file} user@server:/path/to/nba-player-props-model/data/")
    print()
    print("2. SSH to server and run:")
    print("   python emergency_retrain.py")
    print()

except Exception as e:
    print(f"❌ FAILED: {e}")
    print()
    print("If this fails, you may need to:")
    print("1. Wait a few minutes (API rate limit)")
    print("2. Try again")
    print("3. Check NBA API status")
    sys.exit(1)
