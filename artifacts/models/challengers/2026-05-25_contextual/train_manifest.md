# Phase 13Q Contextual Challenger — 2026-05-25

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82037
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16408 | 212.143713 | 141.603971 | +33.2509% |
| pts | 15942 | 0.097097 | 0.097078 | +0.0191% |
| reb | 15942 | 0.024271 | 0.024273 | -0.0076% |
| ast | 15942 | 0.009911 | 0.009910 | +0.0061% |
| tov | 15942 | 0.007637 | 0.007638 | -0.0038% |
| stl | 15942 | 0.004148 | 0.004148 | +0.0134% |
| blk | 15942 | 0.002635 | 0.002635 | +0.0135% |
| fg3m | 15942 | 0.005475 | 0.005472 | +0.0585% |
