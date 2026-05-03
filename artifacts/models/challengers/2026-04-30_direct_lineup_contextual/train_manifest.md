# Phase 13S Direct-Lineup Contextual Challenger — 2026-04-30

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 81125
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16225 | 212.188599 | 81.518992 | +61.5818% |
| pts | 15751 | 0.095357 | 0.095260 | +0.1016% |
| reb | 15751 | 0.024002 | 0.024013 | -0.0483% |
| ast | 15751 | 0.009744 | 0.009743 | +0.0100% |
| tov | 15751 | 0.007352 | 0.007347 | +0.0763% |
| stl | 15751 | 0.004121 | 0.004121 | -0.0112% |
| blk | 15751 | 0.002630 | 0.002629 | +0.0129% |
| fg3m | 15751 | 0.005518 | 0.005515 | +0.0408% |
