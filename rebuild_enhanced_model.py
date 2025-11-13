#!/usr/bin/env python3
"""
ALL-IN-ONE: Rebuild enhanced model with all improvements
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import pickle
import warnings
warnings.filterwarnings('ignore')

print("REBUILDING ENHANCED MODEL - ALL IN ONE")
print("="*80)

# Load data
df = pd.read_csv('data/processed_training_data.csv')
df['date'] = pd.to_datetime(df['date'])
print(f"✓ Loaded {len(df)} games")

# Add usage rate
df['usage_rate'] = (df['fga'] + 0.44*df['fta'] + df['turnover']) / ((df.get('opp_pace', 100) * df['min_decimal'] / 48).replace(0, 1))
df['usage_rate'] = df['usage_rate'].clip(0, 0.5)

# Add combinations
df['pts_reb'] = df['pts'] + df['reb']
df['pts_ast'] = df['pts'] + df['ast']
df['reb_ast'] = df['reb'] + df['ast']
df['pts_reb_ast'] = df['pts'] + df['reb'] + df['ast']

# Add rolling averages
df = df.sort_values(['player_id', 'date'])
for stat in ['stl', 'blk', 'fga', 'fgm', 'fta', 'ftm', 'pts_reb', 'pts_ast', 'reb_ast', 'pts_reb_ast', 'usage_rate']:
    for w in [3, 5, 7, 10]:
        df[f'{stat}_L{w}'] = df.groupby('player_id')[stat].transform(lambda x: x.rolling(w, min_periods=1).mean())

print(f"✓ Added enhanced features")

# Train/val split
split_idx = int(len(df) * 0.8)
df_sorted = df.sort_values('date')
train_df, val_df = df_sorted.iloc[:split_idx], df_sorted.iloc[split_idx:]

# Features
features = [c for c in df.columns if any(x in c for x in ['_L3', '_L5', '_L7', '_L10', 'min_decimal', 'is_home', 'rest_days', 'opp_', 'games_last', 'fg_pct', 'usage'])]
features = [f for f in features if f in df.columns][:80]  # Limit to 80 best

X_train, X_val = train_df[features].fillna(0), val_df[features].fillna(0)

# Train all props
props = ['pts', 'reb', 'ast', 'stl', 'blk', 'fga', 'fgm', 'fta', 'ftm', 'pts_reb', 'pts_ast', 'reb_ast', 'pts_reb_ast']
models = {}

for prop in props:
    print(f"\nTraining {prop.upper()}...", end=' ')
    y_train, y_val = train_df[prop].values, val_df[prop].values

    rf = RandomForestRegressor(n_estimators=200, max_depth=15, n_jobs=-1, random_state=42)
    gb = GradientBoostingRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42)

    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)

    pred = 0.6*rf.predict(X_val) + 0.4*gb.predict(X_val)
    mae = np.mean(np.abs(pred - y_val))

    models[prop] = {'rf': rf, 'gb': gb, 'val_results': {'mae': mae}}
    print(f"MAE {mae:.2f}")

# Save
with open('model_cache/enhanced_models.pkl', 'wb') as f:
    pickle.dump(models, f)

with open('model_cache/trained_models.pkl', 'wb') as f:
    pickle.dump(models, f)

print("\n" + "="*80)
print("✓ ENHANCED MODEL COMPLETE")
print("="*80)
for prop in props:
    print(f"{prop.upper():<15} MAE {models[prop]['val_results']['mae']:.2f}")
print("="*80)
