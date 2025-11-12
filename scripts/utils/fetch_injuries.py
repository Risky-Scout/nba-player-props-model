#!/usr/bin/env python3
"""
Fetch NBA Injury Report and Convert to CSV
Automatically downloads and processes the official NBA injury report

Usage:
    python fetch_injuries.py                    # Fetch today's report
    python fetch_injuries.py 2025-11-12         # Fetch specific date
"""

import sys
import requests
from datetime import datetime
import pandas as pd
import os

def fetch_injury_report_html(date_str=None):
    """
    Fetch injury report from NBA API (JSON format)
    This is easier than parsing PDFs
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')

    print(f"Fetching injury report for {date_str}...")

    # Try multiple NBA API endpoints
    endpoints = [
        # Official NBA stats API
        f"https://stats.nba.com/stats/leaguedashplayerstats?Season=2025-26&SeasonType=Regular+Season",
        # Alternative: Try the roster endpoint with injury info
        "https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2025/players.json"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nba.com/'
    }

    # For now, let's use a simpler approach: screen scraping the official page
    # NBA publishes injury reports here: https://official.nba.com/nba-injury-report-2025-26-season/

    try:
        # Try to fetch from the official NBA injury report page
        url = "https://ak-static.cms.nba.com/referee/injury/Injury-Report.json"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return parse_nba_json_report(data, date_str)
    except Exception as e:
        print(f"JSON API failed: {e}")

    # Fallback: Try to parse from PDF (requires pypdf2)
    print("Trying PDF fallback...")
    return fetch_from_pdf(date_str)


def parse_nba_json_report(data, date_str):
    """Parse NBA JSON injury report"""
    injuries = []

    # The structure varies, but typically:
    # data['teams'] -> each team has 'players' with injury status

    if 'teams' in data:
        for team in data['teams']:
            team_name = team.get('teamName', 'Unknown')

            if 'players' in team:
                for player in team['players']:
                    status = player.get('status', '').upper()

                    if status in ['OUT', 'DOUBTFUL', 'QUESTIONABLE', 'PROBABLE', 'GTD']:
                        injuries.append({
                            'player': player.get('name', ''),
                            'status': status,
                            'reason': player.get('injury', ''),
                            'out_flag': 1 if status == 'OUT' else 0,
                            'questionable_flag': 1 if status in ['QUESTIONABLE', 'DOUBTFUL', 'GTD'] else 0,
                            'probable_flag': 1 if status == 'PROBABLE' else 0,
                            'game_date': date_str
                        })

    if injuries:
        return pd.DataFrame(injuries)
    return None


def fetch_from_pdf(date_str):
    """
    Fallback: Download and parse PDF injury report
    This requires PyPDF2 which may not be installed
    """
    print("PDF parsing not yet implemented")
    print("Please manually create the injury file or install PDF parser")
    return None


def create_manual_template(date_str):
    """Create a template CSV for manual entry"""
    template = pd.DataFrame({
        'player': ['Example Player Name'],
        'status': ['Out'],
        'reason': ['Injury description'],
        'out_flag': [1],
        'questionable_flag': [0],
        'probable_flag': [0],
        'game_date': [date_str]
    })

    filename = f"data/injuries/injuries_{date_str}_TEMPLATE.csv"
    os.makedirs('data/injuries', exist_ok=True)
    template.to_csv(filename, index=False)

    print(f"\n📝 Template created: {filename}")
    print("\nEdit this file with actual injury data:")
    print("  - player: Full player name")
    print("  - status: Out, Questionable, Probable")
    print("  - reason: Injury description")
    print("  - out_flag: 1 if OUT, else 0")
    print("  - questionable_flag: 1 if QUESTIONABLE/DOUBTFUL, else 0")
    print("  - probable_flag: 1 if PROBABLE, else 0")
    print("\nRemove '_TEMPLATE' from filename when done editing")


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')

    print("="*80)
    print(f"NBA INJURY REPORT FETCHER - {date_str}")
    print("="*80)

    # Try to fetch from NBA API
    df = fetch_injury_report_html(date_str)

    if df is not None and len(df) > 0:
        # Save to CSV
        filename = f"data/injuries/injuries_{date_str}.csv"
        os.makedirs('data/injuries', exist_ok=True)
        df.to_csv(filename, index=False)

        print(f"\n✅ Success! Injury report saved to: {filename}")
        print(f"\nFound {len(df)} injured players:")
        print(df[['player', 'status', 'reason']].to_string(index=False))
    else:
        print("\n⚠️  Could not fetch injury report automatically")
        print("\nOptions:")
        print(f"  1. Download manually from: https://ak-static.cms.nba.com/referee/injury/Injury-Report_{date_str}_0530PM.pdf")
        print(f"  2. Create template: python {sys.argv[0]} --template")
        print("  3. Check back later (API might be temporarily down)")

        # Create template for manual entry
        if '--template' in sys.argv:
            create_manual_template(date_str)


if __name__ == '__main__':
    main()
