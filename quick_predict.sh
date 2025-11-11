#!/bin/bash
################################################################################
# QUICK PREDICTION GENERATOR
# Simple one-command prediction generation
#
# Usage:
#   ./quick_predict.sh "GSW@OKC,IND@UTA,TOR@BKN,BOS@PHI,DEN@SAC"
#
# This will:
#   1. Generate all predictions (PMF, SGPs, individual props)
#   2. Auto-commit and push to GitHub
#   3. Display summary
################################################################################

set -e

DATE=$(date +%Y-%m-%d)
GAMES=${1:-""}
BRANCH="claude/nba-prop-model-training-011CV1dsbtVTuFpucny19p6F"

# If no games provided as argument, try to auto-fetch
if [ -z "$GAMES" ]; then
    echo "No games provided, attempting auto-fetch..."
    GAMES=$(python scripts/utils/fetch_todays_games.py 2>/dev/null)

    # If auto-fetch fails, try todays_games.txt
    if [ -z "$GAMES" ] && [ -f "todays_games.txt" ]; then
        echo "Auto-fetch failed, reading from todays_games.txt..."
        GAMES=$(grep -v "^#" todays_games.txt | grep -v "^$" | tr '\n' ',' | sed 's/,$//' | tr -d ' ')
    fi

    # If still no games, show error
    if [ -z "$GAMES" ]; then
        echo "❌ No games found!"
        echo ""
        echo "Usage: $0 \"AWAY@HOME,AWAY@HOME,...\""
        echo "Example: $0 \"GSW@OKC,IND@UTA,TOR@BKN\""
        echo ""
        echo "Or update todays_games.txt file"
        exit 1
    fi
fi

echo "================================================================================"
echo "🏀 QUICK NBA PREDICTIONS FOR $DATE"
echo "================================================================================"
echo "Games: $GAMES"
echo ""

# Generate comprehensive predictions (PMF + SGPs)
echo "📊 Generating comprehensive predictions..."
python scripts/prediction/generate_final_predictions.py "$DATE"

echo ""
echo "✅ Predictions generated!"
echo ""

# Commit and push
echo "📤 Committing to GitHub..."
git add predictions/*$(date +%Y%m%d)* scripts/prediction/generate_final_predictions.py 2>/dev/null || true

if ! git diff --staged --quiet; then
    git commit -m "Generate predictions for $DATE

Games: $GAMES

Auto-generated at $(date +'%I:%M %p')"

    git push -u origin "$BRANCH"
    echo "✅ Pushed to GitHub!"
else
    echo "ℹ️  No changes to commit"
fi

echo ""
echo "================================================================================"
echo "📋 TOP PREDICTIONS SUMMARY"
echo "================================================================================"
cat predictions/summary_$(date +%Y%m%d).txt

echo ""
echo "================================================================================"
echo "✅ DONE! Check predictions/ folder for full details"
echo "================================================================================"
