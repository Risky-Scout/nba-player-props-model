# Phase 13Q Contextual Challenger — 2026-04-30

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 81125
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16225 | 212.188599 | 141.230827 | +33.4409% |
| pts | 15762 | 0.095791 | 0.095766 | +0.0267% |
| reb | 15762 | 0.024062 | 0.024064 | -0.0083% |
| ast | 15762 | 0.009785 | 0.009786 | -0.0148% |
| tov | 15762 | 0.007439 | 0.007438 | +0.0058% |
| stl | 15762 | 0.004112 | 0.004112 | -0.0052% |
| blk | 15762 | 0.002632 | 0.002632 | +0.0177% |
| fg3m | 15762 | 0.005503 | 0.005500 | +0.0516% |
