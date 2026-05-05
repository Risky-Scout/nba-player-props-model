# Derek edge root-cause audit — 2026-05-04

- snapshots audited: **1**
- total calculation issues: **0**
- non-actionable rows: **32**

## Headline finding

**No calculation bug.** Every row's model_prob, market_prob, raw_edge, and EV recomputed within 0.5 percentage points of the recorded values, using the **push-excluded** convention for integer lines (consistent with the sportsbook win-probability standard).

## deliveries/2026-05-04/derek_game_snapshots/21707972/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 32
- bucket_counts: {'EDGE_LT_10': 9, 'EDGE_10_20': 21, 'EDGE_20_30': 1, 'EDGE_30_PLUS': 1}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 30, 'REVIEW_LARGE_EDGE': 1, 'PUBLISH_BLOCKER': 1}
- ⚠️ top 20 edges UNDER-skewed share=95%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | reb | UNDER | 11.5 | 0.810 | 0.812 | 0.488 | 0.488 | +0.322 | +0.324 | +0.637 | +0.641 | +0.639 | False | 0.000 | 0.012 | 8.44 | EDGE_30_PLUS | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | pts | UNDER | 27.5 | 0.741 | 0.742 | 0.509 | 0.509 | +0.232 | +0.233 | +0.414 | +0.417 | +0.416 | False | 0.000 | 0.010 | 21.19 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Anthony Edwards | fg3m | UNDER | 3.5 | 0.804 | 0.805 | 0.614 | 0.614 | +0.191 | +0.190 | +0.224 | +0.224 | +0.224 | False | 0.000 | 0.100 | 2.48 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Naz Reid | reb | UNDER | 5.5 | 0.629 | 0.630 | 0.456 | 0.456 | +0.173 | +0.174 | +0.352 | +0.354 | +0.353 | False | 0.000 | 0.030 | 4.90 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Mike Conley | fg3m | OVER | 1.5 | 0.553 | 0.553 | 0.391 | 0.391 | +0.162 | +0.162 | +0.333 | +0.333 | +0.333 | False | 0.000 | 0.143 | 2.15 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Stephon Castle | reb | UNDER | 5.5 | 0.655 | 0.656 | 0.498 | 0.498 | +0.158 | +0.159 | +0.262 | +0.264 | +0.264 | False | 0.000 | 0.033 | 4.67 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Ayo Dosunmu | blk | UNDER | 0.5 | 0.819 | 0.819 | 0.663 | 0.663 | +0.156 | +0.156 | +0.146 | +0.146 | +0.146 | False | 0.000 | 0.819 | 0.29 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Anthony Edwards | pts | UNDER | 24.5 | 0.672 | 0.673 | 0.516 | 0.516 | +0.156 | +0.156 | +0.223 | +0.224 | +0.224 | False | 0.000 | 0.009 | 20.60 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | reb | UNDER | 3.5 | 0.605 | 0.606 | 0.450 | 0.450 | +0.155 | +0.156 | +0.330 | +0.332 | +0.332 | False | 0.000 | 0.078 | 3.25 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | blk | UNDER | 0.5 | 0.660 | 0.660 | 0.513 | 0.513 | +0.147 | +0.147 | +0.234 | +0.234 | +0.234 | False | 0.000 | 0.660 | 0.59 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julius Randle | ast | UNDER | 4.5 | 0.681 | 0.683 | 0.537 | 0.537 | +0.144 | +0.146 | +0.227 | +0.229 | +0.229 | False | 0.000 | 0.065 | 3.64 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julian Champagnie | fg3m | UNDER | 1.5 | 0.540 | 0.540 | 0.396 | 0.396 | +0.144 | +0.144 | +0.328 | +0.328 | +0.328 | False | 0.000 | 0.203 | 1.82 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Ayo Dosunmu | ast | UNDER | 3.5 | 0.565 | 0.567 | 0.426 | 0.426 | +0.139 | +0.140 | +0.272 | +0.275 | +0.274 | False | 0.000 | 0.073 | 3.35 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jaden McDaniels | pts | UNDER | 16.5 | 0.622 | 0.622 | 0.484 | 0.484 | +0.138 | +0.138 | +0.215 | +0.215 | +0.215 | False | 0.000 | 0.017 | 14.43 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Ayo Dosunmu | pts | UNDER | 17.5 | 0.634 | 0.635 | 0.503 | 0.503 | +0.131 | +0.132 | +0.221 | +0.223 | +0.223 | False | 0.000 | 0.013 | 15.11 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Rudy Gobert | blk | UNDER | 1.5 | 0.710 | 0.710 | 0.580 | 0.580 | +0.131 | +0.131 | +0.184 | +0.184 | +0.184 | False | 0.000 | 0.451 | 1.14 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Anthony Edwards | reb | UNDER | 4.5 | 0.580 | 0.581 | 0.453 | 0.452 | +0.127 | +0.128 | +0.218 | +0.220 | +0.219 | False | 0.000 | 0.042 | 4.31 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julian Champagnie | reb | UNDER | 4.5 | 0.563 | 0.564 | 0.437 | 0.437 | +0.126 | +0.127 | +0.228 | +0.230 | +0.229 | False | 0.000 | 0.040 | 4.38 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Anthony Edwards | ast | UNDER | 3.5 | 0.598 | 0.599 | 0.481 | 0.481 | +0.117 | +0.118 | +0.163 | +0.164 | +0.164 | False | 0.000 | 0.078 | 3.16 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Naz Reid | pts | UNDER | 12.5 | 0.613 | 0.614 | 0.496 | 0.496 | +0.117 | +0.118 | +0.209 | +0.210 | +0.210 | False | 0.000 | 0.024 | 11.21 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julius Randle | reb | UNDER | 6.5 | 0.596 | 0.597 | 0.479 | 0.479 | +0.117 | +0.118 | +0.216 | +0.218 | +0.218 | False | 0.000 | 0.020 | 6.02 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | stl | OVER | 0.5 | 0.715 | 0.715 | 0.600 | 0.600 | +0.115 | +0.115 | +0.136 | +0.135 | +0.135 | False | 0.000 | 0.285 | 1.42 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | blk | UNDER | 3.5 | 0.618 | 0.618 | 0.504 | 0.504 | +0.114 | +0.114 | +0.235 | +0.235 | +0.235 | False | 0.000 | 0.059 | 3.13 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jaden McDaniels | ast | UNDER | 2.5 | 0.576 | 0.578 | 0.486 | 0.486 | +0.090 | +0.092 | +0.164 | +0.167 | +0.166 | False | 0.000 | 0.148 | 2.34 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Stephon Castle | ast | UNDER | 7.5 | 0.638 | 0.639 | 0.548 | 0.548 | +0.090 | +0.092 | +0.148 | +0.151 | +0.151 | False | 0.000 | 0.021 | 6.50 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

