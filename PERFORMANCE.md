# Live Performance

All results are forward-looking — generated before game outcomes were known, graded against actual BDL box scores the following morning. No backtesting. No hindsight.

CLV (Closing Line Value) is the primary metric. See [METHODOLOGY.md](METHODOLOGY.md) for the full definition and why it matters more than win rate.

---

## Season-to-Date Summary

**Grading period:** 2026-03-09 — present
**Graded picks:** 210
**Data source:** `graded/performance_log.csv` and `graded/cumulative_report.json`

| Metric | Value |
|---|---|
| Graded Picks | 210 |
| Hit Rate | 57.1% |
| ROI | +9.7% |
| Mean CLV | −7.3% |
| Brier Score | 0.306 |
| Sharpe Ratio | 1.56 |
| Max Drawdown | 6.47 units |

---

## By Stat

| Stat | N | Hit Rate | ROI | Mean CLV | Sharpe |
|---|---|---|---|---|---|
| Points | 41 | 61.0% | +16.9% | −3.4% | 2.86 |
| Rebounds | 46 | 60.9% | +17.1% | −11.2% | 2.85 |
| Assists | 37 | 56.8% | +8.2% | −2.8% | 1.34 |
| 3-Pointers Made | 34 | 52.9% | −2.3% | −11.5% | −0.38 |
| Steals | 26 | 57.7% | +27.2% | −8.2% | 3.80 |
| Blocks | 26 | 50.0% | −14.2% | −6.7% | −2.26 |

---

## By Side

| Side | N | Hit Rate | ROI | Mean CLV | Sharpe |
|---|---|---|---|---|---|
| OVER | 58 | 56.9% | +16.8% | **+10.3%** | 2.51 |
| UNDER | 152 | 57.2% | +7.0% | **−14.1%** | 1.16 |

---

## Calibration Issue — UNDER Bias

The OVER / UNDER CLV split reveals a systematic problem: OVER picks are beating the closing line (+10.3% mean CLV) while UNDER picks are losing to it (−14.1% mean CLV).

This is consistent with retail OVER volume in player prop markets. After the model issues UNDER picks, public money steams lines toward the OVER, moving the closing line against the model's position. The model is finding genuine statistical UNDER value (57% hit rate, +7% ROI) but is fighting against retail-driven post-pick line movement.

**Root cause:** The model has too many high-confidence UNDER picks. The isotonic calibration pipeline (`calibrate_models.py`) is designed to correct this as graded data accumulates — it will learn to down-weight UNDER probabilities in regimes where the market consistently disagrees. This requires approximately 50 graded UNDER picks per stat (~4–6 weeks of data) before calibrators are reliable enough to deploy.

**Interim signal:** OVER picks with positive CLV (+10.3%) represent the cleanest edge the model has identified in the current dataset. The model is systematically finding OVER positions that the market subsequently confirms.

---

## Sample Size Warning

210 picks across 1 graded day does not constitute statistical significance for any of these metrics. A 57% hit rate on −110 lines has a standard error of approximately ±3.4% over 210 observations. The CLV directional signal (OVERs positive, UNDERs negative) is more meaningful than the absolute values at this sample size.

Full statistical significance on CLV requires approximately 500–1,000 graded picks with at least one full season of data to control for within-season distribution shift.

---

## Raw Data

Full graded results with per-pick CLV, quantile distributions, and model probabilities are in:

- `graded/performance_log.csv` — all graded picks
- `graded/cumulative_report.json` — aggregate statistics by stat, side, and rolling window
- `graded/graded_{date}.csv` — per-date detail files
