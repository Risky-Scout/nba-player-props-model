# Model Performance and Calibration — 2026-05-02

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

- rows scored: 18
- mean NLL: 2.3281
- mean RPS: 0.0829
- mean abs error: 3.2378
- mean outcome_prob_assigned: 0.1025

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 2 | 2.2750 | 0.0629 | 1.9682 |
| fg3m | 7 | 1.9794 | 0.0440 | 1.0562 |
| pts | 3 | 1.6412 | 0.1002 | 8.6837 |
| reb | 6 | 3.0959 | 0.1262 | 3.4833 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 1 | 3.7564 | 0.1575 | 4.0076 |
| rotation | 2 | 1.4891 | 0.0238 | 0.6465 |
| starter | 15 | 2.3447 | 0.0858 | 3.5320 |

## Market-line scoring (model only)

- rows scored: 406
- mean model logloss at market lines: 0.8029
- mean model Brier at market lines: 0.2926

## Model vs market

- rows_paired: 406 (threshold for hard claim: 20)
- delta_logloss = model - market = **+0.1368** (negative favors model)
- delta_brier   = model - market = **+0.0555** (negative favors model)

## Stats blocked by upstream phases

### tov — `phase11c_market_driven_prediction_layer` (phase11c)

TOV PMFs are not emitted by the current prediction layer when no market line is offered, because predict.py is market-line-driven. Resolving this requires the Phase 11C player-stat-grid prediction refactor (emit one model-only PMF row per (player, eligible_stat) regardless of whether a market line is offered). Outcomes are available in data/player_game_stats.parquet under the 'turnover' column; the gap is upstream of after-game scoring.

