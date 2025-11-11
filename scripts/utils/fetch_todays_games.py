#!/usr/bin/env python3
"""
Fetch today's NBA games automatically
Returns game slate in format: "AWAY@HOME,AWAY@HOME,..."
"""
from datetime import datetime
import sys

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not installed, using nba_api only", file=sys.stderr)

try:
    from nba_api.live.nba.endpoints import scoreboard
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False

# Team ID to abbreviation mapping (reverse of what we have in run_daily_predictions.py)
TEAM_ID_TO_ABBREV = {
    1: 'ATL', 2: 'BOS', 3: 'BKN', 5: 'CHI', 6: 'CLE',
    7: 'DAL', 8: 'DEN', 10: 'GSW', 11: 'HOU', 12: 'IND',
    13: 'LAC', 14: 'LAL', 15: 'MEM', 16: 'MIA', 17: 'MIL',
    18: 'MIN', 19: 'NOP', 20: 'NYK', 21: 'OKC', 22: 'ORL',
    23: 'PHI', 24: 'PHX', 25: 'POR', 26: 'SAC', 27: 'SAS',
    28: 'TOR', 29: 'UTA', 30: 'WAS', 4: 'CHA', 9: 'DET'
}

# Full team names to abbreviations (backup method)
TEAM_NAME_TO_ABBREV = {
    'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
    'LA Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
    'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
}

def fetch_games_from_espn(date_str=None):
    """
    Fetch games from ESPN API

    Args:
        date_str: Date in YYYYMMDD format, defaults to today

    Returns:
        List of game strings in format "AWAY@HOME"
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y%m%d')

    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        games = []

        if 'events' in data:
            for event in data['events']:
                if 'competitions' in event and len(event['competitions']) > 0:
                    competition = event['competitions'][0]

                    if 'competitors' in competition and len(competition['competitors']) >= 2:
                        # competitors[0] is typically home, competitors[1] is away
                        # but check homeAway field to be sure
                        home_team = None
                        away_team = None

                        for competitor in competition['competitors']:
                            team_name = competitor['team']['displayName']
                            is_home = competitor.get('homeAway') == 'home'

                            abbrev = TEAM_NAME_TO_ABBREV.get(team_name)

                            if abbrev:
                                if is_home:
                                    home_team = abbrev
                                else:
                                    away_team = abbrev

                        if home_team and away_team:
                            games.append(f"{away_team}@{home_team}")

        return games

    except Exception as e:
        print(f"ESPN API failed: {e}", file=sys.stderr)
        return None

def fetch_games_from_balldontlie():
    """
    Fetch games from balldontlie.io API (backup method)

    Returns:
        List of game strings in format "AWAY@HOME"
    """
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://www.balldontlie.io/api/v1/games?dates[]={today}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        games = []

        if 'data' in data:
            for game in data['data']:
                home_team = game['home_team']['full_name']
                away_team = game['visitor_team']['full_name']

                home_abbrev = TEAM_NAME_TO_ABBREV.get(home_team)
                away_abbrev = TEAM_NAME_TO_ABBREV.get(away_team)

                if home_abbrev and away_abbrev:
                    games.append(f"{away_abbrev}@{home_abbrev}")

        return games

    except Exception as e:
        print(f"BallDontLie API failed: {e}", file=sys.stderr)
        return None

def fetch_games_from_nba_api():
    """
    Fetch games using nba_api (most reliable)

    Returns:
        List of game strings in format "AWAY@HOME"
    """
    if not NBA_API_AVAILABLE:
        return None

    try:
        board = scoreboard.ScoreBoard()
        data = board.get_dict()

        games = []

        if 'scoreboard' in data and 'games' in data['scoreboard']:
            for game in data['scoreboard']['games']:
                home_team = game['homeTeam']['teamTricode']
                away_team = game['awayTeam']['teamTricode']
                games.append(f"{away_team}@{home_team}")

        return games

    except Exception as e:
        print(f"nba_api failed: {e}", file=sys.stderr)
        return None

def get_todays_games():
    """
    Get today's NBA games using multiple fallback methods

    Returns:
        String in format "AWAY@HOME,AWAY@HOME,..." or None if no games
    """
    # Try nba_api first (most reliable and doesn't get blocked)
    games = fetch_games_from_nba_api()

    # Fallback to ESPN if requests is available
    if (games is None or len(games) == 0) and REQUESTS_AVAILABLE:
        games = fetch_games_from_espn()

    # Fallback to balldontlie
    if (games is None or len(games) == 0) and REQUESTS_AVAILABLE:
        games = fetch_games_from_balldontlie()

    # If still no games, return None
    if games is None or len(games) == 0:
        return None

    return ','.join(sorted(games))

if __name__ == '__main__':
    # Can provide date as argument (YYYYMMDD format)
    date_str = sys.argv[1] if len(sys.argv) > 1 else None

    if date_str:
        # Use specific date
        games = fetch_games_from_espn(date_str)
    else:
        # Use today
        games = get_todays_games()

    if games:
        if isinstance(games, list):
            print(','.join(games))
        else:
            print(games)
    else:
        print("No games found", file=sys.stderr)
        sys.exit(1)
