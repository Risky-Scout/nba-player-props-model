# Model Performance and Calibration — 2026-05-01

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

- rows scored: 69
- mean NLL: 2.2529
- mean RPS: 0.0909
- mean abs error: 3.4146
- mean outcome_prob_assigned: 0.1078

## Per stat

| Stat | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| ast | 16 | 2.4780 | 0.0850 | 2.4794 |
| fg3m | 11 | 1.4112 | 0.0297 | 1.0660 |
| pts | 18 | 2.2090 | 0.1358 | 6.9905 |
| reb | 24 | 2.5215 | 0.0894 | 2.4327 |

## Per role bucket

| Role | n | NLL | RPS | abs_mean_error |
| --- | ---: | ---: | ---: | ---: |
| bench | 6 | 2.1231 | 0.0597 | 1.7851 |
| rotation | 21 | 2.5952 | 0.1304 | 4.3610 |
| starter | 42 | 2.1003 | 0.0757 | 3.1742 |

## Market-line scoring (model only)

- rows scored: 1,202
- mean model logloss at market lines: 0.6928
- mean model Brier at market lines: 0.2492

## Model vs market

- rows_paired: 1202 (threshold for hard claim: 20)
- delta_logloss = model - market = **+0.0285** (negative favors model)
- delta_brier   = model - market = **+0.0132** (negative favors model)

## Stats blocked by upstream phases

### tov — `phase11c_market_driven_prediction_layer` (phase11c)

TOV PMFs are not emitted by the current prediction layer when no market line is offered, because predict.py is market-line-driven. Resolving this requires the Phase 11C player-stat-grid prediction refactor (emit one model-only PMF row per (player, eligible_stat) regardless of whether a market line is offered). Outcomes are available in data/player_game_stats.parquet under the 'turnover' column; the gap is upstream of after-game scoring.

