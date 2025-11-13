# VEGAS FEATURES - THE ISSUE & SOLUTION

## What Went Wrong

I just added Vegas features and the model got **WORSE**:
- PTS MAE: 0.89 → 1.61 (-81% worse!)
- Reason: **Data leakage**

### The Problem:

**Data Leakage:**
```python
# I calculated game totals from actual scores
game_total = team1_actual_pts + team2_actual_pts  # Includes our player!

# Then used it to predict our player's points
predict(player_pts, features=[..., game_total])  # Circular logic!
```

This is like:
- Predicting a player will score 25 points
- Using "the game had 225 total points" as a feature
- But those 225 points INCLUDE his 25!

**Missing Historical Data:**
- Real Vegas lines don't exist for 2023-24 training data
- Can't retroactively get what bookmakers set lines at
- Estimates from actuals = data leakage

---

## The REAL Solution

### For Training (Historical Data):
**DON'T use Vegas features in training** - we don't have clean historical data

### For Predictions (Today's Games):
**DO use real Vegas lines** - they're available and predictive

---

## How To Actually Use Vegas Features

### Option 1: Manual Input (BEST for now)

**Morning of predictions:**
```python
# Manually input today's lines
todays_vegas_lines = {
    'ORL@NYK': {'total': 218.5, 'spread': -5.5},  # NYK favored by 5.5
    'CHI@DET': {'total': 224.0, 'spread': -3.0},
    # ... rest of games
}

# Then adjust predictions
if game_total >= 230:
    pace_multiplier = 1.12
    # Apply to all predictions for that game
```

### Option 2: Scrape Real Vegas Lines

```python
# Fetch from Odds API (free tier)
import requests

def get_vegas_lines():
    # API endpoint (example)
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

    response = requests.get(url)
    lines = response.json()

    # Parse and return
    return lines
```

### Option 3: Train Without, Adjust After

**Keep current model** (no Vegas features in training)
**At prediction time**, apply manual adjustments:

```python
# Generate base predictions
base_prediction = model.predict(player_features)

# Manual Vegas adjustments
if game_total >= 230:
    adjusted_prediction = base_prediction * 1.08
elif spread >= 15:  # Blowout risk
    adjusted_prediction = base_prediction * 0.85

return adjusted_prediction
```

---

## What I'm Doing NOW

1. **Restored the working model** (PTS MAE 0.89)
2. **Removed the buggy Vegas features** from training
3. **Creating a prediction-time adjustment system**

This way:
- Model trains on clean data (no leakage)
- Predictions use real Vegas info (when available)
- You can manually input lines each morning

---

## For Tomorrow Morning

**Step 1:** Generate base predictions
```bash
python scripts/prediction/run_daily_predictions.py
```

**Step 2:** Manually adjust for Vegas info
- Check game totals on ESPN/Action Network
- High total (230+)? Add 8% to all predictions in that game
- Big spread (12+)? Reduce favorites' starters by 15%

---

## Bottom Line

**Vegas features ARE valuable** - but only at prediction time with REAL lines.

**For training:** Use clean features only (no leakage)

**For predictions:** Apply Vegas adjustments manually or via API

**Current model (PTS 0.89) is restored and working.**

---

I'll build the prediction-time adjustment system properly. That's the right way to use Vegas data.
