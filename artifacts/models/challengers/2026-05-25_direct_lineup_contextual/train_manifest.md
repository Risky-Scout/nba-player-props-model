# Phase 13S Direct-Lineup Contextual Challenger — 2026-05-25

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82037
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16408 | 57.803608 | 48.992252 | +15.2436% |
| pts | 15952 | 0.093138 | 0.092811 | +0.3511% |
| reb | 15952 | 0.023314 | 0.023321 | -0.0299% |
| ast | 15952 | 0.009595 | 0.009397 | +2.0691% |
| tov | 15952 | 0.007202 | 0.007196 | +0.0937% |
| stl | 15952 | 0.004054 | 0.004053 | +0.0221% |
| blk | 15952 | 0.002510 | 0.002510 | -0.0079% |
| fg3m | 15952 | 0.005089 | 0.005087 | +0.0437% |
