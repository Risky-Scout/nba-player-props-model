# Phase 13Q Contextual Challenger — 2026-06-06

- feature_set_id: `phase13q_contextual_pmf_engine_v1`
- rows_used: 82149
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- game_context_features_present: ['is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16430 | 213.567587 | 143.330993 | +32.8873% |
| pts | 15966 | 0.096641 | 0.096595 | +0.0481% |
| reb | 15966 | 0.024177 | 0.024179 | -0.0050% |
| ast | 15966 | 0.009993 | 0.009991 | +0.0201% |
| tov | 15966 | 0.007618 | 0.007617 | +0.0108% |
| stl | 15966 | 0.004254 | 0.004253 | +0.0254% |
| blk | 15966 | 0.002631 | 0.002631 | +0.0091% |
| fg3m | 15966 | 0.005502 | 0.005499 | +0.0635% |
