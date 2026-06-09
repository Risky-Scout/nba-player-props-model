# Model Performance and Calibration — 2026-06-08

- champion_model_id: `challenger-2026-06-06`
- trained_through_date: `2026-06-06`
- calibrated_through_date: `2026-06-06`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 144
- mean NLL: 2.2942
- mean RPS: 0.0797
- mean abs error: 2.6370
- mean outcome_prob_assigned: 0.1896

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 12 | 2.4223 | 0.0717 | 1.7340 |
| blk | 12 | 1.3317 | 0.1517 | 0.8344 |
| fg3m | 12 | 1.5213 | 0.1620 | 0.9145 |
| pa | 12 | 3.3439 | 0.0490 | 5.4490 |
| pr | 12 | 3.1727 | 0.0409 | 5.2664 |
| pra | 12 | 3.3324 | 0.0426 | 5.8160 |
| pts | 12 | 3.1709 | 0.0533 | 4.6219 |
| ra | 12 | 2.4505 | 0.0457 | 2.2768 |
| reb | 12 | 2.1704 | 0.0492 | 1.7211 |
| stl | 12 | 1.2315 | 0.1139 | 0.7861 |
| stocks | 12 | 1.7616 | 0.1140 | 1.3091 |
| tov | 12 | 1.6207 | 0.0627 | 0.9151 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 12 | 1.6655 | 0.0341 | 0.8704 |
| core | 24 | 2.0246 | 0.0662 | 2.2523 |
| rotation | 12 | 2.0206 | 0.0662 | 2.1165 |
| starter | 96 | 2.4743 | 0.0905 | 3.0191 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

