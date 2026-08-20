# Phase 13S Direct-Lineup Contextual Challenger — 2026-08-19

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82211
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16443 | 57.748337 | 48.953807 | +15.2291% |
| pts | 15987 | 0.093149 | 0.092826 | +0.3472% |
| reb | 15987 | 0.023296 | 0.023302 | -0.0285% |
| ast | 15987 | 0.009598 | 0.009398 | +2.0814% |
| tov | 15987 | 0.007200 | 0.007193 | +0.0924% |
| stl | 15987 | 0.004051 | 0.004050 | +0.0216% |
| blk | 15987 | 0.002520 | 0.002520 | -0.0044% |
| fg3m | 15987 | 0.005087 | 0.005085 | +0.0400% |
