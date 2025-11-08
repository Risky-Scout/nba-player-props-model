# Daily NBA Props Prediction Workflow

## Two Outputs Every Day

### 1. FULL TECHNICAL OUTPUT (For Employers/Portfolio)
- **13,940 lines** of comprehensive predictions
- Shows complete PMF distributions for all props
- Demonstrates sportsbook-grade analytical depth
- File: `predictions/tonight_INJURY_ADJUSTED_YYYY-MM-DD.csv`

### 2. CLEAN SUMMARY REPORT (For Subscribers)
- **"The Risky Scout's NBA Player Prop Favorites"**
- Top 15 individual props (70-80% confidence)
- Top 10 two-leg SGPs
- Top 5 three-leg SGPs
- File: `predictions/RISKY_SCOUT_FAVORITES_YYYY-MM-DD.txt`

---

## Quick Start (Every Day)

### Step 1: Get NBA Injury Report

**Official Source:**
```
https://ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_09AM.pdf
```

**Updated 3x Daily:**
- 9:00 AM ET (morning)
- 1:30 PM ET (afternoon)
- 5:30 PM ET (final pre-game)

### Step 2: Create Injury CSV

Create `data/injuries/injuries_YYYY-MM-DD.csv`:

```csv
player,status,reason,out_flag,questionable_flag,probable_flag,game_date
LeBron James,Out,Right sciatica,1,0,0,2025-11-08
Austin Reaves,Out,Right groin strain,1,0,0,2025-11-08
Maxi Kleber,Questionable,Abdominal muscle strain,0,1,0,2025-11-08
Shaedon Sharpe,Probable,Left calf strain,0,0,1,2025-11-08
```

### Step 3: Run Daily Pipeline

```bash
# Generate full technical predictions (13,940 lines)
python run_daily_predictions.py \
  --date 2025-11-08 \
  --games "DAL@WAS,TOR@PHI,CHI@CLE,LAL@ATL,POR@MIA,NOP@SAS,IND@DEN,PHX@LAC" \
  --injuries data/injuries/injuries_2025-11-08.csv
```

### Step 4: Generate Clean Summary Report

```bash
# Generate subscriber-facing report
python generate_risky_scout_report.py --date 2025-11-08
```

**Output:**
- `predictions/RISKY_SCOUT_FAVORITES_2025-11-08.txt` - Beautiful formatted report
- `predictions/top_props_2025-11-08.csv` - Top 15 individual props
- `predictions/sgp_2leg_2025-11-08.csv` - Top 10 two-leg SGPs
- `predictions/sgp_3leg_2025-11-08.csv` - Top 5 three-leg SGPs

---

## What the Pipeline Does

### Injury Adjustments
1. ✅ Removes OUT players completely
2. ✅ Reduces minutes for QUESTIONABLE players (-25%)
3. ✅ Reduces minutes for PROBABLE players (-7%)
4. ✅ Applies usage boosts for teams with key injuries:
   - **2+ stars OUT**: +25% usage for remaining players
   - **1 star OUT**: +15% usage for remaining players

### Model Features
- ✅ Real opponent defensive ratings (103.18 to 117.91)
- ✅ Real correlations for SGPs (PTS-REB: 0.647)
- ✅ Rolling averages (L3, L5, L7, L10) with shift(1) to prevent leakage
- ✅ Home/away splits
- ✅ Rest days
- ✅ Opponent pace

---

## Model Performance

**Validation Results:**
- **Points**: MAE 2.31 points (71.6% within 3 points)
- **Rebounds**: MAE 1.05 rebounds (90.4% within 3 rebounds)
- **Assists**: MAE 0.80 assists (95.1% within 3 assists)

**Training Data:**
- 9,573 real NBA games
- 735 unique players
- Date range: Oct 2023 - Nov 2025

---

## Team Abbreviations

```
ATL=1   BOS=2   BKN=3   CHA=4   CHI=5   CLE=6   DAL=7   DEN=8
DET=9   GSW=10  HOU=11  IND=12  LAC=13  LAL=14  MEM=15  MIA=16
MIL=17  MIN=18  NOP=19  NYK=20  OKC=21  ORL=22  PHI=23  PHX=24
POR=25  SAC=26  SAS=27  TOR=28  UTA=29  WAS=30
```

---

## Example: "The Risky Scout's NBA Player Prop Favorites"

```
================================================================================
THE RISKY SCOUT'S NBA PLAYER PROP FAVORITES
Date: 2025-11-08
Generated: 2025-11-08 09:30 PM ET
================================================================================

MODEL PERFORMANCE
--------------------------------------------------------------------------------
Points:   MAE 2.31 pts  | 71.6% within 3 points
Rebounds: MAE 1.05 reb  | 90.4% within 3 rebounds
Assists:  MAE 0.80 ast  | 95.1% within 3 assists

================================================================================
TOP 15 INDIVIDUAL PROPS (70-80% Confidence)
================================================================================

# 1.              Evan Mobley (   Cleveland Cavaliers)
     REB Over   8.0
     Probability:  80.0%  |  Expected Value: 9.5  |  Fair Odds:  -400

# 2.          Bilal Coulibaly (    Washington Wizards)
     AST Over   2.0
     Probability:  80.0%  |  Expected Value: 3.2  |  Fair Odds:  -400

# 3.         Victor Wembanyama (     San Antonio Spurs)
     PTS Over  25.0
     Probability:  79.7%  |  Expected Value: 28.2  |  Fair Odds:  -391
...
```

---

## Files & Directories

```
nba-player-props-model/
├── run_daily_predictions.py          # Main pipeline script
├── generate_risky_scout_report.py    # Summary report generator
├── data/
│   ├── injuries/                     # Daily injury reports
│   ├── processed_training_data.csv   # Training data (9,573 games)
│   └── team_ratings.csv              # Real defensive ratings
├── model_cache/
│   └── trained_models.pkl            # Trained ensemble models
└── predictions/
    ├── tonight_INJURY_ADJUSTED_*.csv # Full technical output (13,940 lines)
    ├── RISKY_SCOUT_FAVORITES_*.txt   # Clean subscriber report
    ├── top_props_*.csv               # Top 15 props
    ├── sgp_2leg_*.csv                # Top 10 two-leg SGPs
    └── sgp_3leg_*.csv                # Top 5 three-leg SGPs
```

---

## Why Two Outputs?

**Full Technical Output (13,940 lines):**
- Impresses employers: "This guy built a real sportsbook-grade system"
- Shows depth of analysis (complete PMF distributions)
- Demonstrates understanding of probability theory
- Portfolio piece: "One-man operation competing with 1000-person sportsbooks"

**Clean Summary Report:**
- Customer-ready product for paying subscribers
- Easy to read and actionable
- Professional branding ("The Risky Scout")
- Daily value proposition for membership

---

## Future Enhancements

1. ✅ Auto-fetch injury reports from NBA.com PDF
2. ✅ Auto-detect usage boosts based on star players OUT
3. ✅ PDF export of summary report
4. ✅ Email delivery to subscribers
5. ✅ Historical tracking of prediction accuracy

---

© The Risky Scout - Advanced NBA Analytics
