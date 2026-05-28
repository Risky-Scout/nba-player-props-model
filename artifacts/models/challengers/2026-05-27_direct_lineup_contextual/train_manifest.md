# Phase 13S Direct-Lineup Contextual Challenger — 2026-05-27

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82063
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16413 | 57.809729 | 49.002339 | +15.2351% |
| pts | 15958 | 0.093208 | 0.092882 | +0.3498% |
| reb | 15958 | 0.023309 | 0.023316 | -0.0301% |
| ast | 15958 | 0.009594 | 0.009396 | +2.0688% |
| tov | 15958 | 0.007201 | 0.007194 | +0.0931% |
| stl | 15958 | 0.004053 | 0.004052 | +0.0207% |
| blk | 15958 | 0.002509 | 0.002509 | -0.0058% |
| fg3m | 15958 | 0.005089 | 0.005087 | +0.0434% |
