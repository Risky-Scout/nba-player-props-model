# Daily NBA Props Prediction Workflow

## Quick Start (Every Day)

### Step 1: Create Today's Injury Report

Create `data/injuries/injuries_YYYY-MM-DD.csv` with this format:

```csv
player,status,reason,out_flag,questionable_flag,probable_flag,game_date
LeBron James,Out,Right sciatica,1,0,0,2025-11-08
Austin Reaves,Out,Right groin strain,1,0,0,2025-11-08
Maxi Kleber,Questionable,Abdominal muscle strain,0,1,0,2025-11-08
```

**Flags:**
- `out_flag=1` if player is OUT
- `questionable_flag=1` if QUESTIONABLE
- `probable_flag=1` if PROBABLE

### Step 2: Run the Daily Pipeline

```bash
python run_daily_predictions.py \
  --date 2025-11-08 \
  --games "DAL@WAS,TOR@PHI,CHI@CLE,LAL@ATL,POR@MIA,NOP@SAS,IND@DEN,PHX@LAC" \
  --injuries data/injuries/injuries_2025-11-08.csv
```

### Step 3: Get Your Picks

Open `predictions/daily_2025-11-08.csv` for all predictions

Filter for high-confidence picks (70-80% probability)

## What the Pipeline Does

1. ✅ Loads injury report
2. ✅ Removes OUT players from predictions
3. ✅ Reduces minutes for QUESTIONABLE players (75%)
4. ✅ Applies usage boosts for teams with multiple injuries:
   - 2+ stars out: +25% usage for remaining players
   - 1 star out: +15% usage for remaining players
5. ✅ Generates predictions with REAL opponent defensive ratings
6. ✅ Outputs probabilities and fair odds

## Model Performance

- **PTS**: MAE 2.31 points (71.6% within 3 points)
- **REB**: MAE 1.05 rebounds (90.4% within 3 rebounds)
- **AST**: MAE 0.80 assists (95.1% within 3 assists)

Trained on 9,573 real NBA games with real opponent defensive ratings (103.18 to 117.91).

## Team Abbreviations

```
ATL=1, CHI=5, CLE=6, DAL=7, DEN=8, IND=12, LAC=13,
LAL=14, MIA=16, NOP=19, PHI=23, PHX=24, POR=25,
SAS=27, TOR=28, WAS=30
```

## Future Improvements

1. **Auto-fetch injury reports** from NBA.com PDF
2. **Auto-detect usage boosts** based on star players OUT
3. **SGP generation** with correlation adjustments
4. **Real-time updates** (morning, midday, pre-game)

## Files

- `run_daily_predictions.py` - Main pipeline script
- `data/injuries/` - Daily injury reports
- `predictions/` - Daily prediction outputs
- `model_cache/trained_models.pkl` - Trained ensemble models
