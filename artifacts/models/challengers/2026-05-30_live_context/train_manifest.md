# Phase 13P Live-Context Challenger — 2026-05-30

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82110
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
| minutes | 16422 | 57.790765 | 57.152254 | +1.1049% |
| pts | 16422 | 0.096022 | 0.096005 | +0.0175% |
| reb | 16422 | 0.024110 | 0.024110 | -0.0008% |
| ast | 16422 | 0.009933 | 0.009933 | -0.0013% |
| tov | 16422 | 0.007634 | 0.007634 | +0.0033% |
| stl | 16422 | 0.004220 | 0.004220 | -0.0052% |
| blk | 16422 | 0.002615 | 0.002615 | -0.0067% |
| fg3m | 16422 | 0.005465 | 0.005464 | +0.0188% |
