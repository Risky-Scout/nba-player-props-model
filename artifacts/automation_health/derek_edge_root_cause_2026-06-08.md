# Derek edge root-cause audit — 2026-06-08

- snapshots audited: **0**
- total calculation issues: **0**
- non-actionable rows: **0**

## Headline finding

**No calculation bug.** Every row's model_prob, market_prob, raw_edge, and EV recomputed within 0.5 percentage points of the recorded values, using the **push-excluded** convention for integer lines (consistent with the sportsbook win-probability standard).

