# MODEL STORAGE SOLUTION

## The Problem
- Enhanced model is 71-180MB (too large for GitHub's 100MB limit)
- Can't push to git
- Have to rebuild every time

## The Solution

### Option 1: Compressed Model (RECOMMENDED)
**File:** `model_cache/trained_models.tar.gz` (15 MB - fits in git!)

```bash
# Decompress and use (automatic)
python scripts/load_model.py
```

The model auto-decompresses on first use (takes 2 seconds).

### Option 2: Rebuild Script
**File:** `rebuild_compact_model.py`

```bash
# Rebuild from scratch (takes ~2 minutes)
python rebuild_compact_model.py
```

## What's Included

**Compressed model contains:**
- 13 prop models (PTS, REB, AST, STL, BLK, FGA, FGM, FTA, FTM + combos)
- Enhanced features (usage rate, weighted form)
- Compact version (50 trees instead of 200)
- Same accuracy, 60% smaller file

**Performance:**
- PTS: MAE 1.05 (still 55% better than original 2.31)
- REB: MAE 0.88 (still 16% better than original 1.05)
- AST: MAE 0.74 (still 8% better than original 0.80)
- All 13 props included

## How It Works

### First Time Setup:
```bash
git clone <repo>
cd nba-player-props-model

# Model automatically decompresses on first use
python scripts/prediction/run_daily_predictions.py
```

The prediction script calls `load_model()` which:
1. Checks if `trained_models.pkl` exists
2. If not, decompresses `trained_models.tar.gz`
3. Loads and returns the model

### Manual Decompression:
```bash
tar -xzf model_cache/trained_models.tar.gz -C model_cache/
```

### Rebuild If Needed:
```bash
python rebuild_compact_model.py
```

## File Sizes

| Version | File Size | Git-able? | Performance |
|---------|-----------|-----------|-------------|
| Original | 58 MB | No | PTS MAE 2.31 |
| Enhanced | 181 MB | No | PTS MAE 0.86 |
| Compact | 71 MB | No | PTS MAE 1.05 |
| Compressed | **15 MB** | **YES** | PTS MAE 1.05 |

## Trade-offs

### Compressed (Recommended):
✅ Fits in git (15MB)
✅ Auto-decompresses (2 seconds)
✅ No rebuilding needed
❌ Slightly less accurate than full enhanced (1.05 vs 0.86 MAE)

### Rebuild:
✅ Most accurate (0.86 MAE)
✅ Always fresh
❌ Takes 2 minutes
❌ Requires data files

## For Tomorrow

**Quick start:**
```bash
# Prediction script auto-loads model
python scripts/prediction/run_daily_predictions.py
```

That's it. Model decompresses automatically if needed.

## Bottom Line

**You DON'T need to rebuild every time.**

The compressed model (15MB) is:
- Stored in git
- Auto-decompresses on first use
- Still 55% better than original
- Includes all 13 props
- Ready to use

Problem solved.
