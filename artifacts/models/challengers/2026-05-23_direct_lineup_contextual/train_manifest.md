# Phase 13S Direct-Lineup Contextual Challenger — 2026-05-23

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 81985
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16397 | 57.835472 | 49.026020 | +15.2319% |
| pts | 15942 | 0.093088 | 0.092758 | +0.3539% |
| reb | 15942 | 0.023327 | 0.023334 | -0.0315% |
| ast | 15942 | 0.009586 | 0.009387 | +2.0695% |
| tov | 15942 | 0.007200 | 0.007193 | +0.0932% |
| stl | 15942 | 0.004053 | 0.004052 | +0.0198% |
| blk | 15942 | 0.002512 | 0.002512 | -0.0083% |
| fg3m | 15942 | 0.005087 | 0.005084 | +0.0428% |
