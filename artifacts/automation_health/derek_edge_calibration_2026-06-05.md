# Derek edge calibration audit — 2026-06-05

- high-edge rows audited: **48**
- scoring corpus: **11426 rows** across 14 delivery dates
- thin/limited buckets: **19**
- review-required buckets: **0**
- supported buckets: **29**

## Per-row calibration support

| player | stat | side | line | edge_bucket | n | model_ll | market_ll | Δll | calibration_status |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| De'Aaron Fox | ast | UNDER | 5.5 | EDGE_10_20 | 219 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Landry Shamet | fg3m | UNDER | 1.5 | EDGE_10_20 | 283 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Luke Kornet | blk | UNDER | 0.5 | EDGE_10_20 | 77 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Jalen Brunson | stl | OVER | 0.5 | EDGE_10_20 | 83 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Josh Hart | reb | UNDER | 8.5 | EDGE_10_20 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | ast | UNDER | 4.5 | EDGE_10_20 | 219 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Stephon Castle | ast | UNDER | 6.5 | EDGE_20_30 | 97 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Devin Vassell | pts | UNDER | 12.5 | EDGE_10_20 | 1034 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | ast | UNDER | 2.5 | EDGE_10_20 | 148 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | blk | UNDER | 0.5 | EDGE_10_20 | 77 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Mitchell Robinson | blk | UNDER | 0.5 | EDGE_20_30 | 24 | nan | nan | +nan | **CALIBRATION_SAMPLE_THIN** |
| Julian Champagnie | pts | UNDER | 10.5 | EDGE_10_20 | 230 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Julian Champagnie | reb | UNDER | 5.5 | EDGE_10_20 | 400 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| OG Anunoby | fg3m | UNDER | 1.5 | EDGE_10_20 | 283 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| OG Anunoby | blk | UNDER | 0.5 | EDGE_10_20 | 77 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Dylan Harper | pts | UNDER | 12.5 | EDGE_10_20 | 1034 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | ast | UNDER | 3.5 | EDGE_10_20 | 219 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Keldon Johnson | reb | UNDER | 2.5 | EDGE_10_20 | 88 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Keldon Johnson | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | pts | UNDER | 27.5 | EDGE_20_30 | 296 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | reb | UNDER | 11.5 | EDGE_20_30 | 53 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | ast | UNDER | 3.5 | EDGE_20_30 | 161 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | stl | UNDER | 1.5 | EDGE_20_30 | 15 | nan | nan | +nan | **CALIBRATION_SAMPLE_THIN** |
| Karl-Anthony Towns | pts | UNDER | 16.5 | EDGE_10_20 | 1034 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Karl-Anthony Towns | stl | UNDER | 0.5 | EDGE_20_30 | 53 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Karl-Anthony Towns | blk | UNDER | 0.5 | EDGE_20_30 | 24 | nan | nan | +nan | **CALIBRATION_SAMPLE_THIN** |
| De'Aaron Fox | ast | UNDER | 5.5 | EDGE_10_20 | 219 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Landry Shamet | fg3m | UNDER | 1.5 | EDGE_10_20 | 283 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Jalen Brunson | fg3m | UNDER | 2.5 | EDGE_10_20 | 283 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Jalen Brunson | stl | OVER | 0.5 | EDGE_10_20 | 83 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Josh Hart | reb | UNDER | 8.5 | EDGE_10_20 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | ast | UNDER | 4.5 | EDGE_10_20 | 219 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Stephon Castle | ast | UNDER | 6.5 | EDGE_20_30 | 97 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Devin Vassell | pts | UNDER | 12.5 | EDGE_10_20 | 1034 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | ast | UNDER | 2.5 | EDGE_10_20 | 148 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Mitchell Robinson | blk | UNDER | 0.5 | EDGE_10_20 | 77 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Julian Champagnie | pts | UNDER | 10.5 | EDGE_10_20 | 230 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Julian Champagnie | reb | UNDER | 5.5 | EDGE_10_20 | 400 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Julian Champagnie | fg3m | UNDER | 2.5 | EDGE_10_20 | 283 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | pts | UNDER | 11.5 | EDGE_10_20 | 1034 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | ast | UNDER | 3.5 | EDGE_20_30 | 161 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Keldon Johnson | reb | UNDER | 2.5 | EDGE_10_20 | 88 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Keldon Johnson | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | pts | UNDER | 27.5 | EDGE_20_30 | 296 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | reb | UNDER | 11.5 | EDGE_20_30 | 53 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | ast | UNDER | 3.5 | EDGE_20_30 | 161 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | stl | UNDER | 1.5 | EDGE_10_20 | 62 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Karl-Anthony Towns | pts | UNDER | 16.5 | EDGE_10_20 | 1034 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |

## Stat-level model-vs-market summary (historical corpus)

| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast/OVER | 1534 | nan | nan | +nan | nan | nan | +nan |
| ast/UNDER | 1534 | nan | nan | +nan | nan | nan | +nan |
| blk/OVER | 215 | nan | nan | +nan | nan | nan | +nan |
| blk/UNDER | 215 | nan | nan | +nan | nan | nan | +nan |
| fg3m/OVER | 1538 | nan | nan | +nan | nan | nan | +nan |
| fg3m/UNDER | 1538 | nan | nan | +nan | nan | nan | +nan |
| pa/OVER | 610 | nan | nan | +nan | nan | nan | +nan |
| pa/UNDER | 610 | nan | nan | +nan | nan | nan | +nan |
| pr/OVER | 704 | nan | nan | +nan | nan | nan | +nan |
| pr/UNDER | 704 | nan | nan | +nan | nan | nan | +nan |
| pra/OVER | 722 | nan | nan | +nan | nan | nan | +nan |
| pra/UNDER | 722 | nan | nan | +nan | nan | nan | +nan |
| pts/OVER | 3094 | nan | nan | +nan | nan | nan | +nan |
| pts/UNDER | 3094 | nan | nan | +nan | nan | nan | +nan |
| ra/OVER | 391 | nan | nan | +nan | nan | nan | +nan |
| ra/UNDER | 391 | nan | nan | +nan | nan | nan | +nan |
| reb/OVER | 2251 | nan | nan | +nan | nan | nan | +nan |
| reb/UNDER | 2251 | nan | nan | +nan | nan | nan | +nan |
| stl/OVER | 251 | nan | nan | +nan | nan | nan | +nan |
| stl/UNDER | 251 | nan | nan | +nan | nan | nan | +nan |
| stocks/OVER | 115 | nan | nan | +nan | nan | nan | +nan |
| stocks/UNDER | 115 | nan | nan | +nan | nan | nan | +nan |
| tov/OVER | 1 | nan | nan | +nan | nan | nan | +nan |
| tov/UNDER | 1 | nan | nan | +nan | nan | nan | +nan |
