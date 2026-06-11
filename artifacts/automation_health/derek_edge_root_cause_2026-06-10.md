# Derek edge root-cause audit — 2026-06-10

- snapshots audited: **1**
- total calculation issues: **2**
- non-actionable rows: **35**

## Headline finding

**Calculation bug found.** See per-row issues below — these are recompute mismatches > 0.5 percentage points.

## deliveries/2026-06-10/derek_game_snapshots/21716137/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 35
- bucket_counts: {'EDGE_LT_10': 16, 'EDGE_10_20': 15, 'EDGE_20_30': 4}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 30, 'REVIEW_LARGE_EDGE': 3, 'PUBLISH_BLOCKER': 2}
- ⚠️ top 20 edges UNDER-skewed share=85%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Keldon Johnson | fg3m | OVER | 0.5 | 0.794 | 0.794 | 0.497 | 0.497 | +0.298 | +0.298 | +0.536 | +0.536 | +0.536 | False | 0.000 | 0.206 | 1.46 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | reb | UNDER | 11.5 | 0.784 | 0.785 | 0.534 | 0.534 | +0.251 | +0.251 | +0.416 | +0.419 | +0.418 | False | 0.000 | 0.013 | 8.60 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Miles McBride | fg3m | OVER | 0.5 | 0.835 | 0.835 | 0.608 | 0.608 | +0.227 | +0.227 | +0.303 | +0.303 | +0.303 | False | 0.000 | 0.166 | 1.55 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | pts | UNDER | 27.5 | 0.726 | 0.729 | 0.514 | 0.514 | +0.215 | +0.215 | +0.357 | +0.363 | +0.362 | False | 0.000 | 0.005 | 22.23 | EDGE_20_30 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Stephon Castle | ast | UNDER | 6.5 | 0.712 | 0.713 | 0.516 | 0.516 | +0.197 | +0.197 | +0.370 | +0.372 | +0.372 | False | 0.000 | 0.033 | 5.14 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | reb | UNDER | 5.5 | 0.626 | 0.628 | 0.437 | 0.437 | +0.191 | +0.191 | +0.347 | +0.349 | +0.349 | False | 0.000 | 0.040 | 5.00 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | pts | UNDER | 17.5 | 0.688 | 0.691 | 0.524 | 0.524 | +0.167 | +0.167 | +0.252 | +0.257 | +0.256 | False | 0.000 | 0.013 | 14.41 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Brunson | fg3m | UNDER | 2.5 | 0.722 | 0.722 | 0.560 | 0.560 | +0.162 | +0.162 | +0.249 | +0.249 | +0.249 | False | 0.000 | 0.160 | 1.80 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | reb | UNDER | 8.5 | 0.649 | 0.651 | 0.496 | 0.496 | +0.155 | +0.155 | +0.256 | +0.259 | +0.258 | False | 0.000 | 0.018 | 7.48 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | pts | UNDER | 12.5 | 0.660 | 0.661 | 0.511 | 0.511 | +0.150 | +0.150 | +0.249 | +0.251 | +0.251 | False | 0.000 | 0.018 | 10.76 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | reb | OVER | 3.5 | 0.588 | 0.587 | 0.446 | 0.446 | +0.142 | +0.142 | +0.317 | +0.316 | +0.315 | False | 0.000 | 0.067 | 4.16 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Mikal Bridges | fg3m | UNDER | 1.5 | 0.694 | 0.694 | 0.554 | 0.554 | +0.140 | +0.140 | +0.190 | +0.190 | +0.190 | False | 0.000 | 0.303 | 1.07 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Mitchell Robinson | stl | UNDER | 0.5 | 0.728 | 0.728 | 0.589 | 0.589 | +0.139 | +0.139 | +0.192 | +0.192 | +0.192 | False | 0.000 | 0.728 | 0.40 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | stl | UNDER | 0.5 | 0.774 | 0.774 | 0.637 | 0.637 | +0.137 | +0.137 | +0.182 | +0.182 | +0.182 | False | 0.000 | 0.774 | 0.31 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | ast | UNDER | 3.5 | 0.704 | 0.704 | 0.571 | 0.571 | +0.133 | +0.133 | +0.185 | +0.186 | +0.186 | False | 0.000 | 0.147 | 2.61 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| OG Anunoby | stl | UNDER | 1.5 | 0.747 | 0.747 | 0.615 | 0.615 | +0.132 | +0.132 | +0.192 | +0.192 | +0.192 | False | 0.000 | 0.428 | 0.99 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | ast | UNDER | 3.5 | 0.702 | 0.703 | 0.575 | 0.574 | +0.128 | +0.128 | +0.170 | +0.171 | +0.171 | False | 0.000 | 0.122 | 2.61 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | reb | UNDER | 2.5 | 0.583 | 0.583 | 0.456 | 0.456 | +0.128 | +0.128 | +0.252 | +0.255 | +0.254 | False | 0.000 | 0.177 | 2.43 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | pts | UNDER | 13.5 | 0.601 | 0.603 | 0.497 | 0.497 | +0.106 | +0.106 | +0.141 | +0.146 | +0.145 | False | 0.000 | 0.016 | 12.11 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | stl | UNDER | 1.5 | 0.673 | 0.673 | 0.575 | 0.575 | +0.099 | +0.099 | +0.117 | +0.117 | +0.117 | False | 0.000 | 0.446 | 1.02 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| OG Anunoby | pts | UNDER | 16.5 | 0.600 | 0.602 | 0.507 | 0.507 | +0.096 | +0.096 | +0.146 | +0.150 | +0.150 | False | 0.000 | 0.010 | 15.11 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | ast | UNDER | 4.5 | 0.572 | 0.573 | 0.478 | 0.478 | +0.094 | +0.094 | +0.143 | +0.145 | +0.145 | False | 0.000 | 0.061 | 4.16 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Brunson | pts | UNDER | 27.5 | 0.598 | 0.601 | 0.508 | 0.508 | +0.093 | +0.093 | +0.132 | +0.137 | +0.136 | False | 0.000 | 0.004 | 24.92 | EDGE_LT_10 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| De'Aaron Fox | ast | UNDER | 6.5 | 0.669 | 0.670 | 0.579 | 0.579 | +0.091 | +0.091 | +0.101 | +0.102 | +0.102 | False | 0.000 | 0.035 | 5.25 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Mitchell Robinson | blk | UNDER | 0.5 | 0.622 | 0.622 | 0.533 | 0.533 | +0.089 | +0.089 | +0.149 | +0.149 | +0.149 | False | 0.000 | 0.622 | 0.55 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

