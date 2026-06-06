# Phase 13S Direct-Lineup Contextual Challenger — 2026-06-05

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82149
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16430 | 57.773254 | 48.971027 | +15.2358% |
| pts | 15975 | 0.093147 | 0.092820 | +0.3511% |
| reb | 15975 | 0.023292 | 0.023298 | -0.0286% |
| ast | 15975 | 0.009589 | 0.009390 | +2.0740% |
| tov | 15975 | 0.007201 | 0.007195 | +0.0922% |
| stl | 15975 | 0.004051 | 0.004050 | +0.0222% |
| blk | 15975 | 0.002506 | 0.002506 | -0.0038% |
| fg3m | 15975 | 0.005086 | 0.005084 | +0.0426% |
