# Model Performance and Calibration — 2026-05-03

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

- rows scored: 46
- mean NLL: 3.2537
- mean RPS: 0.0820
- mean abs error: 3.1144
- mean outcome_prob_assigned: 0.1010

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 8 | 2.5153 | 0.0800 | 2.1808 |
| fg3m | 12 | 5.9621 | 0.0541 | 1.3267 |
| pts | 13 | 2.0599 | 0.1076 | 5.8749 |
| reb | 13 | 2.4020 | 0.0833 | 2.5786 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 8 | 5.5231 | 0.0905 | 2.6930 |
| rotation | 16 | 3.9044 | 0.1009 | 3.3656 |
| starter | 22 | 1.9553 | 0.0651 | 3.0849 |

## Market-line scoring (model only)

- rows scored: 489
- mean model logloss at market lines: 0.6400
- mean model Brier at market lines: 0.2273

## Model vs market

- rows_paired: 489 (threshold for hard claim: 20)
- delta_logloss = model - market = **-0.0141** (negative favors model)
- delta_brier   = model - market = **-0.0050** (negative favors model)

## Stats blocked by upstream phases

### tov — `phase11c_market_driven_prediction_layer` (phase11c)

TOV PMFs are not emitted by the current prediction layer when no market line is offered, because predict.py is market-line-driven. Resolving this requires the Phase 11C player-stat-grid prediction refactor (emit one model-only PMF row per (player, eligible_stat) regardless of whether a market line is offered). Outcomes are available in data/player_game_stats.parquet under the 'turnover' column; the gap is upstream of after-game scoring.

