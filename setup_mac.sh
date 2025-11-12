#!/bin/bash
################################################################################
# ONE-COMMAND SETUP FOR MAC
# Sets up complete automation on your local machine
#
# Usage:
#   chmod +x setup_mac.sh
#   ./setup_mac.sh
################################################################################

set -e

echo "================================================================================"
echo "🏀 NBA PLAYER PROPS - MAC SETUP"
echo "================================================================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Step 1: Pull latest code from GitHub..."
git pull origin claude/zip-nba-dashboard-011CV3ZYXGBaGVj5fC5UyMia

echo ""
echo "🐍 Step 2: Install Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "🤖 Step 3: Install cron jobs..."
chmod +x install_cron.sh fetch_injuries.sh quick_predict.sh auto_daily_pipeline.sh
./install_cron.sh

echo ""
echo "✅ Step 4: Test installation..."
echo "Git status:"
git status | head -5

echo ""
echo "Python packages:"
pip3 list | grep -E "pandas|numpy|scikit|xgboost" | head -5

echo ""
echo "Cron jobs:"
crontab -l | grep -v "^#" | grep nba

echo ""
echo "================================================================================"
echo "✅ SETUP COMPLETE!"
echo "================================================================================"
echo ""
echo "🎯 What happens now:"
echo "  - 7:00 AM CST: Model trains automatically"
echo "  - 5:45 PM CST: Injury report fetched"
echo "  - 6:00 PM CST: Predictions generated"
echo ""
echo "📊 Check predictions:"
echo "  cat predictions/summary_\$(date +%Y%m%d).txt"
echo ""
echo "📝 View logs:"
echo "  tail -f logs/cron_train.log"
echo "  tail -f logs/cron_injuries.log"
echo "  tail -f logs/cron_predict.log"
echo ""
echo "🎉 You're all set! Everything runs automatically now."
echo ""
