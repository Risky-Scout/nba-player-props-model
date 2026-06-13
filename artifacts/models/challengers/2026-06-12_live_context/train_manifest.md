# Phase 13P Live-Context Challenger — 2026-06-12

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82190
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
| minutes | 16438 | 57.760167 | 57.126124 | +1.0977% |
| pts | 16438 | 0.095967 | 0.095952 | +0.0166% |
| reb | 16438 | 0.024113 | 0.024113 | -0.0006% |
| ast | 16438 | 0.009926 | 0.009926 | -0.0015% |
| tov | 16438 | 0.007635 | 0.007634 | +0.0032% |
| stl | 16438 | 0.004219 | 0.004219 | -0.0051% |
| blk | 16438 | 0.002619 | 0.002619 | -0.0065% |
| fg3m | 16438 | 0.005463 | 0.005462 | +0.0185% |
