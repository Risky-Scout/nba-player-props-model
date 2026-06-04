# Phase 13Q Contextual Challenger — 2026-06-03

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82130
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16426 | 215.400980 | 142.778961 | +33.7148% |
| pts | 15960 | 0.096874 | 0.096843 | +0.0321% |
| reb | 15960 | 0.024098 | 0.024100 | -0.0082% |
| ast | 15960 | 0.009966 | 0.009964 | +0.0201% |
| tov | 15960 | 0.007572 | 0.007572 | +0.0058% |
| stl | 15960 | 0.004212 | 0.004212 | +0.0079% |
| blk | 15960 | 0.002644 | 0.002643 | +0.0311% |
| fg3m | 15960 | 0.005479 | 0.005475 | +0.0616% |
