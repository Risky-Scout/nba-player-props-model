# Model Performance and Calibration — 2026-05-23

- champion_model_id: `challenger-2026-04-30`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 180
- mean NLL: 2.2561
- mean RPS: 0.0417
- mean abs error: 2.4827
- mean outcome_prob_assigned: 0.1972

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 15 | 1.7101 | 0.0311 | 1.0929 |
| blk | 15 | 0.7943 | 0.0290 | 0.5705 |
| fg3m | 15 | 1.3694 | 0.0368 | 0.9083 |
| pa | 15 | 3.0775 | 0.0296 | 4.3146 |
| pr | 15 | 3.2574 | 0.0337 | 5.2458 |
| pra | 15 | 3.3146 | 0.0312 | 5.5003 |
| pts | 15 | 3.1340 | 0.0350 | 4.1783 |
| ra | 15 | 2.5442 | 0.0334 | 2.5008 |
| reb | 15 | 2.2100 | 0.0405 | 1.8224 |
| stl | 15 | 1.8451 | 0.0741 | 1.0162 |
| stocks | 15 | 1.9245 | 0.0461 | 1.2307 |
| tov | 15 | 1.8920 | 0.0803 | 1.4111 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 12 | 1.7366 | 0.0248 | 2.9020 |
| core | 36 | 2.4255 | 0.0469 | 2.7514 |
| rotation | 48 | 1.9398 | 0.0290 | 2.3856 |
| starter | 84 | 2.4385 | 0.0492 | 2.3631 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

