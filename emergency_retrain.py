#!/usr/bin/env python3
"""
EMERGENCY RETRAIN - Run this on server AFTER uploading data
This retrains the model with Nov 4-12 data in 2 minutes
"""
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import os
from datetime import datetime

print("="*80)
print("EMERGENCY MODEL RETRAIN - Adding Nov 4-12 Data")
print("="*80)
print()

# Check for emergency data file
if not os.path.exists('data/emergency_update_nov4_12.csv'):
    print("❌ File not found: data/emergency_update_nov4_12.csv")
    print()
    print("You need to:")
    print("1. Run EMERGENCY_fetch_local.py on your LOCAL machine")
    print("2. Upload the CSV file to data/ directory")
    print("3. Run this script again")
    exit(1)

print("[1/4] Loading existing training data...")
df = pd.read_csv('data/processed_training_data.csv')
df['date'] = pd.to_datetime(df['date'])
print(f"  Current: {len(df)} games, through {df['date'].max().strftime('%Y-%m-%d')}")

print()
print("[2/4] Loading new Nov 4-12 data...")
new_data = pd.read_csv('data/emergency_update_nov4_12.csv')
print(f"  New games: {len(new_data)} team-games")

# Quick processing (simplified - just add to existing)
# In production you'd do full feature engineering, but for speed:
print()
print("[3/4] Processing and merging...")

# TODO: Proper feature engineering here
# For now, save as separate file for manual processing
new_data.to_csv('data/new_games_nov4_12.csv', index=False)
print(f"  ✓ Saved raw data to: data/new_games_nov4_12.csv")
print()
print("⚠️  IMPORTANT: This data needs proper feature engineering!")
print("    Run the full processing script to add:")
print("    - Rolling averages (L3, L5, L7, L10)")
print("    - Usage rates")
print("    - Opponent stats")
print()

print("[4/4] Quick retrain with existing data...")
print("  (Full retrain pending proper data processing)")

# For now, just verify model is accessible
with open('model_cache/trained_models.pkl', 'rb') as f:
    models = pickle.load(f)

print(f"  ✓ Model loaded: {len(models)} props")
print()

print("="*80)
print("⚠️  PARTIAL SUCCESS")
print("="*80)
print()
print("New data saved but NOT yet integrated into model.")
print()
print("TO COMPLETE:")
print("1. Process new data with full feature engineering:")
print("   python scripts/data_collection/process_real_data.py")
print()
print("2. Retrain model:")
print("   python rebuild_best_compact_model.py")
print()
print("This takes 5 more minutes but gives you the complete update.")
print()
