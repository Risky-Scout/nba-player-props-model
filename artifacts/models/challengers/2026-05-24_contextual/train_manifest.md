# Phase 13Q Contextual Challenger — 2026-05-24

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82010
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16402 | 214.282082 | 142.411220 | +33.5403% |
| pts | 15938 | 0.096412 | 0.096377 | +0.0358% |
| reb | 15938 | 0.024271 | 0.024272 | -0.0024% |
| ast | 15938 | 0.009885 | 0.009884 | +0.0032% |
| tov | 15938 | 0.007709 | 0.007710 | -0.0079% |
| stl | 15938 | 0.004204 | 0.004204 | -0.0052% |
| blk | 15938 | 0.002546 | 0.002545 | +0.0295% |
| fg3m | 15938 | 0.005538 | 0.005534 | +0.0623% |
