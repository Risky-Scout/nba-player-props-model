#!/bin/bash
################################################################################
# DAILY PREDICTIONS - Streamlined Version
# Generates predictions with current model + injury adjustments
# Run this every day at 4:30 PM before games start
################################################################################

set -e

DATE=$(date +%Y-%m-%d)
DATETIME=$(date +'%Y%m%d')

echo "================================================================================"
echo "NBA DAILY PREDICTIONS - $DATE"
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

# Step 1: Fetch today's games automatically
echo "[1/4] Fetching today's games..."
echo "--------------------------------------------------------------------------------"

GAMES=$(timeout 10 python scripts/utils/fetch_todays_games.py 2>/dev/null || echo "")

if [ -z "$GAMES" ]; then
    echo "⚠️  Auto-fetch failed. Checking todays_games.txt..."

    if [ -f "todays_games.txt" ]; then
        GAMES=$(grep -v "^#" todays_games.txt | grep -v "^$" | tr '\n' ',' | sed 's/,$//' | tr -d ' ')
    fi

    if [ -z "$GAMES" ]; then
        echo "❌ No games found!"
        echo ""
        echo "Please create todays_games.txt with format:"
        echo "  DAL@WAS"
        echo "  TOR@PHI"
        echo "  CHI@CLE"
        exit 1
    fi
fi

echo "✓ Today's games: $GAMES"
echo ""

# Step 2: Check for injury report
echo "[2/4] Checking for injury report..."
echo "--------------------------------------------------------------------------------"

INJURY_FILE="data/injuries/injuries_$DATE.csv"

if [ ! -f "$INJURY_FILE" ]; then
    echo "⚠️  No injury file found: $INJURY_FILE"
    echo "   Predictions will run without injury adjustments"
    INJURY_FILE=""
else
    echo "✓ Found injury report: $INJURY_FILE"
fi

echo ""

# Step 3: Generate predictions
echo "[3/4] Generating predictions..."
echo "--------------------------------------------------------------------------------"

python scripts/prediction/generate_today_predictions.py

if [ $? -ne 0 ]; then
    echo "❌ Prediction generation failed!"
    exit 1
fi

echo ""

# Step 4: Generate diverse parlays
echo "[4/4] Generating diverse parlays..."
echo "--------------------------------------------------------------------------------"

PRED_FILE="predictions/tonight_INJURY_ADJUSTED_${DATETIME}.csv"

if [ ! -f "$PRED_FILE" ]; then
    # Try without injury adjusted
    PRED_FILE="predictions/tonight_${DATETIME}.csv"
fi

if [ -f "$PRED_FILE" ]; then
    python scripts/prediction/generate_diverse_parlays.py "$PRED_FILE"
    echo "✓ Diverse parlays generated"
else
    echo "⚠️  Prediction file not found, skipping parlays"
fi

echo ""
echo "================================================================================"
echo "✅ DAILY PREDICTIONS COMPLETE"
echo "================================================================================"
echo ""
echo "📁 Output files:"
echo "   predictions/tonight_INJURY_ADJUSTED_${DATETIME}.csv"
echo "   predictions/tonight_INJURY_ADJUSTED_${DATETIME}_DIVERSE_PARLAYS.csv"
echo ""
echo "================================================================================"
