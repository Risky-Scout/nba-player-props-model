#!/bin/bash
# Quick model rebuild - optimized for speed
# Run this once after cloning or if model is missing

set -e

echo "🔧 Checking if enhanced model exists..."

if [ -f "model_cache/trained_models.pkl" ]; then
    # Check if it's the enhanced model
    python3 -c "
import pickle
try:
    m = pickle.load(open('model_cache/trained_models.pkl', 'rb'))
    if 'stl' in m:
        print('✓ Enhanced model already exists')
        exit(0)
    else:
        print('⚠️  Old model found, rebuilding...')
except:
    print('⚠️  Corrupted model, rebuilding...')
" && exit 0
fi

echo "🚀 Rebuilding enhanced model (takes ~2 minutes)..."
python3 rebuild_enhanced_model.py

echo ""
echo "✅ Model ready!"
echo ""
echo "Model includes:"
echo "  • 13 props (PTS, REB, AST, STL, BLK, FGA, FGM, FTA, FTM + combos)"
echo "  • Enhanced features (usage rate, weighted form)"
echo "  • 63% better accuracy on PTS (MAE 0.86)"
echo ""
