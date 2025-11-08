#!/bin/bash

################################################################################
# DAILY NBA PREDICTIONS UPDATE SCRIPT
# Run this once per day to:
# 1. Collect latest NBA game data
# 2. Retrain model with new games
# 3. Generate predictions for tonight
################################################################################

echo "================================================================================"
echo "NBA PLAYER PROPS MODEL - DAILY UPDATE"
echo "================================================================================"
echo ""
echo "Started at: $(date)"
echo ""

# Step 1: Collect current season data
echo "STEP 1: Collecting current season data..."
echo "--------------------------------------------------------------------------------"
python collect_current_season_data.py
if [ $? -ne 0 ]; then
    echo "ERROR: Data collection failed"
    exit 1
fi
echo ""

# Step 2: Train model on latest data
echo "STEP 2: Training model on latest data..."
echo "--------------------------------------------------------------------------------"
python train_latest_model.py
if [ $? -ne 0 ]; then
    echo "ERROR: Model training failed"
    exit 1
fi
echo ""

# Step 3: Generate tonight's predictions
echo "STEP 3: Generating tonight's predictions..."
echo "--------------------------------------------------------------------------------"
python generate_tonight_predictions.py
if [ $? -ne 0 ]; then
    echo "ERROR: Prediction generation failed"
    exit 1
fi
echo ""

echo "================================================================================"
echo "✓ DAILY UPDATE COMPLETE"
echo "================================================================================"
echo "Completed at: $(date)"
echo ""
echo "Check predictions/tonight_predictions.csv for tonight's picks!"
echo "================================================================================"
