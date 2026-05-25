# Phase 13S Direct-Lineup Contextual Challenger — 2026-05-24

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82010
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16402 | 57.823904 | 49.011949 | +15.2393% |
| pts | 15947 | 0.093091 | 0.092761 | +0.3539% |
| reb | 15947 | 0.023321 | 0.023329 | -0.0316% |
| ast | 15947 | 0.009591 | 0.009392 | +2.0685% |
| tov | 15947 | 0.007200 | 0.007193 | +0.0928% |
| stl | 15947 | 0.004053 | 0.004053 | +0.0207% |
| blk | 15947 | 0.002512 | 0.002512 | -0.0088% |
| fg3m | 15947 | 0.005086 | 0.005084 | +0.0435% |
