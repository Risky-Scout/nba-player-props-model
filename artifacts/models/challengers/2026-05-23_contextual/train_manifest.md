# Phase 13Q Contextual Challenger — 2026-05-23

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 81985
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16397 | 214.660349 | 141.034349 | +34.2988% |
| pts | 15932 | 0.097148 | 0.097116 | +0.0332% |
| reb | 15932 | 0.024422 | 0.024423 | -0.0064% |
| ast | 15932 | 0.009888 | 0.009887 | +0.0141% |
| tov | 15932 | 0.007703 | 0.007703 | -0.0004% |
| stl | 15932 | 0.004270 | 0.004270 | -0.0007% |
| blk | 15932 | 0.002610 | 0.002610 | +0.0282% |
| fg3m | 15932 | 0.005474 | 0.005471 | +0.0427% |
