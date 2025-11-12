# 🤖 NBA Player Props - Complete Automation Setup

## Quick Start (5 minutes)

Run this **once** on your server/machine:

```bash
chmod +x install_cron.sh
./install_cron.sh
```

That's it! Your model will now:
- ✅ Train itself daily at 7:00 AM CST
- ✅ Fetch injury reports at 5:45 PM CST
- ✅ Generate predictions at 6:00 PM CST
- ✅ Auto-commit & push to GitHub

---

## 📅 Automated Daily Schedule

| Time (CST) | Action | What Happens |
|------------|--------|--------------|
| 7:00 AM | **Training** | Collects latest game data, retrains RF + GB models |
| 5:45 PM | **Injury Fetch** | Downloads NBA injury report, converts to CSV |
| 6:00 PM | **Predictions** | Generates all predictions with injury adjustments, commits to GitHub |

---

## 📊 What Gets Generated Daily

Every evening at 6 PM, these files appear in `predictions/`:

1. **complete_pmf_distributions_YYYYMMDD.csv** - Full probability distributions
2. **sgp_2leg_YYYYMMDD.csv** - Top 50 two-leg same-game parlays
3. **sgp_3leg_YYYYMMDD.csv** - Top 30 three-leg same-game parlays
4. **summary_YYYYMMDD.txt** - Human-readable top picks
5. **premium/** folder - Top 100 rankings + HTML client deliverable

---

## 🔧 Verify Installation

After running `install_cron.sh`, check:

```bash
# View installed cron jobs
crontab -l

# You should see 3 jobs:
#  - 0 13 * * * ... (7 AM CST training)
#  - 45 23 * * * ... (5:45 PM CST injury fetch)
#  - 0 0 * * * ... (6 PM CST predictions)
```

---

## 📝 Monitor Daily Operations

### Check Logs

```bash
# Training log (runs at 7 AM)
tail -f logs/cron_train.log

# Injury fetch log (runs at 5:45 PM)
tail -f logs/cron_injuries.log

# Prediction log (runs at 6 PM)
tail -f logs/cron_predict.log
```

### Today's Predictions

```bash
# View summary
cat predictions/summary_$(date +%Y%m%d).txt

# View top SGPs
head -20 predictions/sgp_2leg_$(date +%Y%m%d).csv
```

---

## ⚠️ Manual Fallback (If Injury Fetch Fails)

The injury scraper tries to fetch from NBA APIs automatically. If it fails:

### Option 1: Create CSV Manually

Download from: https://ak-static.cms.nba.com/referee/injury/Injury-Report_2025-11-12_0530PM.pdf

Create: `data/injuries/injuries_2025-11-12.csv`

Format:
```csv
player,status,reason,out_flag,questionable_flag,probable_flag,game_date
LeBron James,Out,Right ankle sprain,1,0,0,2025-11-12
Anthony Davis,Questionable,Left knee soreness,0,1,0,2025-11-12
```

### Option 2: Use Template

```bash
python scripts/utils/fetch_injuries.py --template
```

This creates a template CSV you can fill in manually.

---

## 🎯 Update Today's Games (Optional)

The system auto-fetches games, but if that fails, update `todays_games.txt`:

```bash
# Edit the file
nano todays_games.txt

# Add today's games (one per line or comma-separated)
ORL@NYK,CHI@DET,MIL@CHA,MEM@BOS,CLE@MIA
```

---

## 🔒 Security Notes

- ✅ Repo is now private (your models are protected)
- ✅ Git commits show as Joey <Josephshack@gmail.com>
- ✅ All pushes go to your private branch
- ✅ No credentials stored in scripts

---

## 🚨 Troubleshooting

### Cron jobs not running?

**Check if cron daemon is running:**
```bash
sudo service cron status
```

**If stopped, start it:**
```bash
sudo service cron start
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog
```

### Predictions failed?

**Check the log:**
```bash
tail -50 logs/cron_predict.log
```

**Common issues:**
1. **No injury file** - Create manually or run `./fetch_injuries.sh`
2. **No games found** - Update `todays_games.txt`
3. **Git push failed** - Check internet connection

### Injury fetch failed?

**Manual fetch:**
```bash
./fetch_injuries.sh 2025-11-12
```

**If that fails, create CSV manually** (see "Manual Fallback" above)

---

## 📈 Next Steps

1. ✅ **Installed cron** - Automation is running
2. **Wait for first run** - Check logs at 7 AM and 6 PM
3. **Verify predictions** - Look in `predictions/` folder
4. **Check GitHub** - Commits should appear automatically

---

## 🎉 You're Done!

Your NBA player props model is now **fully automated**.

Just check the `predictions/` folder daily around 6 PM CST for fresh predictions with injury adjustments!

**Questions?** Check logs first, then review this guide.

---

## 📊 System Architecture

```
Daily Flow:

  7:00 AM CST
     ↓
  [Auto-Train Model]
     ↓
  [Update model_cache/trained_models.pkl]
     ↓
  5:45 PM CST
     ↓
  [Fetch NBA Injury Report]
     ↓
  [Save to data/injuries/injuries_YYYY-MM-DD.csv]
     ↓
  6:00 PM CST
     ↓
  [Generate Predictions]
     ↓
  [Create PMF, SGPs, Summary]
     ↓
  [Git Commit & Push]
     ↓
  [Predictions Ready!]
```

---

Built with ❤️ by Joey | Powered by ensemble ML (RF + GB)
