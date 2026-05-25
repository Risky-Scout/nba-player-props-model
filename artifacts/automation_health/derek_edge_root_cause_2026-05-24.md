# Derek edge root-cause audit — 2026-05-24

- snapshots audited: **1**
- total calculation issues: **1695**
- non-actionable rows: **0**

## Headline finding

**Calculation bug found.** See per-row issues below — these are recompute mismatches > 0.5 percentage points.

## deliveries/2026-05-24/derek_game_snapshots/21713531/close_lock

- snapshot_type: `close_lock`  lineup_confirmed: **False**
- row_count: 0
- bucket_counts: {}
- publish_status_counts: {}

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

