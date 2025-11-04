"""
Generate realistic NBA player game data for model training
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse

class NBADataGenerator:
    def __init__(self, seed=42):
        np.random.seed(seed)

        # NBA player archetypes with realistic stat distributions
        self.player_archetypes = {
            'superstar': {
                'pts': (28, 6), 'reb': (8, 3), 'ast': (7, 3),
                'min': (35, 3), 'fg_pct': (0.48, 0.05), 'fg3_pct': (0.36, 0.06), 'ft_pct': (0.82, 0.08)
            },
            'allstar': {
                'pts': (22, 5), 'reb': (6, 2.5), 'ast': (5, 2.5),
                'min': (32, 3), 'fg_pct': (0.46, 0.05), 'fg3_pct': (0.35, 0.06), 'ft_pct': (0.80, 0.08)
            },
            'starter_guard': {
                'pts': (15, 4), 'reb': (3, 1.5), 'ast': (6, 2),
                'min': (28, 4), 'fg_pct': (0.44, 0.05), 'fg3_pct': (0.37, 0.06), 'ft_pct': (0.78, 0.09)
            },
            'starter_big': {
                'pts': (13, 4), 'reb': (9, 2.5), 'ast': (2, 1),
                'min': (26, 4), 'fg_pct': (0.52, 0.06), 'fg3_pct': (0.28, 0.08), 'ft_pct': (0.72, 0.10)
            }
        }

        # Real NBA player names for authenticity
        self.player_names = {
            'superstar': ['LeBron James', 'Kevin Durant', 'Stephen Curry', 'Giannis Antetokounmpo',
                         'Joel Embiid', 'Nikola Jokic', 'Luka Doncic', 'Damian Lillard'],
            'allstar': ['Jayson Tatum', 'Anthony Davis', 'Jimmy Butler', 'Paul George',
                       'Devin Booker', 'Donovan Mitchell', 'Trae Young', 'Julius Randle'],
            'starter_guard': ['Chris Paul', 'Kyle Lowry', 'Fred VanVleet', 'Malcolm Brogdon',
                             'Mike Conley', 'Dejounte Murray', 'Marcus Smart', 'Tyrese Haliburton'],
            'starter_big': ['Clint Capela', 'Jarrett Allen', 'Myles Turner', 'Jonas Valanciunas',
                           'Jusuf Nurkic', 'Robert Williams', 'Domantas Sabonis', 'Bam Adebayo']
        }

    def generate_player_list(self):
        """Generate list of players with assigned archetypes"""
        players = []
        player_id = 1000

        for archetype, names in self.player_names.items():
            for name in names:
                players.append({
                    'player_id': player_id,
                    'player_name': name,
                    'archetype': archetype
                })
                player_id += 1

        # Add more generic players to reach 49 total
        additional_archetypes = ['allstar', 'starter_guard', 'starter_big'] * 5
        for i, arch in enumerate(additional_archetypes[:17]):
            players.append({
                'player_id': player_id,
                'player_name': f'Player {player_id}',
                'archetype': arch
            })
            player_id += 1

        return players

    def generate_game_log(self, player, num_games=60):
        """Generate realistic game log for a player"""
        archetype = self.player_archetypes[player['archetype']]
        games = []

        # Start date: October 24, 2023 (2023-24 season start)
        start_date = datetime(2023, 10, 24)

        for game_num in range(num_games):
            # Generate game date (roughly every 3 days)
            game_date = start_date + timedelta(days=game_num * 3)

            # Home/away split
            home_game = np.random.choice([0, 1])

            # Rest days (0-4 days)
            rest_days = np.random.choice([0, 1, 1, 2, 2, 3, 4], p=[0.05, 0.30, 0.30, 0.20, 0.10, 0.03, 0.02])

            # Minutes played (with some variance)
            min_played = max(15, np.random.normal(archetype['min'][0], archetype['min'][1]))

            # Generate stats based on archetype and minutes
            min_factor = min_played / archetype['min'][0]

            pts = max(0, np.random.normal(archetype['pts'][0] * min_factor, archetype['pts'][1]))
            reb = max(0, np.random.normal(archetype['reb'][0] * min_factor, archetype['reb'][1]))
            ast = max(0, np.random.normal(archetype['ast'][0] * min_factor, archetype['ast'][1]))
            stl = max(0, np.random.normal(1.2 * min_factor, 0.6))
            blk = max(0, np.random.normal(0.8 * min_factor, 0.5))
            tov = max(0, np.random.normal(2.5 * min_factor, 1.0))

            fg_pct = max(0.2, min(0.7, np.random.normal(archetype['fg_pct'][0], archetype['fg_pct'][1])))
            fg3_pct = max(0.0, min(0.6, np.random.normal(archetype['fg3_pct'][0], archetype['fg3_pct'][1])))
            ft_pct = max(0.5, min(1.0, np.random.normal(archetype['ft_pct'][0], archetype['ft_pct'][1])))

            # Opponent stats (realistic NBA team ranges)
            opp_def_rating = np.random.uniform(108, 118)
            opp_off_rating = np.random.uniform(108, 118)
            opp_pace = np.random.uniform(97, 103)

            # Usage rate
            usage_rate = np.random.uniform(18, 32) if player['archetype'] in ['superstar', 'allstar'] else np.random.uniform(12, 22)

            # Games in last 7 days
            games_last_7 = min(game_num, np.random.choice([2, 3, 3, 4, 4], p=[0.2, 0.3, 0.3, 0.15, 0.05]))

            games.append({
                'PLAYER_ID': player['player_id'],
                'PLAYER_NAME': player['player_name'],
                'GAME_DATE': game_date.strftime('%Y-%m-%d'),
                'HOME_GAME': home_game,
                'REST_DAYS': rest_days,
                'MIN': round(min_played, 1),
                'PTS': round(pts, 1),
                'REB': round(reb, 1),
                'AST': round(ast, 1),
                'STL': round(stl, 1),
                'BLK': round(blk, 1),
                'TOV': round(tov, 1),
                'FG_PCT': round(fg_pct, 3),
                'FG3_PCT': round(fg3_pct, 3),
                'FT_PCT': round(ft_pct, 3),
                'OPP_DEF_RATING': round(opp_def_rating, 1),
                'OPP_OFF_RATING': round(opp_off_rating, 1),
                'OPP_PACE': round(opp_pace, 1),
                'USAGE_RATE': round(usage_rate, 1),
                'GAMES_LAST_7': games_last_7
            })

        return games

    def calculate_rolling_features(self, df):
        """Calculate rolling averages for each player"""
        df = df.sort_values(['PLAYER_ID', 'GAME_DATE']).reset_index(drop=True)

        rolling_stats = ['PTS', 'REB', 'AST', 'MIN', 'FG_PCT', 'FG3_PCT', 'FT_PCT']

        for stat in rolling_stats:
            df[f'{stat}_L3'] = df.groupby('PLAYER_ID')[stat].transform(
                lambda x: x.rolling(window=3, min_periods=1).mean()
            )
            df[f'{stat}_L5'] = df.groupby('PLAYER_ID')[stat].transform(
                lambda x: x.rolling(window=5, min_periods=1).mean()
            )
            df[f'{stat}_L7'] = df.groupby('PLAYER_ID')[stat].transform(
                lambda x: x.rolling(window=7, min_periods=1).mean()
            )
            df[f'{stat}_L10'] = df.groupby('PLAYER_ID')[stat].transform(
                lambda x: x.rolling(window=10, min_periods=1).mean()
            )

        return df

    def generate_complete_dataset(self, total_games=2000, games_per_player=None):
        """Generate complete dataset with specified number of games"""
        players = self.generate_player_list()

        if games_per_player is None:
            games_per_player = int(total_games / len(players)) + 1

        print(f"Generating dataset with {len(players)} players, {games_per_player} games each...")

        all_games = []
        for i, player in enumerate(players):
            if i % 10 == 0:
                print(f"  Processing player {i+1}/{len(players)}...")
            games = self.generate_game_log(player, num_games=games_per_player)
            all_games.extend(games)

        df = pd.DataFrame(all_games)

        print("Calculating rolling averages...")
        df = self.calculate_rolling_features(df)

        # Shuffle to simulate real data collection
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)

        # Limit to target number of games
        df = df.iloc[:total_games]

        print(f"\nDataset generated: {len(df)} games")
        print(f"Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
        print(f"Unique players: {df['PLAYER_NAME'].nunique()}")

        return df

def main():
    parser = argparse.ArgumentParser(description='Generate NBA player game data')
    parser.add_argument('--games', type=int, default=2000, help='Total number of games to generate')
    parser.add_argument('--output', type=str, default='data/nba_data_2024.csv', help='Output file path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')

    args = parser.parse_args()

    print("=" * 80)
    print("NBA DATA GENERATOR")
    print("=" * 80)

    generator = NBADataGenerator(seed=args.seed)
    df = generator.generate_complete_dataset(total_games=args.games)

    # Save to file
    df.to_csv(args.output, index=False)
    print(f"\nData saved to: {args.output}")
    print(f"File size: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
