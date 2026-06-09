# Derek edge calibration audit — 2026-06-08

- high-edge rows audited: **21**
- scoring corpus: **11797 rows** across 15 delivery dates
- thin/limited buckets: **6**
- review-required buckets: **0**
- supported buckets: **15**

## Per-row calibration support

| player | stat | side | line | edge_bucket | n | model_ll | market_ll | Δll | calibration_status |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| De'Aaron Fox | reb | OVER | 3.5 | EDGE_10_20 | 405 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| De'Aaron Fox | ast | UNDER | 5.5 | EDGE_10_20 | 219 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Landry Shamet | pts | UNDER | 8.5 | EDGE_10_20 | 237 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | reb | UNDER | 8.5 | EDGE_10_20 | 300 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | ast | UNDER | 4.5 | EDGE_10_20 | 219 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Stephon Castle | ast | UNDER | 6.5 | EDGE_10_20 | 193 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Stephon Castle | stl | OVER | 0.5 | EDGE_10_20 | 83 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Devin Vassell | pts | UNDER | 13.5 | EDGE_10_20 | 1061 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | ast | UNDER | 2.5 | EDGE_10_20 | 162 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Julian Champagnie | pts | UNDER | 10.5 | EDGE_10_20 | 237 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | pts | UNDER | 13.5 | EDGE_10_20 | 1061 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | ast | UNDER | 3.5 | EDGE_20_30 | 161 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Keldon Johnson | reb | UNDER | 2.5 | EDGE_10_20 | 89 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Keldon Johnson | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Mikal Bridges | fg3m | UNDER | 1.5 | EDGE_10_20 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | pts | UNDER | 27.5 | EDGE_20_30 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | reb | UNDER | 11.5 | EDGE_20_30 | 53 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | ast | UNDER | 3.5 | EDGE_10_20 | 219 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | blk | UNDER | 3.5 | EDGE_30_PLUS | 17 | nan | nan | +nan | **CALIBRATION_SAMPLE_THIN** |
| Karl-Anthony Towns | pts | UNDER | 17.5 | EDGE_10_20 | 1061 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Karl-Anthony Towns | stl | UNDER | 0.5 | EDGE_10_20 | 83 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |

## Stat-level model-vs-market summary (historical corpus)

| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast/OVER | 1568 | nan | nan | +nan | nan | nan | +nan |
| ast/UNDER | 1568 | nan | nan | +nan | nan | nan | +nan |
| blk/OVER | 230 | nan | nan | +nan | nan | nan | +nan |
| blk/UNDER | 230 | nan | nan | +nan | nan | nan | +nan |
| fg3m/OVER | 1575 | nan | nan | +nan | nan | nan | +nan |
| fg3m/UNDER | 1575 | nan | nan | +nan | nan | nan | +nan |
| pa/OVER | 658 | nan | nan | +nan | nan | nan | +nan |
| pa/UNDER | 658 | nan | nan | +nan | nan | nan | +nan |
| pr/OVER | 754 | nan | nan | +nan | nan | nan | +nan |
| pr/UNDER | 754 | nan | nan | +nan | nan | nan | +nan |
| pra/OVER | 755 | nan | nan | +nan | nan | nan | +nan |
| pra/UNDER | 755 | nan | nan | +nan | nan | nan | +nan |
| pts/OVER | 3164 | nan | nan | +nan | nan | nan | +nan |
| pts/UNDER | 3164 | nan | nan | +nan | nan | nan | +nan |
| ra/OVER | 408 | nan | nan | +nan | nan | nan | +nan |
| ra/UNDER | 408 | nan | nan | +nan | nan | nan | +nan |
| reb/OVER | 2294 | nan | nan | +nan | nan | nan | +nan |
| reb/UNDER | 2294 | nan | nan | +nan | nan | nan | +nan |
| stl/OVER | 267 | nan | nan | +nan | nan | nan | +nan |
| stl/UNDER | 267 | nan | nan | +nan | nan | nan | +nan |
| stocks/OVER | 123 | nan | nan | +nan | nan | nan | +nan |
| stocks/UNDER | 123 | nan | nan | +nan | nan | nan | +nan |
| tov/OVER | 1 | nan | nan | +nan | nan | nan | +nan |
| tov/UNDER | 1 | nan | nan | +nan | nan | nan | +nan |
