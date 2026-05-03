# Model vs Market Realized Scoring — 2026-05-02

- rows_paired: 406 (rows_total=406)
- model_logloss: **0.8029**
- market_logloss: **0.6661**
- delta_logloss (model - market, lower is better): **+0.1368**
- model_brier: **0.2926**
- market_brier: **0.2370**
- delta_brier (model - market, lower is better): **+0.0555**

## By stat

| Group | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast | 44 | 0.9842 | 0.6258 | +0.3584 | 0.3865 | 0.2203 | +0.1662 |
| fg3m | 122 | 0.6221 | 0.7023 | -0.0802 | 0.2165 | 0.2525 | -0.0360 |
| pts | 114 | 0.7561 | 0.6245 | +0.1317 | 0.2757 | 0.2183 | +0.0574 |
| reb | 126 | 0.9569 | 0.6829 | +0.2741 | 0.3487 | 0.2449 | +0.1038 |

## By role bucket

| Group | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| starter | 367 | 0.7619 | 0.6671 | +0.0948 | 0.2799 | 0.2374 | +0.0425 |

## By edge bucket

| Group | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| near_zero | 45 | 0.6614 | 0.6661 | -0.0047 | 0.2356 | 0.2376 | -0.0020 |
| over | 42 | 0.6284 | 0.6756 | -0.0472 | 0.2157 | 0.2343 | -0.0186 |
| under | 48 | 0.7012 | 0.6916 | +0.0096 | 0.2544 | 0.2500 | +0.0044 |
| very_over | 59 | 0.5567 | 0.7430 | -0.1863 | 0.1853 | 0.2728 | -0.0875 |
| very_under | 212 | 0.9590 | 0.6371 | +0.3219 | 0.3584 | 0.2246 | +0.1338 |

## By book

| Group | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bovada | 58 | 0.8505 | 0.6685 | +0.1820 | 0.3106 | 0.2380 | +0.0725 |
| espnbet | 48 | 0.8812 | 0.6964 | +0.1848 | 0.3221 | 0.2501 | +0.0721 |
| fanduel | 114 | 0.6624 | 0.5976 | +0.0648 | 0.2353 | 0.2047 | +0.0306 |

