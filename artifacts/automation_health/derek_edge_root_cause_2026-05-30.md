# Derek edge root-cause audit — 2026-05-30

- snapshots audited: **1**
- total calculation issues: **5**
- non-actionable rows: **41**

## Headline finding

**Calculation bug found.** See per-row issues below — these are recompute mismatches > 0.5 percentage points.

## deliveries/2026-05-30/derek_game_snapshots/21713534/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 41
- bucket_counts: {'EDGE_20_30': 9, 'EDGE_LT_10': 13, 'EDGE_10_20': 19}
- publish_status_counts: {'REVIEW_LARGE_EDGE': 7, 'WATCHLIST_NOT_CONFIRMED_LINEUP': 30, 'PUBLISH_BLOCKER': 4}
- ⚠️ top 20 edges UNDER-skewed share=80%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Julian Champagnie | blk | OVER | 0.5 | 0.636 | 0.636 | 0.338 | 0.338 | +0.298 | +0.298 | +0.780 | +0.780 | +0.780 | False | 0.000 | 0.364 | 0.94 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Kenrich Williams | fg3m | OVER | 0.5 | 0.716 | 0.716 | 0.429 | 0.429 | +0.287 | +0.287 | +0.590 | +0.590 | +0.590 | False | 0.000 | 0.284 | 1.12 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Shai Gilgeous-Alexander | pts | UNDER | 30.5 | 0.759 | 0.762 | 0.490 | 0.490 | +0.268 | +0.272 | +0.481 | +0.488 | +0.486 | False | 0.000 | 0.006 | 24.19 | EDGE_20_30 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Alex Caruso | fg3m | UNDER | 1.5 | 0.650 | 0.650 | 0.389 | 0.389 | +0.261 | +0.261 | +0.605 | +0.605 | +0.605 | False | 0.000 | 0.278 | 1.15 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Alex Caruso | pts | UNDER | 10.5 | 0.726 | 0.730 | 0.475 | 0.475 | +0.252 | +0.255 | +0.452 | +0.460 | +0.458 | False | 0.000 | 0.059 | 7.73 | EDGE_20_30 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Shai Gilgeous-Alexander | blk | UNDER | 0.5 | 0.664 | 0.664 | 0.435 | 0.435 | +0.229 | +0.229 | +0.441 | +0.441 | +0.441 | False | 0.000 | 0.664 | 0.46 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | fg3m | OVER | 0.5 | 0.807 | 0.807 | 0.579 | 0.579 | +0.228 | +0.228 | +0.321 | +0.321 | +0.321 | False | 0.000 | 0.193 | 1.52 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Isaiah Joe | fg3m | OVER | 0.5 | 0.721 | 0.721 | 0.508 | 0.509 | +0.212 | +0.212 | +0.347 | +0.347 | +0.347 | False | 0.000 | 0.279 | 1.12 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Alex Caruso | reb | UNDER | 3.5 | 0.721 | 0.722 | 0.512 | 0.512 | +0.209 | +0.210 | +0.377 | +0.378 | +0.378 | False | 0.000 | 0.110 | 2.74 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Jared McCain | pts | UNDER | 13.5 | 0.707 | 0.710 | 0.507 | 0.507 | +0.200 | +0.203 | +0.322 | +0.328 | +0.326 | False | 0.000 | 0.048 | 10.38 | EDGE_10_20 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Isaiah Hartenstein | blk | UNDER | 0.5 | 0.711 | 0.711 | 0.512 | 0.512 | +0.199 | +0.199 | +0.330 | +0.330 | +0.330 | False | 0.000 | 0.711 | 0.40 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Alex Caruso | ast | UNDER | 2.5 | 0.684 | 0.685 | 0.489 | 0.489 | +0.194 | +0.195 | +0.367 | +0.369 | +0.369 | False | 0.000 | 0.233 | 1.92 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | pts | UNDER | 26.5 | 0.677 | 0.679 | 0.501 | 0.501 | +0.175 | +0.178 | +0.321 | +0.326 | +0.325 | False | 0.000 | 0.007 | 22.27 | EDGE_10_20 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Jaylin Williams | stl | UNDER | 0.5 | 0.770 | 0.770 | 0.598 | 0.598 | +0.172 | +0.172 | +0.206 | +0.206 | +0.206 | False | 0.000 | 0.770 | 0.33 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | reb | UNDER | 12.5 | 0.654 | 0.656 | 0.486 | 0.486 | +0.169 | +0.170 | +0.296 | +0.299 | +0.298 | False | 0.000 | 0.010 | 10.82 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Cason Wallace | fg3m | UNDER | 1.5 | 0.661 | 0.661 | 0.495 | 0.495 | +0.166 | +0.166 | +0.322 | +0.322 | +0.322 | False | 0.000 | 0.256 | 1.16 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Luguentz Dort | stl | UNDER | 0.5 | 0.667 | 0.667 | 0.502 | 0.502 | +0.165 | +0.165 | +0.273 | +0.273 | +0.273 | False | 0.000 | 0.667 | 0.56 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | ast | UNDER | 3.5 | 0.744 | 0.745 | 0.582 | 0.582 | +0.163 | +0.164 | +0.215 | +0.217 | +0.217 | False | 0.000 | 0.108 | 2.61 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Shai Gilgeous-Alexander | fg3m | UNDER | 1.5 | 0.681 | 0.681 | 0.536 | 0.536 | +0.145 | +0.145 | +0.225 | +0.225 | +0.225 | False | 0.000 | 0.276 | 1.11 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Cason Wallace | ast | UNDER | 2.5 | 0.606 | 0.606 | 0.462 | 0.462 | +0.144 | +0.145 | +0.272 | +0.273 | +0.273 | False | 0.000 | 0.239 | 2.10 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Isaiah Hartenstein | reb | UNDER | 8.5 | 0.660 | 0.661 | 0.534 | 0.534 | +0.126 | +0.127 | +0.210 | +0.212 | +0.212 | False | 0.000 | 0.022 | 7.26 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Stephon Castle | fg3m | OVER | 1.5 | 0.574 | 0.574 | 0.448 | 0.448 | +0.126 | +0.126 | +0.263 | +0.263 | +0.263 | False | 0.000 | 0.167 | 1.85 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | blk | UNDER | 3.5 | 0.636 | 0.636 | 0.512 | 0.512 | +0.124 | +0.124 | +0.214 | +0.214 | +0.214 | False | 0.000 | 0.095 | 2.92 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | reb | OVER | 4.5 | 0.536 | 0.536 | 0.422 | 0.422 | +0.114 | +0.113 | +0.222 | +0.221 | +0.221 | False | 0.000 | 0.047 | 4.83 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Luguentz Dort | fg3m | UNDER | 1.5 | 0.718 | 0.718 | 0.605 | 0.605 | +0.113 | +0.113 | +0.190 | +0.190 | +0.190 | False | 0.000 | 0.329 | 1.02 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

