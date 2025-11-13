#!/usr/bin/env python3
"""
TEST ACTUAL MODEL PERFORMANCE
Find out what the model REALLY does
"""

import sys
sys.path.insert(0, 'scripts/utils')

import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split

print("="*80)
print("TESTING REAL MODEL PERFORMANCE")
print("="*80)

# Load model
print("\n[1/4] Loading model...")
try:
    with open('model_cache/trained_models.pkl', 'rb') as f:
        models = pickle.load(f)
    print(f"✓ Loaded models: {list(models.keys())}")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    sys.exit(1)

# Load data
print("\n[2/4] Loading training data...")
try:
    df = pd.read_csv('data/processed_training_data.csv')
    print(f"✓ Loaded {len(df)} games")
    print(f"✓ Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"✓ Columns: {len(df.columns)}")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    sys.exit(1)

# Create temporal test split (last 20%)
print("\n[3/4] Creating test split...")
df['date'] = pd.to_datetime(df['date'])
df_sorted = df.sort_values('date')
split_idx = int(len(df_sorted) * 0.8)
train_df = df_sorted.iloc[:split_idx]
test_df = df_sorted.iloc[split_idx:]

print(f"✓ Train: {len(train_df)} games ({train_df['date'].min()} to {train_df['date'].max()})")
print(f"✓ Test:  {len(test_df)} games ({test_df['date'].min()} to {test_df['date'].max()})")

# Test each model
print("\n[4/4] Testing models on holdout data...")
print("="*80)

results = {}

for prop_type in ['PTS', 'REB', 'AST']:
    print(f"\n{prop_type} Model:")
    print("-" * 40)

    if prop_type not in models or models[prop_type] is None:
        print(f"  ⚠️  No model found for {prop_type}")
        continue

    model = models[prop_type]

    # Get test data
    y_test = test_df[prop_type].values

    # Try to predict
    try:
        # The model expects specific features - let's prepare them
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

        # Check which features exist
        available_features = [f for f in feature_columns if f in test_df.columns]

        if len(available_features) == 0:
            print(f"  ❌ No matching features found!")
            print(f"  Available columns: {list(test_df.columns[:10])}")
            continue

        X_test = test_df[available_features].fillna(0)

        # Predict
        y_pred = model.predict(X_test)

        # Calculate metrics
        mae = np.mean(np.abs(y_pred - y_test))
        rmse = np.sqrt(np.mean((y_pred - y_test)**2))
        within_3 = np.mean(np.abs(y_pred - y_test) <= 3) * 100
        within_5 = np.mean(np.abs(y_pred - y_test) <= 5) * 100

        # Calculate "over/under" accuracy
        # For this, we'd need actual lines, but we can estimate using median
        median_val = np.median(y_test)
        correct_direction = np.mean((y_pred > median_val) == (y_test > median_val)) * 100

        print(f"  MAE:              {mae:.2f}")
        print(f"  RMSE:             {rmse:.2f}")
        print(f"  Within ±3:        {within_3:.1f}%")
        print(f"  Within ±5:        {within_5:.1f}%")
        print(f"  Direction Acc:    {correct_direction:.1f}%")

        results[prop_type] = {
            'mae': mae,
            'rmse': rmse,
            'within_3': within_3,
            'within_5': within_5
        }

    except Exception as e:
        print(f"  ❌ Error testing {prop_type}: {e}")
        import traceback
        traceback.print_exc()

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if results:
    print("\nREAL MODEL PERFORMANCE:")
    print("-" * 40)
    for prop_type, metrics in results.items():
        print(f"{prop_type:4}: MAE {metrics['mae']:.2f}  |  Within ±3: {metrics['within_3']:.1f}%")
else:
    print("\n⚠️  Could not test models - check errors above")

print("\n" + "="*80)
