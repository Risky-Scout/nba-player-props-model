# Model Performance and Calibration — 2026-05-08

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

- rows scored: 230
- mean NLL: 1.6869
- mean RPS: 0.0617
- mean abs error: 1.8004
- mean outcome_prob_assigned: 0.2987

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 46 | 1.5257 | 0.0435 | 1.3289 |
| fg3m | 46 | 1.0057 | 0.1166 | 0.6953 |
| pts | 46 | 2.6608 | 0.0549 | 4.2659 |
| reb | 46 | 2.0720 | 0.0558 | 1.9606 |
| tov | 46 | 1.1701 | 0.0380 | 0.7514 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 55 | 1.2458 | 0.0473 | 1.4668 |
| core | 50 | 2.4642 | 0.1027 | 3.0474 |
| fringe | 30 | 0.7814 | 0.0133 | 0.9459 |
| inactive_risk | 15 | 0.8880 | 0.0278 | 1.1022 |
| rotation | 25 | 1.6874 | 0.0741 | 1.3185 |
| starter | 55 | 2.1328 | 0.0690 | 1.8760 |

## Market-line scoring (model only)

- rows scored: 578
- mean model logloss at market lines: 0.9083
- mean model Brier at market lines: 0.3079

## Model vs market

- rows_paired: 578 (threshold for hard claim: 20)
- delta_logloss = model - market = **+0.2169** (negative favors model)
- delta_brier   = model - market = **+0.0587** (negative favors model)

