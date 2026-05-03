# Expected Target Stats Coverage — 2026-05-02

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
| pts | scored | 3 | 4 | 19 |  |
| reb | scored | 6 | 7 | 19 |  |
| ast | scored | 2 | 3 | 19 |  |
| fg3m | scored | 7 | 8 | 19 |  |
| tov | documented_blocked | 0 | 0 | 19 | phase11c_market_driven_prediction_layer |

## Documented blockers

### tov — `phase11c_market_driven_prediction_layer`

TOV PMFs are not emitted by the current prediction layer when no market line is offered, because predict.py is market-line-driven. Resolving this requires the Phase 11C player-stat-grid prediction refactor (emit one model-only PMF row per (player, eligible_stat) regardless of whether a market line is offered). Outcomes are available in data/player_game_stats.parquet under the 'turnover' column; the gap is upstream of after-game scoring.

Outcome source column present: `turnover`. Remediation phase: `phase11c`.

