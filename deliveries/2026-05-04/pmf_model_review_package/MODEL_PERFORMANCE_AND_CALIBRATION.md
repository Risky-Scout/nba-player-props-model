# Model Performance and Calibration — 2026-05-04

- champion_model_id: `challenger-2026-04-30`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`
- after_game_status: **scored**
- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m']
- documented_blocked_target_stats: ['tov']
- missing_target_stats (undocumented): []

PMFs are model-only and are NOT market-anchored. Comparisons against
market lines below use realized outcomes only.

## Aggregate PMF metrics

- rows scored: 48
- mean NLL: 2.3346
- mean RPS: 0.0799
- mean abs error: 2.6373
- mean outcome_prob_assigned: 0.1141

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 9 | 2.1932 | 0.0606 | 1.8235 |
| fg3m | 10 | 1.8356 | 0.0428 | 1.1852 |
| pts | 12 | 2.8778 | 0.1290 | 4.8995 |
| reb | 17 | 2.3196 | 0.0773 | 2.3253 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 6 | 1.7982 | 0.0464 | 1.6760 |
| rotation | 14 | 2.7682 | 0.1143 | 3.1040 |
| starter | 28 | 2.2327 | 0.0699 | 2.6099 |

## Market-line scoring (model only)

- No market-line rows were scored for this delivery.

## Model vs market

- rows_paired: 0 — no overall delta computed for this slate.

## Stats blocked by upstream phases

### tov — `phase11c_market_driven_prediction_layer` (phase11c)

TOV PMFs are not emitted by the current prediction layer when no market line is offered, because predict.py is market-line-driven. Resolving this requires the Phase 11C player-stat-grid prediction refactor (emit one model-only PMF row per (player, eligible_stat) regardless of whether a market line is offered). Outcomes are available in data/player_game_stats.parquet under the 'turnover' column; the gap is upstream of after-game scoring.

