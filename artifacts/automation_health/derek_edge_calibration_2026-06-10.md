# Derek edge calibration audit — 2026-06-10

- high-edge rows audited: **19**
- scoring corpus: **12137 rows** across 16 delivery dates
- thin/limited buckets: **7**
- review-required buckets: **0**
- supported buckets: **12**

## Per-row calibration support

| player | stat | side | line | edge_bucket | n | model_ll | market_ll | Δll | calibration_status |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| Mitchell Robinson | stl | UNDER | 0.5 | EDGE_10_20 | 83 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| OG Anunoby | stl | UNDER | 1.5 | EDGE_10_20 | 85 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| De'Aaron Fox | reb | OVER | 3.5 | EDGE_10_20 | 421 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Stephon Castle | ast | UNDER | 6.5 | EDGE_10_20 | 197 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | pts | UNDER | 13.5 | EDGE_10_20 | 1061 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | reb | UNDER | 5.5 | EDGE_10_20 | 421 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | ast | UNDER | 3.5 | EDGE_10_20 | 235 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Keldon Johnson | reb | UNDER | 2.5 | EDGE_10_20 | 90 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Keldon Johnson | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Keldon Johnson | stl | UNDER | 0.5 | EDGE_10_20 | 83 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Mikal Bridges | fg3m | UNDER | 1.5 | EDGE_10_20 | 313 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | pts | UNDER | 27.5 | EDGE_20_30 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | reb | UNDER | 11.5 | EDGE_20_30 | 53 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | ast | UNDER | 3.5 | EDGE_10_20 | 235 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Karl-Anthony Towns | pts | UNDER | 17.5 | EDGE_10_20 | 1061 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Jalen Brunson | fg3m | UNDER | 2.5 | EDGE_10_20 | 313 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | reb | UNDER | 8.5 | EDGE_10_20 | 300 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Miles McBride | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Devin Vassell | pts | UNDER | 12.5 | EDGE_10_20 | 1061 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |

## Stat-level model-vs-market summary (historical corpus)

| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast/OVER | 1605 | nan | nan | +nan | nan | nan | +nan |
| ast/UNDER | 1605 | nan | nan | +nan | nan | nan | +nan |
| blk/OVER | 243 | nan | nan | +nan | nan | nan | +nan |
| blk/UNDER | 243 | nan | nan | +nan | nan | nan | +nan |
| fg3m/OVER | 1609 | nan | nan | +nan | nan | nan | +nan |
| fg3m/UNDER | 1609 | nan | nan | +nan | nan | nan | +nan |
| pa/OVER | 711 | nan | nan | +nan | nan | nan | +nan |
| pa/UNDER | 711 | nan | nan | +nan | nan | nan | +nan |
| pr/OVER | 778 | nan | nan | +nan | nan | nan | +nan |
| pr/UNDER | 778 | nan | nan | +nan | nan | nan | +nan |
| pra/OVER | 786 | nan | nan | +nan | nan | nan | +nan |
| pra/UNDER | 786 | nan | nan | +nan | nan | nan | +nan |
| pts/OVER | 3242 | nan | nan | +nan | nan | nan | +nan |
| pts/UNDER | 3242 | nan | nan | +nan | nan | nan | +nan |
| ra/OVER | 425 | nan | nan | +nan | nan | nan | +nan |
| ra/UNDER | 425 | nan | nan | +nan | nan | nan | +nan |
| reb/OVER | 2326 | nan | nan | +nan | nan | nan | +nan |
| reb/UNDER | 2326 | nan | nan | +nan | nan | nan | +nan |
| stl/OVER | 283 | nan | nan | +nan | nan | nan | +nan |
| stl/UNDER | 283 | nan | nan | +nan | nan | nan | +nan |
| stocks/OVER | 128 | nan | nan | +nan | nan | nan | +nan |
| stocks/UNDER | 128 | nan | nan | +nan | nan | nan | +nan |
| tov/OVER | 1 | nan | nan | +nan | nan | nan | +nan |
| tov/UNDER | 1 | nan | nan | +nan | nan | nan | +nan |
