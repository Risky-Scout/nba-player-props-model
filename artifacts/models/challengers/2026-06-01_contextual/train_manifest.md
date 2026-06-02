# Phase 13Q Contextual Challenger — 2026-06-01

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82110
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16422 | 212.971687 | 141.199320 | +33.7004% |
| pts | 15956 | 0.096396 | 0.096382 | +0.0143% |
| reb | 15956 | 0.024295 | 0.024297 | -0.0067% |
| ast | 15956 | 0.009942 | 0.009941 | +0.0099% |
| tov | 15956 | 0.007630 | 0.007629 | +0.0135% |
| stl | 15956 | 0.004246 | 0.004245 | +0.0205% |
| blk | 15956 | 0.002621 | 0.002620 | +0.0151% |
| fg3m | 15956 | 0.005495 | 0.005492 | +0.0556% |
