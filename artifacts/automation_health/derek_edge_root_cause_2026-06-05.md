# Derek edge root-cause audit — 2026-06-05

- snapshots audited: **2**
- total calculation issues: **8**
- non-actionable rows: **52**

## Headline finding

**Calculation bug found.** See per-row issues below — these are recompute mismatches > 0.5 percentage points.

## deliveries/2026-06-05/derek_game_snapshots/21716135/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 43
- bucket_counts: {'EDGE_LT_10': 17, 'EDGE_10_20': 17, 'EDGE_20_30': 9}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 34, 'REVIEW_LARGE_EDGE': 8, 'PUBLISH_BLOCKER': 1}
- ⚠️ top 20 edges UNDER-skewed share=90%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | reb | UNDER | 11.5 | 0.759 | 0.760 | 0.472 | 0.472 | +0.288 | +0.288 | +0.526 | +0.528 | +0.527 | False | 0.000 | 0.012 | 8.89 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | blk | UNDER | 0.5 | 0.700 | 0.700 | 0.416 | 0.416 | +0.283 | +0.283 | +0.644 | +0.644 | +0.644 | False | 0.000 | 0.700 | 0.45 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | pts | UNDER | 27.5 | 0.772 | 0.775 | 0.514 | 0.514 | +0.261 | +0.261 | +0.474 | +0.480 | +0.478 | False | 0.000 | 0.008 | 20.91 | EDGE_20_30 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Stephon Castle | ast | UNDER | 6.5 | 0.714 | 0.716 | 0.488 | 0.488 | +0.228 | +0.228 | +0.401 | +0.404 | +0.403 | False | 0.000 | 0.038 | 5.16 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | fg3m | OVER | 0.5 | 0.785 | 0.785 | 0.557 | 0.557 | +0.227 | +0.227 | +0.371 | +0.371 | +0.371 | False | 0.000 | 0.215 | 1.45 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Mitchell Robinson | blk | UNDER | 0.5 | 0.734 | 0.734 | 0.510 | 0.510 | +0.224 | +0.224 | +0.401 | +0.401 | +0.401 | False | 0.000 | 0.734 | 0.36 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | stl | UNDER | 0.5 | 0.672 | 0.672 | 0.448 | 0.448 | +0.224 | +0.224 | +0.444 | +0.444 | +0.444 | False | 0.000 | 0.672 | 0.56 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | ast | UNDER | 3.5 | 0.807 | 0.808 | 0.595 | 0.595 | +0.213 | +0.213 | +0.308 | +0.310 | +0.310 | False | 0.000 | 0.162 | 2.17 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | stl | UNDER | 1.5 | 0.850 | 0.850 | 0.648 | 0.648 | +0.202 | +0.202 | +0.286 | +0.286 | +0.286 | False | 0.000 | 0.595 | 0.63 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Dylan Harper | ast | UNDER | 3.5 | 0.774 | 0.775 | 0.586 | 0.586 | +0.189 | +0.189 | +0.290 | +0.292 | +0.292 | False | 0.000 | 0.182 | 2.21 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| OG Anunoby | blk | UNDER | 0.5 | 0.654 | 0.654 | 0.475 | 0.475 | +0.179 | +0.179 | +0.335 | +0.335 | +0.335 | False | 0.000 | 0.654 | 0.49 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| OG Anunoby | fg3m | UNDER | 1.5 | 0.538 | 0.538 | 0.368 | 0.368 | +0.170 | +0.170 | +0.425 | +0.426 | +0.426 | False | 0.000 | 0.164 | 1.57 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julian Champagnie | pts | UNDER | 10.5 | 0.648 | 0.650 | 0.481 | 0.481 | +0.169 | +0.169 | +0.309 | +0.313 | +0.312 | False | 0.000 | 0.025 | 9.47 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | ast | UNDER | 5.5 | 0.631 | 0.632 | 0.462 | 0.462 | +0.169 | +0.169 | +0.324 | +0.326 | +0.326 | False | 0.000 | 0.043 | 4.68 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Landry Shamet | fg3m | UNDER | 1.5 | 0.679 | 0.679 | 0.514 | 0.514 | +0.165 | +0.165 | +0.297 | +0.297 | +0.297 | False | 0.000 | 0.227 | 1.18 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | pts | UNDER | 12.5 | 0.634 | 0.635 | 0.477 | 0.477 | +0.158 | +0.158 | +0.299 | +0.303 | +0.302 | False | 0.000 | 0.024 | 11.00 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Brunson | stl | OVER | 0.5 | 0.713 | 0.713 | 0.554 | 0.554 | +0.158 | +0.158 | +0.248 | +0.249 | +0.249 | False | 0.000 | 0.287 | 1.20 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | reb | UNDER | 8.5 | 0.625 | 0.626 | 0.470 | 0.470 | +0.156 | +0.156 | +0.281 | +0.283 | +0.282 | False | 0.000 | 0.017 | 7.59 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julian Champagnie | reb | UNDER | 5.5 | 0.606 | 0.607 | 0.464 | 0.464 | +0.143 | +0.143 | +0.259 | +0.262 | +0.262 | False | 0.000 | 0.038 | 5.07 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | pts | UNDER | 12.5 | 0.659 | 0.661 | 0.519 | 0.519 | +0.143 | +0.143 | +0.222 | +0.227 | +0.226 | False | 0.000 | 0.024 | 10.47 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | pts | UNDER | 16.5 | 0.637 | 0.639 | 0.497 | 0.497 | +0.142 | +0.142 | +0.243 | +0.247 | +0.246 | False | 0.000 | 0.013 | 14.55 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | reb | UNDER | 2.5 | 0.616 | 0.617 | 0.493 | 0.493 | +0.125 | +0.125 | +0.187 | +0.189 | +0.189 | False | 0.000 | 0.197 | 2.26 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | ast | UNDER | 4.5 | 0.574 | 0.575 | 0.459 | 0.459 | +0.116 | +0.116 | +0.204 | +0.207 | +0.206 | False | 0.000 | 0.058 | 3.99 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | blk | UNDER | 0.5 | 0.746 | 0.746 | 0.635 | 0.635 | +0.111 | +0.111 | +0.147 | +0.148 | +0.148 | False | 0.000 | 0.746 | 0.30 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | ast | UNDER | 2.5 | 0.652 | 0.653 | 0.543 | 0.543 | +0.109 | +0.109 | +0.173 | +0.175 | +0.174 | False | 0.000 | 0.216 | 1.98 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

## deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25

- snapshot_type: `t_minus_25`  lineup_confirmed: **False**
- row_count: 35
- bucket_counts: {'EDGE_LT_10': 13, 'EDGE_10_20': 16, 'EDGE_20_30': 6}
- publish_status_counts: {'ACTIONABLE_REVIEWED': 26, 'REVIEW_LARGE_EDGE': 5, 'PUBLISH_BLOCKER': 4}
- ⚠️ top 20 edges UNDER-skewed share=95%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | reb | UNDER | 11.5 | 0.733 | 0.735 | 0.451 | 0.451 | +0.282 | +0.284 | +0.554 | +0.557 | +0.556 | False | 0.000 | 0.013 | 8.95 | EDGE_20_30 | REVIEW_LARGE_EDGE | line_vs_median_gap | yes |
| Victor Wembanyama | pts | UNDER | 27.5 | 0.760 | 0.764 | 0.509 | 0.509 | +0.251 | +0.255 | +0.464 | +0.472 | +0.469 | False | 0.000 | 0.006 | 21.06 | EDGE_20_30 | PUBLISH_BLOCKER | line_vs_median_gap | **NO** |
| Stephon Castle | ast | UNDER | 6.5 | 0.729 | 0.730 | 0.493 | 0.493 | +0.236 | +0.237 | +0.430 | +0.433 | +0.432 | False | 0.000 | 0.040 | 4.93 | EDGE_20_30 | REVIEW_LARGE_EDGE | line_vs_median_gap | yes |
| Dylan Harper | ast | UNDER | 3.5 | 0.801 | 0.803 | 0.588 | 0.588 | +0.213 | +0.215 | +0.336 | +0.338 | +0.337 | False | 0.000 | 0.217 | 2.10 | EDGE_20_30 | REVIEW_LARGE_EDGE | line_vs_median_gap | yes |
| Keldon Johnson | fg3m | OVER | 0.5 | 0.767 | 0.767 | 0.554 | 0.554 | +0.213 | +0.213 | +0.357 | +0.357 | +0.357 | False | 0.000 | 0.233 | 1.40 | EDGE_20_30 | REVIEW_LARGE_EDGE | low_line_discrete_stat | yes |
| Victor Wembanyama | ast | UNDER | 3.5 | 0.809 | 0.810 | 0.597 | 0.597 | +0.212 | +0.213 | +0.302 | +0.304 | +0.303 | False | 0.000 | 0.191 | 2.08 | EDGE_20_30 | REVIEW_LARGE_EDGE | line_vs_median_gap | yes |
| De'Aaron Fox | ast | UNDER | 5.5 | 0.649 | 0.650 | 0.462 | 0.462 | +0.186 | +0.187 | +0.363 | +0.365 | +0.364 | False | 0.000 | 0.044 | 4.64 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Josh Hart | ast | UNDER | 4.5 | 0.639 | 0.640 | 0.466 | 0.466 | +0.173 | +0.175 | +0.310 | +0.313 | +0.312 | False | 0.000 | 0.066 | 3.82 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Josh Hart | reb | UNDER | 8.5 | 0.623 | 0.625 | 0.459 | 0.459 | +0.164 | +0.165 | +0.340 | +0.343 | +0.342 | False | 0.000 | 0.018 | 7.61 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Landry Shamet | fg3m | UNDER | 1.5 | 0.659 | 0.659 | 0.514 | 0.514 | +0.145 | +0.145 | +0.259 | +0.259 | +0.259 | False | 0.000 | 0.263 | 1.16 | EDGE_10_20 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Jalen Brunson | fg3m | UNDER | 2.5 | 0.740 | 0.740 | 0.596 | 0.596 | +0.144 | +0.144 | +0.203 | +0.203 | +0.203 | False | 0.000 | 0.185 | 1.75 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Dylan Harper | pts | UNDER | 11.5 | 0.596 | 0.598 | 0.454 | 0.454 | +0.142 | +0.144 | +0.276 | +0.280 | +0.279 | False | 0.000 | 0.030 | 10.54 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Julian Champagnie | reb | UNDER | 5.5 | 0.612 | 0.613 | 0.470 | 0.470 | +0.142 | +0.143 | +0.273 | +0.275 | +0.275 | False | 0.000 | 0.043 | 5.03 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Julian Champagnie | pts | UNDER | 10.5 | 0.625 | 0.628 | 0.485 | 0.485 | +0.140 | +0.143 | +0.250 | +0.256 | +0.255 | False | 0.000 | 0.030 | 9.55 | EDGE_10_20 | PUBLISH_BLOCKER | line_vs_median_gap | **NO** |
| Mitchell Robinson | blk | UNDER | 0.5 | 0.641 | 0.641 | 0.513 | 0.513 | +0.128 | +0.128 | +0.224 | +0.224 | +0.224 | False | 0.000 | 0.641 | 0.64 | EDGE_10_20 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Keldon Johnson | reb | UNDER | 2.5 | 0.609 | 0.610 | 0.481 | 0.481 | +0.128 | +0.129 | +0.230 | +0.232 | +0.232 | False | 0.000 | 0.189 | 2.35 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Devin Vassell | pts | UNDER | 12.5 | 0.610 | 0.613 | 0.486 | 0.486 | +0.124 | +0.127 | +0.232 | +0.238 | +0.237 | False | 0.000 | 0.021 | 11.14 | EDGE_10_20 | PUBLISH_BLOCKER | line_vs_median_gap | **NO** |
| Julian Champagnie | fg3m | UNDER | 2.5 | 0.630 | 0.630 | 0.512 | 0.512 | +0.118 | +0.118 | +0.203 | +0.203 | +0.203 | False | 0.000 | 0.102 | 2.21 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Victor Wembanyama | stl | UNDER | 1.5 | 0.761 | 0.761 | 0.646 | 0.646 | +0.115 | +0.115 | +0.161 | +0.161 | +0.161 | False | 0.000 | 0.486 | 0.98 | EDGE_10_20 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Devin Vassell | ast | UNDER | 2.5 | 0.678 | 0.679 | 0.569 | 0.569 | +0.110 | +0.111 | +0.163 | +0.164 | +0.164 | False | 0.000 | 0.210 | 1.94 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Jalen Brunson | stl | OVER | 0.5 | 0.665 | 0.665 | 0.559 | 0.559 | +0.106 | +0.106 | +0.144 | +0.144 | +0.144 | False | 0.000 | 0.335 | 1.28 | EDGE_10_20 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Karl-Anthony Towns | pts | UNDER | 16.5 | 0.611 | 0.614 | 0.509 | 0.509 | +0.102 | +0.105 | +0.166 | +0.172 | +0.171 | False | 0.000 | 0.011 | 14.69 | EDGE_10_20 | PUBLISH_BLOCKER | line_vs_median_gap | **NO** |
| Josh Hart | fg3m | UNDER | 1.5 | 0.569 | 0.569 | 0.475 | 0.475 | +0.094 | +0.094 | +0.223 | +0.223 | +0.223 | False | 0.000 | 0.218 | 1.43 | EDGE_LT_10 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Devin Vassell | blk | UNDER | 0.5 | 0.730 | 0.730 | 0.635 | 0.635 | +0.094 | +0.094 | +0.122 | +0.122 | +0.122 | False | 0.000 | 0.730 | 0.43 | EDGE_LT_10 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Mikal Bridges | fg3m | UNDER | 1.5 | 0.705 | 0.705 | 0.615 | 0.615 | +0.091 | +0.091 | +0.106 | +0.106 | +0.106 | False | 0.000 | 0.297 | 1.07 | EDGE_LT_10 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |

