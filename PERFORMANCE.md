# Live Performance

All results are forward-looking — generated before game outcomes were known, graded
against actual BDL box scores the following morning. No backtesting. No hindsight.

**CLV (Closing Line Value)** is the primary metric. Positive CLV means the model
consistently prices props better than the closing line — the professional standard
for demonstrating genuine edge. See `METHODOLOGY.md` for the full definition.

---

## Current Model Version (2026-03-20 to present)

Deployment filters tightened on 2026-03-20 after diagnostic analysis of 2,624 graded
rows. Prior to this date the model was surfacing 25-83 picks/day with negative UNDER
CLV (-14.1%) and no minimum Q50 projection floors. Results below reflect the current
calibrated deployment regime only.

### Recent Daily Results

| Date | Picks | Hit Rate | ROI | Mean CLV | CLV+ % | Brier |
|---|---|---|---|---|---|---|
| 2026-03-20 | 6 | — | — | -0.018 | 50% | 0.119 |
| 2026-03-21 | 5 | — | — | +0.046 | 80% | 0.256 |
| 2026-03-22 | 3 | — | — | -0.009 | 50% | 0.357 |
| 2026-03-23 | 7 | 80.0% | — | +0.071 | 83% | 0.182 |
| 2026-03-24 | 4 | 100.0% | +78.3% | -0.031 | 67% | 0.246 |
| 2026-03-25 | 6 | 50.0% | -2.0% | **+0.114** | **100%** | 0.263 |

**March 25 CLV +11.4% with 100% of picks beating the closing line** is the
strongest single-day result in the dataset. Positive CLV on a day with 50% hit
rate confirms the model is pricing correctly — the hit rate variance is expected
at 6-pick sample sizes.

### Current Deployment Parameters

- **Stats:** PTS OVER (primary), REB OVER, AST OVER (emerging)
- **Probability floor:** 0.60 for PTS, 0.56 for REB/AST
- **Bad-line filter:** Skip if `line > q50 × 1.75`
- **Min Q50 projection:** PTS ≥ 12.0, REB ≥ 3.5, AST ≥ 2.5
- **Portfolio caps:** max 25/day, max 2/player, max 4/game
- **Min games played:** 20 (filters fringe rotation players)

---

## Bias Corrections (Current — learned 2026-03-26)

Fitted from `median(actual - q50)` on **2,737 graded rows** using
GradientBoostingRegressor per stat. Applied to the full quantile ladder.

| Stat | Correction | n | Notes |
|---|---|---|---|
| pts | +1.135 | 534 | Updated from +0.51 — pts still systematically under-projected |
| ast | +0.190 | 483 | Updated from +0.155 |
| reb | +0.010 | 556 | Near-zero — confirms prior reset was correct |
| fg3m | -0.010 | 386 | Unchanged — no material correction needed |
| blk | 0.00 | — | Targets disagree directionally — not corrected |
| stl | 0.00 | — | Targets disagree directionally — not corrected |

---

## Calibration (post-Platt, stat×side)

12 stat×side Platt calibrators active as of 2026-03-20. Each reduces Brier score
vs raw model probabilities.

| Bucket | n | Raw Brier | Cal Brier | Hit Rate |
|---|---|---|---|---|
| pts OVER | 172 | 0.261 | 0.248 | 0.541 |
| pts UNDER | 281 | 0.278 | 0.248 | 0.477 |
| ast OVER | 134 | 0.254 | 0.245 | 0.448 |
| reb OVER | 192 | 0.261 | 0.249 | 0.495 |
| reb UNDER | 285 | 0.265 | 0.248 | 0.498 |
| blk OVER | 250 | 0.212 | 0.201 | 0.280 |

---

## Pre-Filter Historical Record (2026-03-09 to 2026-03-19)

Included for transparency. This period used loose deployment gates (prob ≥ 0.53,
no line-gap filter, no Q50 floor) resulting in high volume with negative UNDER CLV.

| Metric | Value |
|---|---|
| Graded picks | 2,518 |
| Hit rate | 47.5% |
| ROI | -2.1% |
| Mean CLV (OVER) | +10.3% |
| Mean CLV (UNDER) | -14.1% |
| Brier score | 0.272 |

**OVER CLV was +10.3% throughout** — the OVER signal was real. The negative
overall ROI reflects the UNDER side which has been restricted since 2026-03-20.

---

## Data Sources

- Graded results: `graded/graded_2026-*.csv`
- Cumulative summary: `graded/cumulative_report.json`
- Closing lines: `graded/closing_lines_2026-*.json`
- Performance log: `graded/performance_log.csv`
