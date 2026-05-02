# Phase 13P Live-Context Challenger — 2026-04-30

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 81125
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
| minutes | 16225 | 57.872896 | 57.177677 | +1.2013% |
| pts | 16225 | 0.095755 | 0.095736 | +0.0194% |
| reb | 16225 | 0.024139 | 0.024140 | -0.0010% |
| ast | 16225 | 0.009918 | 0.009918 | +0.0006% |
| tov | 16225 | 0.007485 | 0.007485 | +0.0048% |
| stl | 16225 | 0.004228 | 0.004228 | -0.0053% |
| blk | 16225 | 0.002624 | 0.002624 | -0.0070% |
| fg3m | 16225 | 0.005505 | 0.005504 | +0.0199% |
