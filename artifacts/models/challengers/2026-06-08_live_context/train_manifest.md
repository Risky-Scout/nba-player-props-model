# Phase 13P Live-Context Challenger — 2026-06-08

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82169
- fitted_targets: ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']

## Feature columns

```
is_actionable
is_confirmed_out
is_inactive
is_doubtful
is_questionable
is_probable
injury_status_encoded
availability_status_encoded
injury_features_missing
num_teammates_out_total
num_teammates_out_guard
num_teammates_out_wing
num_teammates_out_big
vacated_minutes_total
vacated_minutes_guard
vacated_minutes_wing
vacated_minutes_big
vacated_fga_total
vacated_features_missing
starter_proxy_lagged
```

## Per-target metrics (test split)

| target | n_test | baseline_mse | challenger_mse | rel_improvement |
| --- | ---: | ---: | ---: | ---: |
| minutes | 16434 | 57.762518 | 57.126980 | +1.1003% |
| pts | 16434 | 0.095973 | 0.095957 | +0.0170% |
| reb | 16434 | 0.024103 | 0.024103 | -0.0007% |
| ast | 16434 | 0.009928 | 0.009928 | -0.0014% |
| tov | 16434 | 0.007635 | 0.007635 | +0.0031% |
| stl | 16434 | 0.004217 | 0.004218 | -0.0052% |
| blk | 16434 | 0.002616 | 0.002616 | -0.0065% |
| fg3m | 16434 | 0.005465 | 0.005464 | +0.0187% |
