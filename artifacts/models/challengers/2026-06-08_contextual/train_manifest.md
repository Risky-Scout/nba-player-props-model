# Phase 13Q Contextual Challenger — 2026-06-08

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82169
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16434 | 213.299162 | 142.989194 | +32.9631% |
| pts | 15969 | 0.097041 | 0.097001 | +0.0412% |
| reb | 15969 | 0.024273 | 0.024275 | -0.0091% |
| ast | 15969 | 0.009956 | 0.009952 | +0.0354% |
| tov | 15969 | 0.007590 | 0.007589 | +0.0096% |
| stl | 15969 | 0.004204 | 0.004204 | +0.0085% |
| blk | 15969 | 0.002607 | 0.002607 | +0.0206% |
| fg3m | 15969 | 0.005533 | 0.005529 | +0.0758% |
