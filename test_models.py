#!/usr/bin/env python3
"""
Compare current model vs the good model from Nov 8
"""
import pickle
import sys

print("="*80)
print("COMPARING MODELS")
print("="*80)

try:
    # Load good model
    with open('/tmp/good_model.pkl', 'rb') as f:
        good_model = pickle.load(f)
    print("\n✓ Loaded GOOD model (Nov 8)")

    # Load current model
    with open('model_cache/trained_models.pkl', 'rb') as f:
        current_model = pickle.load(f)
    print("✓ Loaded CURRENT model")

    print("\n" + "="*80)
    print("MODEL COMPARISON")
    print("="*80)

    # Check what's in each
    print("\nGOOD MODEL keys:", list(good_model.keys()))
    print("\nCURRENT MODEL keys:", list(current_model.keys()))

    # Check if they're the same
    if str(good_model.keys()) == str(current_model.keys()):
        print("\n✓ Same model structure")

        # Check model sizes
        import sys
        good_size = sys.getsizeof(str(good_model))
        current_size = sys.getsizeof(str(current_model))

        print(f"\nGOOD model size: ~{good_size:,} bytes")
        print(f"CURRENT model size: ~{current_size:,} bytes")

        if good_size != current_size:
            print("\n⚠️  MODELS ARE DIFFERENT!")
            print("The current model is NOT the same as the good Nov 8 model")
        else:
            print("\n✓ Models appear identical")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("SOLUTION")
print("="*80)
print("\n1. The GOOD model from Nov 8 had these test results:")
print("   PTS MAE: 2.31 (excellent)")
print("   REB MAE: 1.05 (excellent)")
print("   AST MAE: 0.80 (excellent)")
print("\n2. The CURRENT model shows:")
print("   PTS MAE: 3.80 (worse)")
print("   REB MAE: 1.57 (worse)")
print("   AST MAE: 1.09 (worse)")
print("\n3. TO FIX: Restore the Nov 8 model")
print("   cp /tmp/good_model.pkl model_cache/trained_models.pkl")
print("\n" + "="*80)
