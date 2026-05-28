# Derek edge calibration audit — 2026-05-28

- high-edge rows audited: **20**
- scoring corpus: **10760 rows** across 12 delivery dates
- thin/limited buckets: **7**
- review-required buckets: **0**
- supported buckets: **13**

## Per-row calibration support

| player | stat | side | line | edge_bucket | n | model_ll | market_ll | Δll | calibration_status |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| Jalen Williams | reb | OVER | 3.5 | EDGE_10_20 | 378 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Jalen Williams | ast | OVER | 3.5 | EDGE_10_20 | 202 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Cason Wallace | ast | UNDER | 2.5 | EDGE_10_20 | 136 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Cason Wallace | fg3m | UNDER | 1.5 | EDGE_10_20 | 280 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Jared McCain | pts | UNDER | 13.5 | EDGE_10_20 | 957 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Stephon Castle | ast | UNDER | 6.5 | EDGE_10_20 | 191 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | fg3m | UNDER | 2.5 | EDGE_10_20 | 280 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | stl | OVER | 1.0 | EDGE_10_20 | 82 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Shai Gilgeous-Alexander | pts | UNDER | 29.5 | EDGE_10_20 | 957 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Shai Gilgeous-Alexander | fg3m | UNDER | 1.5 | EDGE_10_20 | 280 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Luguentz Dort | fg3m | UNDER | 1.5 | EDGE_10_20 | 280 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Chet Holmgren | blk | UNDER | 1.5 | EDGE_10_20 | 2 | nan | nan | +nan | **CALIBRATION_SAMPLE_THIN** |
| Dylan Harper | ast | UNDER | 2.5 | EDGE_10_20 | 136 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | stl | OVER | 0.5 | EDGE_10_20 | 82 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Alex Caruso | pts | UNDER | 10.5 | EDGE_10_20 | 208 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Alex Caruso | blk | UNDER | 0.5 | EDGE_10_20 | 76 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Keldon Johnson | fg3m | OVER | 0.5 | EDGE_10_20 | 44 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | pts | UNDER | 27.5 | EDGE_20_30 | 285 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | reb | UNDER | 12.5 | EDGE_10_20 | 30 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | blk | UNDER | 3.5 | EDGE_20_30 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |

## Stat-level model-vs-market summary (historical corpus)

| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast/OVER | 1457 | nan | nan | +nan | nan | nan | +nan |
| ast/UNDER | 1457 | nan | nan | +nan | nan | nan | +nan |
| blk/OVER | 191 | nan | nan | +nan | nan | nan | +nan |
| blk/UNDER | 191 | nan | nan | +nan | nan | nan | +nan |
| fg3m/OVER | 1465 | nan | nan | +nan | nan | nan | +nan |
| fg3m/UNDER | 1465 | nan | nan | +nan | nan | nan | +nan |
| pa/OVER | 516 | nan | nan | +nan | nan | nan | +nan |
| pa/UNDER | 516 | nan | nan | +nan | nan | nan | +nan |
| pr/OVER | 662 | nan | nan | +nan | nan | nan | +nan |
| pr/UNDER | 662 | nan | nan | +nan | nan | nan | +nan |
| pra/OVER | 664 | nan | nan | +nan | nan | nan | +nan |
| pra/UNDER | 664 | nan | nan | +nan | nan | nan | +nan |
| pts/OVER | 2956 | nan | nan | +nan | nan | nan | +nan |
| pts/UNDER | 2956 | nan | nan | +nan | nan | nan | +nan |
| ra/OVER | 359 | nan | nan | +nan | nan | nan | +nan |
| ra/UNDER | 359 | nan | nan | +nan | nan | nan | +nan |
| reb/OVER | 2172 | nan | nan | +nan | nan | nan | +nan |
| reb/UNDER | 2172 | nan | nan | +nan | nan | nan | +nan |
| stl/OVER | 220 | nan | nan | +nan | nan | nan | +nan |
| stl/UNDER | 220 | nan | nan | +nan | nan | nan | +nan |
| stocks/OVER | 97 | nan | nan | +nan | nan | nan | +nan |
| stocks/UNDER | 97 | nan | nan | +nan | nan | nan | +nan |
| tov/OVER | 1 | nan | nan | +nan | nan | nan | +nan |
| tov/UNDER | 1 | nan | nan | +nan | nan | nan | +nan |
