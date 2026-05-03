# Derek edge root-cause audit — 2026-05-03

- snapshots audited: **2**
- total calculation issues: **0**
- non-actionable rows: **69**

## Headline finding

**No calculation bug.** Every row's model_prob, market_prob, raw_edge, and EV recomputed within 0.5 percentage points of the recorded values, using the **push-excluded** convention for integer lines (consistent with the sportsbook win-probability standard).

## deliveries/2026-05-03/derek_game_snapshots/21682000/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 36
- bucket_counts: {'EDGE_10_20': 23, 'EDGE_20_30': 5, 'EDGE_LT_10': 7, 'EDGE_30_PLUS': 1}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 30, 'REVIEW_LARGE_EDGE': 5, 'PUBLISH_BLOCKER': 1}
- ⚠️ top 20 edges UNDER-skewed share=90%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Evan Mobley | blk | UNDER | 1.5 | 0.789 | 0.789 | 0.473 | 0.473 | +0.316 | +0.315 | +0.617 | +0.617 | +0.617 | False | 0.000 | 0.390 | 1.09 | EDGE_30_PLUS | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | yes |
| Donovan Mitchell | fg3m | UNDER | 2.5 | 0.735 | 0.735 | 0.479 | 0.479 | +0.257 | +0.257 | +0.529 | +0.529 | +0.529 | False | 0.000 | 0.177 | 2.01 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Scottie Barnes | ast | UNDER | 7.5 | 0.668 | 0.669 | 0.440 | 0.440 | +0.228 | +0.229 | +0.482 | +0.486 | +0.484 | False | 0.000 | 0.028 | 6.21 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Collin Murray-Boyles | pts | UNDER | 12.5 | 0.693 | 0.694 | 0.469 | 0.468 | +0.225 | +0.225 | +0.442 | +0.443 | +0.443 | False | 0.000 | 0.030 | 10.01 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Scottie Barnes | fg3m | UNDER | 1.0 | 0.746 | 0.746 | 0.526 | 0.526 | +0.220 | +0.220 | +0.978 | +0.978 | +0.659 | True | 0.326 | 0.503 | 0.97 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Jamal Shead | ast | UNDER | 5.5 | 0.668 | 0.669 | 0.467 | 0.467 | +0.201 | +0.202 | +0.430 | +0.433 | +0.432 | False | 0.000 | 0.050 | 4.54 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| RJ Barrett | pts | UNDER | 23.5 | 0.708 | 0.708 | 0.508 | 0.508 | +0.200 | +0.200 | +0.334 | +0.334 | +0.334 | False | 0.000 | 0.011 | 19.25 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| James Harden | blk | UNDER | 0.5 | 0.755 | 0.755 | 0.561 | 0.561 | +0.194 | +0.194 | +0.269 | +0.269 | +0.269 | False | 0.000 | 0.755 | 0.40 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Sandro Mamukelashvili | reb | OVER | 3.5 | 0.627 | 0.626 | 0.435 | 0.435 | +0.192 | +0.191 | +0.373 | +0.371 | +0.370 | False | 0.000 | 0.042 | 4.74 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jamal Shead | pts | UNDER | 8.5 | 0.676 | 0.677 | 0.488 | 0.488 | +0.189 | +0.189 | +0.333 | +0.334 | +0.334 | False | 0.000 | 0.115 | 6.68 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Ja'Kobe Walter | reb | UNDER | 3.5 | 0.654 | 0.655 | 0.472 | 0.472 | +0.182 | +0.183 | +0.340 | +0.342 | +0.342 | False | 0.000 | 0.114 | 2.96 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Scottie Barnes | reb | UNDER | 6.5 | 0.624 | 0.625 | 0.446 | 0.446 | +0.178 | +0.179 | +0.310 | +0.312 | +0.312 | False | 0.000 | 0.028 | 5.67 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Donovan Mitchell | stl | UNDER | 1.5 | 0.789 | 0.789 | 0.612 | 0.612 | +0.178 | +0.178 | +0.283 | +0.283 | +0.283 | False | 0.000 | 0.513 | 0.96 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| James Harden | stl | UNDER | 1.5 | 0.790 | 0.790 | 0.615 | 0.615 | +0.175 | +0.175 | +0.284 | +0.284 | +0.284 | False | 0.000 | 0.531 | 0.93 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| James Harden | fg3m | UNDER | 2.5 | 0.624 | 0.624 | 0.451 | 0.451 | +0.173 | +0.173 | +0.342 | +0.342 | +0.342 | False | 0.000 | 0.101 | 2.47 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Donovan Mitchell | pts | UNDER | 25.5 | 0.676 | 0.677 | 0.505 | 0.505 | +0.171 | +0.171 | +0.264 | +0.265 | +0.265 | False | 0.000 | 0.007 | 21.53 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| RJ Barrett | ast | UNDER | 3.5 | 0.655 | 0.656 | 0.486 | 0.486 | +0.170 | +0.170 | +0.297 | +0.299 | +0.298 | False | 0.000 | 0.097 | 2.90 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Sam Merrill | stl | UNDER | 0.5 | 0.701 | 0.701 | 0.556 | 0.556 | +0.145 | +0.145 | +0.175 | +0.175 | +0.175 | False | 0.000 | 0.701 | 0.53 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Scottie Barnes | blk | UNDER | 1.5 | 0.733 | 0.733 | 0.589 | 0.589 | +0.144 | +0.144 | +0.177 | +0.177 | +0.177 | False | 0.000 | 0.320 | 1.25 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dennis Schroder | fg3m | OVER | 0.5 | 0.624 | 0.624 | 0.485 | 0.485 | +0.138 | +0.138 | +0.191 | +0.191 | +0.191 | False | 0.000 | 0.376 | 1.29 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Evan Mobley | pts | UNDER | 16.5 | 0.639 | 0.640 | 0.503 | 0.503 | +0.136 | +0.137 | +0.232 | +0.233 | +0.233 | False | 0.000 | 0.018 | 14.12 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Ja'Kobe Walter | stl | UNDER | 1.5 | 0.731 | 0.731 | 0.596 | 0.596 | +0.135 | +0.135 | +0.149 | +0.149 | +0.149 | False | 0.000 | 0.376 | 1.22 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| James Harden | ast | UNDER | 6.5 | 0.631 | 0.632 | 0.498 | 0.498 | +0.133 | +0.134 | +0.195 | +0.197 | +0.197 | False | 0.000 | 0.026 | 5.69 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Scottie Barnes | pts | UNDER | 21.5 | 0.643 | 0.643 | 0.510 | 0.510 | +0.133 | +0.134 | +0.207 | +0.208 | +0.208 | False | 0.000 | 0.012 | 18.65 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jarrett Allen | blk | UNDER | 1.5 | 0.739 | 0.739 | 0.617 | 0.616 | +0.123 | +0.123 | +0.182 | +0.182 | +0.182 | False | 0.000 | 0.303 | 1.28 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

## deliveries/2026-05-03/derek_game_snapshots/21684819/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 33
- bucket_counts: {'EDGE_10_20': 21, 'EDGE_LT_10': 12}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 33}
- ⚠️ top 20 edges UNDER-skewed share=75%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jamal Cain | reb | UNDER | 3.5 | 0.754 | 0.755 | 0.557 | 0.557 | +0.197 | +0.198 | +0.348 | +0.350 | +0.350 | False | 0.000 | 0.161 | 2.42 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Suggs | blk | UNDER | 0.5 | 0.621 | 0.621 | 0.426 | 0.426 | +0.194 | +0.194 | +0.384 | +0.384 | +0.384 | False | 0.000 | 0.621 | 0.67 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Isaiah Stewart | reb | OVER | 3.5 | 0.617 | 0.615 | 0.423 | 0.423 | +0.194 | +0.192 | +0.443 | +0.440 | +0.438 | False | 0.000 | 0.047 | 4.71 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Desmond Bane | fg3m | UNDER | 2.5 | 0.699 | 0.699 | 0.506 | 0.506 | +0.193 | +0.193 | +0.398 | +0.398 | +0.398 | False | 0.000 | 0.142 | 2.15 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Tobias Harris | pts | UNDER | 17.5 | 0.673 | 0.674 | 0.483 | 0.483 | +0.190 | +0.191 | +0.346 | +0.348 | +0.347 | False | 0.000 | 0.014 | 14.64 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Cade Cunningham | pts | UNDER | 28.5 | 0.675 | 0.675 | 0.490 | 0.490 | +0.185 | +0.186 | +0.336 | +0.337 | +0.337 | False | 0.000 | 0.009 | 24.08 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Ausar Thompson | blk | OVER | 1.5 | 0.625 | 0.625 | 0.442 | 0.442 | +0.182 | +0.182 | +0.393 | +0.393 | +0.393 | False | 0.000 | 0.102 | 2.52 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Tobias Harris | blk | OVER | 0.5 | 0.647 | 0.647 | 0.468 | 0.468 | +0.180 | +0.180 | +0.347 | +0.347 | +0.347 | False | 0.000 | 0.353 | 1.36 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Anthony Black | pts | UNDER | 11.5 | 0.690 | 0.690 | 0.517 | 0.517 | +0.173 | +0.173 | +0.289 | +0.291 | +0.290 | False | 0.000 | 0.041 | 9.15 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Daniss Jenkins | ast | UNDER | 2.5 | 0.733 | 0.734 | 0.585 | 0.585 | +0.148 | +0.149 | +0.238 | +0.240 | +0.240 | False | 0.000 | 0.211 | 1.78 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Tobias Harris | stl | UNDER | 1.5 | 0.786 | 0.786 | 0.641 | 0.641 | +0.145 | +0.145 | +0.189 | +0.189 | +0.189 | False | 0.000 | 0.499 | 0.97 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Duncan Robinson | fg3m | UNDER | 2.5 | 0.686 | 0.686 | 0.544 | 0.544 | +0.142 | +0.142 | +0.198 | +0.198 | +0.198 | False | 0.000 | 0.132 | 2.20 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Suggs | ast | UNDER | 4.5 | 0.575 | 0.576 | 0.441 | 0.441 | +0.134 | +0.135 | +0.254 | +0.256 | +0.256 | False | 0.000 | 0.052 | 4.18 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Cade Cunningham | reb | OVER | 5.5 | 0.666 | 0.665 | 0.536 | 0.536 | +0.130 | +0.129 | +0.198 | +0.197 | +0.197 | False | 0.000 | 0.017 | 7.30 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jalen Duren | stl | UNDER | 0.5 | 0.629 | 0.629 | 0.503 | 0.503 | +0.126 | +0.126 | +0.176 | +0.176 | +0.176 | False | 0.000 | 0.629 | 0.62 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Anthony Black | blk | UNDER | 0.5 | 0.635 | 0.635 | 0.512 | 0.512 | +0.123 | +0.123 | +0.187 | +0.187 | +0.187 | False | 0.000 | 0.635 | 0.68 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Cade Cunningham | ast | UNDER | 8.5 | 0.621 | 0.622 | 0.499 | 0.499 | +0.122 | +0.123 | +0.185 | +0.188 | +0.188 | False | 0.000 | 0.020 | 7.51 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Daniss Jenkins | fg3m | OVER | 0.5 | 0.612 | 0.612 | 0.495 | 0.495 | +0.117 | +0.117 | +0.143 | +0.143 | +0.144 | False | 0.000 | 0.388 | 1.26 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Daniss Jenkins | stl | UNDER | 0.5 | 0.647 | 0.647 | 0.544 | 0.544 | +0.104 | +0.104 | +0.113 | +0.113 | +0.113 | False | 0.000 | 0.647 | 0.63 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Tristan Da Silva | reb | UNDER | 2.5 | 0.584 | 0.585 | 0.483 | 0.483 | +0.101 | +0.102 | +0.169 | +0.171 | +0.170 | False | 0.000 | 0.167 | 2.41 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Cade Cunningham | blk | OVER | 0.5 | 0.656 | 0.656 | 0.556 | 0.556 | +0.100 | +0.100 | +0.153 | +0.153 | +0.153 | False | 0.000 | 0.344 | 1.30 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Cade Cunningham | stl | UNDER | 1.5 | 0.681 | 0.681 | 0.581 | 0.581 | +0.100 | +0.100 | +0.106 | +0.106 | +0.106 | False | 0.000 | 0.237 | 1.50 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Paolo Banchero | stl | UNDER | 1.5 | 0.633 | 0.634 | 0.534 | 0.534 | +0.099 | +0.099 | +0.508 | +0.508 | +0.508 | False | 0.000 | 0.364 | 1.38 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Tobias Harris | fg3m | UNDER | 1.5 | 0.707 | 0.707 | 0.611 | 0.611 | +0.096 | +0.096 | +0.148 | +0.148 | +0.148 | False | 0.000 | 0.360 | 1.32 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Paolo Banchero | reb | UNDER | 8.5 | 0.608 | 0.609 | 0.514 | 0.514 | +0.094 | +0.095 | +0.161 | +0.163 | +0.163 | False | 0.000 | 0.013 | 7.74 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

