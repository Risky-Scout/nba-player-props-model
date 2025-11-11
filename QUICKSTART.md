# 🏀 NBA Props Model - Quick Start Guide

## ⚡ Generate Today's Predictions (One Command!)

```bash
./quick_predict.sh "TOR@BKN,MEM@NYK,GSW@OKC,BOS@PHI,IND@UTA,DEN@SAC"
```

That's it! This will:
- ✅ Generate ALL predictions (PMF, SGPs, individual props)
- ✅ Auto-commit to GitHub as **Risky-Scout**
- ✅ Display summary on screen

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

**Note:** You'll need to add today's games to the script or set up automatic game fetching.

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
