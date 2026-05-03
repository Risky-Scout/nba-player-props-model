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
| minutes | 16225 | 57.872896 | 48.996196 | +15.3383% |
| pts | 15770 | 0.092377 | 0.092062 | +0.3413% |
| reb | 15770 | 0.023285 | 0.023293 | -0.0361% |
| ast | 15770 | 0.009565 | 0.009365 | +2.0951% |
| tov | 15770 | 0.007029 | 0.007024 | +0.0784% |
| stl | 15770 | 0.004056 | 0.004055 | +0.0217% |
| blk | 15770 | 0.002526 | 0.002527 | -0.0108% |
| fg3m | 15770 | 0.005090 | 0.005088 | +0.0478% |
