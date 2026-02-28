# DARKO v4 — NBA Player Props Prediction Model

**Version:** 2026-02-28-v9  
**Architecture:** Quantile Regression + Bivariate Normal SGP Engine  
**Target:** Professional-grade NBA player prop prediction for WizardOfOdds.com

---

## Architecture

### Core Principle
**No sportsbook lines exist in training.** Labels are real game outcomes only.

The model predicts a full calibrated distribution for each player/stat using quantile regression (Q10–Q90). At inference time, the CDF is interpolated against today's real sportsbook line to produce P(over) and P(under). This means the model generalizes to any line without retraining.

### Why Quantile Regression
- **Pinball loss** is a proper scoring rule — it is only minimized by the true conditional quantile. You cannot game it.
- Produces a full distribution, not just a point estimate.
- Allows CDF interpolation to any line at inference time.
- Calibration is directly measurable and provable: Q75 predictions should have 75% of actuals fall below them.

### SGP Engine
Joint probabilities use the exact **bivariate normal CDF** (Drezner-Wesolowsky algorithm) with an empirical correlation matrix derived from 120K+ historical NBA player-game observations.

```
P(pts OVER AND ast OVER) = Φ₂(-z₁, -z₂, ρ=0.412)
```

This is materially different from (and more accurate than) multiplying individual probabilities.

---

## Files

| File | Purpose |
|------|---------|
| `train_darko_v4.py` | Quantile regression training pipeline |
| `predict_darko_v4.py` | Singles + SGP prediction engine |
| `grade_darko_v4.py` | Grades predictions against actual outcomes |
| `correlation_engine.py` | Bivariate normal CDF, CDF interpolation, SGP joint probability |
| `feature_engineering.py` | 150+ engineered features (zero leakage) |
| `bdl_client.py` | BallDontLie API client (incremental, price-shopping) |

---

## Outputs (Separate Files)

```
predictions/
  singles_{date}.json    ← individual prop bets (EV > 2.5%)
  sgps_{date}.json       ← 2-leg and 3-leg SGPs (EV > 2.5%)
  paper_trade_log.csv    ← forward paper trade ledger

graded/
  graded_{date}.csv      ← actual outcomes vs predictions
  cumulative_performance.csv
```

---

## Automation Schedule

| Time (EST) | Job |
|------------|-----|
| 6:00 AM | `daily_training.yml` — incremental data fetch + full model retrain |
| 8:00 AM | `daily_predictions.yml` — grade yesterday + generate today's picks |

Daily training uses incremental data fetching. After the initial run, each day fetches only new games (seconds, not minutes).

---

## Safety Rules (Pre-Calibration Period)

Until 500+ forward-tested bets are logged:

- **EV > 2.5%** required to surface any bet
- **Quarter-Kelly (0.25×)** bet sizing
- **Hard cap: 2 units** per single bet
- **Hard cap: 1 unit** per SGP
- **Minimum 15 games** this season for any player/stat
- **SGP legs**: odds between -200 and +200 only
- **No cross-game parlays**
- **2-leg SGP**: avg ρ ≥ 0.10
- **3-leg SGP**: avg ρ ≥ 0.12

---

## Setup

```bash
# 1. Install dependencies
pip install lightgbm scikit-learn pandas numpy requests pyarrow joblib

# 2. Set API key
export BDL_API_KEY=your_key_here

# 3. Initial training (full historical load — 10-30 min first time only)
python train_darko_v4.py

# 4. Generate predictions
python predict_darko_v4.py
```

**GitHub Actions:** Add `BDL_API_KEY` to repo Secrets → Actions for automated daily runs.

---

## Calibration Validation

The model is validated by quantile calibration, not accuracy. For each trained quantile:

```
Q75 prediction is correct if 75% of actual outcomes fall below it.
Q50 prediction is correct if 50% of actual outcomes fall below it (the median).
```

Max calibration error > 5% flags a miscalibrated stat that needs investigation.

---

## Profitability

Profitability claims are made **exclusively** from the forward paper trade ledger (`predictions/paper_trade_log.csv`). No backtesting fiction. The ledger grows daily with every surfaced bet — outcome fields are filled in by `grade_darko_v4.py` after results are in.
