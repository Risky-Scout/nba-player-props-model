# Model Performance and Calibration — 2026-05-18

- champion_model_id: `sim-2099-12-31`
- trained_through_date: `2099-12-31`
- calibrated_through_date: `2099-12-31`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 168
- mean NLL: 3.5364
- mean RPS: 0.0772
- mean abs error: 4.4000
- mean outcome_prob_assigned: 0.1559

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 14 | 2.1728 | 0.0520 | 1.7711 |
| blk | 14 | 1.6690 | 0.0663 | 0.8355 |
| fg3m | 14 | 5.2433 | 0.0703 | 1.3313 |
| pa | 14 | 3.9398 | 0.0619 | 7.7437 |
| pr | 14 | 4.6769 | 0.0794 | 10.2251 |
| pra | 14 | 4.7070 | 0.0695 | 10.4990 |
| pts | 14 | 3.9545 | 0.0738 | 7.5205 |
| ra | 14 | 4.3280 | 0.0755 | 4.8188 |
| reb | 14 | 3.7919 | 0.0977 | 3.6326 |
| stl | 14 | 2.0374 | 0.1096 | 1.2233 |
| stocks | 14 | 2.7295 | 0.0793 | 1.8827 |
| tov | 14 | 3.1869 | 0.0907 | 1.3166 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| core | 84 | 3.4738 | 0.0777 | 5.0842 |
| rotation | 60 | 3.8955 | 0.0787 | 4.3682 |
| starter | 24 | 2.8578 | 0.0716 | 2.0848 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

