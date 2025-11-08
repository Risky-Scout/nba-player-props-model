# NBA Player Props Prediction Model

**Advanced machine learning system for NBA player prop betting predictions**

Built with ensemble models (Random Forest + Gradient Boosting), injury-adjusted usage modeling, and correlation-aware SGP optimization.

---

## 🎯 Quick Start

### Option 1: Automated Daily Predictions
```bash
./daily_update.sh
```
Runs complete pipeline: data collection → training → predictions

### Option 2: Manual Workflow (For Today's Games)

**Step 1: Create today's injury report**
```bash
# Download from: https://ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_0530PM.pdf
# Create: data/injuries/injuries_YYYY-MM-DD.csv
```

**Step 2: Run predictions**
```bash
python scripts/prediction/run_daily_predictions.py \
  --date 2025-11-08 \
  --games "DAL@WAS,TOR@PHI,CHI@CLE" \
  --injuries data/injuries/injuries_2025-11-08.csv
```

**Step 3: Generate client report**
```bash
python scripts/reports/generate_risky_scout_report.py --date 2025-11-08
```

**Step 4: View today's picks**
```bash
cat predictions/RISKY_SCOUT_FAVORITES_2025-11-08.txt
```

---

## 📁 Repository Structure

```
nba-player-props-model/
│
├── scripts/                           # All Python scripts (organized)
│   ├── data_collection/              # Data gathering scripts
│   │   ├── collect_historical_training_data.py
│   │   ├── collect_current_season_data.py
│   │   ├── collect_2025_26_test_data.py
│   │   ├── collect_nba_bdl.py
│   │   └── process_real_data.py
│   ├── training/                     # Model training scripts
│   │   ├── train_elite_model.py
│   │   └── train_latest_model.py
│   ├── prediction/                   # Prediction generation
│   │   ├── run_daily_predictions.py
│   │   ├── generate_final_predictions.py
│   │   ├── generate_tonight_predictions.py
│   │   └── elite_prediction_system.py
│   ├── reports/                      # Client reporting
│   │   ├── generate_risky_scout_report.py
│   │   └── track_accuracy.py
│   └── utils/                        # Utility scripts
│       ├── correlation_matrix_sgp.py
│       ├── meta_ensemble_model.py
│       ├── generate_sample_nba_data.py
│       └── demonstration_script.py
│
├── docs/                              # Documentation
│   ├── DAILY_WORKFLOW.md             # Step-by-step daily instructions
│   ├── TECHNICAL_REPORT.md           # PhD-level technical documentation
│   ├── QUICK_START.md                # Quick start guide
│   ├── BACKTEST_SUMMARY.md           # Backtesting results
│   ├── MODEL_VALIDATION_REPORT.md    # Validation metrics
│   ├── TECHNICAL_DEEP_DIVE.md        # Deep technical analysis
│   ├── DAILY_OPERATIONS_GUIDE.md     # Operations manual
│   └── TRADER_QUESTIONS.md           # FAQ for traders
│
├── data/                              # Training and reference data
│   ├── processed_training_data.csv   # 9,573 NBA games
│   ├── team_ratings.csv              # Real defensive ratings
│   ├── nba_training_data_real.csv    # Historical training data
│   └── injuries/                     # Daily injury reports
│       └── injuries_YYYY-MM-DD.csv
│
├── model_cache/                       # Trained models
│   └── trained_models.pkl            # Serialized RF + GB models
│
├── predictions/                       # Daily predictions output
│   ├── tonight_INJURY_ADJUSTED_*.csv # Full technical predictions
│   ├── RISKY_SCOUT_FAVORITES_*.txt   # Client report
│   ├── top_props_*.csv               # Top individual props
│   ├── sgp_2leg_*.csv                # 2-leg SGPs
│   └── sgp_3leg_*.csv                # 3-leg SGPs
│
├── accuracy_tracking/                 # Performance tracking
│   ├── accuracy_log.csv              # Master accuracy log
│   ├── daily_results/                # Per-day results
│   │   └── results_YYYY-MM-DD.csv
│   └── ACCURACY_SUMMARY.md           # Public performance report
│
├── logs/                              # Execution logs
│   ├── training.log
│   ├── prediction_log.txt
│   ├── data_collection.log
│   └── *.log
│
├── results/                           # Analysis outputs
│
├── daily_update.sh                    # Main automation script
├── run_elite_predictions.sh           # Elite predictions runner
├── requirements.txt                   # Python dependencies
└── LICENSE
```

---

## 🚀 Features

### Model Architecture
- **Ensemble Learning:** Random Forest (0.6) + Gradient Boosting (0.4)
- **Training Data:** 9,573 real NBA games (Oct 2023 - Nov 2025)
- **Feature Engineering:** 33 features including rolling averages, opponent metrics, injury adjustments
- **Real Defensive Ratings:** 103.18 to 117.91 (not placeholders)

### Performance Metrics
- **Points:** MAE 2.31 pts (71.6% within ±3 points)
- **Rebounds:** MAE 1.05 reb (90.4% within ±3 rebounds)
- **Assists:** MAE 0.80 ast (95.1% within ±3 assists)

### Injury Integration
- Automatic OUT player removal
- QUESTIONABLE: -25% minutes adjustment
- PROBABLE: -7% minutes adjustment
- Usage boosts: +25% (2+ stars out), +15% (1 star out)

### SGP Optimization
- Correlation-adjusted probabilities
- Real correlation matrix (PTS-REB: 0.647, PTS-AST: 0.426)
- 2-leg and 3-leg SGPs with reasoning

### Client Reports
- Bankroll management tiers (Conservative/Moderate/Value)
- Star ratings for confidence levels
- Injury alerts and opportunity highlights
- Professional formatting

---

## 📊 Daily Workflow

**Time Commitment:** 15-20 minutes/day

1. **Get injury report** (5:30 PM ET)
2. **Run predictions** (2 min)
3. **Generate client report** (1 min)
4. **Review and send** (5 min)
5. **Next day: Track accuracy** (5 min)
6. **Commit to GitHub** (2 min)

**Full instructions:** See `docs/DAILY_WORKFLOW.md`

---

## 📈 Accuracy Tracking

Track model performance and build public credibility:

```bash
# After games complete
python scripts/reports/track_accuracy.py --date 2025-11-08 --enter-results

# View summary
python scripts/reports/track_accuracy.py --summary
```

Public record: `accuracy_tracking/ACCURACY_SUMMARY.md`

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `docs/DAILY_WORKFLOW.md` | Step-by-step daily instructions |
| `docs/TECHNICAL_REPORT.md` | PhD-level technical documentation (35 pages) |
| `docs/QUICK_START.md` | Get started in 5 minutes |
| `docs/BACKTEST_SUMMARY.md` | Historical backtesting results |
| `docs/MODEL_VALIDATION_REPORT.md` | Validation metrics and analysis |

---

## 🔧 Installation

```bash
# Clone repository
git clone https://github.com/Risky-Scout/nba-player-props-model.git
cd nba-player-props-model

# Install dependencies
pip install -r requirements.txt

# Verify setup
python scripts/prediction/run_daily_predictions.py --help
```

---

## 💡 Use Cases

### For Bettors
- Daily prop recommendations with probability-based confidence
- Bankroll management guidance
- Injury-adjusted opportunities
- Correlated SGP combinations

### For Employers/Portfolio
- Production-ready ML system
- Real-time data pipeline
- Comprehensive technical documentation
- Public accuracy tracking (transparency)

### For Interviews
- PhD-level technical report to study
- Complete feature engineering methodology
- Ensemble model architecture with empirical validation
- Real-world deployment and monitoring

---

## ⚖️ Disclaimer

This model is for **informational and educational purposes only**.

- Past performance does not guarantee future results
- All betting involves risk
- Model predictions are probabilistic, not guaranteed
- User responsible for compliance with local laws
- No warranties or guarantees of profitability

**Please gamble responsibly.**

---

## 📝 License

See `LICENSE` file for details.

---

## 🤝 Contributing

This is a personal project. Not accepting contributions at this time.

---

## 📧 Contact

**The Risky Scout** - Advanced NBA Analytics

Built with real data, real math, and real transparency.

---

© 2025 The Risky Scout. All rights reserved.
