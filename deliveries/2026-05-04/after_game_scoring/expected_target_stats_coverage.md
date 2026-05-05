# Expected Target Stats Coverage — 2026-05-04

- expected_target_stats: ['pts', 'reb', 'ast', 'fg3m', 'tov']
- scored_target_stats: ['pts', 'reb', 'ast', 'fg3m']
- documented_blocked_target_stats: ['tov']
- missing_target_stats (undocumented): []
- all_accounted: **True**
- all_actually_scored: **False**
- tov_source_column: `turnover`
- tov_rows_scored: 0

## Per stat

| Stat | Status | Scored rows | Canonical PMF rows | Outcome rows | Blocker |
| --- | --- | --- | --- | --- | --- |
| pts | scored | 12 | 13 | 46 |  |
| reb | scored | 17 | 17 | 46 |  |
| ast | scored | 9 | 10 | 46 |  |
| fg3m | scored | 10 | 10 | 46 |  |
| tov | documented_blocked | 0 | 0 | 46 | phase11c_market_driven_prediction_layer |

## Documented blockers

### tov — `phase11c_market_driven_prediction_layer`

TOV PMFs are not emitted by the current prediction layer when no market line is offered, because predict.py is market-line-driven. Resolving this requires the Phase 11C player-stat-grid prediction refactor (emit one model-only PMF row per (player, eligible_stat) regardless of whether a market line is offered). Outcomes are available in data/player_game_stats.parquet under the 'turnover' column; the gap is upstream of after-game scoring.

Outcome source column present: `turnover`. Remediation phase: `phase11c`.

