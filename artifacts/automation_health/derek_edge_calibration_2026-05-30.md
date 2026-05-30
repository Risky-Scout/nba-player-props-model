# Derek edge calibration audit — 2026-05-30

- high-edge rows audited: **27**
- scoring corpus: **11096 rows** across 13 delivery dates
- thin/limited buckets: **12**
- review-required buckets: **0**
- supported buckets: **15**

## Per-row calibration support

| player | stat | side | line | edge_bucket | n | model_ll | market_ll | Δll | calibration_status |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| Isaiah Joe | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| De'Aaron Fox | reb | OVER | 4.5 | EDGE_10_20 | 382 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Jaylin Williams | stl | UNDER | 0.5 | EDGE_10_20 | 82 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Stephon Castle | fg3m | OVER | 1.5 | EDGE_10_20 | 283 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Luguentz Dort | fg3m | UNDER | 1.5 | EDGE_10_20 | 283 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Luguentz Dort | stl | UNDER | 0.5 | EDGE_10_20 | 82 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Shai Gilgeous-Alexander | pts | UNDER | 30.5 | EDGE_20_30 | 285 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Shai Gilgeous-Alexander | fg3m | UNDER | 1.5 | EDGE_10_20 | 283 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Shai Gilgeous-Alexander | blk | UNDER | 0.5 | EDGE_20_30 | 19 | nan | nan | +nan | **CALIBRATION_SAMPLE_THIN** |
| Keldon Johnson | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | pts | UNDER | 26.5 | EDGE_10_20 | 994 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | reb | UNDER | 12.5 | EDGE_10_20 | 30 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | ast | UNDER | 3.5 | EDGE_10_20 | 207 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | blk | UNDER | 3.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Cason Wallace | reb | UNDER | 3.5 | EDGE_10_20 | 382 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Cason Wallace | ast | UNDER | 2.5 | EDGE_10_20 | 136 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Cason Wallace | fg3m | UNDER | 1.5 | EDGE_10_20 | 283 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Isaiah Hartenstein | reb | UNDER | 8.5 | EDGE_10_20 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Isaiah Hartenstein | blk | UNDER | 0.5 | EDGE_10_20 | 76 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Alex Caruso | pts | UNDER | 10.5 | EDGE_20_30 | 61 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Alex Caruso | reb | UNDER | 3.5 | EDGE_20_30 | 221 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Alex Caruso | ast | UNDER | 2.5 | EDGE_10_20 | 136 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Alex Caruso | fg3m | UNDER | 1.5 | EDGE_20_30 | 196 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Alex Caruso | blk | UNDER | 0.5 | EDGE_10_20 | 76 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Kenrich Williams | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Jared McCain | pts | UNDER | 13.5 | EDGE_20_30 | 285 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Julian Champagnie | blk | OVER | 0.5 | EDGE_20_30 | 19 | nan | nan | +nan | **CALIBRATION_SAMPLE_THIN** |

## Stat-level model-vs-market summary (historical corpus)

| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast/OVER | 1498 | nan | nan | +nan | nan | nan | +nan |
| ast/UNDER | 1498 | nan | nan | +nan | nan | nan | +nan |
| blk/OVER | 203 | nan | nan | +nan | nan | nan | +nan |
| blk/UNDER | 203 | nan | nan | +nan | nan | nan | +nan |
| fg3m/OVER | 1501 | nan | nan | +nan | nan | nan | +nan |
| fg3m/UNDER | 1501 | nan | nan | +nan | nan | nan | +nan |
| pa/OVER | 565 | nan | nan | +nan | nan | nan | +nan |
| pa/UNDER | 565 | nan | nan | +nan | nan | nan | +nan |
| pr/OVER | 683 | nan | nan | +nan | nan | nan | +nan |
| pr/UNDER | 683 | nan | nan | +nan | nan | nan | +nan |
| pra/OVER | 693 | nan | nan | +nan | nan | nan | +nan |
| pra/UNDER | 693 | nan | nan | +nan | nan | nan | +nan |
| pts/OVER | 3026 | nan | nan | +nan | nan | nan | +nan |
| pts/UNDER | 3026 | nan | nan | +nan | nan | nan | +nan |
| ra/OVER | 375 | nan | nan | +nan | nan | nan | +nan |
| ra/UNDER | 375 | nan | nan | +nan | nan | nan | +nan |
| reb/OVER | 2210 | nan | nan | +nan | nan | nan | +nan |
| reb/UNDER | 2210 | nan | nan | +nan | nan | nan | +nan |
| stl/OVER | 235 | nan | nan | +nan | nan | nan | +nan |
| stl/UNDER | 235 | nan | nan | +nan | nan | nan | +nan |
| stocks/OVER | 106 | nan | nan | +nan | nan | nan | +nan |
| stocks/UNDER | 106 | nan | nan | +nan | nan | nan | +nan |
| tov/OVER | 1 | nan | nan | +nan | nan | nan | +nan |
| tov/UNDER | 1 | nan | nan | +nan | nan | nan | +nan |
