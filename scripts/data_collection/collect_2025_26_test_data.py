"""
2025-26 SEASON TEST DATA COLLECTOR
Collects REAL 2025-26 season games for out-of-sample testing

This is the holdout test set - should NEVER be used for training
"""
import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class TestDataCollector:
    def __init__(self, season='2025-26'):
        self.season = season
        print(f"="*80)
        print(f"COLLECTING 2025-26 SEASON TEST DATA")
        print(f"="*80)
        print(f"Season: {season}")
        print(f"Purpose: Out-of-sample testing ONLY")
        print(f"="*80)

    def collect_player_data(self, player_id, player_name):
        """Collect all 2025-26 games for a player"""
        try:
            time.sleep(0.6)

            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=self.season,
                timeout=30
            )

            df = gamelog.get_data_frames()[0]

            if len(df) == 0:
                return None

            games = []
            for idx, row in df.iterrows():
                game = {
                    'PLAYER_ID': player_id,
                    'PLAYER_NAME': player_name,
                    'SEASON': self.season,
                    'GAME_DATE': row['GAME_DATE'],
                    'MATCHUP': row['MATCHUP'],
                    'HOME_GAME': 0 if '@' in row['MATCHUP'] else 1,
                    'MIN': float(row['MIN']) if pd.notna(row['MIN']) and row['MIN'] != '' else 0,
                    'PTS': float(row['PTS']) if pd.notna(row['PTS']) else 0,
                    'REB': float(row['REB']) if pd.notna(row['REB']) else 0,
                    'AST': float(row['AST']) if pd.notna(row['AST']) else 0,
                    'STL': float(row['STL']) if pd.notna(row['STL']) else 0,
                    'BLK': float(row['BLK']) if pd.notna(row['BLK']) else 0,
                    'TOV': float(row['TOV']) if pd.notna(row['TOV']) else 0,
                    'FG_PCT': float(row['FG_PCT']) if pd.notna(row['FG_PCT']) else 0,
                    'FG3_PCT': float(row['FG3_PCT']) if pd.notna(row['FG3_PCT']) else 0,
                    'FT_PCT': float(row['FT_PCT']) if pd.notna(row['FT_PCT']) else 0,
                    'PLUS_MINUS': float(row['PLUS_MINUS']) if pd.notna(row['PLUS_MINUS']) else 0
                }
                games.append(game)

            return games

        except Exception as e:
            print(f"  Error: {e}")
            return None

    def collect_test_season(self, player_list_file='data/nba_training_data_real.csv'):
        """
        Collect 2025-26 data for same players as training set

        Args:
            player_list_file: Path to training data (to get player IDs)
        """
        print(f"\nLoading player list from training data...")

        try:
            training_df = pd.read_csv(player_list_file)
            unique_players = training_df[['PLAYER_ID', 'PLAYER_NAME']].drop_duplicates()
            print(f"✓ Found {len(unique_players)} players from training set")
        except:
            print("⚠ Training data not found. Using default player list...")
            all_players = players.get_active_players()
            unique_players = pd.DataFrame([
                {'PLAYER_ID': p['id'], 'PLAYER_NAME': p['full_name']}
                for p in all_players[:100]
            ])

        print(f"\n{'='*80}")
        print(f"COLLECTING 2025-26 TEST DATA")
        print(f"{'='*80}")

        all_games = []

        for i, row in unique_players.iterrows():
            player_id = row['PLAYER_ID']
            player_name = row['PLAYER_NAME']

            print(f"[{i+1}/{len(unique_players)}] {player_name}...", end=" ")

            games = self.collect_player_data(player_id, player_name)

            if games:
                all_games.extend(games)
                print(f"✓ {len(games)} games")
            else:
                print(f"✗ No games")

        df = pd.DataFrame(all_games)

        print(f"\n{'='*80}")
        print(f"TEST DATA COLLECTED")
        print(f"{'='*80}")
        print(f"Total games: {len(df)}")
        print(f"Unique players: {df['PLAYER_NAME'].nunique()}")
        if len(df) > 0:
            print(f"Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")

        return df


def main():
    print("="*80)
    print("2025-26 SEASON TEST DATA COLLECTION")
    print("="*80)
    print("This data will be used ONLY for testing")
    print("It should NEVER be included in model training")
    print("="*80)

    collector = TestDataCollector(season='2025-26')

    # Collect data
    df = collector.collect_test_season()

    if len(df) > 0:
        # Save to file
        output_file = 'data/nba_test_data_2025_26.csv'
        df.to_csv(output_file, index=False)

        print(f"\n{'='*80}")
        print("TEST DATA SAVED")
        print(f"{'='*80}")
        print(f"File: {output_file}")
        print(f"Games: {len(df)}")
        print(f"Players: {df['PLAYER_NAME'].nunique()}")
        print(f"\n⚠️  DO NOT USE THIS DATA FOR TRAINING!")
        print(f"{'='*80}")
    else:
        print("\n⚠️  No 2025-26 games found yet (season may not have started)")

if __name__ == "__main__":
    main()
