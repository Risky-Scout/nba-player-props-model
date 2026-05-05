# Derek edge calibration audit — 2026-05-04

- high-edge rows audited: **23**
- scoring corpus: **3362 rows** across 4 delivery dates
- thin/limited buckets: **10**
- review-required buckets: **1**
- supported buckets: **12**

## Per-row calibration support

| player | stat | side | line | edge_bucket | n | model_ll | market_ll | Δll | calibration_status |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| De'Aaron Fox | reb | UNDER | 3.5 | EDGE_10_20 | 206 | 0.673 | 0.674 | -0.001 | **CALIBRATION_SUPPORTED** |
| Julius Randle | reb | UNDER | 6.5 | EDGE_10_20 | 181 | 0.805 | 0.658 | +0.147 | **CALIBRATION_REVIEW_REQUIRED** |
| Julius Randle | ast | UNDER | 4.5 | EDGE_10_20 | 86 | 0.799 | 0.715 | +0.084 | **CALIBRATION_SAMPLE_LIMITED** |
| Anthony Edwards | pts | UNDER | 24.5 | EDGE_10_20 | 501 | 0.661 | 0.644 | +0.017 | **CALIBRATION_SUPPORTED** |
| Anthony Edwards | reb | UNDER | 4.5 | EDGE_10_20 | 206 | 0.673 | 0.674 | -0.001 | **CALIBRATION_SUPPORTED** |
| Anthony Edwards | ast | UNDER | 3.5 | EDGE_10_20 | 86 | 0.799 | 0.715 | +0.084 | **CALIBRATION_SAMPLE_LIMITED** |
| Anthony Edwards | fg3m | UNDER | 3.5 | EDGE_10_20 | 31 | 0.200 | 0.394 | -0.194 | **CALIBRATION_SAMPLE_LIMITED** |
| Mike Conley | fg3m | OVER | 1.5 | EDGE_10_20 | 114 | 0.621 | 0.688 | -0.067 | **CALIBRATION_SUPPORTED** |
| Stephon Castle | reb | UNDER | 5.5 | EDGE_10_20 | 206 | 0.673 | 0.674 | -0.001 | **CALIBRATION_SUPPORTED** |
| Devin Vassell | blk | UNDER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Ayo Dosunmu | pts | UNDER | 17.5 | EDGE_10_20 | 501 | 0.661 | 0.644 | +0.017 | **CALIBRATION_SUPPORTED** |
| Ayo Dosunmu | ast | UNDER | 3.5 | EDGE_10_20 | 86 | 0.799 | 0.715 | +0.084 | **CALIBRATION_SAMPLE_LIMITED** |
| Ayo Dosunmu | blk | UNDER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Rudy Gobert | blk | UNDER | 1.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Julian Champagnie | reb | UNDER | 4.5 | EDGE_10_20 | 206 | 0.673 | 0.674 | -0.001 | **CALIBRATION_SUPPORTED** |
| Julian Champagnie | fg3m | UNDER | 1.5 | EDGE_10_20 | 114 | 0.621 | 0.688 | -0.067 | **CALIBRATION_SUPPORTED** |
| Naz Reid | pts | UNDER | 12.5 | EDGE_10_20 | 501 | 0.661 | 0.644 | +0.017 | **CALIBRATION_SUPPORTED** |
| Naz Reid | reb | UNDER | 5.5 | EDGE_10_20 | 206 | 0.673 | 0.674 | -0.001 | **CALIBRATION_SUPPORTED** |
| Dylan Harper | stl | OVER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Jaden McDaniels | pts | UNDER | 16.5 | EDGE_10_20 | 501 | 0.661 | 0.644 | +0.017 | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | pts | UNDER | 27.5 | EDGE_20_30 | 180 | 0.692 | 0.712 | -0.020 | **CALIBRATION_SUPPORTED** |
| Victor Wembanyama | reb | UNDER | 11.5 | EDGE_30_PLUS | 18 | 0.261 | 0.821 | -0.560 | **CALIBRATION_SAMPLE_THIN** |
| Victor Wembanyama | blk | UNDER | 3.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |

## Stat-level model-vs-market summary (historical corpus)

| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast/OVER | 560 | 0.638 | 0.672 | -0.035 | 0.226 | 0.240 | -0.014 |
| ast/UNDER | 560 | 0.638 | 0.672 | -0.035 | 0.226 | 0.240 | -0.014 |
| fg3m/OVER | 578 | 0.611 | 0.640 | -0.029 | 0.213 | 0.225 | -0.012 |
| fg3m/UNDER | 578 | 0.611 | 0.640 | -0.029 | 0.213 | 0.225 | -0.012 |
| pts/OVER | 1224 | 0.673 | 0.655 | +0.019 | 0.240 | 0.232 | +0.008 |
| pts/UNDER | 1224 | 0.673 | 0.655 | +0.019 | 0.240 | 0.232 | +0.008 |
| reb/OVER | 1000 | 0.727 | 0.664 | +0.063 | 0.262 | 0.236 | +0.026 |
| reb/UNDER | 1000 | 0.727 | 0.664 | +0.063 | 0.262 | 0.236 | +0.026 |
