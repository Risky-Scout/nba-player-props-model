#!/bin/bash
################################################################################
# Fetch NBA Injury Report
# Simple wrapper around the Python injury fetcher
#
# Usage:
#   ./fetch_injuries.sh              # Fetch today's report
#   ./fetch_injuries.sh 2025-11-12   # Fetch specific date
################################################################################

DATE=${1:-$(date +%Y-%m-%d)}

echo "Fetching NBA injury report for $DATE..."

python scripts/utils/fetch_injuries.py "$DATE"

# Check if file was created
INJURY_FILE="data/injuries/injuries_$DATE.csv"

if [ -f "$INJURY_FILE" ]; then
    echo "✅ Injury file ready: $INJURY_FILE"
    echo ""
    echo "Preview:"
    head -10 "$INJURY_FILE"
else
    echo "⚠️  Injury file not created automatically"
    echo ""
    echo "Manual steps:"
    echo "  1. Download from: https://ak-static.cms.nba.com/referee/injury/Injury-Report_${DATE}_0530PM.pdf"
    echo "  2. Create CSV at: $INJURY_FILE"
    echo ""
    echo "CSV format:"
    echo "  player,status,reason,out_flag,questionable_flag,probable_flag,game_date"
    echo "  LeBron James,Out,Right ankle sprain,1,0,0,$DATE"
fi
