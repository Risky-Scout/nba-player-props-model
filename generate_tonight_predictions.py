"""
TONIGHT'S PREDICTIONS GENERATOR
Generates complete PMF, odds, and betting recommendations for today's NBA games
"""
import pandas as pd
import numpy as np
from meta_ensemble_model import MetaEnsemblePlayerPropModel
from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class TonightsPredictionsGenerator:
    def __init__(self, model_path='model_cache/latest_model.pkl'):
        print("="*80)
        print("TONIGHT'S NBA PREDICTIONS")
        print("="*80)

        # Load trained model
        print("\nLoading trained model...")
        self.model = MetaEnsemblePlayerPropModel()
        try:
            self.model.load_models(model_path)
            print("✓ Model loaded successfully")
        except:
            print("⚠ Model not found. Please run train_latest_model.py first")
            raise

        # Load current season data for recent stats
        print("\nLoading current season data...")
        try:
            self.current_data = pd.read_csv('data/nba_current_season.csv')
            self.current_data['GAME_DATE'] = pd.to_datetime(self.current_data['GAME_DATE'])
            print(f"✓ Loaded {len(self.current_data)} games")
        except:
            print("⚠ Current season data not found")
            self.current_data = None

    def get_todays_games(self):
        """Get today's NBA games from API"""
        print("\nFetching today's games...")

        try:
            board = scoreboard.ScoreBoard()
            games = board.games.get_dict()

            if not games:
                print("No games scheduled for today")
                return []

            print(f"✓ Found {len(games)} games today")
            return games

        except Exception as e:
            print(f"Could not fetch live games: {e}")
            print("Using sample games for demonstration...")
            return self._get_sample_games()

    def _get_sample_games(self):
        """Get sample games if API fails"""
        # Sample games for demonstration
        return [
            {
                'homeTeam': {'teamName': 'Lakers'},
                'awayTeam': {'teamName': 'Warriors'},
                'gameId': 'sample_1'
            },
            {
                'homeTeam': {'teamName': 'Celtics'},
                'awayTeam': {'teamName': 'Heat'},
                'gameId': 'sample_2'
            }
        ]

    def get_player_recent_stats(self, player_id, player_name):
        """Get player's recent game stats for features"""
        if self.current_data is None:
            return None

        player_df = self.current_data[
            self.current_data['PLAYER_ID'] == player_id
        ].copy()

        if len(player_df) == 0:
            # Try by name
            player_df = self.current_data[
                self.current_data['PLAYER_NAME'].str.contains(player_name, case=False, na=False)
            ].copy()

        if len(player_df) == 0:
            return None

        # Get most recent game
        player_df = player_df.sort_values('GAME_DATE', ascending=False)
        latest = player_df.iloc[0]

        features = {
            'HOME_GAME': 1,  # Will be updated
            'REST_DAYS': 2,  # Default
            'GAMES_LAST_7': min(len(player_df), 4),
            'MIN': latest.get('MIN', 30),
            'OPP_DEF_RATING': 112,  # League average
            'OPP_OFF_RATING': 112,
            'OPP_PACE': 100,
            'PTS_L7': latest.get('PTS_L7', latest.get('PTS', 20)),
            'REB_L7': latest.get('REB_L7', latest.get('REB', 5)),
            'AST_L7': latest.get('AST_L7', latest.get('AST', 4)),
            'MIN_L7': latest.get('MIN_L7', latest.get('MIN', 30)),
            'FG_PCT_L7': latest.get('FG_PCT_L7', 0.45),
            'FG3_PCT_L7': latest.get('FG3_PCT_L7', 0.35),
            'FT_PCT_L7': latest.get('FT_PCT_L7', 0.80)
        }

        return features

    def generate_player_prediction(self, player_id, player_name, prop_stat, is_home=True):
        """Generate full prediction with PMF and odds for a player"""

        # Get recent stats as features
        features_dict = self.get_player_recent_stats(player_id, player_name)

        if features_dict is None:
            print(f"  ⚠ No data for {player_name}, skipping")
            return None

        # Update home/away
        features_dict['HOME_GAME'] = 1 if is_home else 0

        # Convert to DataFrame
        features_df = pd.DataFrame([features_dict])

        # Generate full PMF
        try:
            pmf_result = self.model.generate_full_pmf(
                player_id=str(player_id),
                player_name=player_name,
                prop_stat=prop_stat,
                game_features=features_df,
                max_value=60 if prop_stat == 'PTS' else 30
            )

            # Build margin and generate odds
            odds_result = self.model.build_margin_in_probability_space(
                pmf_result=pmf_result,
                target_margin=0.045,  # 4.5% margin (professional level)
                margin_method='power'
            )

            # Get key lines
            expected = pmf_result['expected_value']
            key_lines = [
                int(expected - 2.5),
                int(expected - 1.5),
                int(expected - 0.5),
                int(expected + 0.5),
                int(expected + 1.5),
                int(expected + 2.5)
            ]

            # Extract odds for key lines
            line_odds = []
            for line in key_lines:
                if line in odds_result['bookmaker_odds_over']:
                    line_odds.append({
                        'line': line,
                        'fair_prob_over': odds_result['raw_prob_over'][line],
                        'fair_prob_under': odds_result['raw_prob_under'][line],
                        'book_odds_over': odds_result['bookmaker_odds_over'][line],
                        'book_odds_under': odds_result['bookmaker_odds_under'][line],
                        'expected_value': expected
                    })

            return {
                'player': player_name,
                'prop': prop_stat,
                'expected_value': expected,
                'median': pmf_result['median'],
                'mode': pmf_result['mode'],
                'std': pmf_result['std'],
                'distribution': pmf_result['distribution_type'],
                'lines': line_odds,
                'full_pmf': pmf_result,
                'full_odds': odds_result
            }

        except Exception as e:
            print(f"  Error generating prediction for {player_name} {prop_stat}: {e}")
            return None

    def generate_game_predictions(self, game_info, top_players_per_team=5):
        """Generate predictions for all key players in a game"""

        home_team = game_info['homeTeam']['teamName']
        away_team = game_info['awayTeam']['teamName']

        print(f"\n{'='*80}")
        print(f"GAME: {away_team} @ {home_team}")
        print(f"{'='*80}")

        all_predictions = []

        # Get top players from each team (simplified - in production, query roster)
        sample_players = [
            # Sample player IDs - in production, get from team rosters
            {'id': 2544, 'name': 'LeBron James', 'team': home_team},
            {'id': 201939, 'name': 'Stephen Curry', 'team': away_team},
        ]

        for player_info in sample_players:
            player_id = player_info['id']
            player_name = player_info['name']
            is_home = player_info['team'] == home_team

            print(f"\n{player_name} ({'HOME' if is_home else 'AWAY'})")
            print("-" * 40)

            for prop in ['PTS', 'REB', 'AST']:
                pred = self.generate_player_prediction(
                    player_id, player_name, prop, is_home
                )

                if pred:
                    all_predictions.append(pred)

        return all_predictions

    def generate_all_predictions(self):
        """Generate predictions for all of tonight's games"""

        games = self.get_todays_games()

        if not games:
            print("\nNo games to predict")
            return []

        all_predictions = []

        for i, game in enumerate(games[:3]):  # Limit to first 3 games for demo
            predictions = self.generate_game_predictions(game)
            all_predictions.extend(predictions)

        return all_predictions

    def save_predictions(self, predictions, filename='predictions/tonight_predictions.csv'):
        """Save predictions to CSV"""

        if not predictions:
            print("No predictions to save")
            return

        # Flatten predictions for CSV
        rows = []
        for pred in predictions:
            base = {
                'player': pred['player'],
                'prop': pred['prop'],
                'expected_value': pred['expected_value'],
                'median': pred['median'],
                'mode': pred['mode'],
                'std': pred['std'],
                'distribution': pred['distribution']
            }

            # Add key lines
            for line_info in pred['lines'][:3]:  # Top 3 lines
                row = base.copy()
                row.update({
                    'line': line_info['line'],
                    'fair_prob_over': line_info['fair_prob_over'],
                    'fair_prob_under': line_info['fair_prob_under'],
                    'book_odds_over': line_info['book_odds_over'],
                    'book_odds_under': line_info['book_odds_under']
                })
                rows.append(row)

        df = pd.DataFrame(rows)

        # Create directory if needed
        import os
        os.makedirs('predictions', exist_ok=True)

        df.to_csv(filename, index=False)

        print(f"\n{'='*80}")
        print("PREDICTIONS SAVED")
        print(f"{'='*80}")
        print(f"File: {filename}")
        print(f"Predictions: {len(predictions)}")
        print(f"Lines: {len(df)}")
        print(f"{'='*80}")

        return df

    def print_prediction_summary(self, predictions):
        """Print formatted summary of predictions"""

        if not predictions:
            return

        print(f"\n{'='*80}")
        print("TONIGHT'S BETTING RECOMMENDATIONS")
        print(f"{'='*80}")

        for pred in predictions:
            print(f"\n{pred['player']} - {pred['prop']}")
            print(f"  Expected Value: {pred['expected_value']:.1f}")
            print(f"  Median: {pred['median']:.0f} | Mode: {pred['mode']:.0f} | Std: {pred['std']:.1f}")
            print(f"\n  Key Lines:")
            print(f"  {'Line':>6} | {'Fair P(Over)':>13} | {'Fair P(Under)':>14} | {'Book Over':>10} | {'Book Under':>11}")
            print(f"  {'-'*70}")

            for line_info in pred['lines'][:5]:
                print(f"  {line_info['line']:>6.1f} | "
                      f"{line_info['fair_prob_over']:>12.1%} | "
                      f"{line_info['fair_prob_under']:>13.1%} | "
                      f"{line_info['book_odds_over']:>10.0f} | "
                      f"{line_info['book_odds_under']:>10.0f}")

        print(f"\n{'='*80}")

def main():
    """Main prediction pipeline"""

    # Initialize generator
    generator = TonightsPredictionsGenerator()

    # Generate predictions
    predictions = generator.generate_all_predictions()

    # Print summary
    generator.print_prediction_summary(predictions)

    # Save to file
    df = generator.save_predictions(predictions)

    print("\n✓ DONE! Check predictions/tonight_predictions.csv for full details")

if __name__ == "__main__":
    main()
