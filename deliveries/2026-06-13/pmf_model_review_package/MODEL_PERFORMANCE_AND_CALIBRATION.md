# Model Performance and Calibration — 2026-06-13

- champion_model_id: `challenger-2026-06-12`
- trained_through_date: `2026-06-12`
- calibrated_through_date: `2026-06-12`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 192
- mean NLL: 2.3587
- mean RPS: 0.0749
- mean abs error: 3.0337
- mean outcome_prob_assigned: 0.2109

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 16 | 1.8553 | 0.0535 | 1.3914 |
| blk | 16 | 1.0477 | 0.1033 | 0.6524 |
| fg3m | 16 | 1.6417 | 0.1351 | 1.0502 |
| pa | 16 | 3.5017 | 0.0611 | 6.3998 |
| pr | 16 | 3.5267 | 0.0589 | 6.5203 |
| pra | 16 | 3.6735 | 0.0567 | 6.8600 |
| pts | 16 | 3.2994 | 0.0726 | 6.0061 |
| ra | 16 | 2.4572 | 0.0480 | 2.3902 |
| reb | 16 | 2.3602 | 0.0624 | 2.1247 |
| stl | 16 | 1.2373 | 0.0915 | 0.8299 |
| stocks | 16 | 1.5871 | 0.0769 | 1.1195 |
| tov | 16 | 2.1169 | 0.0794 | 1.0603 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 48 | 1.6340 | 0.0453 | 2.1125 |
| core | 24 | 2.6234 | 0.0862 | 3.1479 |
| rotation | 12 | 1.6628 | 0.0393 | 1.8227 |
| starter | 108 | 2.6994 | 0.0896 | 3.5524 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

