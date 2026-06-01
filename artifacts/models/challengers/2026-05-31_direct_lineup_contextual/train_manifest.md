# Phase 13S Direct-Lineup Contextual Challenger — 2026-05-31

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82110
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16422 | 57.790765 | 48.983160 | +15.2405% |
| pts | 15967 | 0.093184 | 0.092856 | +0.3515% |
| reb | 15967 | 0.023295 | 0.023303 | -0.0302% |
| ast | 15967 | 0.009592 | 0.009393 | +2.0723% |
| tov | 15967 | 0.007199 | 0.007193 | +0.0925% |
| stl | 15967 | 0.004053 | 0.004052 | +0.0223% |
| blk | 15967 | 0.002507 | 0.002507 | -0.0049% |
| fg3m | 15967 | 0.005088 | 0.005086 | +0.0431% |
