#!/usr/bin/env python3
"""
VERIFY MODEL WORKS - QUICK TEST
"""
import sys
sys.path.insert(0, 'scripts/utils')

import pandas as pd
import numpy as np
import pickle

print("="*80)
print("VERIFYING MODEL IS READY FOR TOMORROW")
print("="*80)

# 1. Load model
print("\n[1/3] Loading model...")
try:
    with open('model_cache/trained_models.pkl', 'rb') as f:
        models = pickle.load(f)

    for prop in ['pts', 'reb', 'ast']:
        if prop not in models or models[prop] is None:
            print(f"❌ {prop.upper()} model MISSING")
            sys.exit(1)

        mae = models[prop]['val_results']['mae']
        print(f"✓ {prop.upper()}: MAE {mae:.2f}")

    print("\n✓ ALL MODELS LOADED SUCCESSFULLY")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# 2. Load recent data and test prediction
print("\n[2/3] Testing prediction on recent data...")
try:
    df = pd.read_csv('data/processed_training_data.csv')
    df['date'] = pd.to_datetime(df['date'])

    # Get most recent games
    recent = df.sort_values('date').tail(100)

    # Try to predict
    for prop in ['pts', 'reb', 'ast']:
        model = models[prop]

        # Get features
        feature_columns = [
            'min_decimal', 'pts_L3', 'pts_L5', 'pts_L7', 'pts_L10',
            'reb_L3', 'reb_L5', 'reb_L7', 'reb_L10',
            'ast_L3', 'ast_L5', 'ast_L7', 'ast_L10',
            'min_decimal_L3', 'min_decimal_L5', 'min_decimal_L7', 'min_decimal_L10',
            'fg_pct_L3', 'fg_pct_L5', 'fg_pct_L7', 'fg_pct_L10',
            'fg3_pct_L3', 'fg3_pct_L5', 'fg3_pct_L7', 'fg3_pct_L10',
            'ft_pct_L3', 'ft_pct_L5', 'ft_pct_L7', 'ft_pct_L10',
            'games_last_7', 'rest_days',
            'opp_def_rating', 'opp_off_rating', 'opp_pace'
        ]

        X = recent[feature_columns].fillna(0)

        # Predict using ensemble
        rf_pred = model['rf'].predict(X)
        gb_pred = model['gb'].predict(X)

        # Ensemble (60% RF, 40% GB)
        pred = 0.6 * rf_pred + 0.4 * gb_pred

        actual = recent[prop.upper()].values
        mae = np.mean(np.abs(pred - actual))

        print(f"  {prop.upper()}: Recent MAE {mae:.2f} ✓")

    print("\n✓ PREDICTIONS WORKING")

except Exception as e:
    print(f"❌ PREDICTION ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Check prediction script exists
print("\n[3/3] Checking prediction pipeline...")
import os

files_needed = [
    'scripts/prediction/generate_final_predictions.py',
    'scripts/prediction/run_daily_predictions.py',
    'data/team_ratings.csv'
]

for f in files_needed:
    if os.path.exists(f):
        print(f"  ✓ {f}")
    else:
        print(f"  ❌ MISSING: {f}")
        sys.exit(1)

print("\n" + "="*80)
print("✓ MODEL IS READY FOR TOMORROW")
print("="*80)
print("\nModel Performance:")
print(f"  Points:   MAE {models['pts']['val_results']['mae']:.2f}")
print(f"  Rebounds: MAE {models['reb']['val_results']['mae']:.2f}")
print(f"  Assists:  MAE {models['ast']['val_results']['mae']:.2f}")
print("\nTo generate tomorrow's predictions:")
print("  python scripts/prediction/run_daily_predictions.py")
print("="*80)
