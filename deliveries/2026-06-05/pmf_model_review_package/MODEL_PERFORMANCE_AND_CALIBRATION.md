# Model Performance and Calibration — 2026-06-05

- champion_model_id: `challenger-2026-06-04`
- trained_through_date: `2026-06-04`
- calibrated_through_date: `2026-06-04`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 192
- mean NLL: 2.2841
- mean RPS: 0.0806
- mean abs error: 2.3464
- mean outcome_prob_assigned: 0.1803

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 16 | 1.8174 | 0.0481 | 0.9703 |
| blk | 16 | 1.3570 | 0.1425 | 0.7557 |
| fg3m | 16 | 1.3953 | 0.1696 | 0.9429 |
| pa | 16 | 3.1023 | 0.0427 | 4.6655 |
| pr | 16 | 3.1962 | 0.0385 | 4.7482 |
| pra | 16 | 3.2837 | 0.0406 | 5.1938 |
| pts | 16 | 3.0589 | 0.0496 | 4.1760 |
| ra | 16 | 2.5608 | 0.0477 | 2.0700 |
| reb | 16 | 2.0728 | 0.0413 | 1.5023 |
| stl | 16 | 1.4954 | 0.1367 | 0.8281 |
| stocks | 16 | 1.9782 | 0.1206 | 1.1299 |
| tov | 16 | 2.0916 | 0.0892 | 1.1746 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 36 | 1.7777 | 0.0418 | 1.4353 |
| core | 24 | 1.8351 | 0.0466 | 1.7512 |
| rotation | 24 | 1.8653 | 0.0739 | 1.6772 |
| starter | 108 | 2.6458 | 0.1026 | 2.9312 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

