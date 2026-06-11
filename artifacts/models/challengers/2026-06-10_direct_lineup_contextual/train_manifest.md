# Phase 13S Direct-Lineup Contextual Challenger — 2026-06-10

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- rows_used: 82190
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- trained_with_direct_lineup_features: **True**
- trained_with_lineup_composition_features: **True**
- trained_with_injury_features: True
- trained_with_vacated_opportunity_features: True
- trained_with_game_context_features: True

## Per-target metrics

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16438 | 57.760167 | 48.962943 | +15.2306% |
| pts | 15983 | 0.093143 | 0.092821 | +0.3460% |
| reb | 15983 | 0.023299 | 0.023306 | -0.0289% |
| ast | 15983 | 0.009586 | 0.009387 | +2.0761% |
| tov | 15983 | 0.007200 | 0.007194 | +0.0931% |
| stl | 15983 | 0.004051 | 0.004050 | +0.0213% |
| blk | 15983 | 0.002512 | 0.002512 | -0.0039% |
| fg3m | 15983 | 0.005088 | 0.005086 | +0.0394% |
