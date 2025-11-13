#!/usr/bin/env python3
"""
Verify Nov 8, 2025 predictions against actual results
"""

import pandas as pd
import sys

# Load predictions
try:
    preds = pd.read_csv('predictions/top_props_2025-11-08.csv')
    print(f"✓ Loaded {len(preds)} predictions from Nov 8")
except Exception as e:
    print(f"❌ Error loading predictions: {e}")
    sys.exit(1)

# Display predictions we need to verify
print("\n" + "="*80)
print("TOP PREDICTIONS TO VERIFY (70%+ confidence)")
print("="*80)

# Filter to 70%+ confidence
high_conf = preds[preds['prob_over'] >= 0.70].copy()
high_conf = high_conf.sort_values('prob_over', ascending=False).head(20)

print(f"\nPlayer                    Team             Prop   Line   Expected  Prob(Over)")
print("-"*80)
for idx, row in high_conf.iterrows():
    print(f"{row['player']:25} {row['team'][:20]:20} {row['prop']:4}  {row['line']:5.1f}  {row['expected_value']:7.2f}   {row['prob_over']:.1%}")

print("\n" + "="*80)
print("\nNow we need to fetch actual results from NBA API...")
print("\nAttempting to get actual stats from Nov 8, 2025...")

# Try to get actual results
try:
    from nba_api.stats.endpoints import leaguegamefinder
    from datetime import datetime
    import time

    print("\n✓ NBA API is available, fetching Nov 8 games...")

    # Get games from Nov 8, 2025
    gamefinder = leaguegamefinder.LeagueGameFinder(
        date_from_nullable='11/08/2025',
        date_to_nullable='11/08/2025',
        season_nullable='2025-26'
    )
    games = gamefinder.get_data_frames()[0]

    print(f"✓ Found {len(games)//2} games on Nov 8, 2025")

    if len(games) == 0:
        print("\n⚠️  No games found for Nov 8, 2025")
        print("This might mean:")
        print("  1. The date is in the future")
        print("  2. The NBA API doesn't have data for that date yet")
        print("  3. It was an off day (no games scheduled)")
    else:
        print("\nGames played on Nov 8, 2025:")
        for team in games['TEAM_NAME'].unique():
            print(f"  - {team}")

except ImportError:
    print("\n⚠️  NBA API not installed - cannot fetch actual results automatically")
    print("\nTo verify predictions manually:")
    print("  1. Go to NBA.com or Basketball Reference")
    print("  2. Look up Nov 8, 2025 games")
    print("  3. Compare actual stats to predictions above")
    print("\nOr install NBA API: pip install nba-api")
except Exception as e:
    print(f"\n⚠️  Error fetching NBA data: {e}")

print("\n" + "="*80)
print("\nMANUAL VERIFICATION INSTRUCTIONS")
print("="*80)
print("\n1. Visit: https://www.nba.com/games?date=2025-11-08")
print("2. Click on each game to see box scores")
print("3. Check if each player's actual stats were OVER or UNDER the line")
print("\nExample:")
print("  Evan Mobley REB O8.0 (we predicted 9.46)")
print("  → Check if Mobley actually had more than 8 rebounds")
print("\n" + "="*80)
