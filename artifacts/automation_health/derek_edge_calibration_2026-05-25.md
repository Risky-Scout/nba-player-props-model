# Derek edge calibration audit — 2026-05-25

- high-edge rows audited: **24**
- scoring corpus: **10461 rows** across 11 delivery dates
- thin/limited buckets: **8**
- review-required buckets: **0**
- supported buckets: **16**

## Per-row calibration support

| player | stat | side | line | edge_bucket | n | model_ll | market_ll | Δll | calibration_status |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| James Harden | reb | UNDER | 4.5 | EDGE_10_20 | 376 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| James Harden | ast | UNDER | 6.5 | EDGE_20_30 | 97 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| James Harden | fg3m | UNDER | 2.5 | EDGE_10_20 | 277 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| James Harden | blk | UNDER | 0.5 | EDGE_10_20 | 70 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Donovan Mitchell | pts | UNDER | 26.5 | EDGE_10_20 | 955 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Donovan Mitchell | reb | UNDER | 4.5 | EDGE_10_20 | 376 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Donovan Mitchell | ast | UNDER | 4.5 | EDGE_10_20 | 200 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Donovan Mitchell | blk | UNDER | 0.5 | EDGE_10_20 | 70 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Jalen Brunson | fg3m | UNDER | 2.5 | EDGE_20_30 | 174 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | reb | UNDER | 7.5 | EDGE_10_20 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Jarrett Allen | reb | UNDER | 7.5 | EDGE_20_30 | 121 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Jarrett Allen | stl | UNDER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Evan Mobley | pts | UNDER | 16.5 | EDGE_10_20 | 955 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Evan Mobley | reb | UNDER | 8.5 | EDGE_20_30 | 121 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Evan Mobley | ast | UNDER | 3.5 | EDGE_10_20 | 200 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Max Strus | pts | UNDER | 9.5 | EDGE_10_20 | 205 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Max Strus | reb | UNDER | 4.5 | EDGE_10_20 | 376 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Max Strus | fg3m | UNDER | 2.5 | EDGE_10_20 | 277 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Max Strus | stl | UNDER | 0.5 | EDGE_10_20 | 74 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Mikal Bridges | fg3m | UNDER | 1.5 | EDGE_10_20 | 277 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Mikal Bridges | blk | UNDER | 0.5 | EDGE_10_20 | 70 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Karl-Anthony Towns | pts | UNDER | 17.5 | EDGE_10_20 | 955 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Karl-Anthony Towns | reb | UNDER | 11.5 | EDGE_20_30 | 53 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Karl-Anthony Towns | stl | OVER | 0.5 | EDGE_10_20 | 74 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |

## Stat-level model-vs-market summary (historical corpus)

| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast/OVER | 1421 | nan | nan | +nan | nan | nan | +nan |
| ast/UNDER | 1421 | nan | nan | +nan | nan | nan | +nan |
| blk/OVER | 179 | nan | nan | +nan | nan | nan | +nan |
| blk/UNDER | 179 | nan | nan | +nan | nan | nan | +nan |
| fg3m/OVER | 1429 | nan | nan | +nan | nan | nan | +nan |
| fg3m/UNDER | 1429 | nan | nan | +nan | nan | nan | +nan |
| pa/OVER | 480 | nan | nan | +nan | nan | nan | +nan |
| pa/UNDER | 480 | nan | nan | +nan | nan | nan | +nan |
| pr/OVER | 642 | nan | nan | +nan | nan | nan | +nan |
| pr/UNDER | 642 | nan | nan | +nan | nan | nan | +nan |
| pra/OVER | 640 | nan | nan | +nan | nan | nan | +nan |
| pra/UNDER | 640 | nan | nan | +nan | nan | nan | +nan |
| pts/OVER | 2888 | nan | nan | +nan | nan | nan | +nan |
| pts/UNDER | 2888 | nan | nan | +nan | nan | nan | +nan |
| ra/OVER | 349 | nan | nan | +nan | nan | nan | +nan |
| ra/UNDER | 349 | nan | nan | +nan | nan | nan | +nan |
| reb/OVER | 2140 | nan | nan | +nan | nan | nan | +nan |
| reb/UNDER | 2140 | nan | nan | +nan | nan | nan | +nan |
| stl/OVER | 204 | nan | nan | +nan | nan | nan | +nan |
| stl/UNDER | 204 | nan | nan | +nan | nan | nan | +nan |
| stocks/OVER | 88 | nan | nan | +nan | nan | nan | +nan |
| stocks/UNDER | 88 | nan | nan | +nan | nan | nan | +nan |
| tov/OVER | 1 | nan | nan | +nan | nan | nan | +nan |
| tov/UNDER | 1 | nan | nan | +nan | nan | nan | +nan |
