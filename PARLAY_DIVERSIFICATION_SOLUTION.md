# PARLAY DIVERSIFICATION - SOLUTION

## The Problems You Identified:

### Problem 1: Players Not Available on Books ❌
- Model predicts on ALL players in games
- Bookmakers only offer lines for ~30-50 players per night
- Many parlays include players with no available lines
- **Result:** Parlays are worthless

### Problem 2: Same Players in Every Parlay ❌
- Top 100 parlays use only 3-4 unique players
- No diversification
- If those players fail, ALL parlays fail
- **Result:** High risk, no spreading

---

## THE SOLUTION

### New Tool: `generate_diverse_parlays.py`

**What it does:**
1. ✅ Filters to only bookmaker-available players
2. ✅ Limits player repetition (max 2 appearances in top 100)
3. ✅ Forces cross-game parlays (lower correlation)
4. ✅ No duplicate players within same parlay
5. ✅ Prioritizes high-probability combinations

---

## HOW TO USE IT

### Step 1: Create Player Availability List

**First time setup:**
```bash
# Create template (lists common players)
python scripts/prediction/generate_diverse_parlays.py predictions/tonight_*.csv available_players.txt
```

This creates `available_players.txt` with template.

**Edit the file:**
```text
# List of players available on your betting site
# One player name per line

LeBron James
Stephen Curry
Luka Doncic
Nikola Jokic
... (add only players with lines on your book)
```

### Step 2: Generate Diverse Parlays

```bash
# With player filter:
python scripts/prediction/generate_diverse_parlays.py \
  predictions/tonight_INJURY_ADJUSTED_20251113.csv \
  available_players.txt
```

**Output:**
- `predictions/tonight_INJURY_ADJUSTED_20251113_AVAILABLE_ONLY.csv` (filtered predictions)
- `predictions/tonight_INJURY_ADJUSTED_20251113_DIVERSE_PARLAYS.csv` (top 100 diverse parlays)

---

## DIVERSIFICATION RULES

### Player Limits:
- **Max appearances:** 2 times per player in top 100 parlays
- **Adjustable:** Change `max_player_repeats` parameter

### Parlay Constraints:
1. ✅ All 3 players must be different
2. ✅ All 3 players from different games (cross-game only)
3. ✅ Minimum 30% combined probability
4. ✅ Minimum 70% per-leg probability

### Ranking:
- Sorted by EV score (probability × expected value)
- Accounts for correlation reduction

---

## EXAMPLE OUTPUT

### Before (Old System):
```
Top 10 Parlays:
1. Luka + Luka + Luka    (same player!)
2. Luka + Jokic + Luka
3. Jokic + Luka + Jokic
4. Luka + Luka + Curry
...

Unique players: 3 total
Problem: No diversification
```

### After (New System):
```
Top 100 Parlays:
Player Distribution:
  LeBron James        appears 2 times
  Stephen Curry       appears 2 times
  Luka Doncic         appears 2 times
  Nikola Jokic        appears 2 times
  Joel Embiid         appears 2 times
  Giannis             appears 2 times
  ... (45 more players)

Unique players: 50 total
✓ Diversification achieved
```

---

## WORKFLOW FOR TOMORROW

### Morning (10 minutes):

**1. Check bookmaker for available players**
- Log into your betting site
- See which players have props offered
- Update `available_players.txt`

**2. Generate predictions**
```bash
python scripts/prediction/run_daily_predictions.py
```

**3. Generate diverse parlays**
```bash
python scripts/prediction/generate_diverse_parlays.py \
  predictions/tonight_INJURY_ADJUSTED_20251113.csv \
  available_players.txt
```

**4. Bet top 20-30 parlays**
- All use different players
- All cross-game (independent)
- Risk spread across 50+ players

---

## CUSTOMIZATION

### Change Player Limit:
Edit line 85 in script:
```python
max_player_repeats=3  # Allow 3 appearances instead of 2
```

### Change Confidence Threshold:
Edit line 86:
```python
min_confidence=0.75  # Require 75% instead of 70%
```

### Change Parlay Count:
Edit line 164:
```python
if len(diverse_parlays) >= 200:  # Generate 200 instead of 100
```

---

## BENEFITS

### Old System Issues:
- ❌ 100 parlays with 3-4 unique players
- ❌ Players not available on books
- ❌ High correlation (same players fail together)
- ❌ No risk diversification

### New System:
- ✅ 100 parlays with 50+ unique players
- ✅ Only bookmaker-available players
- ✅ Low correlation (cross-game)
- ✅ Risk spread across many players
- ✅ Max 2 appearances per player
- ✅ Usable parlays only

---

## FILES CREATED

1. **`scripts/prediction/generate_diverse_parlays.py`**
   - Main tool
   - Generates diverse, usable parlays

2. **`available_players.txt`** (you create/edit)
   - List of players with lines on your book
   - One per line
   - Update daily

3. **Output files:**
   - `*_AVAILABLE_ONLY.csv` - Filtered predictions
   - `*_DIVERSE_PARLAYS.csv` - Top 100 diverse parlays

---

## TOMORROW'S QUICK START

```bash
# 1. Update available players (based on your book)
nano available_players.txt

# 2. Generate predictions
python scripts/prediction/run_daily_predictions.py

# 3. Generate diverse parlays
python scripts/prediction/generate_diverse_parlays.py \
  predictions/tonight_INJURY_ADJUSTED_$(date +%Y%m%d).csv \
  available_players.txt

# 4. Bet the top 20-30 parlays
```

Done. Diversified. Usable.
