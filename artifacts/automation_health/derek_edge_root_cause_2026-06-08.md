# Derek edge root-cause audit — 2026-06-08

- snapshots audited: **1**
- total calculation issues: **8**
- non-actionable rows: **30**

## Headline finding

**Calculation bug found.** See per-row issues below — these are recompute mismatches > 0.5 percentage points.

## deliveries/2026-06-08/derek_game_snapshots/21716136/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 30
- bucket_counts: {'EDGE_10_20': 16, 'EDGE_LT_10': 10, 'EDGE_20_30': 3, 'EDGE_30_PLUS': 1}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 22, 'PUBLISH_BLOCKER': 6, 'REVIEW_LARGE_EDGE': 2}
- ⚠️ top 20 edges UNDER-skewed share=85%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | blk | UNDER | 3.5 | 0.809 | 0.809 | 0.509 | 0.509 | +0.300 | +0.300 | +0.532 | +0.532 | +0.532 | False | 0.000 | 0.138 | 2.16 | EDGE_30_PLUS | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | fg3m | OVER | 0.5 | 0.769 | 0.769 | 0.512 | 0.512 | +0.257 | +0.257 | +0.431 | +0.432 | +0.431 | False | 0.000 | 0.231 | 1.39 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | pts | UNDER | 27.5 | 0.734 | 0.737 | 0.506 | 0.506 | +0.228 | +0.232 | +0.400 | +0.408 | +0.406 | False | 0.000 | 0.005 | 22.00 | EDGE_20_30 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Victor Wembanyama | reb | UNDER | 11.5 | 0.712 | 0.713 | 0.490 | 0.490 | +0.222 | +0.224 | +0.410 | +0.413 | +0.412 | False | 0.000 | 0.014 | 9.14 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Dylan Harper | ast | UNDER | 3.5 | 0.777 | 0.779 | 0.578 | 0.578 | +0.200 | +0.201 | +0.279 | +0.281 | +0.281 | False | 0.000 | 0.199 | 2.24 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | ast | UNDER | 3.5 | 0.774 | 0.775 | 0.609 | 0.609 | +0.165 | +0.166 | +0.211 | +0.213 | +0.212 | False | 0.000 | 0.150 | 2.31 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | pts | UNDER | 17.5 | 0.663 | 0.667 | 0.500 | 0.500 | +0.163 | +0.167 | +0.301 | +0.308 | +0.307 | False | 0.000 | 0.010 | 14.92 | EDGE_10_20 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Karl-Anthony Towns | stl | UNDER | 0.5 | 0.609 | 0.609 | 0.453 | 0.453 | +0.156 | +0.156 | +0.279 | +0.279 | +0.279 | False | 0.000 | 0.609 | 0.84 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | reb | OVER | 3.5 | 0.598 | 0.597 | 0.447 | 0.447 | +0.151 | +0.150 | +0.286 | +0.284 | +0.284 | False | 0.000 | 0.059 | 4.37 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Mikal Bridges | fg3m | UNDER | 1.5 | 0.700 | 0.700 | 0.552 | 0.552 | +0.148 | +0.148 | +0.239 | +0.239 | +0.239 | False | 0.000 | 0.301 | 1.07 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Stephon Castle | ast | UNDER | 6.5 | 0.705 | 0.706 | 0.557 | 0.557 | +0.147 | +0.148 | +0.204 | +0.206 | +0.206 | False | 0.000 | 0.037 | 5.08 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| De'Aaron Fox | ast | UNDER | 5.5 | 0.616 | 0.618 | 0.482 | 0.482 | +0.134 | +0.135 | +0.264 | +0.266 | +0.266 | False | 0.000 | 0.044 | 4.84 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | pts | UNDER | 13.5 | 0.636 | 0.638 | 0.504 | 0.504 | +0.133 | +0.135 | +0.242 | +0.247 | +0.246 | False | 0.000 | 0.023 | 11.53 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Stephon Castle | stl | OVER | 0.5 | 0.755 | 0.755 | 0.624 | 0.624 | +0.131 | +0.131 | +0.152 | +0.152 | +0.152 | False | 0.000 | 0.245 | 1.41 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | reb | UNDER | 8.5 | 0.646 | 0.647 | 0.529 | 0.529 | +0.117 | +0.118 | +0.185 | +0.186 | +0.186 | False | 0.000 | 0.022 | 7.32 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Julian Champagnie | pts | UNDER | 10.5 | 0.630 | 0.633 | 0.514 | 0.514 | +0.116 | +0.119 | +0.193 | +0.198 | +0.197 | False | 0.000 | 0.028 | 9.35 | EDGE_10_20 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Devin Vassell | ast | UNDER | 2.5 | 0.650 | 0.650 | 0.535 | 0.535 | +0.115 | +0.115 | +0.157 | +0.158 | +0.158 | False | 0.000 | 0.205 | 2.04 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Devin Vassell | pts | UNDER | 13.5 | 0.635 | 0.638 | 0.522 | 0.522 | +0.114 | +0.117 | +0.165 | +0.170 | +0.170 | False | 0.000 | 0.020 | 11.56 | EDGE_10_20 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Josh Hart | ast | UNDER | 4.5 | 0.605 | 0.606 | 0.497 | 0.497 | +0.108 | +0.109 | +0.181 | +0.183 | +0.183 | False | 0.000 | 0.071 | 4.04 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Landry Shamet | pts | UNDER | 8.5 | 0.599 | 0.601 | 0.498 | 0.498 | +0.102 | +0.103 | +0.165 | +0.168 | +0.168 | False | 0.000 | 0.082 | 7.70 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Keldon Johnson | reb | UNDER | 2.5 | 0.567 | 0.568 | 0.468 | 0.468 | +0.099 | +0.101 | +0.162 | +0.164 | +0.164 | False | 0.000 | 0.184 | 2.54 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Victor Wembanyama | stl | UNDER | 1.5 | 0.722 | 0.722 | 0.626 | 0.626 | +0.096 | +0.096 | +0.101 | +0.101 | +0.101 | False | 0.000 | 0.399 | 1.15 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | reb | UNDER | 11.5 | 0.594 | 0.595 | 0.518 | 0.518 | +0.076 | +0.077 | +0.129 | +0.131 | +0.131 | False | 0.000 | 0.012 | 10.48 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Dylan Harper | reb | UNDER | 5.5 | 0.621 | 0.622 | 0.545 | 0.545 | +0.076 | +0.077 | +0.098 | +0.100 | +0.100 | False | 0.000 | 0.047 | 4.93 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Mikal Bridges | reb | OVER | 3.5 | 0.534 | 0.534 | 0.459 | 0.459 | +0.075 | +0.074 | +0.133 | +0.131 | +0.131 | False | 0.000 | 0.069 | 3.95 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

