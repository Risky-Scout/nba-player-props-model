# Phase 13S Direct-Lineup Contextual Challenger — 2026-06-03

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82130
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16426 | 57.779915 | 48.974616 | +15.2394% |
| pts | 15971 | 0.093162 | 0.092835 | +0.3510% |
| reb | 15971 | 0.023294 | 0.023300 | -0.0292% |
| ast | 15971 | 0.009591 | 0.009392 | +2.0734% |
| tov | 15971 | 0.007199 | 0.007192 | +0.0932% |
| stl | 15971 | 0.004052 | 0.004051 | +0.0223% |
| blk | 15971 | 0.002507 | 0.002507 | -0.0043% |
| fg3m | 15971 | 0.005087 | 0.005085 | +0.0429% |
