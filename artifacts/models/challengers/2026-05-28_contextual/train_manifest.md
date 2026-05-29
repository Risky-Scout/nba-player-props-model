# Phase 13Q Contextual Challenger — 2026-05-28

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82091
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16419 | 214.480268 | 141.822403 | +33.8762% |
| pts | 15952 | 0.095884 | 0.095856 | +0.0297% |
| reb | 15952 | 0.024134 | 0.024138 | -0.0128% |
| ast | 15952 | 0.009883 | 0.009882 | +0.0137% |
| tov | 15952 | 0.007678 | 0.007677 | +0.0151% |
| stl | 15952 | 0.004216 | 0.004215 | +0.0175% |
| blk | 15952 | 0.002629 | 0.002629 | +0.0118% |
| fg3m | 15952 | 0.005488 | 0.005484 | +0.0656% |
