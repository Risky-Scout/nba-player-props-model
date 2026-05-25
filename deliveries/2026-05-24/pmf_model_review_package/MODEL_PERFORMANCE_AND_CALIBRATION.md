# Model Performance and Calibration — 2026-05-24

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

- rows scored: 168
- mean NLL: 2.2050
- mean RPS: 0.0397
- mean abs error: 3.0616
- mean outcome_prob_assigned: 0.1949

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 14 | 1.5888 | 0.0270 | 1.0466 |
| blk | 14 | 1.1493 | 0.0357 | 0.5050 |
| fg3m | 14 | 1.0978 | 0.0337 | 1.0637 |
| pa | 14 | 3.5026 | 0.0485 | 7.6723 |
| pr | 14 | 3.3977 | 0.0386 | 6.2995 |
| pra | 14 | 3.5286 | 0.0381 | 7.1954 |
| pts | 14 | 3.3762 | 0.0529 | 6.7764 |
| ra | 14 | 2.2151 | 0.0256 | 1.9522 |
| reb | 14 | 2.1776 | 0.0390 | 1.5982 |
| stl | 14 | 1.2150 | 0.0460 | 0.7368 |
| stocks | 14 | 1.5217 | 0.0286 | 0.7815 |
| tov | 14 | 1.6901 | 0.0626 | 1.1120 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| core | 36 | 1.9547 | 0.0298 | 2.5101 |
| rotation | 60 | 2.0409 | 0.0348 | 3.0277 |
| starter | 72 | 2.4670 | 0.0487 | 3.3657 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

