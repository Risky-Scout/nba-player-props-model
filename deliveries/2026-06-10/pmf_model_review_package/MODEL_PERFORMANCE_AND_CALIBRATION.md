# Model Performance and Calibration — 2026-06-10

- champion_model_id: `challenger-2026-06-09`
- trained_through_date: `2026-06-09`
- calibrated_through_date: `2026-06-09`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 180
- mean NLL: 2.1370
- mean RPS: 0.0720
- mean abs error: 2.8240
- mean outcome_prob_assigned: 0.2168

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 15 | 1.5296 | 0.0391 | 0.9887 |
| blk | 15 | 0.8059 | 0.0667 | 0.5852 |
| fg3m | 15 | 1.4717 | 0.1644 | 1.3167 |
| pa | 15 | 3.3270 | 0.0595 | 6.2742 |
| pr | 15 | 3.3388 | 0.0526 | 6.2738 |
| pra | 15 | 3.4327 | 0.0502 | 6.4273 |
| pts | 15 | 3.1931 | 0.0736 | 5.8827 |
| ra | 15 | 2.1745 | 0.0361 | 1.8126 |
| reb | 15 | 1.7938 | 0.0348 | 1.1713 |
| stl | 15 | 1.3584 | 0.1350 | 0.9350 |
| stocks | 15 | 1.6408 | 0.0839 | 1.1859 |
| tov | 15 | 1.5781 | 0.0685 | 1.0342 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 36 | 1.6599 | 0.0381 | 2.1127 |
| core | 36 | 2.1933 | 0.0898 | 2.6546 |
| rotation | 12 | 1.7542 | 0.0518 | 3.4203 |
| starter | 96 | 2.3427 | 0.0806 | 3.0797 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

