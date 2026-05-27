# Phase 13Q Contextual Challenger — 2026-05-26

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82063
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16413 | 213.988665 | 142.990019 | +33.1787% |
| pts | 15948 | 0.095707 | 0.095668 | +0.0405% |
| reb | 15948 | 0.024170 | 0.024171 | -0.0031% |
| ast | 15948 | 0.010015 | 0.010013 | +0.0264% |
| tov | 15948 | 0.007481 | 0.007480 | +0.0182% |
| stl | 15948 | 0.004227 | 0.004226 | +0.0055% |
| blk | 15948 | 0.002625 | 0.002625 | -0.0003% |
| fg3m | 15948 | 0.005465 | 0.005462 | +0.0538% |
