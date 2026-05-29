# Model Performance and Calibration — 2026-05-28

- champion_model_id: `challenger-2026-05-27`
- trained_through_date: `2026-05-27`
- calibrated_through_date: `2026-05-27`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov', 'stl', 'blk', 'stocks', 'pa', 'pr', 'pra']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 168
- mean NLL: 2.4632
- mean RPS: 0.0781
- mean abs error: 3.1230
- mean outcome_prob_assigned: 0.1780

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 14 | 2.1659 | 0.0657 | 1.8731 |
| blk | 14 | 0.8998 | 0.0744 | 0.5682 |
| fg3m | 14 | 1.8459 | 0.1809 | 1.0890 |
| pa | 14 | 3.5762 | 0.0583 | 6.4392 |
| pr | 14 | 3.6908 | 0.0591 | 6.5002 |
| pra | 14 | 3.9695 | 0.0620 | 7.4840 |
| pts | 14 | 3.3874 | 0.0676 | 5.3160 |
| ra | 14 | 3.2535 | 0.0661 | 3.5265 |
| reb | 14 | 2.4192 | 0.0572 | 1.9751 |
| stl | 14 | 1.3148 | 0.1073 | 0.7342 |
| stocks | 14 | 1.6443 | 0.0787 | 1.1661 |
| tov | 14 | 1.3907 | 0.0596 | 0.8046 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| core | 48 | 2.5828 | 0.0813 | 3.3826 |
| rotation | 60 | 2.2616 | 0.0715 | 2.4570 |
| starter | 60 | 2.5690 | 0.0820 | 3.5814 |

## Market-line scoring (model only)

- rows scored: 0
- no non-push market rows


## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

