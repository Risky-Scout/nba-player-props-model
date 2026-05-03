# Derek edge calibration audit — 2026-05-03

- high-edge rows audited: **50**
- scoring corpus: **2873 rows** across 3 delivery dates
- thin/limited buckets: **31**
- review-required buckets: **1**
- supported buckets: **18**

## Per-row calibration support

| player | stat | side | line | edge_bucket | n | model_ll | market_ll | Δll | calibration_status |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| James Harden | ast | UNDER | 6.5 | EDGE_10_20 | 115 | 0.633 | 0.585 | +0.048 | **CALIBRATION_SUPPORTED** |
| James Harden | fg3m | UNDER | 2.5 | EDGE_10_20 | 78 | 0.644 | 0.690 | -0.046 | **CALIBRATION_SAMPLE_LIMITED** |
| James Harden | stl | UNDER | 1.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| James Harden | blk | UNDER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Donovan Mitchell | pts | UNDER | 25.5 | EDGE_10_20 | 383 | 0.698 | 0.655 | +0.043 | **CALIBRATION_SUPPORTED** |
| Donovan Mitchell | reb | OVER | 4.5 | EDGE_10_20 | 156 | 0.651 | 0.691 | -0.040 | **CALIBRATION_SUPPORTED** |
| Donovan Mitchell | fg3m | UNDER | 2.5 | EDGE_20_30 | 69 | 0.571 | 0.712 | -0.141 | **CALIBRATION_SAMPLE_LIMITED** |
| Donovan Mitchell | stl | UNDER | 1.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Sam Merrill | stl | UNDER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Brandon Ingram | reb | OVER | 4.5 | EDGE_10_20 | 156 | 0.651 | 0.691 | -0.040 | **CALIBRATION_SUPPORTED** |
| Ja'Kobe Walter | reb | UNDER | 3.5 | EDGE_10_20 | 156 | 0.651 | 0.691 | -0.040 | **CALIBRATION_SUPPORTED** |
| Ja'Kobe Walter | fg3m | UNDER | 2.5 | EDGE_10_20 | 78 | 0.644 | 0.690 | -0.046 | **CALIBRATION_SAMPLE_LIMITED** |
| Ja'Kobe Walter | stl | UNDER | 1.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Jarrett Allen | blk | UNDER | 1.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Evan Mobley | pts | UNDER | 16.5 | EDGE_10_20 | 383 | 0.698 | 0.655 | +0.043 | **CALIBRATION_SUPPORTED** |
| Evan Mobley | blk | UNDER | 1.5 | EDGE_30_PLUS | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| RJ Barrett | pts | UNDER | 23.5 | EDGE_10_20 | 383 | 0.698 | 0.655 | +0.043 | **CALIBRATION_SUPPORTED** |
| RJ Barrett | reb | UNDER | 5.5 | EDGE_10_20 | 156 | 0.651 | 0.691 | -0.040 | **CALIBRATION_SUPPORTED** |
| RJ Barrett | ast | UNDER | 3.5 | EDGE_10_20 | 82 | 0.794 | 0.693 | +0.101 | **CALIBRATION_SAMPLE_LIMITED** |
| Collin Murray-Boyles | pts | UNDER | 12.5 | EDGE_20_30 | 157 | 0.736 | 0.703 | +0.033 | **CALIBRATION_SUPPORTED** |
| Scottie Barnes | pts | UNDER | 21.5 | EDGE_10_20 | 383 | 0.698 | 0.655 | +0.043 | **CALIBRATION_SUPPORTED** |
| Scottie Barnes | reb | UNDER | 6.5 | EDGE_10_20 | 147 | 0.798 | 0.646 | +0.152 | **CALIBRATION_REVIEW_REQUIRED** |
| Scottie Barnes | ast | UNDER | 7.5 | EDGE_20_30 | 62 | 0.685 | 0.647 | +0.039 | **CALIBRATION_SAMPLE_LIMITED** |
| Scottie Barnes | fg3m | UNDER | 1.0 | EDGE_20_30 | 7 | 1.685 | 0.943 | +0.742 | **CALIBRATION_SAMPLE_THIN** |
| Scottie Barnes | blk | UNDER | 1.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Dennis Schroder | fg3m | OVER | 0.5 | EDGE_10_20 | 11 | 0.883 | 0.941 | -0.059 | **CALIBRATION_SAMPLE_THIN** |
| Jamal Shead | pts | UNDER | 8.5 | EDGE_10_20 | 28 | 0.625 | 0.622 | +0.003 | **CALIBRATION_SAMPLE_THIN** |
| Jamal Shead | ast | UNDER | 5.5 | EDGE_20_30 | 67 | 0.541 | 0.702 | -0.161 | **CALIBRATION_SAMPLE_LIMITED** |
| Sandro Mamukelashvili | reb | OVER | 3.5 | EDGE_10_20 | 156 | 0.651 | 0.691 | -0.040 | **CALIBRATION_SUPPORTED** |
| Daniss Jenkins | ast | UNDER | 2.5 | EDGE_10_20 | 33 | 0.842 | 0.825 | +0.017 | **CALIBRATION_SAMPLE_LIMITED** |
| Daniss Jenkins | fg3m | OVER | 0.5 | EDGE_10_20 | 11 | 0.883 | 0.941 | -0.059 | **CALIBRATION_SAMPLE_THIN** |
| Daniss Jenkins | stl | UNDER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Ausar Thompson | blk | OVER | 1.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Anthony Black | pts | UNDER | 11.5 | EDGE_10_20 | 383 | 0.698 | 0.655 | +0.043 | **CALIBRATION_SUPPORTED** |
| Anthony Black | blk | UNDER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Isaiah Stewart | reb | OVER | 3.5 | EDGE_10_20 | 156 | 0.651 | 0.691 | -0.040 | **CALIBRATION_SUPPORTED** |
| Jamal Cain | reb | UNDER | 3.5 | EDGE_10_20 | 156 | 0.651 | 0.691 | -0.040 | **CALIBRATION_SUPPORTED** |
| Tobias Harris | pts | UNDER | 17.5 | EDGE_10_20 | 383 | 0.698 | 0.655 | +0.043 | **CALIBRATION_SUPPORTED** |
| Tobias Harris | stl | UNDER | 1.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Tobias Harris | blk | OVER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Jalen Suggs | ast | UNDER | 4.5 | EDGE_10_20 | 82 | 0.794 | 0.693 | +0.101 | **CALIBRATION_SAMPLE_LIMITED** |
| Jalen Suggs | blk | UNDER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Cade Cunningham | pts | UNDER | 28.5 | EDGE_10_20 | 383 | 0.698 | 0.655 | +0.043 | **CALIBRATION_SUPPORTED** |
| Cade Cunningham | reb | OVER | 5.5 | EDGE_10_20 | 156 | 0.651 | 0.691 | -0.040 | **CALIBRATION_SUPPORTED** |
| Cade Cunningham | ast | UNDER | 8.5 | EDGE_10_20 | 115 | 0.633 | 0.585 | +0.048 | **CALIBRATION_SUPPORTED** |
| Cade Cunningham | blk | OVER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |
| Duncan Robinson | fg3m | UNDER | 2.5 | EDGE_10_20 | 78 | 0.644 | 0.690 | -0.046 | **CALIBRATION_SAMPLE_LIMITED** |
| Desmond Bane | fg3m | UNDER | 2.5 | EDGE_10_20 | 78 | 0.644 | 0.690 | -0.046 | **CALIBRATION_SAMPLE_LIMITED** |
| Tristan Da Silva | reb | UNDER | 2.5 | EDGE_10_20 | 23 | 0.593 | 0.694 | -0.101 | **CALIBRATION_SAMPLE_THIN** |
| Jalen Duren | stl | UNDER | 0.5 | EDGE_10_20 | 0 | 0.000 | 0.000 | +0.000 | **CALIBRATION_SAMPLE_THIN** |

## Stat-level model-vs-market summary (historical corpus)

| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast/OVER | 496 | 0.647 | 0.669 | -0.021 | 0.230 | 0.238 | -0.008 |
| ast/UNDER | 496 | 0.647 | 0.669 | -0.021 | 0.230 | 0.238 | -0.008 |
| fg3m/OVER | 484 | 0.616 | 0.641 | -0.025 | 0.214 | 0.225 | -0.010 |
| fg3m/UNDER | 484 | 0.616 | 0.641 | -0.025 | 0.214 | 0.225 | -0.010 |
| pts/OVER | 1012 | 0.687 | 0.657 | +0.030 | 0.246 | 0.233 | +0.013 |
| pts/UNDER | 1012 | 0.687 | 0.657 | +0.030 | 0.246 | 0.233 | +0.013 |
| reb/OVER | 881 | 0.720 | 0.665 | +0.055 | 0.258 | 0.236 | +0.022 |
| reb/UNDER | 881 | 0.720 | 0.665 | +0.055 | 0.258 | 0.236 | +0.022 |
