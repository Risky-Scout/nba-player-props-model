#!/bin/bash
################################################################################
# Install Cron Job for Daily NBA Predictions
# Sets up automatic predictions every day at 4:30 PM
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================================================"
echo "NBA DAILY PREDICTIONS - CRON INSTALLATION"
echo "================================================================================"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Create crontab entry
cat > /tmp/nba_predictions_cron.txt << CRONEOF
# NBA Player Props - Daily Predictions
# System timezone: UTC (CST is UTC-6, EST is UTC-5)
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin
MAILTO=""

# Generate predictions every day at 4:30 PM CST (22:30 UTC / 10:30 PM UTC)
30 22 * * * cd $SCRIPT_DIR && ./daily_predictions.sh >> logs/daily_predictions.log 2>&1
CRONEOF

# Install crontab
if command -v crontab &> /dev/null; then
    crontab /tmp/nba_predictions_cron.txt
    rm /tmp/nba_predictions_cron.txt

    echo "✅ Cron job installed successfully!"
    echo ""
    echo "📅 Schedule:"
    echo "  - Daily predictions: 4:30 PM CST (10:30 PM UTC) every day"
    echo ""
    echo "📋 Verify installation:"
    echo "  crontab -l"
    echo ""
    echo "📊 View logs:"
    echo "  tail -f $SCRIPT_DIR/logs/daily_predictions.log"
    echo ""
    echo "🤖 What happens automatically:"
    echo "  1. Fetches today's games (4:30 PM)"
    echo "  2. Loads injury report if available"
    echo "  3. Generates predictions with injury adjustments"
    echo "  4. Creates diverse parlays (151+ unique players)"
    echo "  5. Outputs to predictions/ folder"
    echo ""
    echo "📝 Manual workflow for injuries:"
    echo "  Before 4:30 PM, create: data/injuries/injuries_YYYY-MM-DD.csv"
    echo "  Format: player_name,status"
    echo "  Example: LeBron James,OUT"
    echo ""
    echo "📝 Manual workflow for games:"
    echo "  If auto-fetch fails, create: todays_games.txt"
    echo "  Format: AWAY@HOME (one per line)"
    echo "  Example: DAL@WAS"
    echo ""
    echo "⚙️  Model updates:"
    echo "  Current model: Nov 3, 2025 (PTS MAE 0.89 - ELITE)"
    echo "  Update frequency: Weekly (recommended)"
    echo "  Update script: scripts/data_collection/fetch_weekly_data.py"
    echo "  Note: Run data fetch LOCALLY (APIs blocked in container)"
    echo ""
else
    echo "❌ Error: crontab command not found"
    echo "Please install cron: sudo apt-get install cron"
    exit 1
fi

echo "================================================================================"
echo "✅ AUTOMATION READY"
echo "================================================================================"
echo ""
echo "Your daily predictions will now run automatically at 4:30 PM CST!"
echo ""
