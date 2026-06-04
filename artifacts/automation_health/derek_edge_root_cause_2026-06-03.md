# Derek edge root-cause audit — 2026-06-03

- snapshots audited: **3**
- total calculation issues: **9**
- non-actionable rows: **44**

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
| Victor Wembanyama | reb | UNDER | 11.5 | 0.769 | 0.771 | 0.484 | 0.484 | +0.287 | +0.287 | +0.546 | +0.549 | +0.548 | False | 0.000 | 0.013 | 8.72 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | blk | UNDER | 0.5 | 0.686 | 0.686 | 0.404 | 0.404 | +0.282 | +0.282 | +0.715 | +0.715 | +0.715 | False | 0.000 | 0.686 | 0.43 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | pts | UNDER | 26.5 | 0.737 | 0.739 | 0.487 | 0.487 | +0.252 | +0.252 | +0.452 | +0.457 | +0.455 | False | 0.000 | 0.008 | 21.08 | EDGE_20_30 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Mitchell Robinson | blk | UNDER | 0.5 | 0.682 | 0.682 | 0.456 | 0.456 | +0.226 | +0.226 | +0.399 | +0.399 | +0.399 | False | 0.000 | 0.682 | 0.44 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Stephon Castle | ast | UNDER | 6.5 | 0.677 | 0.678 | 0.468 | 0.468 | +0.210 | +0.210 | +0.401 | +0.404 | +0.403 | False | 0.000 | 0.034 | 5.39 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Julian Champagnie | reb | UNDER | 5.5 | 0.695 | 0.696 | 0.499 | 0.499 | +0.197 | +0.197 | +0.327 | +0.329 | +0.328 | False | 0.000 | 0.051 | 4.41 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | stl | UNDER | 1.5 | 0.817 | 0.817 | 0.620 | 0.620 | +0.197 | +0.197 | +0.242 | +0.242 | +0.242 | False | 0.000 | 0.456 | 0.85 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Luke Kornet | reb | UNDER | 2.5 | 0.666 | 0.667 | 0.474 | 0.474 | +0.193 | +0.193 | +0.345 | +0.348 | +0.347 | False | 0.000 | 0.238 | 2.19 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | ast | UNDER | 3.5 | 0.785 | 0.786 | 0.601 | 0.601 | +0.185 | +0.185 | +0.260 | +0.262 | +0.262 | False | 0.000 | 0.135 | 2.38 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | reb | UNDER | 3.5 | 0.760 | 0.761 | 0.579 | 0.579 | +0.183 | +0.183 | +0.274 | +0.275 | +0.275 | False | 0.000 | 0.139 | 2.44 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Stephon Castle | reb | UNDER | 4.5 | 0.608 | 0.609 | 0.443 | 0.443 | +0.166 | +0.166 | +0.326 | +0.328 | +0.328 | False | 0.000 | 0.064 | 4.10 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | pts | UNDER | 16.5 | 0.654 | 0.656 | 0.491 | 0.491 | +0.165 | +0.165 | +0.277 | +0.280 | +0.279 | False | 0.000 | 0.011 | 14.33 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | pts | UNDER | 13.5 | 0.667 | 0.669 | 0.506 | 0.506 | +0.163 | +0.163 | +0.303 | +0.307 | +0.306 | False | 0.000 | 0.024 | 11.31 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | reb | UNDER | 11.5 | 0.647 | 0.649 | 0.502 | 0.502 | +0.146 | +0.146 | +0.294 | +0.297 | +0.296 | False | 0.000 | 0.010 | 10.07 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | reb | UNDER | 8.5 | 0.694 | 0.694 | 0.553 | 0.553 | +0.141 | +0.141 | +0.200 | +0.201 | +0.201 | False | 0.000 | 0.020 | 6.99 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | reb | UNDER | 4.5 | 0.702 | 0.703 | 0.563 | 0.563 | +0.140 | +0.140 | +0.222 | +0.223 | +0.223 | False | 0.000 | 0.065 | 3.58 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | ast | OVER | 3.5 | 0.698 | 0.697 | 0.566 | 0.566 | +0.131 | +0.131 | +0.179 | +0.178 | +0.177 | False | 0.000 | 0.054 | 5.11 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | ast | UNDER | 2.5 | 0.590 | 0.591 | 0.459 | 0.459 | +0.131 | +0.131 | +0.268 | +0.270 | +0.269 | False | 0.000 | 0.238 | 2.18 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | blk | UNDER | 0.5 | 0.695 | 0.695 | 0.566 | 0.566 | +0.129 | +0.129 | +0.158 | +0.158 | +0.158 | False | 0.000 | 0.695 | 0.37 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | ast | UNDER | 5.5 | 0.566 | 0.567 | 0.458 | 0.458 | +0.109 | +0.109 | +0.190 | +0.191 | +0.191 | False | 0.000 | 0.042 | 4.99 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Mikal Bridges | blk | UNDER | 0.5 | 0.691 | 0.691 | 0.597 | 0.597 | +0.094 | +0.094 | +0.095 | +0.095 | +0.095 | False | 0.000 | 0.691 | 0.39 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Brunson | pts | UNDER | 25.5 | 0.583 | 0.586 | 0.495 | 0.495 | +0.091 | +0.091 | +0.166 | +0.172 | +0.171 | False | 0.000 | 0.006 | 23.84 | EDGE_LT_10 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| De'Aaron Fox | reb | UNDER | 3.5 | 0.597 | 0.598 | 0.509 | 0.509 | +0.089 | +0.089 | +0.140 | +0.141 | +0.141 | False | 0.000 | 0.097 | 3.21 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julian Champagnie | pts | UNDER | 10.5 | 0.586 | 0.588 | 0.506 | 0.506 | +0.082 | +0.082 | +0.145 | +0.148 | +0.147 | False | 0.000 | 0.024 | 9.99 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | ast | UNDER | 2.5 | 0.643 | 0.644 | 0.574 | 0.574 | +0.070 | +0.070 | +0.077 | +0.079 | +0.079 | False | 0.000 | 0.210 | 2.01 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

## deliveries/2026-06-03/derek_game_snapshots/21716134/t_minus_25

- snapshot_type: `t_minus_25`  lineup_confirmed: **False**
- row_count: 31
- bucket_counts: {'EDGE_LT_10': 12, 'EDGE_10_20': 14, 'EDGE_20_30': 4, 'EDGE_30_PLUS': 1}
- publish_status_counts: {'ACTIONABLE_REVIEWED': 24, 'PUBLISH_BLOCKER': 3, 'REVIEW_LARGE_EDGE': 4}
- ⚠️ top 20 edges UNDER-skewed share=95%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | reb | UNDER | 11.5 | 0.778 | 0.779 | 0.477 | 0.477 | +0.301 | +0.302 | +0.595 | +0.598 | +0.597 | False | 0.000 | 0.012 | 8.71 | EDGE_30_PLUS | PUBLISH_BLOCKER | line_vs_median_gap | yes |
| Karl-Anthony Towns | blk | UNDER | 0.5 | 0.686 | 0.686 | 0.409 | 0.409 | +0.277 | +0.277 | +0.680 | +0.681 | +0.681 | False | 0.000 | 0.686 | 0.43 | EDGE_20_30 | REVIEW_LARGE_EDGE | low_line_discrete_stat | yes |
| Victor Wembanyama | pts | UNDER | 26.5 | 0.736 | 0.737 | 0.486 | 0.486 | +0.250 | +0.252 | +0.457 | +0.460 | +0.459 | False | 0.000 | 0.008 | 21.12 | EDGE_20_30 | REVIEW_LARGE_EDGE | line_vs_median_gap | yes |
| Stephon Castle | ast | UNDER | 6.5 | 0.673 | 0.674 | 0.453 | 0.453 | +0.220 | +0.221 | +0.448 | +0.450 | +0.449 | False | 0.000 | 0.033 | 5.39 | EDGE_20_30 | REVIEW_LARGE_EDGE | line_vs_median_gap | yes |
| Mitchell Robinson | blk | UNDER | 0.5 | 0.682 | 0.682 | 0.464 | 0.464 | +0.219 | +0.219 | +0.379 | +0.379 | +0.379 | False | 0.000 | 0.682 | 0.44 | EDGE_20_30 | REVIEW_LARGE_EDGE | low_line_discrete_stat | yes |
| Luke Kornet | reb | UNDER | 2.5 | 0.663 | 0.665 | 0.468 | 0.468 | +0.196 | +0.197 | +0.379 | +0.383 | +0.382 | False | 0.000 | 0.237 | 2.20 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Victor Wembanyama | stl | UNDER | 1.5 | 0.817 | 0.817 | 0.628 | 0.628 | +0.189 | +0.188 | +0.247 | +0.247 | +0.247 | False | 0.000 | 0.456 | 0.85 | EDGE_10_20 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Julian Champagnie | reb | UNDER | 5.5 | 0.697 | 0.698 | 0.512 | 0.512 | +0.185 | +0.186 | +0.330 | +0.332 | +0.331 | False | 0.000 | 0.052 | 4.42 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Keldon Johnson | reb | UNDER | 3.5 | 0.758 | 0.759 | 0.580 | 0.580 | +0.178 | +0.179 | +0.291 | +0.293 | +0.293 | False | 0.000 | 0.135 | 2.44 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Josh Hart | reb | UNDER | 7.5 | 0.582 | 0.583 | 0.427 | 0.427 | +0.155 | +0.156 | +0.338 | +0.340 | +0.340 | False | 0.000 | 0.021 | 6.97 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Karl-Anthony Towns | pts | UNDER | 16.5 | 0.653 | 0.655 | 0.505 | 0.505 | +0.148 | +0.150 | +0.268 | +0.272 | +0.271 | False | 0.000 | 0.011 | 14.35 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Stephon Castle | reb | UNDER | 4.5 | 0.600 | 0.601 | 0.452 | 0.452 | +0.148 | +0.149 | +0.295 | +0.298 | +0.297 | False | 0.000 | 0.066 | 4.11 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Devin Vassell | reb | UNDER | 4.5 | 0.707 | 0.708 | 0.563 | 0.563 | +0.144 | +0.145 | +0.230 | +0.232 | +0.232 | False | 0.000 | 0.064 | 3.57 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Devin Vassell | pts | UNDER | 12.5 | 0.606 | 0.608 | 0.467 | 0.467 | +0.139 | +0.141 | +0.242 | +0.246 | +0.245 | False | 0.000 | 0.024 | 11.34 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Dylan Harper | ast | UNDER | 2.5 | 0.591 | 0.592 | 0.454 | 0.454 | +0.137 | +0.138 | +0.300 | +0.302 | +0.301 | False | 0.000 | 0.239 | 2.19 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Victor Wembanyama | ast | UNDER | 2.5 | 0.537 | 0.538 | 0.404 | 0.404 | +0.134 | +0.134 | +0.290 | +0.291 | +0.291 | False | 0.000 | 0.133 | 2.41 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Devin Vassell | blk | UNDER | 0.5 | 0.695 | 0.695 | 0.566 | 0.566 | +0.129 | +0.129 | +0.158 | +0.158 | +0.158 | False | 0.000 | 0.695 | 0.37 | EDGE_10_20 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Karl-Anthony Towns | reb | UNDER | 11.5 | 0.650 | 0.652 | 0.522 | 0.522 | +0.128 | +0.130 | +0.216 | +0.218 | +0.218 | False | 0.000 | 0.010 | 10.05 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Karl-Anthony Towns | ast | OVER | 3.5 | 0.703 | 0.702 | 0.575 | 0.575 | +0.128 | +0.127 | +0.194 | +0.194 | +0.193 | False | 0.000 | 0.053 | 5.15 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Mikal Bridges | blk | UNDER | 0.5 | 0.691 | 0.691 | 0.600 | 0.600 | +0.091 | +0.091 | +0.095 | +0.095 | +0.095 | False | 0.000 | 0.691 | 0.39 | EDGE_LT_10 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Julian Champagnie | pts | UNDER | 10.5 | 0.585 | 0.587 | 0.499 | 0.499 | +0.086 | +0.088 | +0.142 | +0.146 | +0.145 | False | 0.000 | 0.025 | 10.00 | EDGE_LT_10 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Jalen Brunson | pts | UNDER | 25.5 | 0.582 | 0.584 | 0.500 | 0.500 | +0.082 | +0.084 | +0.163 | +0.168 | +0.168 | False | 0.000 | 0.008 | 23.90 | EDGE_LT_10 | PUBLISH_BLOCKER | line_vs_median_gap | **NO** |
| Mitchell Robinson | reb | UNDER | 5.5 | 0.635 | 0.637 | 0.554 | 0.554 | +0.081 | +0.083 | +0.095 | +0.098 | +0.098 | False | 0.000 | 0.061 | 4.87 | EDGE_LT_10 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| De'Aaron Fox | reb | UNDER | 3.5 | 0.599 | 0.600 | 0.519 | 0.519 | +0.080 | +0.081 | +0.144 | +0.145 | +0.145 | False | 0.000 | 0.096 | 3.20 | EDGE_LT_10 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| De'Aaron Fox | ast | UNDER | 5.5 | 0.555 | 0.555 | 0.476 | 0.476 | +0.079 | +0.080 | +0.121 | +0.122 | +0.122 | False | 0.000 | 0.039 | 5.04 | EDGE_LT_10 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |

## deliveries/2026-06-03/derek_game_snapshots/21716134/close_lock

- snapshot_type: `close_lock`  lineup_confirmed: **False**
- row_count: 31
- bucket_counts: {'EDGE_LT_10': 12, 'EDGE_20_30': 6, 'EDGE_10_20': 13}
- publish_status_counts: {'ACTIONABLE_REVIEWED': 23, 'REVIEW_LARGE_EDGE': 5, 'PUBLISH_BLOCKER': 3}
- ⚠️ top 20 edges UNDER-skewed share=95%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | reb | UNDER | 11.5 | 0.773 | 0.775 | 0.477 | 0.477 | +0.296 | +0.298 | +0.585 | +0.588 | +0.587 | False | 0.000 | 0.013 | 8.72 | EDGE_20_30 | REVIEW_LARGE_EDGE | line_vs_median_gap | yes |
| Karl-Anthony Towns | blk | UNDER | 0.5 | 0.686 | 0.686 | 0.409 | 0.409 | +0.277 | +0.277 | +0.680 | +0.681 | +0.681 | False | 0.000 | 0.686 | 0.43 | EDGE_20_30 | REVIEW_LARGE_EDGE | low_line_discrete_stat | yes |
| Victor Wembanyama | pts | UNDER | 26.5 | 0.741 | 0.744 | 0.486 | 0.486 | +0.255 | +0.258 | +0.467 | +0.474 | +0.472 | False | 0.000 | 0.009 | 21.01 | EDGE_20_30 | PUBLISH_BLOCKER | line_vs_median_gap | **NO** |
| Stephon Castle | ast | UNDER | 6.5 | 0.673 | 0.674 | 0.453 | 0.453 | +0.220 | +0.221 | +0.446 | +0.448 | +0.448 | False | 0.000 | 0.033 | 5.40 | EDGE_20_30 | REVIEW_LARGE_EDGE | line_vs_median_gap | yes |
| Mitchell Robinson | blk | UNDER | 0.5 | 0.682 | 0.682 | 0.464 | 0.464 | +0.219 | +0.219 | +0.379 | +0.379 | +0.379 | False | 0.000 | 0.682 | 0.44 | EDGE_20_30 | REVIEW_LARGE_EDGE | low_line_discrete_stat | yes |
| Luke Kornet | reb | UNDER | 2.5 | 0.675 | 0.677 | 0.468 | 0.468 | +0.207 | +0.209 | +0.404 | +0.407 | +0.406 | False | 0.000 | 0.259 | 2.14 | EDGE_20_30 | REVIEW_LARGE_EDGE | market_prob_disagreement | yes |
| Victor Wembanyama | stl | UNDER | 1.5 | 0.817 | 0.817 | 0.628 | 0.628 | +0.189 | +0.188 | +0.247 | +0.247 | +0.247 | False | 0.000 | 0.456 | 0.85 | EDGE_10_20 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Julian Champagnie | reb | UNDER | 5.5 | 0.696 | 0.697 | 0.512 | 0.512 | +0.185 | +0.185 | +0.329 | +0.331 | +0.330 | False | 0.000 | 0.051 | 4.41 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Keldon Johnson | reb | UNDER | 3.5 | 0.758 | 0.759 | 0.580 | 0.580 | +0.178 | +0.179 | +0.291 | +0.293 | +0.293 | False | 0.000 | 0.135 | 2.44 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Stephon Castle | reb | UNDER | 4.5 | 0.607 | 0.608 | 0.452 | 0.452 | +0.155 | +0.157 | +0.311 | +0.314 | +0.314 | False | 0.000 | 0.064 | 4.08 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Karl-Anthony Towns | pts | UNDER | 16.5 | 0.653 | 0.655 | 0.505 | 0.505 | +0.148 | +0.150 | +0.269 | +0.273 | +0.272 | False | 0.000 | 0.012 | 14.34 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Josh Hart | reb | UNDER | 7.5 | 0.574 | 0.574 | 0.427 | 0.427 | +0.146 | +0.147 | +0.319 | +0.321 | +0.320 | False | 0.000 | 0.021 | 6.97 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Devin Vassell | pts | UNDER | 12.5 | 0.606 | 0.608 | 0.467 | 0.467 | +0.139 | +0.141 | +0.242 | +0.246 | +0.245 | False | 0.000 | 0.024 | 11.30 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Dylan Harper | ast | UNDER | 2.5 | 0.592 | 0.593 | 0.454 | 0.454 | +0.138 | +0.139 | +0.302 | +0.304 | +0.303 | False | 0.000 | 0.231 | 2.20 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Devin Vassell | reb | UNDER | 4.5 | 0.699 | 0.700 | 0.563 | 0.563 | +0.136 | +0.137 | +0.217 | +0.218 | +0.218 | False | 0.000 | 0.066 | 3.60 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Victor Wembanyama | ast | UNDER | 2.5 | 0.539 | 0.539 | 0.404 | 0.404 | +0.135 | +0.136 | +0.293 | +0.295 | +0.294 | False | 0.000 | 0.132 | 2.40 | EDGE_10_20 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Devin Vassell | blk | UNDER | 0.5 | 0.695 | 0.695 | 0.566 | 0.566 | +0.129 | +0.129 | +0.158 | +0.158 | +0.158 | False | 0.000 | 0.695 | 0.37 | EDGE_10_20 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Karl-Anthony Towns | reb | UNDER | 11.5 | 0.650 | 0.651 | 0.522 | 0.522 | +0.128 | +0.129 | +0.215 | +0.218 | +0.217 | False | 0.000 | 0.010 | 10.05 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Karl-Anthony Towns | ast | OVER | 3.5 | 0.701 | 0.701 | 0.575 | 0.575 | +0.126 | +0.126 | +0.192 | +0.191 | +0.191 | False | 0.000 | 0.054 | 5.15 | EDGE_10_20 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Julian Champagnie | pts | UNDER | 10.5 | 0.590 | 0.592 | 0.499 | 0.499 | +0.091 | +0.093 | +0.152 | +0.156 | +0.156 | False | 0.000 | 0.025 | 9.96 | EDGE_LT_10 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| Mikal Bridges | blk | UNDER | 0.5 | 0.691 | 0.691 | 0.600 | 0.600 | +0.091 | +0.091 | +0.095 | +0.095 | +0.095 | False | 0.000 | 0.691 | 0.39 | EDGE_LT_10 | ACTIONABLE_REVIEWED | low_line_discrete_stat | yes |
| Mitchell Robinson | reb | UNDER | 5.5 | 0.638 | 0.640 | 0.554 | 0.554 | +0.085 | +0.086 | +0.101 | +0.104 | +0.104 | False | 0.000 | 0.065 | 4.87 | EDGE_LT_10 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| De'Aaron Fox | reb | UNDER | 3.5 | 0.599 | 0.600 | 0.519 | 0.519 | +0.080 | +0.081 | +0.144 | +0.145 | +0.145 | False | 0.000 | 0.097 | 3.21 | EDGE_LT_10 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |
| Jalen Brunson | pts | UNDER | 25.5 | 0.579 | 0.581 | 0.500 | 0.500 | +0.079 | +0.081 | +0.157 | +0.161 | +0.161 | False | 0.000 | 0.007 | 23.91 | EDGE_LT_10 | ACTIONABLE_REVIEWED | line_vs_median_gap | yes |
| De'Aaron Fox | ast | UNDER | 5.5 | 0.554 | 0.555 | 0.476 | 0.476 | +0.079 | +0.079 | +0.120 | +0.121 | +0.121 | False | 0.000 | 0.041 | 5.04 | EDGE_LT_10 | ACTIONABLE_REVIEWED | market_prob_disagreement | yes |

