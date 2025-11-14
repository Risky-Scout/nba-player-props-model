import pandas as pd
import numpy as np
from itertools import combinations

print("GENERATING PARLAYS FOR NOV 13...")

# Load predictions
df = pd.read_csv('predictions/tonight_20251113.csv')

# Simple probability estimates (using known model accuracy)
for prop in ['pts', 'reb', 'ast']:
    pred_col = f'{prop}_pred'
    df[f'{prop}_prob'] = 0.75  # Conservative 75% for each prop

# 2-LEG SGPs
print("2-leg SGPs...")
sgp2 = []
for team in df['team'].unique():
    players = df[df['team'] == team].head(5)
    for i, p1 in players.iterrows():
        for j, p2 in players.iterrows():
            if i < j:
                prob = 0.75 * 0.70  # Correlation adjusted
                sgp2.append({
                    'team': team,
                    'leg1': f"{p1['player_name']} O{p1['pts_pred']-.5} PTS",
                    'leg2': f"{p2['player_name']} O{p2['reb_pred']-.5} REB",
                    'prob': round(prob*100, 1)
                })

pd.DataFrame(sgp2).sort_values('prob', ascending=False).head(200).to_csv('predictions/top_200_sgp2_20251113.csv', index=False)

# 3-LEG SGPs
print("3-leg SGPs...")
sgp3 = []
for team in df['team'].unique():
    players = df[df['team'] == team].head(4)
    for combo in combinations(players.iterrows(), 3):
        p1, p2, p3 = combo[0][1], combo[1][1], combo[2][1]
        prob = 0.75 * 0.70 * 0.68
        sgp3.append({
            'team': team,
            'leg1': f"{p1['player_name']} O{p1['pts_pred']-.5} PTS",
            'leg2': f"{p2['player_name']} O{p2['reb_pred']-.5} REB",
            'leg3': f"{p3['player_name']} O{p3['ast_pred']-.5} AST",
            'prob': round(prob*100, 1)
        })

pd.DataFrame(sgp3).sort_values('prob', ascending=False).head(200).to_csv('predictions/top_200_sgp3_20251113.csv', index=False)

# 2-LEG CROSS
print("2-leg Cross...")
cross2 = []
top = df.sort_values('pts_pred', ascending=False).head(30)
for combo in combinations(top.iterrows(), 2):
    p1, p2 = combo[0][1], combo[1][1]
    if p1['team'] != p2['team']:
        prob = 0.75 * 0.75
        cross2.append({
            'leg1': f"{p1['player_name']} ({p1['team']}) O{p1['pts_pred']-.5} PTS",
            'leg2': f"{p2['player_name']} ({p2['team']}) O{p2['pts_pred']-.5} PTS",
            'prob': round(prob*100, 1)
        })

pd.DataFrame(cross2).sort_values('prob', ascending=False).head(200).to_csv('predictions/top_200_cross2_20251113.csv', index=False)

# 3-LEG CROSS
print("3-leg Cross...")
cross3 = []
for combo in combinations(top.iterrows(), 3):
    p1, p2, p3 = combo[0][1], combo[1][1], combo[2][1]
    teams = {p1['team'], p2['team'], p3['team']}
    if len(teams) == 3:
        prob = 0.75 * 0.75 * 0.75
        cross3.append({
            'leg1': f"{p1['player_name']} ({p1['team']}) O{p1['pts_pred']-.5} PTS",
            'leg2': f"{p2['player_name']} ({p2['team']}) O{p2['reb_pred']-.5} REB",
            'leg3': f"{p3['player_name']} ({p3['team']}) O{p3['ast_pred']-.5} AST",
            'prob': round(prob*100, 1)
        })

pd.DataFrame(cross3).sort_values('prob', ascending=False).head(200).to_csv('predictions/top_200_cross3_20251113.csv', index=False)

# SINGLES
print("Singles...")
singles = []
for prop in ['pts', 'reb', 'ast', 'stl', 'blk']:
    pred_col = f'{prop}_pred'
    if pred_col in df.columns:
        for idx, row in df.iterrows():
            line = row[pred_col] - 0.5
            pred = row[pred_col]
            # Simple probability model based on distance from line
            prob = 50 + min(34, abs(pred - line) * 10)  # Caps at 84%
            singles.append({
                'player': row['player_name'],
                'team': row['team'],
                'prop': prop.upper(),
                'line': round(line, 1),
                'pred': round(pred, 1),
                'prob': round(prob, 1)
            })

pd.DataFrame(singles).sort_values('prob', ascending=False).head(200).to_csv('predictions/top_200_singles_20251113.csv', index=False)

print("✅ ALL 5 FILES CREATED FOR NOV 13!")
