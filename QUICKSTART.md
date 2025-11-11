# 🏀 NBA Props Model - Quick Start Guide

## ⚡ Generate Today's Predictions (Three Ways!)

### Option 1: Just Run It! (Semi-Automatic)
```bash
./quick_predict.sh
```

The script will:
1. Try to auto-fetch games from NBA API
2. If that fails, read from `todays_games.txt`
3. Generate ALL predictions (PMF, SGPs, individual props)
4. Auto-commit to GitHub as **Risky-Scout**
5. Display summary on screen

**Note:** Update `todays_games.txt` each day with tonight's games

### Option 2: Provide Games Manually
```bash
./quick_predict.sh "TOR@BKN,MEM@NYK,GSW@OKC,BOS@PHI,IND@UTA,DEN@SAC"
```

### Option 3: Edit todays_games.txt
```bash
nano todays_games.txt  # Update with today's games
./quick_predict.sh     # Run without arguments
```

---

## 📅 Today's Games (November 11, 2025)

```
TOR@BKN  - Toronto Raptors @ Brooklyn Nets (7:30 PM ET)
MEM@NYK  - Memphis Grizzlies @ New York Knicks (7:30 PM ET)
GSW@OKC  - Golden State Warriors @ Oklahoma City Thunder (8:00 PM ET)
BOS@PHI  - Boston Celtics @ Philadelphia 76ers (8:00 PM ET)
IND@UTA  - Indiana Pacers @ Utah Jazz (9:00 PM ET)
DEN@SAC  - Denver Nuggets @ Sacramento Kings (11:00 PM ET)
```

---

## 📊 What You Get

### All predictions saved to `predictions/` folder:

1. **`daily_2025-11-11.csv`** - 10,000+ individual prop predictions
2. **`complete_pmf_distributions_20251111.csv`** - Full probability distributions
3. **`sgp_2leg_20251111.csv`** - Top 50 2-leg Same Game Parlays with correlations
4. **`sgp_3leg_20251111.csv`** - Top 30 3-leg Same Game Parlays with correlations
5. **`summary_20251111.txt`** - Human-readable summary

---

## 🤖 Full Automation (Optional)

Set it and forget it! Add to crontab (`crontab -e`):

```bash
# Train model every morning at 7 AM
0 7 * * * cd /home/user/nba-player-props-model && ./auto_daily_pipeline.sh train

# Generate predictions at 4:30 PM
30 16 * * * cd /home/user/nba-player-props-model && ./auto_daily_pipeline.sh predict
```

**How it works:**
1. Script tries to auto-fetch games from NBA API
2. If auto-fetch fails, reads from `todays_games.txt`
3. You just need to update `todays_games.txt` once per day (takes 10 seconds)

**Pro tip:** Set a phone reminder at 3 PM to update `todays_games.txt`, then the 4:30 PM cron runs automatically!

---

## 🎯 Key Features

✅ **Correlation Analysis** - 0.647 PTS/REB, 0.639 PTS/AST, 0.506 REB/AST
✅ **SGP Optimization** - Books don't account for correlations, we do!
✅ **PMF Distributions** - Full probability mass functions for every line
✅ **Auto GitHub Sync** - All commits show as Risky-Scout
✅ **Model Accuracy** - PTS: 3.80 MAE | REB: 1.57 MAE | AST: 1.09 MAE

---

## 📝 Team Abbreviations

| Code | Team | Code | Team |
|------|------|------|------|
| ATL | Atlanta Hawks | MEM | Memphis Grizzlies |
| BOS | Boston Celtics | MIA | Miami Heat |
| BKN | Brooklyn Nets | NOP | New Orleans Pelicans |
| CHI | Chicago Bulls | NYK | New York Knicks |
| CLE | Cleveland Cavaliers | OKC | Oklahoma City Thunder |
| DAL | Dallas Mavericks | PHI | Philadelphia 76ers |
| DEN | Denver Nuggets | PHX | Phoenix Suns |
| GSW | Golden State Warriors | POR | Portland Trail Blazers |
| IND | Indiana Pacers | SAC | Sacramento Kings |
| LAC | LA Clippers | SAS | San Antonio Spurs |
| LAL | LA Lakers | TOR | Toronto Raptors |
| UTA | Utah Jazz | WAS | Washington Wizards |

---

## 🚀 That's It!

Every day, just run:
```bash
./quick_predict.sh "GAMES_HERE"
```

Everything else happens automatically! 🎉
