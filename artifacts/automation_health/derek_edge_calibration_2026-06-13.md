# Derek edge calibration audit — 2026-06-13

- high-edge rows audited: **60**
- scoring corpus: **12463 rows** across 17 delivery dates
- thin/limited buckets: **26**
- review-required buckets: **0**
- supported buckets: **34**

## Per-row calibration support

| player | stat | side | line | edge_bucket | n | model_ll | market_ll | Δll | calibration_status |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| De'Aaron Fox | reb | OVER | 3.5 | EDGE_10_20 | 443 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| De'Aaron Fox | stl | UNDER | 1.5 | EDGE_10_20 | 86 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Jose Alvarado | stl | UNDER | 0.5 | EDGE_20_30 | 66 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Landry Shamet | fg3m | OVER | 1.5 | EDGE_10_20 | 328 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Landry Shamet | stl | UNDER | 0.5 | EDGE_10_20 | 83 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Miles McBride | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Jalen Brunson | reb | OVER | 3.5 | EDGE_10_20 | 443 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | reb | UNDER | 8.5 | EDGE_10_20 | 300 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | ast | UNDER | 4.5 | EDGE_10_20 | 235 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | fg3m | OVER | 1.5 | EDGE_10_20 | 328 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | stl | UNDER | 1.5 | EDGE_10_20 | 86 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Stephon Castle | ast | UNDER | 6.5 | EDGE_10_20 | 197 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | pts | UNDER | 13.5 | EDGE_10_20 | 1071 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | fg3m | UNDER | 2.5 | EDGE_10_20 | 328 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Mitchell Robinson | blk | OVER | 0.5 | EDGE_10_20 | 97 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| OG Anunoby | pts | UNDER | 17.5 | EDGE_10_20 | 1071 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| OG Anunoby | fg3m | UNDER | 2.5 | EDGE_10_20 | 328 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| OG Anunoby | stl | UNDER | 1.5 | EDGE_10_20 | 86 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Dylan Harper | pts | UNDER | 14.5 | EDGE_20_30 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | reb | UNDER | 5.5 | EDGE_10_20 | 443 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | ast | UNDER | 3.5 | EDGE_10_20 | 235 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | blk | UNDER | 0.5 | EDGE_10_20 | 97 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Keldon Johnson | reb | UNDER | 2.5 | EDGE_10_20 | 90 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Keldon Johnson | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | pts | UNDER | 28.5 | EDGE_20_30 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | reb | UNDER | 11.5 | EDGE_20_30 | 53 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | ast | UNDER | 3.5 | EDGE_10_20 | 235 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | stl | UNDER | 1.5 | EDGE_10_20 | 86 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | blk | UNDER | 3.5 | EDGE_30_PLUS | 17 | nan | nan | +nan | **CALIBRATION_SAMPLE_THIN** |
| Karl-Anthony Towns | pts | UNDER | 16.5 | EDGE_10_20 | 1071 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Karl-Anthony Towns | reb | UNDER | 11.5 | EDGE_10_20 | 30 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| De'Aaron Fox | reb | OVER | 3.5 | EDGE_10_20 | 443 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| De'Aaron Fox | stl | UNDER | 1.5 | EDGE_10_20 | 86 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Jose Alvarado | stl | UNDER | 0.5 | EDGE_20_30 | 66 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Landry Shamet | fg3m | OVER | 1.5 | EDGE_10_20 | 328 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Miles McBride | fg3m | OVER | 0.5 | EDGE_20_30 | 48 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Jalen Brunson | reb | OVER | 3.5 | EDGE_10_20 | 443 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | reb | UNDER | 8.5 | EDGE_10_20 | 300 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | ast | UNDER | 4.5 | EDGE_10_20 | 235 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | fg3m | OVER | 1.5 | EDGE_10_20 | 328 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Josh Hart | stl | UNDER | 1.5 | EDGE_10_20 | 86 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Stephon Castle | ast | UNDER | 6.5 | EDGE_10_20 | 197 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | pts | UNDER | 13.5 | EDGE_10_20 | 1071 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Devin Vassell | fg3m | UNDER | 2.5 | EDGE_10_20 | 328 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Mitchell Robinson | blk | OVER | 0.5 | EDGE_10_20 | 97 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| OG Anunoby | pts | UNDER | 17.5 | EDGE_10_20 | 1071 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| OG Anunoby | fg3m | UNDER | 2.5 | EDGE_10_20 | 328 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| OG Anunoby | stl | UNDER | 1.5 | EDGE_10_20 | 86 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Dylan Harper | pts | UNDER | 15.5 | EDGE_20_30 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | reb | UNDER | 5.5 | EDGE_10_20 | 443 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | ast | UNDER | 3.5 | EDGE_10_20 | 235 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Dylan Harper | blk | UNDER | 0.5 | EDGE_10_20 | 97 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Keldon Johnson | fg3m | OVER | 0.5 | EDGE_30_PLUS | 30 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | pts | UNDER | 28.5 | EDGE_20_30 | 297 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | reb | UNDER | 11.5 | EDGE_20_30 | 53 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | ast | UNDER | 3.5 | EDGE_10_20 | 235 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | stl | UNDER | 1.5 | EDGE_10_20 | 86 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |
| Victor Wembanyama | blk | UNDER | 3.5 | EDGE_30_PLUS | 17 | nan | nan | +nan | **CALIBRATION_SAMPLE_THIN** |
| Karl-Anthony Towns | pts | UNDER | 16.5 | EDGE_10_20 | 1071 | nan | nan | +nan | **CALIBRATION_SUPPORTED** |
| Karl-Anthony Towns | reb | UNDER | 11.5 | EDGE_10_20 | 30 | nan | nan | +nan | **CALIBRATION_SAMPLE_LIMITED** |

## Stat-level model-vs-market summary (historical corpus)

| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast/OVER | 1634 | nan | nan | +nan | nan | nan | +nan |
| ast/UNDER | 1634 | nan | nan | +nan | nan | nan | +nan |
| blk/OVER | 259 | nan | nan | +nan | nan | nan | +nan |
| blk/UNDER | 259 | nan | nan | +nan | nan | nan | +nan |
| fg3m/OVER | 1643 | nan | nan | +nan | nan | nan | +nan |
| fg3m/UNDER | 1643 | nan | nan | +nan | nan | nan | +nan |
| pa/OVER | 745 | nan | nan | +nan | nan | nan | +nan |
| pa/UNDER | 745 | nan | nan | +nan | nan | nan | +nan |
| pr/OVER | 805 | nan | nan | +nan | nan | nan | +nan |
| pr/UNDER | 805 | nan | nan | +nan | nan | nan | +nan |
| pra/OVER | 821 | nan | nan | +nan | nan | nan | +nan |
| pra/UNDER | 821 | nan | nan | +nan | nan | nan | +nan |
| pts/OVER | 3315 | nan | nan | +nan | nan | nan | +nan |
| pts/UNDER | 3315 | nan | nan | +nan | nan | nan | +nan |
| ra/OVER | 436 | nan | nan | +nan | nan | nan | +nan |
| ra/UNDER | 436 | nan | nan | +nan | nan | nan | +nan |
| reb/OVER | 2365 | nan | nan | +nan | nan | nan | +nan |
| reb/UNDER | 2365 | nan | nan | +nan | nan | nan | +nan |
| stl/OVER | 300 | nan | nan | +nan | nan | nan | +nan |
| stl/UNDER | 300 | nan | nan | +nan | nan | nan | +nan |
| stocks/OVER | 139 | nan | nan | +nan | nan | nan | +nan |
| stocks/UNDER | 139 | nan | nan | +nan | nan | nan | +nan |
| tov/OVER | 1 | nan | nan | +nan | nan | nan | +nan |
| tov/UNDER | 1 | nan | nan | +nan | nan | nan | +nan |
