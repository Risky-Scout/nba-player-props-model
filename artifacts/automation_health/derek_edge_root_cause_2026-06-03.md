# Derek edge root-cause audit — 2026-06-03

- snapshots audited: **1**
- total calculation issues: **2**
- non-actionable rows: **29**

## Headline finding

**Calculation bug found.** See per-row issues below — these are recompute mismatches > 0.5 percentage points.

## deliveries/2026-06-03/derek_game_snapshots/21716134/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 29
- bucket_counts: {'EDGE_LT_10': 9, 'EDGE_10_20': 15, 'EDGE_20_30': 5}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 23, 'PUBLISH_BLOCKER': 2, 'REVIEW_LARGE_EDGE': 4}
- ⚠️ top 20 edges UNDER-skewed share=95%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | reb | UNDER | 11.5 | 0.769 | 0.771 | 0.484 | 0.484 | +0.285 | +0.287 | +0.546 | +0.549 | +0.548 | False | 0.000 | 0.013 | 8.72 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | blk | UNDER | 0.5 | 0.686 | 0.686 | 0.404 | 0.404 | +0.282 | +0.282 | +0.715 | +0.715 | +0.715 | False | 0.000 | 0.686 | 0.43 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | pts | UNDER | 26.5 | 0.737 | 0.739 | 0.487 | 0.487 | +0.250 | +0.252 | +0.452 | +0.457 | +0.455 | False | 0.000 | 0.008 | 21.08 | EDGE_20_30 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Mitchell Robinson | blk | UNDER | 0.5 | 0.682 | 0.682 | 0.456 | 0.456 | +0.226 | +0.226 | +0.399 | +0.399 | +0.399 | False | 0.000 | 0.682 | 0.44 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Stephon Castle | ast | UNDER | 6.5 | 0.677 | 0.678 | 0.468 | 0.468 | +0.209 | +0.210 | +0.401 | +0.404 | +0.403 | False | 0.000 | 0.034 | 5.39 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | stl | UNDER | 1.5 | 0.817 | 0.817 | 0.620 | 0.620 | +0.197 | +0.197 | +0.242 | +0.242 | +0.242 | False | 0.000 | 0.456 | 0.85 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julian Champagnie | reb | UNDER | 5.5 | 0.695 | 0.696 | 0.499 | 0.499 | +0.196 | +0.197 | +0.327 | +0.329 | +0.328 | False | 0.000 | 0.051 | 4.41 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Luke Kornet | reb | UNDER | 2.5 | 0.666 | 0.667 | 0.474 | 0.474 | +0.192 | +0.193 | +0.345 | +0.348 | +0.347 | False | 0.000 | 0.238 | 2.19 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | ast | UNDER | 3.5 | 0.785 | 0.786 | 0.601 | 0.601 | +0.183 | +0.185 | +0.260 | +0.262 | +0.262 | False | 0.000 | 0.135 | 2.38 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | reb | UNDER | 3.5 | 0.760 | 0.761 | 0.579 | 0.579 | +0.181 | +0.183 | +0.274 | +0.275 | +0.275 | False | 0.000 | 0.139 | 2.44 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Stephon Castle | reb | UNDER | 4.5 | 0.608 | 0.609 | 0.443 | 0.443 | +0.165 | +0.166 | +0.326 | +0.328 | +0.328 | False | 0.000 | 0.064 | 4.10 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | pts | UNDER | 16.5 | 0.654 | 0.656 | 0.491 | 0.491 | +0.163 | +0.165 | +0.277 | +0.280 | +0.279 | False | 0.000 | 0.011 | 14.33 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | pts | UNDER | 13.5 | 0.667 | 0.669 | 0.506 | 0.506 | +0.161 | +0.163 | +0.303 | +0.307 | +0.306 | False | 0.000 | 0.024 | 11.31 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | reb | UNDER | 11.5 | 0.647 | 0.649 | 0.502 | 0.502 | +0.144 | +0.146 | +0.294 | +0.297 | +0.296 | False | 0.000 | 0.010 | 10.07 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | reb | UNDER | 8.5 | 0.694 | 0.694 | 0.553 | 0.553 | +0.141 | +0.141 | +0.200 | +0.201 | +0.201 | False | 0.000 | 0.020 | 6.99 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | reb | UNDER | 4.5 | 0.702 | 0.703 | 0.563 | 0.563 | +0.139 | +0.140 | +0.222 | +0.223 | +0.223 | False | 0.000 | 0.065 | 3.58 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | ast | OVER | 3.5 | 0.698 | 0.697 | 0.566 | 0.566 | +0.132 | +0.131 | +0.179 | +0.178 | +0.177 | False | 0.000 | 0.054 | 5.11 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | ast | UNDER | 2.5 | 0.590 | 0.591 | 0.459 | 0.459 | +0.131 | +0.131 | +0.268 | +0.270 | +0.269 | False | 0.000 | 0.238 | 2.18 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | blk | UNDER | 0.5 | 0.695 | 0.695 | 0.566 | 0.566 | +0.129 | +0.129 | +0.158 | +0.158 | +0.158 | False | 0.000 | 0.695 | 0.37 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | ast | UNDER | 5.5 | 0.566 | 0.567 | 0.458 | 0.458 | +0.108 | +0.109 | +0.190 | +0.191 | +0.191 | False | 0.000 | 0.042 | 4.99 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Mikal Bridges | blk | UNDER | 0.5 | 0.691 | 0.691 | 0.597 | 0.597 | +0.094 | +0.094 | +0.095 | +0.095 | +0.095 | False | 0.000 | 0.691 | 0.39 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Brunson | pts | UNDER | 25.5 | 0.583 | 0.586 | 0.495 | 0.495 | +0.088 | +0.091 | +0.166 | +0.172 | +0.171 | False | 0.000 | 0.006 | 23.84 | EDGE_LT_10 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| De'Aaron Fox | reb | UNDER | 3.5 | 0.597 | 0.598 | 0.509 | 0.509 | +0.088 | +0.089 | +0.140 | +0.141 | +0.141 | False | 0.000 | 0.097 | 3.21 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julian Champagnie | pts | UNDER | 10.5 | 0.586 | 0.588 | 0.506 | 0.506 | +0.080 | +0.082 | +0.145 | +0.148 | +0.147 | False | 0.000 | 0.024 | 9.99 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | ast | UNDER | 2.5 | 0.643 | 0.644 | 0.574 | 0.574 | +0.069 | +0.070 | +0.077 | +0.079 | +0.079 | False | 0.000 | 0.210 | 2.01 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

