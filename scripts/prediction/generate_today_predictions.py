#!/usr/bin/env python3
"""
Simple prediction generator that works with the enhanced model
Generates predictions for all active players
"""
import pandas as pd
import numpy as np
import pickle
import sys
from datetime import datetime

print("="*80)
print(f"NBA PREDICTIONS - {datetime.now().strftime('%Y-%m-%d')}")
print("="*80)

# Load trained models
print("Loading model...")
with open('model_cache/trained_models.pkl', 'rb') as f:
    models = pickle.load(f)

# Load data
print("Loading training data...")
df = pd.read_csv('data/processed_training_data.csv')
df['date'] = pd.to_datetime(df['date'])

# Add enhanced features (matching rebuild_best_compact_model.py)
print("Adding enhanced features...")
df['usage_rate'] = (df['fga'] + 0.44*df['fta'] + df['turnover']) / ((df.get('opp_pace', 100) * df['min_decimal'] / 48).replace(0, 1))
df['usage_rate'] = df['usage_rate'].clip(0, 0.5)

df['pts_reb'] = df['pts'] + df['reb']
df['pts_ast'] = df['pts'] + df['ast']
df['reb_ast'] = df['reb'] + df['ast']
df['pts_reb_ast'] = df['pts'] + df['reb'] + df['ast']

# Add rolling averages for these
df = df.sort_values(['player_id', 'date'])
for stat in ['stl', 'blk', 'fga', 'fgm', 'fta', 'ftm', 'pts_reb', 'pts_ast', 'reb_ast', 'pts_reb_ast', 'usage_rate']:
    for w in [3, 5, 7, 10]:
        df[f'{stat}_L{w}'] = df.groupby('player_id')[stat].transform(lambda x: x.rolling(w, min_periods=1).mean())

# Get features (same as training)
features = [c for c in df.columns if any(x in c for x in ['_L3', '_L5', '_L7', '_L10', 'min_decimal', 'is_home', 'rest_days', 'opp_', 'games_last', 'fg_pct', 'usage'])]
features = [f for f in features if f in df.columns][:80]

print(f"✓ Using {len(features)} features")

# Get most recent stats for each player
latest_stats = df.sort_values('date').groupby('player_id').last().reset_index()

# Filter to active players (15+ min)
active_players = latest_stats[latest_stats['min_decimal'] >= 15]
print(f"✓ Found {len(active_players)} active players (15+ min)")

# Generate predictions
print("\nGenerating predictions...")
all_predictions = []

props = ['pts', 'reb', 'ast', 'stl', 'blk', 'fga', 'fgm', 'fta', 'ftm', 'pts_reb', 'pts_ast', 'reb_ast', 'pts_reb_ast']

for idx, player_row in active_players.iterrows():
    player_name = player_row['player_name']
    team_name = player_row['team']

    X = player_row[features].fillna(0).values.reshape(1, -1)

    pred_row = {
        'player_name': player_name,
        'team': team_name,
        'player_id': player_row['player_id'],
        'min_recent': player_row['min_decimal']
    }

    for prop in props:
        if prop in models:
            rf_pred = models[prop]['rf'].predict(X)[0]
            gb_pred = models[prop]['gb'].predict(X)[0]
            final_pred = 0.6 * rf_pred + 0.4 * gb_pred
            pred_row[f'{prop}_pred'] = round(final_pred, 1)

    all_predictions.append(pred_row)

# Create DataFrame
predictions_df = pd.DataFrame(all_predictions)

# Sort by minutes (most active players first)
predictions_df = predictions_df.sort_values('min_recent', ascending=False)

# Save
date_str = datetime.now().strftime('%Y%m%d')
output_file = f'predictions/tonight_{date_str}.csv'
predictions_df.to_csv(output_file, index=False)

print(f"\n✓ Generated predictions for {len(predictions_df)} players")
print(f"✓ Saved to: {output_file}")

# Show top 10
print("\nTop 10 players by minutes:")
print(predictions_df[['player_name', 'team', 'pts_pred', 'reb_pred', 'ast_pred']].head(10).to_string(index=False))

print("\n" + "="*80)
print("✅ PREDICTIONS COMPLETE")
print("="*80)
