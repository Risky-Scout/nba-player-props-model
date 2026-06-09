# Phase 13S Direct-Lineup Contextual Challenger — 2026-06-08

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82169
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16434 | 57.762518 | 48.963034 | +15.2339% |
| pts | 15979 | 0.093135 | 0.092810 | +0.3498% |
| reb | 15979 | 0.023289 | 0.023296 | -0.0285% |
| ast | 15979 | 0.009588 | 0.009389 | +2.0756% |
| tov | 15979 | 0.007201 | 0.007194 | +0.0927% |
| stl | 15979 | 0.004050 | 0.004049 | +0.0224% |
| blk | 15979 | 0.002509 | 0.002509 | -0.0056% |
| fg3m | 15979 | 0.005088 | 0.005086 | +0.0412% |
