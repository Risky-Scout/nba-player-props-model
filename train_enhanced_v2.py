#!/usr/bin/env python3
"""
TRAIN ENHANCED V2 MODEL - SAFE VERSION
Saves to SEPARATE file: enhanced_v2_models.pkl
Does NOT touch: trained_models.pkl (your working model)
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import pickle
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("TRAINING ENHANCED V2 MODEL (SEPARATE FILE)")
print("="*80)
print("\n⚠️  SAFETY: Working model (trained_models.pkl) will NOT be touched")
print("✓ New model will be saved to: enhanced_v2_models.pkl\n")

# Load safe enhanced data
df = pd.read_csv('data/safe_enhanced_training_data.csv')
df['date'] = pd.to_datetime(df['date'])
print(f"✓ Loaded {len(df)} games with safe enhancements")

# Add combinations
df['pts_reb'] = df['pts'] + df['reb']
df['pts_ast'] = df['pts'] + df['ast']
df['reb_ast'] = df['reb'] + df['ast']
df['pts_reb_ast'] = df['pts'] + df['reb'] + df['ast']

# Add rolling for combos
df = df.sort_values(['player_id', 'date'])
for stat in ['pts_reb', 'pts_ast', 'reb_ast', 'pts_reb_ast']:
    for w in [3, 5, 7, 10]:
        df[f'{stat}_L{w}'] = df.groupby('player_id')[stat].transform(lambda x: x.rolling(w, min_periods=1).mean())

# Train/val split
split_idx = int(len(df) * 0.8)
df_sorted = df.sort_values('date')
train_df, val_df = df_sorted.iloc[:split_idx], df_sorted.iloc[split_idx:]

# Features (include new safe features)
features = [
    'min_decimal', 'is_home', 'rest_days', 'games_last_7',
    'pts_L3', 'pts_L5', 'pts_L7', 'pts_L10',
    'reb_L3', 'reb_L5', 'reb_L7', 'reb_L10',
    'ast_L3', 'ast_L5', 'ast_L7', 'ast_L10',
    'min_decimal_L3', 'min_decimal_L5', 'min_decimal_L7', 'min_decimal_L10',
    'fg_pct_L3', 'fg_pct_L5', 'fg_pct_L7', 'fg_pct_L10',
    'opp_def_rating', 'opp_off_rating', 'opp_pace',
    # NEW: Safe enhancements
    'home_away_pts_mult', 'home_away_reb_mult', 'home_away_ast_mult',
    'teammates_pts_avg', 'teammates_usage_avg',
    # Combos
    'pts_reb_L3', 'pts_reb_L5', 'pts_reb_L7', 'pts_reb_L10',
    'pts_ast_L3', 'pts_ast_L5', 'pts_ast_L7', 'pts_ast_L10',
    'reb_ast_L3', 'reb_ast_L5', 'reb_ast_L7', 'reb_ast_L10',
]

features = [f for f in features if f in df.columns]
print(f"✓ Using {len(features)} features (including home/away splits & teammate context)\n")

X_train, X_val = train_df[features].fillna(0), val_df[features].fillna(0)

# Train all props (100 trees)
props = ['pts', 'reb', 'ast', 'stl', 'blk', 'fga', 'fgm', 'fta', 'ftm', 'pts_reb', 'pts_ast', 'reb_ast', 'pts_reb_ast']
models = {}

print("Training Enhanced V2 (100 trees each)...\n")
for prop in props:
    y_train, y_val = train_df[prop].values, val_df[prop].values

    rf = RandomForestRegressor(n_estimators=100, max_depth=13, min_samples_split=8, n_jobs=-1, random_state=42)
    gb = GradientBoostingRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, subsample=0.85, random_state=42)

    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)

    pred = 0.6*rf.predict(X_val) + 0.4*gb.predict(X_val)
    mae = np.mean(np.abs(pred - y_val))

    models[prop] = {'rf': rf, 'gb': gb, 'val_results': {'mae': mae}}
    print(f"  {prop.upper():<15} MAE {mae:.2f}")

# Save to SEPARATE file
output_file = 'model_cache/enhanced_v2_models.pkl'
with open(output_file, 'wb') as f:
    pickle.dump(models, f)

print("\n" + "="*80)
print("✓ ENHANCED V2 MODEL SAVED")
print("="*80)
print(f"\n✓ Saved to: {output_file}")
print(f"✓ Working model still intact: model_cache/trained_models.pkl")

# Compare
print("\nCOMPARISON:")
print("-"*60)
print(f"{'Prop':<15} {'Original':<12} {'Enhanced V2':<12} {'Change':<12}")
print("-"*60)

orig = {
    'pts': 0.89, 'reb': 0.82, 'ast': 0.70,
    'stl': 0.31, 'blk': 0.20,
    'fga': 0.55, 'fgm': 0.28, 'fta': 0.61, 'ftm': 0.49,
    'pts_reb': 1.31, 'pts_ast': 1.15, 'reb_ast': 0.94, 'pts_reb_ast': 1.46
}

for prop in props:
    new_mae = models[prop]['val_results']['mae']
    old_mae = orig.get(prop, 0)
    if old_mae > 0:
        change = ((old_mae - new_mae) / old_mae * 100)
        symbol = "✓" if change > 0 else "✗"
        print(f"{prop.upper():<15} {old_mae:<12.2f} {new_mae:<12.2f} {symbol} {change:+.1f}%")

print("\n" + "="*80)
print("✅ SAFE: Your working model is untouched")
print("="*80)
