#!/usr/bin/env python3
"""
Save enhanced model with maximum compression
"""
import pickle
import sys

print("Loading enhanced model...")
with open('model_cache/enhanced_models.pkl', 'rb') as f:
    models = pickle.load(f)

print(f"✓ Loaded {len(models)} models")

# Save with highest compression protocol
print("\nSaving with maximum compression...")
with open('model_cache/trained_models.pkl', 'wb') as f:
    pickle.dump(models, f, protocol=pickle.HIGHEST_PROTOCOL)

import os
size = os.path.getsize('model_cache/trained_models.pkl') / (1024*1024)
print(f"✓ Saved: {size:.1f} MB")

# Verify it loads
print("\nVerifying...")
with open('model_cache/trained_models.pkl', 'rb') as f:
    test = pickle.load(f)
print(f"✓ Verified: {len(test)} models")
print(f"✓ PTS MAE: {test['pts']['val_results']['mae']:.2f}")
