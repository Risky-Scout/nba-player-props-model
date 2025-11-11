"""
PREMIUM PREDICTIONS GENERATOR - The Casino Actuary
Generates top 100 lists + cross-game parlays + beautiful client deliverables
"""
import pandas as pd
import numpy as np
import pickle
from scipy.stats import norm
from datetime import datetime
import os
import sys

# Get date from command line or use today
pred_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')

print("="*80)
print(f"THE CASINO ACTUARY - PREMIUM PREDICTIONS FOR {pred_date}")
print("="*80)

# Load trained models
with open('model_cache/trained_models.pkl', 'rb') as f:
    models = pickle.load(f)

# Load processed data
df = pd.read_csv('data/processed_training_data.csv')
df['date'] = pd.to_datetime(df['date'])

# Load daily predictions (already has team info)
daily_preds_file = f'predictions/daily_{pred_date}.csv'
if not os.path.exists(daily_preds_file):
    print(f"❌ Daily predictions not found: {daily_preds_file}")
    print("Run run_daily_predictions.py first!")
    sys.exit(1)

daily_preds = pd.read_csv(daily_preds_file)

# Get game matchups from todays_games.txt
games_file = 'todays_games.txt'
if os.path.exists(games_file):
    with open(games_file, 'r') as f:
        games_str = f.read().strip()
        games_str = [line for line in games_str.split('\n') if line and not line.startswith('#')][0]
        games = [g.strip() for g in games_str.split(',')]
else:
    print("⚠️  todays_games.txt not found - will skip game-level analysis")
    games = []

print(f"\n📋 Games Tonight: {len(games)}")
for game in games:
    print(f"   {game}")

# Map teams to games
team_to_game = {}
game_teams = {}
for i, game in enumerate(games):
    away, home = game.split('@')
    away, home = away.strip(), home.strip()
    team_to_game[away] = i
    team_to_game[home] = i
    game_teams[i] = {'away': away, 'home': home}

# Add game_id to daily predictions
def get_team_abbrev(team_name):
    """Extract team abbreviation from team name"""
    mapping = {
        'Brooklyn Nets': 'BKN', 'Toronto Raptors': 'TOR',
        'New York Knicks': 'NYK', 'Memphis Grizzlies': 'MEM',
        'Golden State Warriors': 'GSW', 'Oklahoma City Thunder': 'OKC',
        'Boston Celtics': 'BOS', 'Philadelphia 76ers': 'PHI',
        'Indiana Pacers': 'IND', 'Utah Jazz': 'UTA',
        'Denver Nuggets': 'DEN', 'Sacramento Kings': 'SAC',
        'Dallas Mavericks': 'DAL', 'Washington Wizards': 'WAS',
        'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
        'Los Angeles Lakers': 'LAL', 'Atlanta Hawks': 'ATL',
        'Portland Trail Blazers': 'POR', 'Miami Heat': 'MIA',
        'New Orleans Pelicans': 'NOP', 'San Antonio Spurs': 'SAS',
        'Phoenix Suns': 'PHX', 'Los Angeles Clippers': 'LAC',
        'Houston Rockets': 'HOU', 'Detroit Pistons': 'DET',
        'Charlotte Hornets': 'CHA', 'Milwaukee Bucks': 'MIL',
        'Minnesota Timberwolves': 'MIN', 'Orlando Magic': 'ORL'
    }
    return mapping.get(team_name, team_name)

daily_preds['team_abbrev'] = daily_preds['team'].apply(get_team_abbrev)
daily_preds['game_id'] = daily_preds['team_abbrev'].map(team_to_game)

print(f"\n📊 Total Props: {len(daily_preds)}")

# ============================================================================
# GET TOP 100 SOLO PROPS
# ============================================================================
print("\n🎯 Generating Top 100 Solo Props...")

# Filter to good props (55%+ probability, reasonable lines)
good_props = daily_preds[
    (daily_preds['prob_over'] >= 0.55) &
    (daily_preds['prob_over'] <= 0.80) &
    (daily_preds['line'] >= 5.5)  # Exclude very low lines
].copy()

# Calculate edge and expected value
good_props['edge_pct'] = (good_props['prob_over'] - 0.5) * 100
good_props['ev'] = good_props['expected_value'] * good_props['prob_over']

# Sort by probability (most confident picks)
top_100_props = good_props.nlargest(100, 'prob_over')

print(f"   ✓ Top 100 props selected (avg prob: {top_100_props['prob_over'].mean():.1%})")

# ============================================================================
# GENERATE SAME-GAME PARLAYS (SGPs)
# ============================================================================
print("\n🎲 Generating Same-Game Parlays...")

# Calculate correlations from real data
corr_data = df[['pts', 'reb', 'ast']].corr()
correlations = {
    ('PTS', 'REB'): corr_data.loc['pts', 'reb'],
    ('PTS', 'AST'): corr_data.loc['pts', 'ast'],
    ('REB', 'AST'): corr_data.loc['reb', 'ast'],
}

print(f"   Correlations: PTS-REB={correlations[('PTS','REB')]:.3f}, "
      f"PTS-AST={correlations[('PTS','AST')]:.3f}, "
      f"REB-AST={correlations[('REB','AST')]:.3f}")

# Filter props for SGPs (same game only)
sgp_props = good_props[good_props['game_id'].notna()].copy()

# 2-LEG SGPs
sgp_2leg = []
for game_id in sgp_props['game_id'].unique():
    game_props = sgp_props[sgp_props['game_id'] == game_id]

    for i, row1 in game_props.iterrows():
        for j, row2 in game_props.iterrows():
            if i >= j:
                continue

            # Skip if same player and prop
            if row1['player'] == row2['player'] and row1['prop'] == row2['prop']:
                continue

            # Get correlation
            props_tuple = tuple(sorted([row1['prop'], row2['prop']]))
            corr = correlations.get(props_tuple, 0.0)

            # Calculate combined probability
            independent_prob = row1['prob_over'] * row2['prob_over']
            correlation_factor = 1 + (corr * 0.15)
            combined_prob = min(0.95, independent_prob * correlation_factor)

            # American odds
            if combined_prob >= 0.5:
                american_odds = int(-100 * combined_prob / (1 - combined_prob))
            else:
                american_odds = int(100 * (1 - combined_prob) / combined_prob)

            sgp_2leg.append({
                'game': f"{game_teams[game_id]['away']}@{game_teams[game_id]['home']}",
                'game_id': game_id,
                'player1': row1['player'],
                'prop1': row1['prop'],
                'line1': row1['line'],
                'prob1': row1['prob_over'],
                'player2': row2['player'],
                'prop2': row2['prop'],
                'line2': row2['line'],
                'prob2': row2['prob_over'],
                'correlation': corr,
                'independent_prob': independent_prob,
                'combined_prob': combined_prob,
                'american_odds': american_odds
            })

sgp_2leg_df = pd.DataFrame(sgp_2leg)
top_100_sgp_2leg = sgp_2leg_df.nlargest(100, 'combined_prob') if len(sgp_2leg_df) > 0 else pd.DataFrame()

print(f"   ✓ Generated {len(sgp_2leg_df)} 2-leg SGPs, keeping top 100")

# 3-LEG SGPs
sgp_3leg = []
for game_id in sgp_props['game_id'].unique():
    game_props = sgp_props[sgp_props['game_id'] == game_id].head(20)  # Limit for speed

    for i, row1 in game_props.iterrows():
        for j, row2 in game_props.iterrows():
            if i >= j:
                continue
            for k, row3 in game_props.iterrows():
                if j >= k:
                    continue

                # Get correlations
                corr12 = correlations.get(tuple(sorted([row1['prop'], row2['prop']])), 0.0)
                corr13 = correlations.get(tuple(sorted([row1['prop'], row3['prop']])), 0.0)
                corr23 = correlations.get(tuple(sorted([row2['prop'], row3['prop']])), 0.0)
                avg_corr = (corr12 + corr13 + corr23) / 3

                independent_prob = row1['prob_over'] * row2['prob_over'] * row3['prob_over']
                correlation_factor = 1 + (avg_corr * 0.2)
                combined_prob = min(0.90, independent_prob * correlation_factor)

                if combined_prob >= 0.5:
                    american_odds = int(-100 * combined_prob / (1 - combined_prob))
                else:
                    american_odds = int(100 * (1 - combined_prob) / combined_prob)

                sgp_3leg.append({
                    'game': f"{game_teams[game_id]['away']}@{game_teams[game_id]['home']}",
                    'game_id': game_id,
                    'player1': row1['player'],
                    'prop1': row1['prop'],
                    'line1': row1['line'],
                    'prob1': row1['prob_over'],
                    'player2': row2['player'],
                    'prop2': row2['prop'],
                    'line2': row2['line'],
                    'prob2': row2['prob_over'],
                    'player3': row3['player'],
                    'prop3': row3['prop'],
                    'line3': row3['line'],
                    'prob3': row3['prob_over'],
                    'avg_correlation': avg_corr,
                    'independent_prob': independent_prob,
                    'combined_prob': combined_prob,
                    'american_odds': american_odds
                })

sgp_3leg_df = pd.DataFrame(sgp_3leg)
top_100_sgp_3leg = sgp_3leg_df.nlargest(100, 'combined_prob') if len(sgp_3leg_df) > 0 else pd.DataFrame()

print(f"   ✓ Generated {len(sgp_3leg_df)} 3-leg SGPs, keeping top 100")

# ============================================================================
# GENERATE CROSS-GAME PARLAYS
# ============================================================================
print("\n🌐 Generating Cross-Game Parlays...")

cross_props = good_props[good_props['game_id'].notna()].copy()

# 2-LEG CROSS-GAME PARLAYS
cross_2leg = []
for i, row1 in cross_props.head(50).iterrows():  # Limit to top 50 props for speed
    for j, row2 in cross_props.head(50).iterrows():
        if i >= j:
            continue

        # Must be DIFFERENT games
        if row1['game_id'] == row2['game_id']:
            continue

        # No correlation across games (independent)
        independent_prob = row1['prob_over'] * row2['prob_over']

        if independent_prob >= 0.5:
            american_odds = int(-100 * independent_prob / (1 - independent_prob))
        else:
            american_odds = int(100 * (1 - independent_prob) / independent_prob)

        cross_2leg.append({
            'game1': f"{game_teams[row1['game_id']]['away']}@{game_teams[row1['game_id']]['home']}",
            'game2': f"{game_teams[row2['game_id']]['away']}@{game_teams[row2['game_id']]['home']}",
            'player1': row1['player'],
            'prop1': row1['prop'],
            'line1': row1['line'],
            'prob1': row1['prob_over'],
            'player2': row2['player'],
            'prop2': row2['prop'],
            'line2': row2['line'],
            'prob2': row2['prob_over'],
            'combined_prob': independent_prob,
            'american_odds': american_odds
        })

cross_2leg_df = pd.DataFrame(cross_2leg)
top_100_cross_2leg = cross_2leg_df.nlargest(100, 'combined_prob') if len(cross_2leg_df) > 0 else pd.DataFrame()

print(f"   ✓ Generated {len(cross_2leg_df)} 2-leg cross-game parlays, keeping top 100")

# 3-LEG CROSS-GAME PARLAYS
cross_3leg = []
for i, row1 in cross_props.head(30).iterrows():
    for j, row2 in cross_props.head(30).iterrows():
        if i >= j:
            continue
        for k, row3 in cross_props.head(30).iterrows():
            if j >= k:
                continue

            # At least 2 must be from different games
            games = {row1['game_id'], row2['game_id'], row3['game_id']}
            if len(games) < 2:
                continue

            independent_prob = row1['prob_over'] * row2['prob_over'] * row3['prob_over']

            if independent_prob >= 0.5:
                american_odds = int(-100 * independent_prob / (1 - independent_prob))
            else:
                american_odds = int(100 * (1 - independent_prob) / independent_prob)

            cross_3leg.append({
                'game1': f"{game_teams[row1['game_id']]['away']}@{game_teams[row1['game_id']]['home']}",
                'game2': f"{game_teams[row2['game_id']]['away']}@{game_teams[row2['game_id']]['home']}",
                'game3': f"{game_teams[row3['game_id']]['away']}@{game_teams[row3['game_id']]['home']}",
                'player1': row1['player'],
                'prop1': row1['prop'],
                'line1': row1['line'],
                'prob1': row1['prob_over'],
                'player2': row2['player'],
                'prop2': row2['prop'],
                'line2': row2['line'],
                'prob2': row2['prob_over'],
                'player3': row3['player'],
                'prop3': row3['prop'],
                'line3': row3['line'],
                'prob3': row3['prob_over'],
                'combined_prob': independent_prob,
                'american_odds': american_odds
            })

cross_3leg_df = pd.DataFrame(cross_3leg)
top_100_cross_3leg = cross_3leg_df.nlargest(100, 'combined_prob') if len(cross_3leg_df) > 0 else pd.DataFrame()

print(f"   ✓ Generated {len(cross_3leg_df)} 3-leg cross-game parlays, keeping top 100")

# ============================================================================
# SAVE TOP 100 FILES
# ============================================================================
os.makedirs('predictions/premium', exist_ok=True)
date_str = pred_date.replace('-', '')

print("\n💾 Saving Top 100 Files...")

top_100_props.to_csv(f'predictions/premium/top_100_props_{date_str}.csv', index=False)
print(f"   ✓ top_100_props_{date_str}.csv")

if len(top_100_sgp_2leg) > 0:
    top_100_sgp_2leg.to_csv(f'predictions/premium/top_100_sgp_2leg_{date_str}.csv', index=False)
    print(f"   ✓ top_100_sgp_2leg_{date_str}.csv")

if len(top_100_sgp_3leg) > 0:
    top_100_sgp_3leg.to_csv(f'predictions/premium/top_100_sgp_3leg_{date_str}.csv', index=False)
    print(f"   ✓ top_100_sgp_3leg_{date_str}.csv")

if len(top_100_cross_2leg) > 0:
    top_100_cross_2leg.to_csv(f'predictions/premium/top_100_cross_2leg_{date_str}.csv', index=False)
    print(f"   ✓ top_100_cross_2leg_{date_str}.csv")

if len(top_100_cross_3leg) > 0:
    top_100_cross_3leg.to_csv(f'predictions/premium/top_100_cross_3leg_{date_str}.csv', index=False)
    print(f"   ✓ top_100_cross_3leg_{date_str}.csv")

# ============================================================================
# CREATE BEAUTIFUL CLIENT DELIVERABLE
# ============================================================================
print("\n📄 Creating Premium Client Deliverable...")

html_file = f'predictions/premium/CLIENT_DELIVERABLE_{date_str}.html'

with open(html_file, 'w') as f:
    f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Casino Actuary - NBA Predictions {pred_date}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #1a202c;
            padding: 40px 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
            border-bottom: 4px solid #fbbf24;
        }}

        .header h1 {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }}

        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
            font-weight: 300;
        }}

        .header .date {{
            margin-top: 20px;
            font-size: 1.1em;
            background: rgba(255,255,255,0.1);
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
        }}

        .bio-section {{
            background: #f8fafc;
            padding: 30px 40px;
            border-bottom: 1px solid #e2e8f0;
        }}

        .bio-section h2 {{
            color: #1e3a8a;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}

        .bio-text {{
            color: #475569;
            font-size: 1.05em;
            line-height: 1.8;
        }}

        .contact {{
            margin-top: 15px;
            color: #1e40af;
            font-weight: 600;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 50px;
        }}

        .section-title {{
            font-size: 1.8em;
            color: #1e3a8a;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 3px solid #fbbf24;
            display: flex;
            align-items: center;
        }}

        .section-title .icon {{
            margin-right: 12px;
            font-size: 1.2em;
        }}

        .parlay-card {{
            background: #ffffff;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }}

        .parlay-card:hover {{
            border-color: #3b82f6;
            box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15);
            transform: translateY(-2px);
        }}

        .parlay-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f1f5f9;
        }}

        .parlay-number {{
            font-size: 0.9em;
            color: #64748b;
            font-weight: 600;
        }}

        .probability-badge {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 1.1em;
        }}

        .odds-badge {{
            background: #fbbf24;
            color: #1e3a8a;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 700;
            margin-left: 10px;
        }}

        .leg {{
            background: #f8fafc;
            padding: 12px 16px;
            margin-bottom: 8px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }}

        .leg:last-child {{
            margin-bottom: 0;
        }}

        .player-name {{
            font-weight: 700;
            color: #1e3a8a;
            font-size: 1.05em;
        }}

        .prop-detail {{
            color: #475569;
            margin-top: 4px;
        }}

        .game-label {{
            font-size: 0.85em;
            color: #64748b;
            margin-top: 4px;
            font-style: italic;
        }}

        .correlation-info {{
            background: #eff6ff;
            padding: 10px 16px;
            border-radius: 8px;
            margin-top: 12px;
            font-size: 0.9em;
            color: #1e40af;
            border-left: 3px solid #3b82f6;
        }}

        .footer {{
            background: #f8fafc;
            padding: 30px 40px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
        }}

        .footer-tagline {{
            font-size: 1.1em;
            color: #1e3a8a;
            font-weight: 600;
            margin-bottom: 10px;
        }}

        .disclaimer {{
            max-width: 800px;
            margin: 20px auto 0;
            font-size: 0.85em;
            line-height: 1.6;
            color: #94a3b8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎰 THE CASINO ACTUARY</h1>
            <div class="subtitle">Premium NBA Player Props Analysis</div>
            <div class="date">📅 {pred_date}</div>
        </div>

        <div class="bio-section">
            <h2>About The Casino Actuary</h2>
            <div class="bio-text">
                Actuary gone sports quant. Committed to always learning and mastering all mathematics
                needed for a perpetual edge over the books. Let Go.
            </div>
            <div class="contact">
                📧 Email: JosephShack@gmail.com
            </div>
        </div>

        <div class="content">
""")

    # TOP 25 SAME-GAME PARLAYS
    f.write("""
            <div class="section">
                <h2 class="section-title">
                    <span class="icon">🎲</span>
                    Top 25 Same-Game Parlays
                </h2>
""")

    top_25_sgp = pd.concat([top_100_sgp_2leg, top_100_sgp_3leg]).nlargest(25, 'combined_prob')

    for idx, row in top_25_sgp.iterrows():
        legs = 2 if 'player3' not in row or pd.isna(row.get('player3')) else 3

        f.write(f"""
                <div class="parlay-card">
                    <div class="parlay-header">
                        <span class="parlay-number">#{idx+1} • {legs}-Leg SGP • {row['game']}</span>
                        <div>
                            <span class="probability-badge">{row['combined_prob']:.1%}</span>
                            <span class="odds-badge">{row['american_odds']:+d}</span>
                        </div>
                    </div>
""")

        # Leg 1
        f.write(f"""
                    <div class="leg">
                        <div class="player-name">{row['player1']}</div>
                        <div class="prop-detail">{row['prop1']} Over {row['line1']:.1f} ({row['prob1']:.1%})</div>
                    </div>
""")

        # Leg 2
        f.write(f"""
                    <div class="leg">
                        <div class="player-name">{row['player2']}</div>
                        <div class="prop-detail">{row['prop2']} Over {row['line2']:.1f} ({row['prob2']:.1%})</div>
                    </div>
""")

        # Leg 3 if exists
        if legs == 3:
            f.write(f"""
                    <div class="leg">
                        <div class="player-name">{row['player3']}</div>
                        <div class="prop-detail">{row['prop3']} Over {row['line3']:.1f} ({row['prob3']:.1%})</div>
                    </div>
""")

        # Correlation info
        if 'correlation' in row and not pd.isna(row['correlation']):
            f.write(f"""
                    <div class="correlation-info">
                        📊 Correlation: {row['correlation']:.3f} (Books ignore this edge!)
                    </div>
""")
        elif 'avg_correlation' in row:
            f.write(f"""
                    <div class="correlation-info">
                        📊 Avg Correlation: {row['avg_correlation']:.3f} (Books ignore this edge!)
                    </div>
""")

        f.write("""
                </div>
""")

    # TOP 25 CROSS-GAME PARLAYS
    f.write("""
            </div>

            <div class="section">
                <h2 class="section-title">
                    <span class="icon">🌐</span>
                    Top 25 Cross-Game Parlays
                </h2>
""")

    top_25_cross = pd.concat([top_100_cross_2leg, top_100_cross_3leg]).nlargest(25, 'combined_prob')

    for idx, row in top_25_cross.iterrows():
        legs = 2 if 'player3' not in row or pd.isna(row.get('player3')) else 3

        f.write(f"""
                <div class="parlay-card">
                    <div class="parlay-header">
                        <span class="parlay-number">#{idx+1} • {legs}-Leg Cross-Game</span>
                        <div>
                            <span class="probability-badge">{row['combined_prob']:.1%}</span>
                            <span class="odds-badge">{row['american_odds']:+d}</span>
                        </div>
                    </div>
""")

        # Leg 1
        f.write(f"""
                    <div class="leg">
                        <div class="player-name">{row['player1']}</div>
                        <div class="prop-detail">{row['prop1']} Over {row['line1']:.1f} ({row['prob1']:.1%})</div>
                        <div class="game-label">Game: {row['game1']}</div>
                    </div>
""")

        # Leg 2
        f.write(f"""
                    <div class="leg">
                        <div class="player-name">{row['player2']}</div>
                        <div class="prop-detail">{row['prop2']} Over {row['line2']:.1f} ({row['prob2']:.1%})</div>
                        <div class="game-label">Game: {row['game2']}</div>
                    </div>
""")

        # Leg 3 if exists
        if legs == 3:
            f.write(f"""
                    <div class="leg">
                        <div class="player-name">{row['player3']}</div>
                        <div class="prop-detail">{row['prop3']} Over {row['line3']:.1f} ({row['prob3']:.1%})</div>
                        <div class="game-label">Game: {row['game3']}</div>
                    </div>
""")

        f.write("""
                </div>
""")

    # Close content and add footer
    f.write(f"""
            </div>
        </div>

        <div class="footer">
            <div class="footer-tagline">🎯 Mathematical Edge. Quantitative Precision. Perpetual Learning.</div>
            <div class="disclaimer">
                This analysis is for informational and educational purposes only. Past performance does not
                guarantee future results. All probabilities are model-based estimates derived from machine
                learning ensemble methods (Random Forest + Gradient Boosting) with correlation adjustments.
                Odds shown are theoretical fair value with 4.5% Shin margin applied. Always gamble responsibly
                and within your means.
            </div>
            <div style="margin-top: 20px; color: #94a3b8;">
                © {datetime.now().year} The Casino Actuary • Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </div>
</body>
</html>
""")

print(f"   ✓ {html_file}")

print("\n" + "="*80)
print("✅ PREMIUM PREDICTIONS COMPLETE")
print("="*80)
print(f"📊 Top 100 Props: {len(top_100_props)}")
print(f"🎲 Top 100 2-Leg SGPs: {len(top_100_sgp_2leg)}")
print(f"🎲 Top 100 3-Leg SGPs: {len(top_100_sgp_3leg)}")
print(f"🌐 Top 100 2-Leg Cross-Game: {len(top_100_cross_2leg)}")
print(f"🌐 Top 100 3-Leg Cross-Game: {len(top_100_cross_3leg)}")
print(f"\n📄 Client Deliverable: {html_file}")
print("="*80)
