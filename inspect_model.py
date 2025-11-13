#!/usr/bin/env python3
import pickle

print("Loading model...")
with open('model_cache/trained_models.pkl', 'rb') as f:
    models = pickle.load(f)

print("\nModel structure:")
print(f"Type: {type(models)}")
print(f"Keys: {list(models.keys())}")

for key in models.keys():
    val = models[key]
    print(f"\n{key}:")
    print(f"  Type: {type(val)}")
    print(f"  Value: {val}")
    if val is not None:
        try:
            print(f"  Dir: {[x for x in dir(val) if not x.startswith('_')][:10]}")
        except:
            pass
