# Model Performance and Calibration — 2026-04-30

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

- rows scored: 68
- mean NLL: 2.2116
- mean RPS: 0.0715
- mean abs error: 2.5987
- mean outcome_prob_assigned: 0.1220

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 12 | 2.1097 | 0.0585 | 1.7462 |
| fg3m | 19 | 1.6113 | 0.0367 | 1.2403 |
| pts | 17 | 2.5694 | 0.1031 | 4.9511 |
| reb | 20 | 2.5388 | 0.0856 | 2.4010 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 9 | 2.2000 | 0.0749 | 2.5539 |
| rotation | 14 | 2.2589 | 0.0776 | 2.1737 |
| starter | 45 | 2.1992 | 0.0689 | 2.7399 |

## Market-line scoring (model only)

- rows scored: 1,265
- mean model logloss at market lines: 0.6249
- mean model Brier at market lines: 0.2185

## Model vs market

- rows_paired: 1265 (threshold for hard claim: 20)
- delta_logloss = model - market = **-0.0262** (negative favors model)
- delta_brier   = model - market = **-0.0114** (negative favors model)

## Stats blocked by upstream phases

### tov — `phase11c_market_driven_prediction_layer` (phase11c)

TOV PMFs are not emitted by the current prediction layer when no market line is offered, because predict.py is market-line-driven. Resolving this requires the Phase 11C player-stat-grid prediction refactor (emit one model-only PMF row per (player, eligible_stat) regardless of whether a market line is offered). Outcomes are available in data/player_game_stats.parquet under the 'turnover' column; the gap is upstream of after-game scoring.

