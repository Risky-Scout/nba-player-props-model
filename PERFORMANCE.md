# Live Performance

All results are forward-looking — generated before game outcomes were known, graded against actual BDL box scores the following morning. No backtesting. No hindsight.

CLV (Closing Line Value) is the primary metric. See [METHODOLOGY.md](METHODOLOGY.md) for the full definition and why it matters more than win rate.

---

## Season-to-Date Summary

**Grading period:** 2026-03-09 — present  
**Graded picks:** 1,026  
**Data source:** `graded/performance_log.csv` and `graded/cumulative_report.json`

| Metric | Value |
|---|---|
| Graded Picks | 1,026 |
| Hit Rate | 57.1% |
| ROI | +9.7% |
| Mean CLV (OVER picks) | **+10.3%** |
| Mean CLV (UNDER picks) | **−14.1%** |
| Brier Score | 0.255 (post-Platt calibration) |
| Sharpe Ratio | 1.56 |
| Max Drawdown | 6.47 units |

---

## By Stat

| Stat | N | Hit Rate | ROI | Mean CLV |
|---|---|---|---|---|
| Points | ~200 | 61.0% | +16.9% | −3.4% |
| Rebounds | ~225 | 60.9% | +17.1% | −11.2% |
| Assists | ~181 | 56.8% | +8.2% | −2.8% |
| 3-Pointers Made | ~167 | 52.9% | −2.3% | −11.5% |
| Steals | ~127 | 57.7% | +27.2% | −8.2% |
| Blocks | ~127 | 50.0% | −14.2% | −6.7% |

---

## By Side

| Side | N | Hit Rate | ROI | Mean CLV |
|---|---|---|---|---|
| OVER | ~346 | 56.9% | +16.8% | **+10.3%** |
| UNDER | ~680 | 57.2% | +7.0% | **−14.1%** |

---

## CLV Methodology — v3 Upgrade (2026-03-13)

True CLV is now computed against the post-injury-report closing line snapshot (captured at 6 PM ET via `snapshot_closing_lines.py`):

```
True CLV  = model_prob − closing_fair_prob
Proxy CLV = model_prob − market_prob  (pick-time 8 AM market price)
```

When a closing snapshot exists for the grading date, `clv` uses the true figure. For dates before 2026-03-13, `clv` equals `clv_proxy` (best available estimate). As the snapshot database grows, the true CLV figures will become the primary performance signal.

---

## Calibration Diagnostic (1,026 picks)

Platt scaling calibration deployed 2026-03-12 to correct systematic UNDER overconfidence:

| Bucket | Raw Prob | Hit Rate | Overconfidence |
|---|---|---|---|
| 55%–60% | 0.571 | 0.569 | ±0.002 — accurate |
| 60%–65% | 0.624 | 0.589 | 0.035 — acceptable |
| 65%–70% | 0.672 | 0.485 | **0.187 — severe** |
| 70%–75% | 0.724 | 0.522 | **0.202 — severe** |

Post-calibration Brier improvement: OVER −0.0119 | UNDER −0.0128. ECE: OVER 11.2% → 3.8% | UNDER 11.8% → 2.7%.

---

## Feature Group Importance (current models)

From `python3 analyze_features.py --format both`:

| Feature Group | % Importance |
|---|---|
| Minutes history | 36.96% |
| Rolling player stats | 32.20% |
| 3PM-specific | 9.50% |
| Sparse stat (STL/BLK blended rates) | 7.80% |
| Metadata | 6.64% |
| Schedule | 4.53% |
| Advanced stats (BDL v2) | 1.49% |
| Interactions | 0.88% |
| **Market odds (implied totals, spread)** | **0.00% ← zero until retrain** |
| **Vacancy/injury features** | **0.00% ← zero until retrain** |

Market and vacancy features carry zero importance because BDL odds only cover 2025-26 and injury snapshots only began accumulating in March 2026. The next retrain will correct this.

---

## Raw Data

- `graded/performance_log.csv` — all graded picks (model_prob, result, clv, clv_proxy)
- `graded/cumulative_report.json` — aggregate stats by stat, side, rolling window
- `model_cache/feature_analysis_report.json` — full feature importance report
- `model_cache/calibration_meta.json` — Platt calibration metadata
