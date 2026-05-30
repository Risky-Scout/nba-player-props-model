# Phase 13S Direct-Lineup Contextual Challenger — 2026-05-29

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82091
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16419 | 57.790628 | 48.983733 | +15.2393% |
| pts | 15963 | 0.093197 | 0.092869 | +0.3512% |
| reb | 15963 | 0.023303 | 0.023309 | -0.0298% |
| ast | 15963 | 0.009595 | 0.009396 | +2.0707% |
| tov | 15963 | 0.007200 | 0.007194 | +0.0925% |
| stl | 15963 | 0.004054 | 0.004053 | +0.0219% |
| blk | 15963 | 0.002508 | 0.002508 | -0.0056% |
| fg3m | 15963 | 0.005089 | 0.005087 | +0.0431% |
