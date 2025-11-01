================================================================================
QUICK START IMPLEMENTATION GUIDE
================================================================================

This guide shows you how to get your model running with REAL NBA data TODAY.

================================================================================
STEP 1: GET NBA DATA (Choose one method)
================================================================================

METHOD A: NBA_API (Free, Official NBA Data)
--------------------------------------------

Install:
pip install nba_api --break-system-packages

Code to get player game logs:

```python
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd
import time

# Get all players
all_players = players.get_players()

# Example: Get LeBron James' game logs
lebron = [p for p in all_players if p['full_name'] == 'LeBron James'][0]
lebron_id = lebron['id']

# Get 2024-25 season game logs
gamelog = playergamelog.PlayerGameLog(
    player_id=lebron_id,
    season='2024-25'
)

df = gamelog.get_data_frames()[0]

# Key columns: PTS, REB, AST, MIN, PLUS_MINUS, etc.
print(df.head())

# Get multiple seasons for training
seasons = ['2021-22', '2022-23', '2023-24', '2024-25']
all_games = []

for season in seasons:
    time.sleep(1)  # Rate limiting
    gamelog = playergamelog.PlayerGameLog(
        player_id=lebron_id,
        season=season
    )
    games = gamelog.get_data_frames()[0]
    all_games.append(games)

full_history = pd.concat(all_games, ignore_index=True)
```

METHOD B: Basketball Reference Scraping
----------------------------------------

Install:
pip install basketball-reference-web-scraper --break-system-packages

Code:

```python
from basketball_reference_web_scraper import client
import pandas as pd

# Get player season totals
season_totals = client.players_season_totals(season_end_year=2024)
df = pd.DataFrame(season_totals)

# Get play-by-play data
pbp = client.play_by_play(home_team=Team.LAKERS, year=2024, month=11, day=1)
```

METHOD C: Sportradar API (Paid but Best Quality)
-------------------------------------------------

If you can afford it ($300-500/month for trial), this is what pros use.

Sign up at: https://developer.sportradar.com/

METHOD D: CSV Files from Kaggle
--------------------------------

Search Kaggle for "NBA player game logs" datasets.
Download CSV, load with pandas.

Quick start:
```python
df = pd.read_csv('nba_games.csv')
```

================================================================================
STEP 2: FEATURE ENGINEERING TEMPLATE
================================================================================

```python
def engineer_features(player_history, target_game_date):
    """
    Engineer features for a single game prediction
    
    Args:
        player_history: DataFrame of player's past games
        target_game_date: Date of game to predict
    
    Returns:
        DataFrame with single row of features
    """
    # Filter to games before target date
    past_games = player_history[player_history['date'] < target_game_date]
    past_games = past_games.sort_values('date', ascending=False)
    
    features = {}
    
    # Recent performance (last N games)
    for n in [3, 5, 7, 10, 15]:
        recent = past_games.head(n)
        features[f'pts_avg_L{n}'] = recent['PTS'].mean()
        features[f'pts_std_L{n}'] = recent['PTS'].std()
        features[f'reb_avg_L{n}'] = recent['REB'].mean()
        features[f'ast_avg_L{n}'] = recent['AST'].mean()
        features[f'min_avg_L{n}'] = recent['MIN'].mean()
    
    # Trends
    if len(past_games) >= 10:
        last_5 = past_games.head(5)['PTS'].mean()
        prev_5 = past_games.iloc[5:10]['PTS'].mean()
        features['pts_trend'] = last_5 - prev_5
    
    # Home/Away splits
    home_games = past_games[past_games['home'] == 1]
    away_games = past_games[past_games['home'] == 0]
    
    if len(home_games) > 0:
        features['pts_home_avg'] = home_games['PTS'].mean()
    if len(away_games) > 0:
        features['pts_away_avg'] = away_games['PTS'].mean()
    
    # Rest days impact
    features['rest_days'] = (target_game_date - past_games.iloc[0]['date']).days
    
    # Season-long stats
    features['pts_season_avg'] = past_games['PTS'].mean()
    features['pts_season_std'] = past_games['PTS'].std()
    features['games_played'] = len(past_games)
    
    # Matchup-specific (if you have opponent data)
    # features['vs_team_pts_avg'] = ...
    
    return pd.DataFrame([features])
```

================================================================================
STEP 3: TRAINING THE MODEL
================================================================================

```python
from meta_ensemble_model import MetaEnsemblePlayerPropModel
import pandas as pd

# Initialize model
model = MetaEnsemblePlayerPropModel()

# Load your data
df = pd.read_csv('nba_player_games.csv')  # Your data

# Prepare features and target
feature_cols = [col for col in df.columns if col.startswith('pts_') or 
                col in ['rest_days', 'home', 'games_played', 'min_avg_L5']]
X = df[feature_cols]
y = df['PTS']  # Target: actual points scored

# Train global model for points
model.train_global_model(X, y, prop_stat='pts')

# Train player-specific model for LeBron
lebron_games = df[df['player_name'] == 'LeBron James']
if len(lebron_games) >= 30:
    model.train_player_specific_model(
        player_id='2544',
        player_name='LeBron James',
        player_history=lebron_games,
        prop_stat='pts'
    )

# Save model
model.save_models('nba_props_model.pkl')
```

================================================================================
STEP 4: MAKING PREDICTIONS
================================================================================

```python
# Load model
model.load_models('nba_props_model.pkl')

# Get today's games from API
today_games = get_todays_games()  # Your function

# For each player playing today
for player in today_players:
    # Engineer features
    game_features = engineer_features(player['history'], today)
    
    # Generate complete PMF
    pmf_result = model.generate_full_pmf(
        player_id=player['id'],
        player_name=player['name'],
        prop_stat='pts',
        game_features=game_features,
        max_value=60
    )
    
    # Build margin and create odds sheet
    odds_sheet = model.generate_complete_odds_sheet(
        player_id=player['id'],
        player_name=player['name'],
        prop_stat='pts',
        game_features=game_features,
        target_margin=0.05,
        margin_method='power',
        key_lines=[15.5, 20.5, 25.5, 30.5]
    )
    
    # Save odds sheet
    odds_sheet.to_csv(f"odds_{player['name'].replace(' ', '_')}.csv")
    
    print(f"Generated odds for {player['name']}")
```

================================================================================
STEP 5: COMPARING TO MARKET (Find +EV Bets)
================================================================================

```python
import requests
from bs4 import BeautifulSoup

# Example: Scrape DraftKings odds (in production, use official API)
def scrape_draftkings_odds():
    """
    IMPORTANT: This is just an example. In production:
    1. Use official APIs (The Odds API, RapidAPI, etc.)
    2. Respect robots.txt and rate limits
    3. Check terms of service
    """
    # Placeholder - you'd implement actual scraping
    market_odds = {
        'LeBron James': {
            'pts': {
                25.5: {'over': -110, 'under': -110},
                30.5: {'over': +150, 'under': -180}
            }
        }
    }
    return market_odds

# Compare your odds to market
market_odds = scrape_draftkings_odds()

for player, props in market_odds.items():
    # Load your odds
    your_odds = pd.read_csv(f"odds_{player.replace(' ', '_')}.csv")
    
    for line, odds in props['pts'].items():
        # Find this line in your sheet
        your_line = your_odds[your_odds['line'] == line]
        
        if len(your_line) > 0:
            # Calculate edge
            market_prob_over = model._american_to_implied(odds['over'])
            your_prob_over = your_line['fair_prob_over'].values[0]
            edge_over = your_prob_over - market_prob_over
            
            market_prob_under = model._american_to_implied(odds['under'])
            your_prob_under = your_line['fair_prob_under'].values[0]
            edge_under = your_prob_under - market_prob_under
            
            # Flag +EV bets
            if edge_over > 0.03:  # 3% edge threshold
                print(f"🔥 VALUE FOUND: {player} OVER {line} pts")
                print(f"   Market: {odds['over']}")
                print(f"   Fair: {your_line['fair_odds_over'].values[0]:.0f}")
                print(f"   Edge: {edge_over:.2%}")
            
            if edge_under > 0.03:
                print(f"🔥 VALUE FOUND: {player} UNDER {line} pts")
                print(f"   Market: {odds['under']}")
                print(f"   Fair: {your_line['fair_odds_under'].values[0]:.0f}")
                print(f"   Edge: {edge_under:.2%}")
```

================================================================================
STEP 6: DAILY AUTOMATION SCRIPT
================================================================================

```python
#!/usr/bin/env python3
"""
Daily NBA Props Analysis Script

Run this every day at 9 AM ET to:
1. Get today's games and players
2. Generate PMFs and odds for all players
3. Compare to market odds
4. Output list of +EV bets
5. Email/Slack results
"""

import pandas as pd
from datetime import datetime
from meta_ensemble_model import MetaEnsemblePlayerPropModel

def main():
    print(f"NBA Props Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load model
    model = MetaEnsemblePlayerPropModel()
    model.load_models('nba_props_model.pkl')
    
    # Get today's games
    todays_games = get_todays_nba_games()  # Implement with NBA API
    
    # Get market odds
    market_odds = get_market_odds()  # Implement with odds API
    
    # Analyze each player
    value_bets = []
    
    for game in todays_games:
        for player in game['players']:
            # Generate odds
            odds_sheet = model.generate_complete_odds_sheet(
                player_id=player['id'],
                player_name=player['name'],
                prop_stat='pts',
                game_features=player['features'],
                target_margin=0.05,
                margin_method='power'
            )
            
            # Compare to market
            edges = compare_to_market(odds_sheet, market_odds, player['name'])
            value_bets.extend(edges)
    
    # Filter for best opportunities
    value_bets = [bet for bet in value_bets if bet['edge'] > 0.03]
    value_bets.sort(key=lambda x: x['edge'], reverse=True)
    
    # Output results
    print(f"\nFound {len(value_bets)} value opportunities:")
    for bet in value_bets[:10]:  # Top 10
        print(f"{bet['player']} {bet['side']} {bet['line']} - "
              f"Edge: {bet['edge']:.2%} - Kelly: {bet['kelly']:.2%}")
    
    # Save to CSV
    pd.DataFrame(value_bets).to_csv(
        f"value_bets_{datetime.now().strftime('%Y%m%d')}.csv",
        index=False
    )
    
    # Email results (implement with smtplib or SendGrid)
    # send_email(value_bets)

if __name__ == "__main__":
    main()
```

Set up as a cron job:
```bash
# Add to crontab (crontab -e)
0 9 * * * /usr/bin/python3 /path/to/daily_analysis.py
```

================================================================================
STEP 7: VISUALIZATION FOR PORTFOLIO
================================================================================

```python
import matplotlib.pyplot as plt
import seaborn as sns

def create_pmf_visualization(pmf_result, player_name, prop_stat):
    """Create publication-quality PMF visualization"""
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # PMF
    axes[0].bar(pmf_result['n_values'], pmf_result['pmf'], 
                alpha=0.7, color='steelblue')
    axes[0].axvline(pmf_result['expected_value'], color='red', 
                    linestyle='--', label=f"E[X] = {pmf_result['expected_value']:.1f}")
    axes[0].axvline(pmf_result['median'], color='green', 
                    linestyle='--', label=f"Median = {pmf_result['median']:.0f}")
    axes[0].set_xlabel('Points')
    axes[0].set_ylabel('Probability')
    axes[0].set_title(f'{player_name} - {prop_stat.upper()} PMF')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    # CDF
    axes[1].plot(pmf_result['n_values'], pmf_result['cdf'], 
                 linewidth=2, color='darkblue')
    axes[1].set_xlabel('Points')
    axes[1].set_ylabel('P(X ≤ n)')
    axes[1].set_title(f'{player_name} - {prop_stat.upper()} CDF')
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'pmf_{player_name.replace(" ", "_")}.png', dpi=300)
    print(f"Saved visualization: pmf_{player_name.replace(' ', '_')}.png")

# Use it:
pmf_result = model.generate_full_pmf(...)
create_pmf_visualization(pmf_result, 'LeBron James', 'pts')
```

================================================================================
STEP 8: BACKTESTING FRAMEWORK
================================================================================

```python
def backtest_model(model, historical_data, start_date, end_date):
    """
    Backtest the model on historical data
    
    Returns:
        Dict with performance metrics
    """
    results = []
    
    # Walk forward through dates
    test_dates = pd.date_range(start_date, end_date)
    
    for date in test_dates:
        # Get games on this date
        games = historical_data[historical_data['date'] == date]
        
        for _, game in games.iterrows():
            # Generate prediction
            features = engineer_features(game['player_history'], date)
            
            odds_sheet = model.generate_complete_odds_sheet(
                player_id=game['player_id'],
                player_name=game['player_name'],
                prop_stat='pts',
                game_features=features
            )
            
            # Compare prediction to actual
            actual = game['PTS']
            line = 25.5  # Example line
            
            # Find our probabilities
            line_row = odds_sheet[odds_sheet['line'] == line]
            if len(line_row) > 0:
                pred_over = line_row['fair_prob_over'].values[0]
                pred_under = line_row['fair_prob_under'].values[0]
                
                # Record result
                results.append({
                    'date': date,
                    'player': game['player_name'],
                    'line': line,
                    'pred_over': pred_over,
                    'pred_under': pred_under,
                    'actual': actual,
                    'outcome_over': 1 if actual > line else 0,
                    'outcome_under': 1 if actual <= line else 0
                })
    
    # Calculate metrics
    df_results = pd.DataFrame(results)
    
    # Brier score (calibration)
    brier_over = ((df_results['pred_over'] - df_results['outcome_over']) ** 2).mean()
    brier_under = ((df_results['pred_under'] - df_results['outcome_under']) ** 2).mean()
    
    # Log loss
    epsilon = 1e-15
    df_results['pred_over_clip'] = df_results['pred_over'].clip(epsilon, 1-epsilon)
    log_loss_over = -(df_results['outcome_over'] * np.log(df_results['pred_over_clip']) + 
                      (1 - df_results['outcome_over']) * np.log(1 - df_results['pred_over_clip'])).mean()
    
    metrics = {
        'total_predictions': len(df_results),
        'brier_score_over': brier_over,
        'brier_score_under': brier_under,
        'log_loss_over': log_loss_over,
        'mean_absolute_error': (df_results['actual'] - line).abs().mean()
    }
    
    return metrics, df_results

# Run backtest
metrics, results = backtest_model(model, historical_data, '2024-01-01', '2024-10-31')
print(f"Backtest Results:")
print(f"  Brier Score: {metrics['brier_score_over']:.4f}")
print(f"  Log Loss: {metrics['log_loss_over']:.4f}")
```

================================================================================
STEP 9: PRODUCTION DEPLOYMENT CHECKLIST
================================================================================

[ ] Set up cloud server (AWS EC2, Google Cloud, DigitalOcean)
[ ] Install all dependencies
[ ] Set up PostgreSQL database for storing predictions and results
[ ] Create API endpoints (Flask or FastAPI)
[ ] Implement logging and monitoring
[ ] Set up automated daily runs (cron or Airflow)
[ ] Create dashboard for viewing results (Streamlit or Plotly Dash)
[ ] Implement alerting (email/Slack when high-value opportunities found)
[ ] Set up version control and backup of models
[ ] Document everything

================================================================================
STEP 10: RESOURCES & NEXT STEPS
================================================================================

Key Libraries to Install:
```bash
pip install nba_api pandas numpy scikit-learn xgboost lightgbm catboost scipy matplotlib seaborn joblib --break-system-packages
```

Data Sources:
• NBA API: https://github.com/swar/nba_api
• Basketball Reference: https://www.basketball-reference.com
• The Odds API: https://the-odds-api.com
• Sportradar API: https://developer.sportradar.com

Learning Resources:
• "Trading and Exchanges" by Larry Harris (market microstructure)
• "Forecasting: Principles and Practice" by Hyndman & Athanasopoulos
• "Machine Learning for Asset Managers" by Marcos López de Prado
• arXiv papers on sports betting modeling

Communities:
• r/sportsbook (Reddit)
• Sports Betting Discord servers
• Betfair Forum
• Twitter sports betting quant community

================================================================================

You now have everything you need to:
1. Get real NBA data
2. Train your model
3. Generate predictions
4. Compare to market odds
5. Find value bets
6. Automate the process
7. Backtest performance

Start with the demonstration script to prove the concept works, then move to
real data and daily automation.

The model is ready. The guide is ready. Now execute.

================================================================================
