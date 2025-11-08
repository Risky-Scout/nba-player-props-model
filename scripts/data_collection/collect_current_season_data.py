"""
LIVE NBA DATA COLLECTOR - 2024-25 Season
Collects real player game logs from NBA API for current season
"""
import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playergamelog, leaguegamefinder, commonplayerinfo
from nba_api.stats.static import players, teams
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class CurrentSeasonDataCollector:
    def __init__(self, season='2024-25'):
        self.season = season
        self.all_players = players.get_active_players()
        print(f"Collecting {season} season data...")
        print(f"Active players: {len(self.all_players)}")

    def get_top_players(self, min_games=5, limit=50):
        """Get top players by games played this season"""
        print(f"\nFinding top {limit} players with at least {min_games} games...")

        player_game_counts = []

        for i, player in enumerate(self.all_players[:200]):  # Check top 200 active players
            if i % 20 == 0:
                print(f"  Checking player {i+1}/200...")

            try:
                time.sleep(0.6)  # Rate limiting

                gamelog = playergamelog.PlayerGameLog(
                    player_id=player['id'],
                    season=self.season,
                    timeout=30
                )

                df = gamelog.get_data_frames()[0]

                if len(df) >= min_games:
                    player_game_counts.append({
                        'player_id': player['id'],
                        'player_name': player['full_name'],
                        'games_played': len(df)
                    })

            except Exception as e:
                continue

        # Sort by games played and take top limit
        player_game_counts = sorted(player_game_counts, key=lambda x: x['games_played'], reverse=True)
        top_players = player_game_counts[:limit]

        print(f"\nFound {len(top_players)} players")
        print(f"Top player: {top_players[0]['player_name']} ({top_players[0]['games_played']} games)")

        return top_players

    def collect_player_data(self, player_id, player_name):
        """Collect all games for a player this season"""
        try:
            time.sleep(0.6)  # Rate limiting

            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=self.season,
                timeout=30
            )

            df = gamelog.get_data_frames()[0]

            if len(df) == 0:
                return None

            # Process game data
            games = []
            for idx, row in df.iterrows():
                game = {
                    'PLAYER_ID': player_id,
                    'PLAYER_NAME': player_name,
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
            print(f"  Error collecting {player_name}: {e}")
            return None

    def add_opponent_stats(self, df):
        """Add opponent defensive rating and pace (simplified version)"""
        # For now, use league averages with some variance
        # In production, you'd fetch real opponent stats

        df['OPP_DEF_RATING'] = np.random.uniform(108, 118, len(df))
        df['OPP_OFF_RATING'] = np.random.uniform(108, 118, len(df))
        df['OPP_PACE'] = np.random.uniform(97, 103, len(df))
        df['USAGE_RATE'] = np.random.uniform(18, 28, len(df))

        return df

    def calculate_rest_days(self, df):
        """Calculate rest days between games"""
        df = df.sort_values(['PLAYER_ID', 'GAME_DATE']).reset_index(drop=True)

        df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])

        rest_days = []
        for player_id in df['PLAYER_ID'].unique():
            player_df = df[df['PLAYER_ID'] == player_id].copy()
            player_df = player_df.sort_values('GAME_DATE')

            player_rest = [2]  # First game of season
            for i in range(1, len(player_df)):
                days_diff = (player_df.iloc[i]['GAME_DATE'] - player_df.iloc[i-1]['GAME_DATE']).days
                player_rest.append(min(days_diff, 5))

            rest_days.extend(player_rest)

        df['REST_DAYS'] = rest_days
        return df

    def calculate_rolling_features(self, df):
        """Calculate rolling averages"""
        df = df.sort_values(['PLAYER_ID', 'GAME_DATE']).reset_index(drop=True)

        rolling_stats = ['PTS', 'REB', 'AST', 'MIN', 'FG_PCT', 'FG3_PCT', 'FT_PCT']

        for stat in rolling_stats:
            for window in [3, 5, 7, 10]:
                df[f'{stat}_L{window}'] = df.groupby('PLAYER_ID')[stat].transform(
                    lambda x: x.rolling(window=window, min_periods=1).mean()
                )

        # Games in last 7 days
        df['GAMES_LAST_7'] = df.groupby('PLAYER_ID')['GAME_DATE'].transform(
            lambda x: x.rolling('7D').count()
        )

        return df

    def collect_full_season(self, top_n_players=50, min_games=5):
        """Collect complete dataset for current season"""
        print("="*80)
        print(f"COLLECTING {self.season} SEASON DATA")
        print("="*80)

        # Get top players
        top_players = self.get_top_players(min_games=min_games, limit=top_n_players)

        # Collect data for each player
        all_games = []

        for i, player_info in enumerate(top_players):
            print(f"\n[{i+1}/{len(top_players)}] {player_info['player_name']} ({player_info['games_played']} games)")

            games = self.collect_player_data(player_info['player_id'], player_info['player_name'])

            if games:
                all_games.extend(games)
                print(f"  ✓ Collected {len(games)} games")

        # Create DataFrame
        df = pd.DataFrame(all_games)

        print(f"\n{'='*80}")
        print(f"RAW DATA COLLECTED")
        print(f"{'='*80}")
        print(f"Total games: {len(df)}")
        print(f"Players: {df['PLAYER_NAME'].nunique()}")
        print(f"Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")

        # Add derived features
        print(f"\n{'='*80}")
        print("ENGINEERING FEATURES")
        print(f"{'='*80}")

        print("Calculating rest days...")
        df = self.calculate_rest_days(df)

        print("Adding opponent stats...")
        df = self.add_opponent_stats(df)

        print("Calculating rolling averages...")
        df = self.calculate_rolling_features(df)

        # Remove rows with insufficient history
        df = df.dropna()

        print(f"\n{'='*80}")
        print("FINAL DATASET")
        print(f"{'='*80}")
        print(f"Games: {len(df)}")
        print(f"Players: {df['PLAYER_NAME'].nunique()}")
        print(f"Features: {len(df.columns)}")
        print(f"Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")

        return df

def main():
    print("="*80)
    print("LIVE NBA DATA COLLECTION - 2024-25 SEASON")
    print("="*80)

    collector = CurrentSeasonDataCollector(season='2024-25')

    # Collect data for top 50 players
    df = collector.collect_full_season(top_n_players=50, min_games=5)

    # Save to file
    output_file = 'data/nba_current_season.csv'
    df.to_csv(output_file, index=False)

    print(f"\n{'='*80}")
    print("DATA SAVED")
    print(f"{'='*80}")
    print(f"File: {output_file}")
    print(f"Size: {len(df)} games")
    print(f"\nReady for model training!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
