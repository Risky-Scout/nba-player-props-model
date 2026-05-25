# Derek edge root-cause audit — 2026-05-25

- snapshots audited: **1**
- total calculation issues: **2**
- non-actionable rows: **32**

## Headline finding

**Calculation bug found.** See per-row issues below — these are recompute mismatches > 0.5 percentage points.

## deliveries/2026-05-25/derek_game_snapshots/21713901/current_live

- snapshot_type: `current_live`  lineup_confirmed: **False**
- row_count: 32
- bucket_counts: {'EDGE_10_20': 18, 'EDGE_20_30': 6, 'EDGE_LT_10': 8}
- publish_status_counts: {'WATCHLIST_NOT_CONFIRMED_LINEUP': 25, 'REVIEW_LARGE_EDGE': 6, 'PUBLISH_BLOCKER': 1}
- ⚠️ top 20 edges UNDER-skewed share=100%

### Top 25 largest edges (by |raw_edge|)

| player | stat | side | line | model | model_re | market | market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | push? | push_p | p0 | mean | bucket | publish_status | root_cause | calc_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Karl-Anthony Towns | reb | UNDER | 11.5 | 0.710 | 0.711 | 0.470 | 0.470 | +0.239 | +0.240 | +0.455 | +0.457 | +0.456 | False | 0.000 | 0.015 | 9.27 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Evan Mobley | reb | UNDER | 8.5 | 0.746 | 0.747 | 0.522 | 0.522 | +0.224 | +0.225 | +0.367 | +0.370 | +0.369 | False | 0.000 | 0.021 | 6.50 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Jalen Brunson | fg3m | UNDER | 2.5 | 0.747 | 0.747 | 0.525 | 0.525 | +0.222 | +0.222 | +0.385 | +0.385 | +0.385 | False | 0.000 | 0.146 | 1.79 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| James Harden | ast | UNDER | 6.5 | 0.764 | 0.765 | 0.562 | 0.562 | +0.202 | +0.203 | +0.298 | +0.301 | +0.300 | False | 0.000 | 0.048 | 4.62 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Jarrett Allen | stl | UNDER | 0.5 | 0.607 | 0.607 | 0.406 | 0.406 | +0.201 | +0.201 | +0.444 | +0.445 | +0.445 | False | 0.000 | 0.607 | 0.61 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Jarrett Allen | reb | UNDER | 7.5 | 0.658 | 0.659 | 0.457 | 0.457 | +0.201 | +0.201 | +0.381 | +0.383 | +0.382 | False | 0.000 | 0.032 | 6.48 | EDGE_20_30 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | yes |
| Evan Mobley | ast | UNDER | 3.5 | 0.667 | 0.669 | 0.486 | 0.486 | +0.182 | +0.183 | +0.322 | +0.324 | +0.324 | False | 0.000 | 0.124 | 2.82 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Max Strus | fg3m | UNDER | 2.5 | 0.750 | 0.750 | 0.572 | 0.572 | +0.177 | +0.178 | +0.250 | +0.250 | +0.250 | False | 0.000 | 0.154 | 1.80 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Donovan Mitchell | pts | UNDER | 26.5 | 0.648 | 0.652 | 0.478 | 0.478 | +0.170 | +0.173 | +0.296 | +0.303 | +0.302 | False | 0.000 | 0.006 | 23.13 | EDGE_10_20 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | **NO** |
| Mikal Bridges | fg3m | UNDER | 1.5 | 0.727 | 0.727 | 0.560 | 0.560 | +0.167 | +0.167 | +0.286 | +0.286 | +0.286 | False | 0.000 | 0.349 | 0.99 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| James Harden | blk | UNDER | 0.5 | 0.753 | 0.753 | 0.594 | 0.594 | +0.159 | +0.159 | +0.209 | +0.209 | +0.209 | False | 0.000 | 0.753 | 0.33 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Max Strus | stl | UNDER | 0.5 | 0.630 | 0.630 | 0.474 | 0.474 | +0.156 | +0.156 | +0.260 | +0.260 | +0.260 | False | 0.000 | 0.630 | 0.59 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Mikal Bridges | blk | UNDER | 0.5 | 0.718 | 0.718 | 0.565 | 0.565 | +0.153 | +0.153 | +0.242 | +0.243 | +0.243 | False | 0.000 | 0.718 | 0.39 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Max Strus | pts | UNDER | 9.5 | 0.625 | 0.628 | 0.478 | 0.478 | +0.147 | +0.149 | +0.251 | +0.255 | +0.254 | False | 0.000 | 0.043 | 8.30 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Donovan Mitchell | reb | UNDER | 4.5 | 0.651 | 0.652 | 0.517 | 0.517 | +0.135 | +0.136 | +0.243 | +0.245 | +0.245 | False | 0.000 | 0.067 | 3.82 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | pts | UNDER | 17.5 | 0.621 | 0.623 | 0.493 | 0.493 | +0.128 | +0.129 | +0.217 | +0.221 | +0.221 | False | 0.000 | 0.010 | 15.56 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| James Harden | reb | UNDER | 4.5 | 0.586 | 0.587 | 0.460 | 0.460 | +0.127 | +0.127 | +0.219 | +0.220 | +0.220 | False | 0.000 | 0.053 | 4.16 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Donovan Mitchell | ast | UNDER | 4.5 | 0.718 | 0.719 | 0.594 | 0.593 | +0.124 | +0.126 | +0.156 | +0.158 | +0.157 | False | 0.000 | 0.090 | 3.35 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Josh Hart | reb | UNDER | 7.5 | 0.654 | 0.655 | 0.534 | 0.534 | +0.120 | +0.121 | +0.177 | +0.179 | +0.179 | False | 0.000 | 0.024 | 6.34 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Donovan Mitchell | blk | UNDER | 0.5 | 0.844 | 0.848 | 0.724 | 0.724 | +0.120 | +0.124 | +0.103 | +0.108 | +0.108 | False | 0.000 | 0.844 | 0.17 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Karl-Anthony Towns | stl | OVER | 0.5 | 0.736 | 0.736 | 0.626 | 0.626 | +0.110 | +0.110 | +0.123 | +0.123 | +0.123 | False | 0.000 | 0.264 | 1.37 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Evan Mobley | pts | UNDER | 16.5 | 0.615 | 0.617 | 0.506 | 0.506 | +0.109 | +0.111 | +0.178 | +0.183 | +0.182 | False | 0.000 | 0.012 | 14.72 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Max Strus | reb | UNDER | 4.5 | 0.608 | 0.609 | 0.504 | 0.504 | +0.105 | +0.105 | +0.199 | +0.201 | +0.200 | False | 0.000 | 0.072 | 4.10 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| James Harden | fg3m | UNDER | 2.5 | 0.666 | 0.666 | 0.564 | 0.564 | +0.102 | +0.102 | +0.160 | +0.160 | +0.160 | False | 0.000 | 0.124 | 2.01 | EDGE_10_20 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |
| Jarrett Allen | blk | UNDER | 1.5 | 0.746 | 0.746 | 0.651 | 0.651 | +0.095 | +0.095 | +0.139 | +0.139 | +0.139 | False | 0.000 | 0.408 | 1.07 | EDGE_LT_10 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | yes |

