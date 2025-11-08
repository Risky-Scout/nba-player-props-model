#!/usr/bin/env python3
"""
BallDontLie.io NBA Data Collector
Collects real NBA game data, player stats, and team box scores

Run locally (not in container) to avoid proxy blocks.
"""
import requests
import pandas as pd
import time
import os
import argparse
from datetime import datetime
from typing import List, Dict, Optional

class BallDontLieCollector:
    """Collector for BallDontLie NBA API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.balldontlie.io/v1"
        self.headers = {'Authorization': api_key}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request(self, endpoint: str, params: Dict = None, max_retries: int = 5) -> Dict:
        """Make API request with retry logic for rate limiting"""
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"  Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                else:
                    print(f"  Error {response.status_code}: {response.text}")
                    return None

            except requests.exceptions.Timeout:
                print(f"  Timeout on attempt {attempt + 1}")
                time.sleep(2 ** attempt)
                continue

            except Exception as e:
                print(f"  Error: {e}")
                return None

        print(f"  Failed after {max_retries} retries")
        return None

    def collect_games(self, seasons: List[int], start_date: str = None,
                     end_date: str = None) -> pd.DataFrame:
        """
        Collect NBA games

        Args:
            seasons: List of season years (e.g., [2023, 2024] for 2023-24 and 2024-25)
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
        """
        print("="*80)
        print("COLLECTING NBA GAMES")
        print("="*80)

        all_games = []

        for season in seasons:
            print(f"\nSeason {season}-{season+1}:")
            page = 1
            total_pages = 1

            while page <= total_pages:
                print(f"  Fetching page {page}/{total_pages}...", end=" ")

                params = {
                    'seasons[]': season,
                    'per_page': 100,
                    'page': page
                }

                if start_date:
                    params['start_date'] = start_date
                if end_date:
                    params['end_date'] = end_date

                data = self._make_request('games', params)

                if data is None:
                    break

                games = data.get('data', [])
                meta = data.get('meta', {})
                total_pages = meta.get('total_pages', 1)

                print(f"✓ {len(games)} games")

                for game in games:
                    all_games.append({
                        'game_id': game['id'],
                        'date': game['date'],
                        'season': game['season'],
                        'home_team_id': game['home_team']['id'],
                        'home_team': game['home_team']['full_name'],
                        'away_team_id': game['visitor_team']['id'],
                        'away_team': game['visitor_team']['full_name'],
                        'home_score': game['home_team_score'],
                        'away_score': game['visitor_team_score'],
                        'status': game['status']
                    })

                page += 1
                time.sleep(0.6)  # Rate limiting

        df = pd.DataFrame(all_games)
        print(f"\n✓ Total games collected: {len(df)}")

        return df

    def collect_player_stats(self, game_ids: List[int]) -> pd.DataFrame:
        """Collect player statistics for given games"""
        print("\n" + "="*80)
        print("COLLECTING PLAYER STATS")
        print("="*80)

        all_stats = []
        total_games = len(game_ids)

        for i, game_id in enumerate(game_ids, 1):
            if i % 50 == 0:
                print(f"  Progress: {i}/{total_games} games...")

            params = {
                'game_ids[]': game_id,
                'per_page': 100
            }

            data = self._make_request('stats', params)

            if data is None:
                continue

            stats = data.get('data', [])

            for stat in stats:
                all_stats.append({
                    'game_id': stat['game']['id'],
                    'player_id': stat['player']['id'],
                    'player_name': f"{stat['player']['first_name']} {stat['player']['last_name']}",
                    'team_id': stat['team']['id'],
                    'team': stat['team']['full_name'],
                    'min': stat.get('min', '0:00'),
                    'pts': stat.get('pts', 0),
                    'reb': stat.get('reb', 0),
                    'ast': stat.get('ast', 0),
                    'stl': stat.get('stl', 0),
                    'blk': stat.get('blk', 0),
                    'turnover': stat.get('turnover', 0),
                    'fgm': stat.get('fgm', 0),
                    'fga': stat.get('fga', 0),
                    'fg_pct': stat.get('fg_pct', 0),
                    'fg3m': stat.get('fg3m', 0),
                    'fg3a': stat.get('fg3a', 0),
                    'fg3_pct': stat.get('fg3_pct', 0),
                    'ftm': stat.get('ftm', 0),
                    'fta': stat.get('fta', 0),
                    'ft_pct': stat.get('ft_pct', 0),
                    'oreb': stat.get('oreb', 0),
                    'dreb': stat.get('dreb', 0),
                    'pf': stat.get('pf', 0)
                })

            time.sleep(0.6)  # Rate limiting

        df = pd.DataFrame(all_stats)
        print(f"✓ Total player stats collected: {len(df)}")

        return df

    def create_team_boxscores(self, player_stats_df: pd.DataFrame,
                            games_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate player stats into team box scores"""
        print("\n" + "="*80)
        print("CREATING TEAM BOX SCORES")
        print("="*80)

        # Convert minutes to decimal
        def min_to_decimal(min_str):
            if pd.isna(min_str) or min_str == '' or min_str == '0:00':
                return 0.0
            try:
                parts = str(min_str).split(':')
                return float(parts[0]) + float(parts[1])/60
            except:
                return 0.0

        player_stats_df['min_decimal'] = player_stats_df['min'].apply(min_to_decimal)

        # Aggregate by game and team
        team_stats = player_stats_df.groupby(['game_id', 'team_id', 'team']).agg({
            'pts': 'sum',
            'reb': 'sum',
            'ast': 'sum',
            'stl': 'sum',
            'blk': 'sum',
            'turnover': 'sum',
            'fgm': 'sum',
            'fga': 'sum',
            'fg3m': 'sum',
            'fg3a': 'sum',
            'ftm': 'sum',
            'fta': 'sum',
            'oreb': 'sum',
            'dreb': 'sum',
            'pf': 'sum',
            'min_decimal': 'sum'
        }).reset_index()

        # Calculate percentages
        team_stats['fg_pct'] = team_stats['fgm'] / team_stats['fga'].replace(0, 1)
        team_stats['fg3_pct'] = team_stats['fg3m'] / team_stats['fg3a'].replace(0, 1)
        team_stats['ft_pct'] = team_stats['ftm'] / team_stats['fta'].replace(0, 1)

        # Merge with game info
        team_stats = team_stats.merge(
            games_df[['game_id', 'date', 'season', 'home_team_id', 'away_team_id']],
            on='game_id'
        )

        # Add home/away indicator
        team_stats['is_home'] = team_stats['team_id'] == team_stats['home_team_id']

        print(f"✓ Team box scores created: {len(team_stats)} team-games")

        return team_stats


def main():
    parser = argparse.ArgumentParser(description='Collect NBA data from BallDontLie API')
    parser.add_argument('--api-key', type=str, help='BallDontLie API key (or set BALLDONTLIE_API_KEY env var)')
    parser.add_argument('--seasons', nargs='+', type=int, default=[2023, 2024],
                       help='Season years to collect (default: 2023 2024)')
    parser.add_argument('--start-date', type=str, default='2023-10-01',
                       help='Start date YYYY-MM-DD (default: 2023-10-01)')
    parser.add_argument('--end-date', type=str, default='2025-06-30',
                       help='End date YYYY-MM-DD (default: 2025-06-30)')
    parser.add_argument('--include-stats', action='store_true',
                       help='Include player stats and team box scores (slower)')
    parser.add_argument('--outdir', type=str, default='./nba_out',
                       help='Output directory (default: ./nba_out)')

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get('BALLDONTLIE_API_KEY')

    if not api_key:
        print("ERROR: No API key provided!")
        print("Either:")
        print("  1. Set environment variable: export BALLDONTLIE_API_KEY='your-key'")
        print("  2. Pass as argument: --api-key 'your-key'")
        return

    print("="*80)
    print("BALLDONTLIE NBA DATA COLLECTOR")
    print("="*80)
    print(f"Seasons: {args.seasons}")
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Include stats: {args.include_stats}")
    print(f"Output directory: {args.outdir}")
    print("="*80)

    # Create output directory
    os.makedirs(args.outdir, exist_ok=True)

    # Initialize collector
    collector = BallDontLieCollector(api_key)

    # Collect games
    games_df = collector.collect_games(args.seasons, args.start_date, args.end_date)

    if games_df is None or len(games_df) == 0:
        print("\n❌ No games collected!")
        return

    # Save games
    games_file = os.path.join(args.outdir, 'nba_games.csv')
    games_df.to_csv(games_file, index=False)
    print(f"\n✓ Saved games: {games_file}")

    # Collect player stats if requested
    if args.include_stats:
        game_ids = games_df['game_id'].unique().tolist()

        player_stats_df = collector.collect_player_stats(game_ids)

        if player_stats_df is not None and len(player_stats_df) > 0:
            # Save player stats
            stats_file = os.path.join(args.outdir, 'nba_player_stats.csv')
            player_stats_df.to_csv(stats_file, index=False)
            print(f"✓ Saved player stats: {stats_file}")

            # Create and save team box scores
            team_box_df = collector.create_team_boxscores(player_stats_df, games_df)
            box_file = os.path.join(args.outdir, 'nba_team_boxscores.csv')
            team_box_df.to_csv(box_file, index=False)
            print(f"✓ Saved team box scores: {box_file}")

    print("\n" + "="*80)
    print("✅ DATA COLLECTION COMPLETE!")
    print("="*80)
    print(f"\nFiles saved in: {args.outdir}/")
    print(f"  - nba_games.csv ({len(games_df)} games)")
    if args.include_stats:
        print(f"  - nba_player_stats.csv ({len(player_stats_df)} player-games)")
        print(f"  - nba_team_boxscores.csv ({len(team_box_df)} team-games)")
    print("\nNext: Send these CSV files for model training!")
    print("="*80)


if __name__ == "__main__":
    main()
