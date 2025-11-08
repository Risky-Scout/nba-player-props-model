#!/usr/bin/env python3
"""
DAILY NBA PLAYER PROPS PREDICTION PIPELINE
Run this once per day to generate predictions with injury adjustments

Usage:
  python run_daily_predictions.py --date 2025-11-08 --games "DAL@WAS,TOR@PHI,CHI@CLE" --injuries injuries_2025-11-08.csv

Or for quick run (manual input):
  python run_daily_predictions.py
"""

import argparse
import pandas as pd
import numpy as np
import pickle
from scipy.stats import norm
from datetime import datetime
import os

def main(prediction_date, games_str, injury_file):
    print("="*80)
    print(f"NBA PLAYER PROPS PIPELINE - {prediction_date}")
    print("="*80)

    # Parse games
    games = [g.strip() for g in games_str.split(',')]
    print(f"\nTonight's games ({len(games)}):")
    for game in games:
        print(f"  {game}")

    # Map team abbreviations to IDs (extend this mapping as needed)
    team_abbrev_to_id = {
        'DAL': 7, 'WAS': 30, 'TOR': 28, 'PHI': 23,
        'CHI': 5, 'CLE': 6, 'LAL': 14, 'ATL': 1,
        'POR': 25, 'MIA': 16, 'NOP': 19, 'SAS': 27,
        'IND': 12, 'DEN': 8, 'PHX': 24, 'LAC': 13
    }

    tonights_teams = set()
    for game in games:
        away, home = game.split('@')
        tonights_teams.add(team_abbrev_to_id.get(away.strip()))
        tonights_teams.add(team_abbrev_to_id.get(home.strip()))

    tonights_teams = [t for t in tonights_teams if t is not None]

    print(f"\nTeam IDs: {tonights_teams}")

    # Load injury report
    if not os.path.exists(injury_file):
        print(f"\n❌ Injury file not found: {injury_file}")
        print("Please create it first or run without injuries")
        return

    injuries = pd.read_csv(injury_file)
    out_players = set(injuries[injuries['out_flag'] == 1]['player'].tolist())
    questionable_players = set(injuries[injuries['questionable_flag'] == 1]['player'].tolist())

    print(f"\nInjuries: {len(out_players)} OUT, {len(questionable_players)} QUESTIONABLE")

    # Load models
    with open('model_cache/trained_models.pkl', 'rb') as f:
        models = pickle.load(f)

    # Load data
    df = pd.read_csv('data/processed_training_data.csv')
    df['date'] = pd.to_datetime(df['date'])

    # Filter to tonight's teams
    df_tonight = df[df['team_id'].isin(tonights_teams)]
    latest_stats = df_tonight.sort_values('date').groupby('player_id').last().reset_index()

    # Remove OUT players
    latest_stats = latest_stats[~latest_stats['player_name'].isin(out_players)]

    print(f"\nPlayers: {len(latest_stats)} (after removing OUT)")

    # Apply usage boosts for teams with injuries
    # TODO: Auto-detect which teams have key players out
    # For now, manually specify based on injury report

    latest_stats['usage_boost'] = 1.0

    # Filter to active players (15+ min)
    active_players = latest_stats[latest_stats['min_decimal'] >= 15]

    # Reduce minutes for QUESTIONABLE players
    for player in questionable_players:
        mask = active_players['player_name'] == player
        if mask.any():
            active_players.loc[mask, 'min_decimal'] *= 0.75

    print(f"Active players: {len(active_players)}")

    # Features
    feature_cols = [
        'min_decimal', 'rest_days', 'is_home',
        'pts_L3', 'pts_L5', 'pts_L7', 'pts_L10',
        'reb_L3', 'reb_L5', 'reb_L7', 'reb_L10',
        'ast_L3', 'ast_L5', 'ast_L7', 'ast_L10',
        'min_decimal_L3', 'min_decimal_L5',
        'fg_pct_L3', 'fg_pct_L5',
        'games_last_7',
        'opp_def_rating', 'opp_off_rating', 'opp_pace'
    ]

    # Generate predictions
    print("\nGenerating predictions...")

    all_pmf_data = []

    for idx, player_row in active_players.iterrows():
        player_name = player_row['player_name']
        team_name = player_row['team']
        X = player_row[feature_cols].fillna(0).values.reshape(1, -1)

        for prop in ['pts', 'reb', 'ast']:
            rf_pred = models[prop]['rf'].predict(X)[0]
            gb_pred = models[prop]['gb'].predict(X)[0]
            expected_value = 0.6 * rf_pred + 0.4 * gb_pred

            if prop == 'pts':
                std_dev = 3.87
                lines = [0.5] + list(range(5, 51, 5)) + [i+0.5 for i in range(10, 41)]
            elif prop == 'reb':
                std_dev = 1.74
                lines = [0.5] + list(range(2, 21, 2)) + [i+0.5 for i in range(3, 16)]
            else:
                std_dev = 1.41
                lines = [0.5] + list(range(2, 16, 2)) + [i+0.5 for i in range(2, 13)]

            lines = sorted(set(lines))

            for line in lines:
                prob_over = 1 - norm.cdf(line, expected_value, std_dev)

                def prob_to_american(p):
                    p = max(0.01, min(0.99, p))
                    if p >= 0.5:
                        return int(-100 * p / (1 - p))
                    else:
                        return int(100 * (1 - p) / p)

                fair_odds_over = prob_to_american(prob_over)

                all_pmf_data.append({
                    'player': player_name,
                    'team': team_name,
                    'prop': prop.upper(),
                    'line': line,
                    'expected_value': expected_value,
                    'prob_over': prob_over,
                    'fair_odds_over': fair_odds_over,
                })

    pmf_df = pd.DataFrame(all_pmf_data)

    # Save
    output_file = f'predictions/daily_{prediction_date}.csv'
    pmf_df.to_csv(output_file, index=False)

    print(f"\n✓ Generated {len(pmf_df)} predictions")
    print(f"✓ Saved to {output_file}")

    # Show top picks
    print("\n" + "="*80)
    print("TOP 10 PICKS FOR TONIGHT")
    print("="*80)

    top_picks = pmf_df[(pmf_df['prob_over'] >= 0.70) & (pmf_df['prob_over'] <= 0.80)].sort_values('prob_over', ascending=False).head(10)

    for i, row in top_picks.iterrows():
        print(f"{row['player']:>25} {row['prop']} Over {row['line']:>5.1f}: {row['prob_over']*100:>5.1f}% | EV: {row['expected_value']:.1f}")

    print("\n✓ Pipeline complete!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate NBA player props predictions')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='Prediction date (YYYY-MM-DD)')
    parser.add_argument('--games', required=True, help='Games (e.g., "DAL@WAS,TOR@PHI,CHI@CLE")')
    parser.add_argument('--injuries', default=None, help='Injury CSV file')

    args = parser.parse_args()

    if args.injuries is None:
        args.injuries = f'data/injuries/injuries_{args.date}.csv'

    main(args.date, args.games, args.injuries)
