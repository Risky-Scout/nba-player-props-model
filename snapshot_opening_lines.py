"""
snapshot_opening_lines.py — Capture opening prop lines (9 AM ET)
Saves to data/opening_lines_{YYYY-MM-DD}.json for training features.
"""
import os, json, requests
from datetime import datetime, timezone

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
OUT  = f"data/opening_lines_{DATE}.json"

MARKETS = [
    "player_points","player_rebounds","player_assists",
    "player_threes","player_steals","player_blocks",
]

def fetch_events():
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events?apiKey={ODDS_API_KEY}"
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        print(f"Events fetch failed: {r.status_code}")
        return []
    return r.json()

def fetch_props(event_id):
    url = (
        f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds"
        f"?apiKey={ODDS_API_KEY}&regions=us,us2"
        f"&markets={','.join(MARKETS)}&oddsFormat=american"
    )
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        return None
    return r.json()

def main():
    if not ODDS_API_KEY:
        print("No ODDS_API_KEY — skipping snapshot")
        return

    events = fetch_events()
    print(f"Found {len(events)} NBA events")

    snapshot = {"date": DATE, "captured_at": datetime.now(timezone.utc).isoformat(), "games": []}

    for event in events:
        eid  = event["id"]
        home = event.get("home_team","")
        away = event.get("away_team","")
        time = event.get("commence_time","")

        props = fetch_props(eid)
        if not props:
            continue

        game = {
            "event_id": eid,
            "home_team": home,
            "away_team": away,
            "commence_time": time,
            "bookmakers": props.get("bookmakers", [])
        }
        snapshot["games"].append(game)
        print(f"  {away} @ {home}: {len(game['bookmakers'])} books")

    os.makedirs("data", exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(snapshot, f)
    print(f"Saved {OUT} ({len(snapshot['games'])} games)")

if __name__ == "__main__":
    main()
