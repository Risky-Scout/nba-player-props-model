# NBA PLAYER PROPS MODEL - DAILY WORKFLOW GUIDE

**Last Updated:** November 8, 2025

This guide provides step-by-step instructions for running the model every single day.
Follow these steps in order to generate predictions, client reports, and track accuracy.

---

## OVERVIEW: THREE DAILY OUTPUTS

### 1. FULL TECHNICAL PREDICTIONS (For Portfolio/Employers)
- **~14,000 lines** of comprehensive PMF distributions
- Shows complete probability distributions for all props
- Demonstrates sportsbook-grade analytical depth
- **File:** `predictions/tonight_INJURY_ADJUSTED_YYYY-MM-DD.csv`

### 2. CLIENT REPORT (For Betting Clients)
- **"The Risky Scout's NBA Player Prop Favorites"**
- Bankroll management tiers (Conservative, Moderate, Value)
- Top 12 two-leg SGPs with reasoning
- Top 5 three-leg SGPs
- Injury alerts and usage boost notifications
- **File:** `predictions/RISKY_SCOUT_FAVORITES_YYYY-MM-DD.txt`

### 3. ACCURACY TRACKING (For Public Record)
- Daily results tracking
- Cumulative win/loss record
- Performance by prop type (PTS, REB, AST)
- **File:** `accuracy_tracking/ACCURACY_SUMMARY.md`

---

## DAILY WORKFLOW (RUN EVERY DAY)

###  STEP 1: GET TODAY'S NBA INJURY REPORT (9:00 AM - 5:30 PM ET)

**Official NBA Injury Report Source:**
```
https://ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_09AM.pdf
```

**Update Times (pick the latest before game time):**
- **9:00 AM ET** - Morning report
- **1:30 PM ET** - Afternoon update
- **5:30 PM ET** - Final pre-game update (RECOMMENDED)

**Example URLs:**
```
https://ak-static.cms.nba.com/referee/injury/Injury-Report_2025-11-08_09AM.pdf
https://ak-static.cms.nba.com/referee/injury/Injury-Report_2025-11-08_0130PM.pdf
https://ak-static.cms.nba.com/referee/injury/Injury-Report_2025-11-08_0530PM.pdf
```

**Create Injury CSV:**

1. Download the PDF from the URL above
2. Create file: `data/injuries/injuries_YYYY-MM-DD.csv`
3. Use this exact format:

```csv
player,status,reason,out_flag,questionable_flag,probable_flag,game_date
LeBron James,Out,Right sciatica,1,0,0,2025-11-08
Austin Reaves,Out,Right groin strain,1,0,0,2025-11-08
Maxi Kleber,Questionable,Abdominal muscle strain,0,1,0,2025-11-08
Shaedon Sharpe,Probable,Left calf strain,0,0,1,2025-11-08
```

**Flags Explanation:**
- `out_flag=1` → Player will NOT play (remove from predictions, boost teammates)
- `questionable_flag=1` → Player might play (-25% minutes if they do)
- `probable_flag=1` → Player likely plays (-7% minutes reduction)

**CRITICAL:** Only ONE flag can be 1 per player.

---

### 🏀 STEP 2: IDENTIFY TONIGHT'S GAMES

**Find today's NBA schedule:**
- Visit: https://www.nba.com/schedule
- Or check ESPN, TheScore, etc.

**Format Games String:**
```
AWAY@HOME,AWAY@HOME,AWAY@HOME
```

**Example (Nov 8, 2025):**
```
DAL@WAS,TOR@PHI,CHI@CLE,LAL@ATL,POR@MIA,NOP@SAS,IND@DEN,PHX@LAC
```

**Team Abbreviations Reference:**
```
ATL  = Atlanta Hawks          BOS  = Boston Celtics
BKN  = Brooklyn Nets          CHA  = Charlotte Hornets
CHI  = Chicago Bulls          CLE  = Cleveland Cavaliers
DAL  = Dallas Mavericks       DEN  = Denver Nuggets
DET  = Detroit Pistons        GSW  = Golden State Warriors
HOU  = Houston Rockets        IND  = Indiana Pacers
LAC  = LA Clippers            LAL  = Los Angeles Lakers
MEM  = Memphis Grizzlies      MIA  = Miami Heat
MIL  = Milwaukee Bucks        MIN  = Minnesota Timberwolves
NOP  = New Orleans Pelicans   NYK  = New York Knicks
OKC  = Oklahoma City Thunder  ORL  = Orlando Magic
PHI  = Philadelphia 76ers     PHX  = Phoenix Suns
POR  = Portland Trail Blazers SAC  = Sacramento Kings
SAS  = San Antonio Spurs      TOR  = Toronto Raptors
UTA  = Utah Jazz              WAS  = Washington Wizards
```

---

### 🤖 STEP 3: RUN THE PREDICTION PIPELINE

**Command:**
```bash
python scripts/prediction/run_daily_predictions.py \
  --date 2025-11-08 \
  --games "DAL@WAS,TOR@PHI,CHI@CLE,LAL@ATL,POR@MIA,NOP@SAS,IND@DEN,PHX@LAC" \
  --injuries data/injuries/injuries_2025-11-08.csv
```

**Replace:**
- `2025-11-08` → Today's date (YYYY-MM-DD)
- Games string → Actual games from Step 2
- Injury file path → Your injury CSV from Step 1

**What This Does:**
1. ✅ Loads trained models from `model_cache/trained_models.pkl`
2. ✅ Loads training data (9,573 games)
3. ✅ Filters to tonight's teams only
4. ✅ Removes OUT players from predictions
5. ✅ Reduces minutes for QUESTIONABLE/PROBABLE players
6. ✅ Applies usage boosts for teams with stars out
7. ✅ Generates complete PMF distributions for all props
8. ✅ Saves full predictions CSV (~14,000 lines)

**Expected Output:**
```
================================================================================
NBA PLAYER PROPS PIPELINE - 2025-11-08
================================================================================

Tonight's games (8):
  DAL@WAS
  TOR@PHI
  ...

Team IDs: [7, 30, 28, 23, 5, 6, 14, 1, 25, 16, 19, 27, 12, 8, 24, 13]

Injuries: 24 OUT, 3 QUESTIONABLE

Players: 147 (after removing OUT)
Active players: 112

Generating predictions...

✓ Generated 13,940 predictions
✓ Saved to predictions/tonight_INJURY_ADJUSTED_20251108.csv

================================================================================
TOP 10 PICKS FOR TONIGHT
================================================================================

              Evan Mobley REB Over   8.0:  80.0% | EV: 9.5
          Bilal Coulibaly AST Over   2.0:  80.0% | EV: 3.2
         Brandon Ingram REB Over   4.0:  79.9% | EV: 5.5
                ...

✓ Pipeline complete!
```

**Output File:** `predictions/tonight_INJURY_ADJUSTED_20251108.csv`

---

### 📊 STEP 4: GENERATE CLIENT REPORT

**Command:**
```bash
python scripts/reports/generate_risky_scout_report.py --date 2025-11-08
```

**What This Does:**
1. ✅ Loads predictions from Step 3
2. ✅ Categorizes props by bankroll tier (Conservative/Moderate/Value)
3. ✅ Generates 2-leg SGPs with correlation analysis
4. ✅ Generates 3-leg SGPs with multi-way correlations
5. ✅ Creates formatted client report
6. ✅ Identifies injury impact opportunities

**Expected Output:**
```
================================================================================
GENERATING THE RISKY SCOUT'S NBA PLAYER PROP FAVORITES
================================================================================

Loaded 13,940 total predictions

Generating SGP recommendations...

✓ Report generated: predictions/RISKY_SCOUT_FAVORITES_2025-11-08.txt
✓ Data files saved

[Full report prints to console...]
```

**Output Files:**
- `predictions/RISKY_SCOUT_FAVORITES_2025-11-08.txt` - Main client report
- `predictions/top_props_2025-11-08.csv` - Top individual props
- `predictions/sgp_2leg_2025-11-08.csv` - 2-leg SGPs
- `predictions/sgp_3leg_2025-11-08.csv` - 3-leg SGPs

**Client Report Structure:**
1. **Key Injury Alerts** - Stars out tonight
2. **Model Performance** - Validation metrics
3. **Conservative Tier** - 75-80% confidence props
4. **Moderate Tier** - 70-75% confidence props
5. **Value Tier** - 65-70% confidence props
6. **2-Leg SGPs** - Correlated parlays with reasoning
7. **3-Leg SGPs** - Higher payout SGPs

---

### ✅ STEP 5: REVIEW AND SEND TO CLIENTS

**Open the client report:**
```bash
cat predictions/RISKY_SCOUT_FAVORITES_2025-11-08.txt
```

**Quality Checks:**
1. ✅ Injury alerts show correct star players
2. ✅ Props make sense (no weird lines like -0.5 points)
3. ✅ SGPs are on the same team (Same Game Parlays)
4. ✅ Probabilities in reasonable range (65-80%)

**Send to Clients:**
- Email the `.txt` file
- Or copy/paste into Substack, Discord, Telegram, etc.

---

### 📈 STEP 6: NEXT DAY - TRACK ACCURACY

**After games complete (next morning):**

```bash
python scripts/reports/track_accuracy.py --date 2025-11-08 --enter-results
```

**Interactive Entry:**
1. Script will prompt you to enter actual results
2. Format: `player,prop,actual_value`
3. Example: `LeBron James,PTS,28`
4. Type `done` when finished

**Or Load from CSV:**
1. Create `actual_results_2025-11-08.csv`:
```csv
player,prop,actual_value
LeBron James,PTS,28
Anthony Davis,REB,12
D'Angelo Russell,AST,6
```
2. When prompted, choose option 2 and provide file path

**What This Does:**
1. ✅ Matches predictions with actual results
2. ✅ Calculates which predictions hit (actual > line)
3. ✅ Updates master accuracy log
4. ✅ Generates public accuracy summary
5. ✅ Shows daily and cumulative win rate

**Expected Output:**
```
================================================================================
ENTERING RESULTS FOR 2025-11-08
================================================================================

Found 15 predictions to track (70-80% confidence)

Enter actual stats for each prediction
Format: player,prop,actual_value

➡️  LeBron James,PTS,28
➡️  Anthony Davis,REB,12
➡️  done

✓ Results saved for 2025-11-08
  Correct: 12/15 (80.0%)
  Average Error: 1.87
  Saved to: accuracy_tracking/daily_results/results_2025-11-08.csv

✓ Summary updated: accuracy_tracking/ACCURACY_SUMMARY.md
```

**View Accuracy Summary:**
```bash
python scripts/reports/track_accuracy.py --summary
```

**Public Record:**
The `accuracy_tracking/ACCURACY_SUMMARY.md` file is your **public proof of model performance**.
Commit this to GitHub to show employers/clients your real track record.

---

### 🔄 STEP 7: COMMIT TO GITHUB

**Stage all changes:**
```bash
git add predictions/ accuracy_tracking/ data/injuries/
```

**Commit with descriptive message:**
```bash
git commit -m "$(cat <<'EOF'
Daily predictions for 2025-11-08

- Generated 13,940 predictions across 8 games
- 24 players OUT (LeBron, Kawhi, Lillard, etc.)
- Applied usage boosts for LAL, LAC, MIL
- Client report: Top 20 props + 12 SGPs
- Previous day accuracy: 12/15 (80.0%)
EOF
)"
```

**Push to GitHub:**
```bash
git push -u origin claude/resume-idle-session-011CUnDRcAXsfAkB5pENHEkG
```

**Why This Matters:**
- ✅ Creates public record of predictions
- ✅ Shows employers real-time model updates
- ✅ Proves you're running this daily
- ✅ Demonstrates GitHub workflow skills

---

## COMPLETE DAILY CHECKLIST

Use this checklist every single day:

- [ ] **9:00 AM - 5:30 PM:** Download NBA injury report
- [ ] Create injury CSV in `data/injuries/injuries_YYYY-MM-DD.csv`
- [ ] Get tonight's NBA schedule (games string)
- [ ] Run `python scripts/prediction/run_daily_predictions.py ...` (Step 3)
- [ ] Verify output: `predictions/tonight_INJURY_ADJUSTED_*.csv` exists
- [ ] Run `python scripts/reports/generate_risky_scout_report.py ...` (Step 4)
- [ ] Review client report: `predictions/RISKY_SCOUT_FAVORITES_*.txt`
- [ ] Send report to clients (email, Discord, etc.)
- [ ] Commit and push to GitHub
- [ ] **Next Morning:** Run `python scripts/reports/track_accuracy.py --enter-results`
- [ ] Verify accuracy summary updated
- [ ] Commit accuracy results to GitHub

---

## TROUBLESHOOTING

### Problem: "Injury file not found"
**Solution:** Check file path. Must be exact: `data/injuries/injuries_YYYY-MM-DD.csv`

### Problem: "No predictions generated"
**Solution:** Verify team abbreviations in games string match the mapping in `run_daily_predictions.py` (line 33-38)

### Problem: "ModuleNotFoundError"
**Solution:** Install dependencies:
```bash
pip install pandas numpy scikit-learn scipy
```

### Problem: "Prediction file not found" (when generating report)
**Solution:** Run Step 3 first! The report needs the predictions CSV from the pipeline.

### Problem: Low accuracy (< 60%)
**Potential Causes:**
1. Not using latest injury report (use 5:30 PM update)
2. Model needs retraining (do monthly)
3. Small sample size (wait for 50+ predictions)

---

## MODEL MAINTENANCE

### Weekly Maintenance
**Not required** - Model is trained on full dataset

### Monthly Maintenance (Recommended)
**Retrain models with new data:**
1. Update `data/processed_training_data.csv` with latest games
2. Run full training pipeline
3. Update `model_cache/trained_models.pkl`

### Quarterly Maintenance
**Recalibrate injury coefficients:**
1. Analyze usage boost accuracy (1.15x vs 1.25x)
2. Update coefficients if needed
3. Recalculate correlation matrix

---

## FILE LOCATIONS REFERENCE

```
nba-player-props-model/
├── data/
│   ├── processed_training_data.csv      # 9,573 training games
│   ├── team_ratings.csv                 # Real defensive ratings
│   └── injuries/
│       └── injuries_YYYY-MM-DD.csv      # Daily injury reports
│
├── model_cache/
│   └── trained_models.pkl               # Trained models (RF + GB)
│
├── predictions/
│   ├── tonight_INJURY_ADJUSTED_*.csv    # Full predictions (~14K lines)
│   ├── RISKY_SCOUT_FAVORITES_*.txt      # Client report
│   ├── top_props_*.csv                  # Top individual props
│   ├── sgp_2leg_*.csv                   # 2-leg SGPs
│   └── sgp_3leg_*.csv                   # 3-leg SGPs
│
├── accuracy_tracking/
│   ├── accuracy_log.csv                 # Master log (all predictions)
│   ├── daily_results/                   # Per-day results
│   │   └── results_YYYY-MM-DD.csv
│   └── ACCURACY_SUMMARY.md              # Public performance report
│
├── run_daily_predictions.py             # Main pipeline (Step 3)
├── generate_risky_scout_report.py       # Client report (Step 4)
├── track_accuracy.py                    # Accuracy tracking (Step 6)
│
├── DAILY_WORKFLOW.md                    # This file
└── TECHNICAL_REPORT.md                  # PhD-level documentation
```

---

## INJURY DATA INTEGRATION - HOW IT WORKS

### Automatic Injury Detection

The model **automatically** retrieves and processes injury data:

1. **Source:** You provide the injury CSV (from NBA.com PDF)
2. **Detection:** Model reads `out_flag`, `questionable_flag`, `probable_flag`
3. **Player Removal:** OUT players completely removed from predictions
4. **Minutes Adjustment:**
   - QUESTIONABLE: -25% minutes
   - PROBABLE: -7% minutes
5. **Usage Boost Detection:**
   - Model identifies star players (LeBron, Kawhi, Lillard, etc.)
   - Counts how many stars are OUT per team
   - Applies usage boosts to teammates:
     - 2+ stars OUT → +25% usage
     - 1 star OUT → +15% usage

### Star Player List

The model recognizes these players as "stars" for usage boost purposes:

```python
star_players = {
    'LeBron James', 'Austin Reaves', 'Paul George', 'Kawhi Leonard',
    'Damian Lillard', 'Zion Williamson', 'Dejounte Murray',
    'Tyrese Haliburton', 'Jordan Poole', 'Scoot Henderson',
    'Stephen Curry', 'Kevin Durant', 'Giannis Antetokounmpo',
    'Joel Embiid', 'Nikola Jokic', 'Luka Doncic', 'Anthony Davis',
    'Jimmy Butler', 'Jayson Tatum', 'Ja Morant'
}
```

### Example: Lakers Without LeBron

**Injury Report:**
```csv
LeBron James,Out,Right sciatica,1,0,0,2025-11-08
```

**Model Actions:**
1. ✅ Removes LeBron from predictions
2. ✅ Identifies Lakers have 1 star OUT
3. ✅ Applies +15% usage boost to AD, DLo, Rui, etc.
4. ✅ Predictions for Lakers players increase by ~15%

**Result:** Client report shows high-value opportunities on Lakers teammates.

---

## QUESTIONS?

**Model not working?** Check:
1. File paths are correct
2. Date format is YYYY-MM-DD
3. Injury CSV has correct columns
4. Games string has correct team abbreviations

**Need to retrain?** See TECHNICAL_REPORT.md Section 5 (Training & Validation)

**Want to add features?** See TECHNICAL_REPORT.md Section 3 (Feature Engineering)

---

## SUMMARY

**Daily Time Commitment:** 15-20 minutes
- 5 min: Get injury report & create CSV
- 5 min: Run pipeline + generate report
- 5 min: Review and send to clients
- 5 min: Next day - enter results

**Weekly Time Commitment:** ~2 hours total (15 min/day × 7 days)

**Monthly Maintenance:** 1-2 hours (optional retraining)

**Result:**
- Professional-grade predictions every day
- Public accuracy record in GitHub
- Portfolio piece for interviews
- Potential revenue from betting clients

---

© The Risky Scout - Advanced NBA Analytics
