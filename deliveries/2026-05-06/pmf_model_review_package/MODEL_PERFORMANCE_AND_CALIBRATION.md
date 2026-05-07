# Model Performance and Calibration — 2026-05-06

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

- rows scored: 86
- mean NLL: 1.9547
- mean RPS: 0.0621
- mean abs error: 2.0275
- mean outcome_prob_assigned: 0.1743

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 13 | 1.9667 | 0.0435 | 1.2028 |
| fg3m | 14 | 1.6418 | 0.0387 | 1.3063 |
| pts | 16 | 2.6963 | 0.1467 | 5.4724 |
| reb | 15 | 2.1650 | 0.0571 | 1.5117 |
| tov | 28 | 1.5692 | 0.0368 | 1.0787 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 6 | 1.9771 | 0.0492 | 1.3485 |
| rotation | 18 | 2.1736 | 0.0704 | 2.1385 |
| starter | 34 | 2.1524 | 0.0808 | 2.8699 |
| nan | 28 | 1.5692 | 0.0368 | 1.0787 |

## Market-line scoring (model only)

- No market-line rows were scored for this delivery.

## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

