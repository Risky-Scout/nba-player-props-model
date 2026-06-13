# Derek edge root-cause audit — 2026-06-13

- snapshots audited: **1**
- total calculation issues: **2**
- non-actionable rows: **41**

## Headline finding

**Calculation bug found.** See per-row issues below — these are recompute mismatches > 0.5 percentage points.

## deliveries/2026-06-13/derek_game_snapshots/21716138/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 41
- bucket_counts: {'EDGE_10_20': 24, 'EDGE_LT_10': 10, 'EDGE_20_30': 6, 'EDGE_30_PLUS': 1}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 33, 'REVIEW_LARGE_EDGE': 5, 'PUBLISH_BLOCKER': 3}
- ⚠️ top 20 edges UNDER-skewed share=80%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | blk | UNDER | 3.5 | 0.836 | 0.836 | 0.523 | 0.523 | +0.313 | +0.313 | +0.563 | +0.563 | +0.563 | False | 0.000 | 0.148 | 2.00 | EDGE_30_PLUS | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | fg3m | OVER | 0.5 | 0.789 | 0.789 | 0.492 | 0.492 | +0.297 | +0.297 | +0.555 | +0.555 | +0.555 | False | 0.000 | 0.211 | 1.45 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | reb | UNDER | 11.5 | 0.770 | 0.771 | 0.492 | 0.492 | +0.279 | +0.279 | +0.489 | +0.492 | +0.491 | False | 0.000 | 0.013 | 8.93 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Miles McBride | fg3m | OVER | 0.5 | 0.790 | 0.790 | 0.535 | 0.535 | +0.255 | +0.255 | +0.422 | +0.422 | +0.422 | False | 0.000 | 0.210 | 1.49 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | pts | UNDER | 28.5 | 0.747 | 0.750 | 0.500 | 0.500 | +0.250 | +0.250 | +0.464 | +0.471 | +0.469 | False | 0.000 | 0.005 | 22.70 | EDGE_20_30 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Dylan Harper | pts | UNDER | 14.5 | 0.688 | 0.690 | 0.476 | 0.476 | +0.214 | +0.214 | +0.389 | +0.393 | +0.392 | False | 0.000 | 0.017 | 11.81 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Jose Alvarado | stl | UNDER | 0.5 | 0.781 | 0.781 | 0.580 | 0.579 | +0.202 | +0.202 | +0.276 | +0.276 | +0.276 | False | 0.000 | 0.781 | 0.28 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Devin Vassell | pts | UNDER | 13.5 | 0.677 | 0.679 | 0.491 | 0.491 | +0.188 | +0.188 | +0.367 | +0.372 | +0.371 | False | 0.000 | 0.022 | 11.10 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Stephon Castle | ast | UNDER | 6.5 | 0.695 | 0.696 | 0.513 | 0.513 | +0.184 | +0.184 | +0.322 | +0.324 | +0.323 | False | 0.000 | 0.044 | 5.08 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | fg3m | UNDER | 2.5 | 0.679 | 0.679 | 0.504 | 0.504 | +0.176 | +0.176 | +0.326 | +0.326 | +0.326 | False | 0.000 | 0.102 | 2.00 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | reb | UNDER | 5.5 | 0.638 | 0.639 | 0.464 | 0.464 | +0.175 | +0.175 | +0.327 | +0.329 | +0.328 | False | 0.000 | 0.044 | 4.82 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| OG Anunoby | pts | UNDER | 17.5 | 0.658 | 0.660 | 0.488 | 0.488 | +0.172 | +0.172 | +0.316 | +0.320 | +0.319 | False | 0.000 | 0.007 | 15.42 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| OG Anunoby | stl | UNDER | 1.5 | 0.780 | 0.780 | 0.613 | 0.613 | +0.167 | +0.167 | +0.256 | +0.256 | +0.256 | False | 0.000 | 0.399 | 0.97 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | ast | UNDER | 3.5 | 0.734 | 0.735 | 0.573 | 0.573 | +0.162 | +0.162 | +0.251 | +0.253 | +0.252 | False | 0.000 | 0.170 | 2.46 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | pts | UNDER | 16.5 | 0.671 | 0.673 | 0.512 | 0.512 | +0.161 | +0.161 | +0.281 | +0.284 | +0.284 | False | 0.000 | 0.013 | 13.85 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | reb | OVER | 3.5 | 0.606 | 0.605 | 0.460 | 0.460 | +0.145 | +0.145 | +0.278 | +0.277 | +0.277 | False | 0.000 | 0.062 | 4.40 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Landry Shamet | fg3m | OVER | 1.5 | 0.637 | 0.637 | 0.493 | 0.493 | +0.145 | +0.145 | +0.227 | +0.227 | +0.227 | False | 0.000 | 0.089 | 2.08 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | ast | UNDER | 3.5 | 0.698 | 0.698 | 0.562 | 0.562 | +0.136 | +0.136 | +0.196 | +0.197 | +0.197 | False | 0.000 | 0.116 | 2.64 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| OG Anunoby | fg3m | UNDER | 2.5 | 0.661 | 0.661 | 0.526 | 0.526 | +0.135 | +0.135 | +0.250 | +0.250 | +0.250 | False | 0.000 | 0.097 | 2.03 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | stl | UNDER | 1.5 | 0.759 | 0.759 | 0.626 | 0.626 | +0.133 | +0.133 | +0.193 | +0.193 | +0.193 | False | 0.000 | 0.435 | 0.96 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | stl | UNDER | 1.5 | 0.772 | 0.772 | 0.640 | 0.640 | +0.131 | +0.131 | +0.139 | +0.139 | +0.139 | False | 0.000 | 0.369 | 1.04 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | reb | UNDER | 11.5 | 0.666 | 0.667 | 0.541 | 0.541 | +0.126 | +0.126 | +0.199 | +0.201 | +0.201 | False | 0.000 | 0.012 | 9.87 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | reb | UNDER | 8.5 | 0.644 | 0.645 | 0.519 | 0.519 | +0.126 | +0.126 | +0.195 | +0.196 | +0.196 | False | 0.000 | 0.020 | 7.42 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Brunson | reb | OVER | 3.5 | 0.554 | 0.553 | 0.427 | 0.427 | +0.126 | +0.126 | +0.274 | +0.272 | +0.272 | False | 0.000 | 0.067 | 3.86 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | fg3m | OVER | 1.5 | 0.532 | 0.532 | 0.407 | 0.407 | +0.125 | +0.125 | +0.276 | +0.276 | +0.276 | False | 0.000 | 0.150 | 1.82 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

