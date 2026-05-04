# Model vs Market Realized Scoring — 2026-05-03

- rows_paired: 489 (rows_total=489)
- model_logloss: **0.6400**
- market_logloss: **0.6541**
- delta_logloss (model - market, lower is better): **-0.0141**
- model_brier: **0.2273**
- market_brier: **0.2323**
- delta_brier (model - market, lower is better): **-0.0050**

## By stat

| Group | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ast | 64 | 0.5643 | 0.7018 | -0.1375 | 0.1925 | 0.2539 | -0.0614 |
| fg3m | 94 | 0.5864 | 0.6370 | -0.0506 | 0.2066 | 0.2248 | -0.0182 |
| pts | 212 | 0.6074 | 0.6454 | -0.0380 | 0.2115 | 0.2282 | -0.0167 |
| reb | 119 | 0.7812 | 0.6576 | +0.1236 | 0.2904 | 0.2338 | +0.0566 |

## By role bucket

| Group | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bench | 39 | 0.9617 | 0.6534 | +0.3082 | 0.3793 | 0.2303 | +0.1490 |
| rotation | 214 | 0.6678 | 0.6818 | -0.0141 | 0.2387 | 0.2451 | -0.0064 |
| starter | 236 | 0.5617 | 0.6291 | -0.0674 | 0.1918 | 0.2210 | -0.0292 |

## By edge bucket

| Group | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| very_over | 41 | 0.9022 | 0.6249 | +0.2773 | 0.3506 | 0.2169 | +0.1336 |
| very_under | 413 | 0.6063 | 0.6539 | -0.0476 | 0.2115 | 0.2324 | -0.0209 |

## By book

| Group | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bovada | 80 | 0.6658 | 0.6917 | -0.0258 | 0.2372 | 0.2491 | -0.0119 |
| espnbet | 60 | 0.6474 | 0.6370 | +0.0105 | 0.2303 | 0.2237 | +0.0065 |
| fanduel | 129 | 0.5114 | 0.5672 | -0.0557 | 0.1711 | 0.1928 | -0.0217 |

