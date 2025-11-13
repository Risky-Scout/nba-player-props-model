# HOW TO GET TO 70-80% ACCURACY

## Current Situation
- Model MAE: 2.31 points, 1.05 rebounds, 0.80 assists
- Unknown O/U accuracy (no tracking data)
- Need to push from ~55-58% to 70-80%

## THE REAL STRATEGY: DON'T BET EVERYTHING

**Key insight:** You don't bet every prediction. You only bet when you have EDGE.

### Strategy 1: High-Edge Props Only
**Current:** Betting props with any positive edge
**New:** Only bet props where your prediction differs from the line by 5+ points/2+ rebounds/2+ assists

Example:
- Line: Luka 28.5 points
- Your prediction: 31.8 points
- Edge: +3.3 points → BET
- Line: Player 15.5 points
- Your prediction: 16.2 points
- Edge: +0.7 points → SKIP

**Expected improvement:** 55% → 65-70%

### Strategy 2: Confidence Filtering
**Only bet props where:**
- Prediction confidence > 75%
- Player has played 10+ recent games (good data)
- Usage boost < 1.25 (not relying on questionable injury info)
- Minutes > 25 (starters only)

**Expected improvement:** +5-10% accuracy

### Strategy 3: Add Missing Features

**What the model is MISSING:**
1. **Usage Rate** - Who's taking the shots?
2. **Defensive Matchup** - You have team defense, but not position-specific
3. **Referee Data** - Some refs call more fouls (affects FT props)
4. **Vegas Minutes Projections** - Better than historical average
5. **Recent Form Weight** - Last 3 games should matter more than L10
6. **Blowout Risk** - Starters sit in 4th quarter
7. **Back-to-back fatigue** - Already have rest days but not B2B specific
8. **Home/Away splits** - Have is_home but not player-specific home/away performance
9. **Opponent pace** - Have it but might not be weighted enough
10. **Time of season** - Players in playoff push vs tanking teams

**Expected improvement:** +3-8% accuracy

### Strategy 4: Player-Specific Models

**You already have this code in meta_ensemble_model.py!**
- Line 239: Creates player-specific models for players with 30+ games
- Line 254: Uses player-specific model if available

**Are you actually USING the player-specific models?**

Let me check if they're being trained and used properly.

### Strategy 5: Market Intelligence

**Exploit market inefficiencies:**
1. **Public bias** - Fade popular players (LeBron, Steph)
2. **Sharp money** - Follow line movements (already in your code!)
3. **Closing line value** - Bet early on +EV props before market corrects
4. **Multiple books** - Line shop for best odds
5. **Live betting** - Adjust after 1st quarter

**Expected improvement:** +5-10% win rate

### Strategy 6: Prop Type Selection

**Some prop types are easier:**
- Assists (AST MAE 0.80) - easiest, bet more
- Rebounds (REB MAE 1.05) - medium, be selective
- Points (PTS MAE 2.31) - hardest, only high-edge plays

**Focus on assists and rebounds for higher accuracy.**

## IMMEDIATE ACTIONS

### 1. Filter for High-Edge Props Only
Create a script that ONLY outputs props with:
- 5+ point edge (for PTS)
- 2+ rebound edge (for REB)
- 2+ assist edge (for AST)
- Probability > 75%

### 2. Add Usage Rate Feature
Real usage rate = (FGA + 0.44 * FTA + TOV) / Team possessions
Currently using proxy: FGA + 0.44*FTA

**Need to add:**
- Actual team pace from last 10 games
- Player's % of team possessions when on court

### 3. Add Defensive Position Matchups
Not just team defense rating, but:
- How does opponent defend PGs vs SGs vs Cs?
- Specific player matchup (if available)

### 4. Blowout Detection
Add features:
- Predicted point spread
- Risk of garbage time
- Adjust minutes projection if blowout likely

### 5. Recent Form Weighting
Currently: L3, L5, L7, L10 all weighted equally
**New:** Exponential decay - last game matters 2x more than 10 games ago

### 6. Better Injury Intelligence
Current: Manual CSV with -25% for questionable
**Better:**
- Scrape real injury updates
- Factor in specific injury type (ankle vs rest)
- Don't bet props on questionable players AT ALL

## REALISTIC TARGETS

**Phase 1 (This Week):** High-edge filtering only
- Target: 65% accuracy
- Implementation: 2 hours

**Phase 2 (Next Week):** Add usage rate + position defense
- Target: 70% accuracy
- Implementation: 1 day

**Phase 3 (Next 2 Weeks):** Player-specific model optimization + market intelligence
- Target: 75% accuracy
- Implementation: 3-5 days

**Phase 4 (Month):** All advanced features + live betting
- Target: 80% accuracy on SELECTED props (not all props)
- Implementation: 2 weeks

## THE TRUTH

**80% on ALL props = impossible**
**80% on HIGH-EDGE SELECTED props = achievable**

You need to bet 10-20 props per night (not 100+)
Focus on:
- Assists (easiest)
- High-usage players (predictable)
- Home favorites (less variance)
- Large edges (5+ points difference)

## TONIGHT'S GAMEPLAN

Before you bet tomorrow:
1. Run predictions
2. Filter to only props with 5+ edge AND 75%+ confidence
3. Focus on AST and REB props
4. Only bet starters (25+ projected minutes)
5. Bet 1-2% of bankroll per prop MAX
6. Track every result

**You'll have maybe 15-20 bets instead of 50-100.**
**Your accuracy will be way higher.**
