# Model Performance and Calibration — 2026-05-30

- champion_model_id: `challenger-2026-05-29`
- trained_through_date: `2026-05-29`
- calibrated_through_date: `2026-05-29`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 192
- mean NLL: 2.4735
- mean RPS: 0.0738
- mean abs error: 2.8611
- mean outcome_prob_assigned: 0.1956

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 16 | 1.6613 | 0.0408 | 1.2548 |
| blk | 16 | 0.9008 | 0.0573 | 0.5382 |
| fg3m | 16 | 3.2601 | 0.1477 | 1.2710 |
| pa | 16 | 3.2416 | 0.0509 | 5.0256 |
| pr | 16 | 3.4742 | 0.0581 | 6.2005 |
| pra | 16 | 3.6819 | 0.0608 | 7.2288 |
| pts | 16 | 3.1434 | 0.0589 | 4.0713 |
| ra | 16 | 3.1496 | 0.0668 | 3.4870 |
| reb | 16 | 2.5700 | 0.0692 | 2.3763 |
| stl | 16 | 1.4219 | 0.1222 | 0.8440 |
| stocks | 16 | 1.5119 | 0.0748 | 1.0517 |
| tov | 16 | 1.6653 | 0.0778 | 0.9835 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 12 | 1.4496 | 0.0264 | 2.6543 |
| core | 24 | 2.8555 | 0.1097 | 4.6456 |
| rotation | 96 | 2.5505 | 0.0710 | 2.5860 |
| starter | 60 | 2.4023 | 0.0733 | 2.6286 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

