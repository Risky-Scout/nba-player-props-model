# Phase 13Q Contextual Challenger — 2026-05-22

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 81966
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16394 | 214.947105 | 141.887343 | +33.9896% |
| pts | 15931 | 0.097088 | 0.097054 | +0.0352% |
| reb | 15931 | 0.024071 | 0.024070 | +0.0043% |
| ast | 15931 | 0.009971 | 0.009970 | +0.0154% |
| tov | 15931 | 0.007455 | 0.007455 | -0.0108% |
| stl | 15931 | 0.004214 | 0.004213 | +0.0160% |
| blk | 15931 | 0.002603 | 0.002603 | +0.0200% |
| fg3m | 15931 | 0.005531 | 0.005529 | +0.0479% |
