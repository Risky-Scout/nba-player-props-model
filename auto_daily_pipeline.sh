#!/bin/bash
################################################################################
# AUTOMATIC DAILY NBA PREDICTION PIPELINE
# This script handles everything automatically:
#   - Morning (7 AM): Train model with latest data
#   - Afternoon (4:30 PM): Generate predictions + commit + push to GitHub
#
# Schedule with cron:
#   0 7 * * * cd /path/to/nba-player-props-model && ./auto_daily_pipeline.sh train
#   30 16 * * * cd /path/to/nba-player-props-model && ./auto_daily_pipeline.sh predict
################################################################################

set -e  # Exit on error

MODE=${1:-predict}  # Default to predict if no argument
DATE=$(date +%Y-%m-%d)
BRANCH="claude/zip-nba-dashboard-011CV3ZYXGBaGVj5fC5UyMia"  # Branch for production predictions

echo "================================================================================"
echo "NBA PREDICTION PIPELINE - $MODE MODE"
echo "Date: $DATE"
echo "================================================================================"

cd "$(dirname "$0")"

if [ "$MODE" == "train" ]; then
    echo ""
    echo "🔄 TRAINING MODEL WITH LATEST DATA..."
    echo "--------------------------------------------------------------------------------"

    # Collect latest data
    echo "Collecting current season data..."
    python scripts/data_collection/collect_current_season_data.py || {
        echo "❌ Data collection failed"
        exit 1
    }

    # Train model
    echo "Training model..."
    python scripts/training/train_latest_model.py || {
        echo "❌ Model training failed"
        exit 1
    }

    echo "✅ Model training complete!"

elif [ "$MODE" == "predict" ]; then
    echo ""
    echo "🎯 GENERATING PREDICTIONS FOR $DATE..."
    echo "--------------------------------------------------------------------------------"

    # Try to fetch games automatically
    echo "Fetching today's games..."
    GAMES=$(python scripts/utils/fetch_todays_games.py 2>/dev/null)

    # If auto-fetch fails, try todays_games.txt file
    if [ -z "$GAMES" ] && [ -f "todays_games.txt" ]; then
        echo "Auto-fetch failed, using todays_games.txt..."
        GAMES=$(grep -v "^#" todays_games.txt | grep -v "^$" | tr '\n' ',' | sed 's/,$//' | tr -d ' ')
    fi

    # If still no games, exit
    if [ -z "$GAMES" ]; then
        echo "❌ No games found!"
        echo "Please update todays_games.txt or provide games manually"
        exit 1
    fi

    echo "Games: $GAMES"
    echo ""

    # Generate daily predictions with injury adjustments
    echo "Generating daily predictions..."
    python scripts/prediction/run_daily_predictions.py --date "$DATE" --games "$GAMES" --injuries "data/injuries/injuries_$DATE.csv" || {
        echo "⚠️  Daily predictions failed, continuing with comprehensive predictions..."
    }

    # Generate comprehensive predictions (PMF, SGPs, props)
    echo "Generating comprehensive predictions (PMF, SGPs, correlations)..."
    python scripts/prediction/generate_final_predictions.py "$DATE" || {
        echo "❌ Prediction generation failed"
        exit 1
    }

    # Generate premium predictions (Top 100s + Client Deliverable)
    echo "Generating premium predictions (Top 100s + Client Deliverable)..."
    python scripts/prediction/generate_premium_predictions.py "$DATE" || {
        echo "⚠️  Premium predictions failed, continuing..."
    }

    echo ""
    echo "📊 Committing predictions to GitHub..."
    echo "--------------------------------------------------------------------------------"

    # Stage all new prediction files (including premium folder)
    git add predictions/*$DATE* predictions/*$(date +%Y%m%d)* predictions/premium/* 2>/dev/null || true

    # Check if there are changes to commit
    if git diff --staged --quiet; then
        echo "ℹ️  No new predictions to commit"
    else
        # Commit with automatic message
        git commit -m "Auto-generate predictions for $DATE

- Complete PMF distributions
- 2-leg and 3-leg SGP recommendations with correlations
- Top individual props
- Top 100 same-game parlays (2-leg and 3-leg)
- Top 100 cross-game parlays (2-leg and 3-leg)
- Premium client deliverable
- Generated at $(date +'%I:%M %p')

[Automated Daily Pipeline]"

        # Push to GitHub
        echo "Pushing to GitHub..."
        git push -u origin "$BRANCH" || {
            echo "⚠️  Push failed - will retry..."
            sleep 2
            git push -u origin "$BRANCH" || {
                echo "❌ Push failed after retry"
                exit 1
            }
        }

        echo "✅ Predictions committed and pushed to GitHub!"
    fi

    echo ""
    echo "📋 PREDICTION SUMMARY"
    echo "--------------------------------------------------------------------------------"
    cat predictions/summary_$(date +%Y%m%d).txt 2>/dev/null || echo "Summary file not found"

else
    echo "❌ Invalid mode: $MODE"
    echo "Usage: $0 [train|predict]"
    exit 1
fi

echo ""
echo "================================================================================"
echo "✅ PIPELINE COMPLETE - $MODE"
echo "================================================================================"
