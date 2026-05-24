# Phase 13P Live-Context Challenger — 2026-05-23

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 81985
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
| minutes | 16397 | 57.835472 | 57.195962 | +1.1057% |
| pts | 16397 | 0.095949 | 0.095933 | +0.0173% |
| reb | 16397 | 0.024123 | 0.024123 | -0.0011% |
| ast | 16397 | 0.009926 | 0.009926 | -0.0010% |
| tov | 16397 | 0.007637 | 0.007637 | +0.0034% |
| stl | 16397 | 0.004221 | 0.004222 | -0.0056% |
| blk | 16397 | 0.002616 | 0.002617 | -0.0068% |
| fg3m | 16397 | 0.005465 | 0.005464 | +0.0196% |
