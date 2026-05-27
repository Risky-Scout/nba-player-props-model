# Model Performance and Calibration — 2026-05-26

- champion_model_id: `challenger-2026-05-25`
- trained_through_date: `2026-05-25`
- calibrated_through_date: `2026-05-25`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 180
- mean NLL: 2.3946
- mean RPS: 0.0809
- mean abs error: 3.0799
- mean outcome_prob_assigned: 0.1806

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 15 | 2.0379 | 0.0610 | 1.4594 |
| blk | 15 | 0.8600 | 0.0637 | 0.4863 |
| fg3m | 15 | 1.8020 | 0.1709 | 1.0883 |
| pa | 15 | 3.4765 | 0.0620 | 6.0540 |
| pr | 15 | 3.5504 | 0.0613 | 6.9004 |
| pra | 15 | 3.6096 | 0.0583 | 7.0732 |
| pts | 15 | 3.3379 | 0.0784 | 5.9149 |
| ra | 15 | 2.5078 | 0.0435 | 2.3903 |
| reb | 15 | 2.2072 | 0.0519 | 1.8823 |
| stl | 15 | 1.7142 | 0.1480 | 1.1995 |
| stocks | 15 | 1.7469 | 0.0800 | 1.3141 |
| tov | 15 | 1.8847 | 0.0920 | 1.1963 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 12 | 1.7491 | 0.0332 | 1.2187 |
| core | 12 | 2.2668 | 0.0721 | 1.7124 |
| rotation | 84 | 2.3189 | 0.0795 | 2.9777 |
| starter | 72 | 2.6118 | 0.0920 | 3.7374 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

