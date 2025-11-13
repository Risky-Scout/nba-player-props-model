#!/usr/bin/env python3
"""
Save with joblib compression (better for sklearn)
"""
import pickle
import joblib

print("Loading enhanced model...")
with open('model_cache/enhanced_models.pkl', 'rb') as f:
    models = pickle.load(f)

print(f"✓ Loaded {len(models)} models")

# Save with joblib compression (level 9 = max)
print("\nSaving with joblib compression...")
joblib.dump(models, 'model_cache/trained_models_compressed.pkl', compress=9)

import os
size = os.path.getsize('model_cache/trained_models_compressed.pkl') / (1024*1024)
print(f"✓ Saved: {size:.1f} MB")

# Verify
print("\nVerifying...")
test = joblib.load('model_cache/trained_models_compressed.pkl')
print(f"✓ Verified: {len(test)} models")
print(f"✓ PTS MAE: {test['pts']['val_results']['mae']:.2f}")
