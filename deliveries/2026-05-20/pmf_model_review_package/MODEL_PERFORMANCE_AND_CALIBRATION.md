# Model Performance and Calibration — 2026-05-20

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

- rows scored: 144
- mean NLL: 2.5290
- mean RPS: 0.0516
- mean abs error: 3.1247
- mean outcome_prob_assigned: 0.1786

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 12 | 2.3295 | 0.0536 | 1.8078 |
| blk | 12 | 1.2600 | 0.0472 | 0.7889 |
| fg3m | 12 | 1.5202 | 0.0590 | 1.4179 |
| pa | 12 | 3.3733 | 0.0393 | 5.3595 |
| pr | 12 | 3.4321 | 0.0406 | 6.1198 |
| pra | 12 | 3.7534 | 0.0419 | 7.5334 |
| pts | 12 | 3.2011 | 0.0402 | 4.4310 |
| ra | 12 | 3.3929 | 0.0592 | 4.0115 |
| reb | 12 | 2.6643 | 0.0612 | 2.5358 |
| stl | 12 | 1.3091 | 0.0472 | 0.7675 |
| stocks | 12 | 1.8304 | 0.0440 | 1.3620 |
| tov | 12 | 2.2820 | 0.0860 | 1.3619 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| core | 48 | 2.8706 | 0.0624 | 4.3390 |
| rotation | 48 | 2.1053 | 0.0359 | 2.3173 |
| starter | 48 | 2.6113 | 0.0565 | 2.7179 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

