# Phase 13Q Contextual Challenger — 2026-06-12

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82190
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16438 | 213.891324 | 142.881781 | +33.1989% |
| pts | 15973 | 0.096181 | 0.096146 | +0.0365% |
| reb | 15973 | 0.024386 | 0.024390 | -0.0137% |
| ast | 15973 | 0.009926 | 0.009925 | +0.0135% |
| tov | 15973 | 0.007675 | 0.007675 | +0.0016% |
| stl | 15973 | 0.004186 | 0.004185 | +0.0164% |
| blk | 15973 | 0.002650 | 0.002650 | +0.0134% |
| fg3m | 15973 | 0.005489 | 0.005485 | +0.0632% |
