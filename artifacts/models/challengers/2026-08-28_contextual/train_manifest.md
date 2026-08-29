# Phase 13Q Contextual Challenger — 2026-08-28

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82211
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16443 | 213.449293 | 141.818028 | +33.5589% |
| pts | 15978 | 0.096848 | 0.096804 | +0.0462% |
| reb | 15978 | 0.024363 | 0.024366 | -0.0101% |
| ast | 15978 | 0.009902 | 0.009901 | +0.0139% |
| tov | 15978 | 0.007708 | 0.007708 | -0.0002% |
| stl | 15978 | 0.004255 | 0.004253 | +0.0335% |
| blk | 15978 | 0.002631 | 0.002631 | -0.0069% |
| fg3m | 15978 | 0.005521 | 0.005517 | +0.0736% |
