#!/bin/bash
#
# MASTER SCRIPT: Generate Elite NBA Predictions
# Runs training + prediction pipeline automatically
#

set -e  # Exit on error

echo "================================================================================"
echo "🏀 ELITE NBA PLAYER PROPS PREDICTION PIPELINE 🏀"
echo "================================================================================"
echo ""

# Check if training data exists
if [ ! -f "data/nba_training_data_real.csv" ]; then
    echo "❌ ERROR: Training data not found!"
    echo "Please run: python scripts/data_collection/collect_historical_training_data.py"
    exit 1
fi

echo "✓ Training data found"
echo ""

# Step 1: Train the model
echo "================================================================================"
echo "STEP 1: TRAINING ELITE MODEL"
echo "================================================================================"
python scripts/training/train_elite_model.py data/nba_training_data_real.csv

if [ $? -ne 0 ]; then
    echo "❌ Training failed!"
    exit 1
fi

echo ""
echo "✓ Model training complete"
echo ""

# Step 2: Generate predictions
echo "================================================================================"
echo "STEP 2: GENERATING ELITE PREDICTIONS"
echo "================================================================================"
python scripts/prediction/elite_prediction_system.py

if [ $? -ne 0 ]; then
    echo "❌ Prediction generation failed!"
    exit 1
fi

echo ""
echo "================================================================================"
echo "🎯 ELITE PREDICTIONS COMPLETE! 🎯"
echo "================================================================================"
echo ""
echo "Check the predictions/ directory for:"
echo "  - predictions_TIMESTAMP.csv (full predictions)"
echo "  - sgps_TIMESTAMP.csv (SGP recommendations)"
echo "  - summary_TIMESTAMP.txt (human-readable summary)"
echo ""
echo "================================================================================"
