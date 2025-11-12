#!/bin/bash
################################################################################
# NBA Player Props Model - Cron Job Installer
# Run this once on your server to set up daily automation
#
# Usage:
#   chmod +x install_cron.sh
#   ./install_cron.sh
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================================================"
echo "NBA PLAYER PROPS MODEL - CRON INSTALLATION"
echo "================================================================================"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Create crontab entries
cat > /tmp/nba_cron_temp.txt << CRONEOF
# NBA Player Props Model - Daily Automation
# System timezone: UTC (CST is UTC-6, EST is UTC-5)
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=""

# Train model every morning at 7:00 AM CST (13:00 UTC / 1:00 PM UTC)
0 13 * * * cd $SCRIPT_DIR && ./auto_daily_pipeline.sh train >> logs/cron_train.log 2>&1

# Fetch injury report at 5:45 PM CST (23:45 UTC / 11:45 PM UTC)
45 23 * * * cd $SCRIPT_DIR && ./fetch_injuries.sh >> logs/cron_injuries.log 2>&1

# Generate predictions every evening at 6:00 PM CST (00:00 UTC / midnight UTC next day)
0 0 * * * cd $SCRIPT_DIR && ./auto_daily_pipeline.sh predict >> logs/cron_predict.log 2>&1
CRONEOF

# Install crontab
if command -v crontab &> /dev/null; then
    crontab /tmp/nba_cron_temp.txt
    rm /tmp/nba_cron_temp.txt

    echo "✅ Cron jobs installed successfully!"
    echo ""
    echo "📅 Schedule:"
    echo "  - Daily training:     7:00 AM CST (1:00 PM UTC)"
    echo "  - Fetch injuries:     5:45 PM CST (11:45 PM UTC)"
    echo "  - Daily predictions:  6:00 PM CST (midnight UTC)"
    echo ""
    echo "📋 Verify installation:"
    echo "  crontab -l"
    echo ""
    echo "📊 View logs:"
    echo "  tail -f $SCRIPT_DIR/logs/cron_train.log"
    echo "  tail -f $SCRIPT_DIR/logs/cron_injuries.log"
    echo "  tail -f $SCRIPT_DIR/logs/cron_predict.log"
    echo ""
    echo "🤖 What happens automatically:"
    echo "  1. Model trains with latest data (7 AM)"
    echo "  2. Injury report fetched (5:45 PM)"
    echo "  3. Predictions generated with injuries (6 PM)"
    echo "  4. Everything committed & pushed to GitHub"
    echo ""
    echo "⚠️  NOTE: If injury fetch fails, manually create:"
    echo "  data/injuries/injuries_YYYY-MM-DD.csv"
    echo ""
else
    echo "❌ Error: crontab command not found"
    echo "Please install cron: sudo apt-get install cron"
    exit 1
fi
