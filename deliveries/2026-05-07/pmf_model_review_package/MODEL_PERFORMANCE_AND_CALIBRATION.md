# Model Performance and Calibration — 2026-05-07

- champion_model_id: `challenger-2026-04-30`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov']
- documented_blocked_target_stats: []
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 220
- mean NLL: 1.7230
- mean RPS: 0.0612
- mean abs error: 1.6479
- mean outcome_prob_assigned: 0.2672

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 44 | 1.6135 | 0.0419 | 1.2209 |
| fg3m | 44 | 1.1116 | 0.1329 | 0.7813 |
| pts | 44 | 2.8229 | 0.0564 | 4.1618 |
| reb | 44 | 1.8567 | 0.0388 | 1.4187 |
| tov | 44 | 1.2105 | 0.0360 | 0.6569 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 55 | 1.4907 | 0.0666 | 1.5693 |
| core | 45 | 1.9690 | 0.0706 | 2.0666 |
| fringe | 20 | 0.9189 | 0.0387 | 0.8696 |
| inactive_risk | 15 | 1.0868 | 0.0292 | 0.7635 |
| rotation | 30 | 1.8347 | 0.0568 | 1.3421 |
| starter | 55 | 2.1591 | 0.0674 | 2.0751 |

## Market-line scoring (model only)

- rows scored: 400
- mean model logloss at market lines: 0.7774
- mean model Brier at market lines: 0.2832

## Model vs market

- rows_paired: 400 (threshold for hard claim: 20)
- delta_logloss = model - market = **+0.0691** (negative favors model)
- delta_brier   = model - market = **+0.0264** (negative favors model)

