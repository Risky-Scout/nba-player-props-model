#!/usr/bin/env python3
"""
Automatically loads the model (decompresses if needed)
"""
import os
import tarfile
import pickle

MODEL_PATH = 'model_cache/trained_models.pkl'
COMPRESSED_PATH = 'model_cache/trained_models.pkl.tar.gz'

def load_model():
    """Load model, decompressing if necessary"""

    # If model exists, load it
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)

    # If compressed version exists, decompress
    if os.path.exists(COMPRESSED_PATH):
        print("📦 Decompressing model (one-time)...")
        with tarfile.open(COMPRESSED_PATH, 'r:gz') as tar:
            tar.extractall('model_cache/')
        print("✓ Model ready")

        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)

    # Need to rebuild
    print("❌ Model not found. Run: python rebuild_compact_model.py")
    return None

if __name__ == '__main__':
    models = load_model()
    if models:
        print(f"\n✓ Loaded {len(models)} prop models")
        print("Models:", list(models.keys()))
