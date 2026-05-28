# Derek edge root-cause audit — 2026-05-28

- snapshots audited: **1**
- total calculation issues: **5**
- non-actionable rows: **39**

## Headline finding

**Calculation bug found.** See per-row issues below — these are recompute mismatches > 0.5 percentage points.

## deliveries/2026-05-28/derek_game_snapshots/21713533/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 39
- bucket_counts: {'EDGE_LT_10': 19, 'EDGE_10_20': 18, 'EDGE_20_30': 2}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 34, 'PUBLISH_BLOCKER': 3, 'REVIEW_PUSH_LINE': 1, 'REVIEW_LARGE_EDGE': 1}
- ⚠️ top 20 edges UNDER-skewed share=75%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | pts | UNDER | 27.5 | 0.685 | 0.688 | 0.474 | 0.474 | +0.211 | +0.214 | +0.404 | +0.411 | +0.409 | False | 0.000 | 0.006 | 23.03 | EDGE_20_30 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Victor Wembanyama | blk | UNDER | 3.5 | 0.719 | 0.719 | 0.514 | 0.514 | +0.206 | +0.206 | +0.356 | +0.356 | +0.356 | False | 0.000 | 0.091 | 2.58 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Chet Holmgren | blk | UNDER | 1.5 | 0.724 | 0.724 | 0.542 | 0.542 | +0.182 | +0.182 | +0.256 | +0.256 | +0.256 | False | 0.000 | 0.393 | 1.05 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | fg3m | OVER | 0.5 | 0.760 | 0.760 | 0.580 | 0.580 | +0.180 | +0.180 | +0.266 | +0.266 | +0.266 | False | 0.000 | 0.240 | 1.36 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | stl | OVER | 1.0 | 0.667 | 0.667 | 0.488 | 0.488 | +0.178 | +0.178 | +0.900 | +0.900 | +0.643 | True | 0.285 | 0.238 | 1.52 | EDGE_10_20 | REVIEW_PUSH_LINE | unconfirmed_lineup_baseline | yes |
| Shai Gilgeous-Alexander | fg3m | UNDER | 1.5 | 0.723 | 0.723 | 0.562 | 0.562 | +0.161 | +0.161 | +0.240 | +0.240 | +0.240 | False | 0.000 | 0.327 | 1.01 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Alex Caruso | pts | UNDER | 10.5 | 0.677 | 0.679 | 0.516 | 0.516 | +0.160 | +0.163 | +0.250 | +0.254 | +0.254 | False | 0.000 | 0.047 | 8.55 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Williams | reb | OVER | 3.5 | 0.620 | 0.619 | 0.479 | 0.479 | +0.140 | +0.140 | +0.270 | +0.269 | +0.268 | False | 0.000 | 0.072 | 4.63 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jared McCain | pts | UNDER | 13.5 | 0.639 | 0.643 | 0.501 | 0.501 | +0.138 | +0.142 | +0.243 | +0.250 | +0.248 | False | 0.000 | 0.047 | 11.51 | EDGE_10_20 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Devin Vassell | fg3m | UNDER | 2.5 | 0.623 | 0.623 | 0.495 | 0.496 | +0.127 | +0.127 | +0.210 | +0.210 | +0.210 | False | 0.000 | 0.107 | 2.22 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Cason Wallace | ast | UNDER | 2.5 | 0.640 | 0.641 | 0.513 | 0.513 | +0.127 | +0.128 | +0.216 | +0.219 | +0.218 | False | 0.000 | 0.241 | 2.14 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Shai Gilgeous-Alexander | pts | UNDER | 29.5 | 0.635 | 0.640 | 0.509 | 0.509 | +0.126 | +0.131 | +0.197 | +0.206 | +0.204 | False | 0.000 | 0.005 | 26.08 | EDGE_10_20 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Cason Wallace | fg3m | UNDER | 1.5 | 0.690 | 0.690 | 0.565 | 0.565 | +0.125 | +0.125 | +0.220 | +0.220 | +0.220 | False | 0.000 | 0.325 | 1.07 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | ast | UNDER | 2.5 | 0.617 | 0.618 | 0.497 | 0.497 | +0.120 | +0.122 | +0.178 | +0.180 | +0.180 | False | 0.000 | 0.207 | 2.25 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | stl | OVER | 0.5 | 0.707 | 0.707 | 0.591 | 0.591 | +0.116 | +0.116 | +0.175 | +0.175 | +0.175 | False | 0.000 | 0.293 | 1.18 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Williams | ast | OVER | 3.5 | 0.570 | 0.569 | 0.456 | 0.456 | +0.115 | +0.114 | +0.226 | +0.224 | +0.224 | False | 0.000 | 0.071 | 4.22 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Luguentz Dort | fg3m | UNDER | 1.5 | 0.743 | 0.743 | 0.632 | 0.632 | +0.110 | +0.111 | +0.140 | +0.140 | +0.140 | False | 0.000 | 0.329 | 0.99 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | reb | UNDER | 12.5 | 0.586 | 0.586 | 0.476 | 0.476 | +0.110 | +0.110 | +0.207 | +0.207 | +0.207 | False | 0.000 | 0.012 | 11.60 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Stephon Castle | ast | UNDER | 6.5 | 0.542 | 0.543 | 0.437 | 0.437 | +0.105 | +0.105 | +0.192 | +0.194 | +0.193 | False | 0.000 | 0.030 | 6.29 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Alex Caruso | blk | UNDER | 0.5 | 0.683 | 0.683 | 0.579 | 0.579 | +0.104 | +0.104 | +0.193 | +0.193 | +0.193 | False | 0.000 | 0.683 | 0.44 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Williams | pts | OVER | 12.5 | 0.622 | 0.620 | 0.524 | 0.524 | +0.097 | +0.096 | +0.139 | +0.137 | +0.136 | False | 0.000 | 0.016 | 15.77 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | stl | UNDER | 1.5 | 0.716 | 0.716 | 0.622 | 0.621 | +0.095 | +0.095 | +0.125 | +0.125 | +0.125 | False | 0.000 | 0.319 | 1.15 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Cason Wallace | pts | UNDER | 8.5 | 0.595 | 0.596 | 0.501 | 0.501 | +0.093 | +0.095 | +0.161 | +0.164 | +0.164 | False | 0.000 | 0.043 | 7.86 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jaylin Williams | reb | UNDER | 3.5 | 0.561 | 0.562 | 0.469 | 0.469 | +0.091 | +0.092 | +0.149 | +0.152 | +0.151 | False | 0.000 | 0.118 | 3.59 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | reb | OVER | 3.5 | 0.602 | 0.601 | 0.521 | 0.521 | +0.081 | +0.081 | +0.126 | +0.124 | +0.124 | False | 0.000 | 0.061 | 4.58 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

