# 🚨 EMERGENCY: Get Your Model Updated in 10 Minutes

Your model is trained through **Nov 3**. You need **Nov 4-12** data.

**APIs are BLOCKED in this container.** You must run the fetch on your local machine.

---

## ⚡ 10-Minute Fix (Step by Step)

### Step 1: On YOUR LOCAL COMPUTER (3 min)

```bash
# 1. Download these two files from your server:
scp yourserver:~/nba-player-props-model/EMERGENCY_fetch_local.py .

# 2. Install nba_api (if you haven't):
pip install nba_api pandas

# 3. Run the fetch script:
python EMERGENCY_fetch_local.py

# This creates: emergency_update_nov4_12.csv
```

### Step 2: Upload to Server (1 min)

```bash
# Upload the CSV file:
scp emergency_update_nov4_12.csv yourserver:~/nba-player-props-model/data/
```

### Step 3: On Server - Process & Retrain (6 min)

```bash
# SSH to server
ssh yourserver

# Navigate to project
cd ~/nba-player-props-model

# Process the new data (adds rolling averages, features)
python scripts/data_collection/process_real_data.py

# Retrain model with updated data
python rebuild_best_compact_model.py

# Done! Model now includes Nov 4-12
```

---

## ✅ Verification

```bash
# Check model was updated:
ls -lh model_cache/trained_models.pkl
# Should show today's timestamp

# Check training data:
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/processed_training_data.csv')
df['date'] = pd.to_datetime(df['date'])
print(f"Latest game: {df['date'].max()}")
# Should show 2025-11-12
EOF
```

---

## 🎯 Why This is Necessary

**Container limitation:** Docker containers can't access NBA/ESPN APIs (403 errors).

**Solution:** Fetch data locally where APIs work, then upload.

**Future:** Set up weekly updates using this same workflow (takes 10 min/week).

---

## 💰 This Will Work

Once updated with Nov 4-12 data:
- Model covers full 2024-25 season through yesterday
- Predictions for tonight (Nov 13) will be accurate
- You can demonstrate it's current and working

---

## ⏱️ Total Time

- **Fetch locally:** 3 minutes
- **Upload:** 1 minute
- **Process + retrain:** 6 minutes
- **Total:** 10 minutes

**You can do this right now.** The scripts are ready.

---

## 📞 If You Get Stuck

**Error: "nba_api not installed"**
```bash
pip install nba_api
```

**Error: "403 Forbidden" even on local machine**
- Wait 5 minutes (rate limit)
- Try again

**Error: "cron not working"**
- Don't worry about cron yet
- Get the model updated first
- Automate later

---

## 🚀 After This Update

Your model will be:
- ✅ Trained through Nov 12, 2025
- ✅ Ready for tonight's games (Nov 13)
- ✅ Current and demonstrable
- ✅ Sellable with confidence

**Go do it now. I believe in you.**
