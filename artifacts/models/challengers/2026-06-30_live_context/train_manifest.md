# Phase 13P Live-Context Challenger — 2026-06-30

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82211
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
| minutes | 16443 | 57.748337 | 57.115738 | +1.0954% |
| pts | 16443 | 0.095970 | 0.095954 | +0.0162% |
| reb | 16443 | 0.024109 | 0.024109 | -0.0007% |
| ast | 16443 | 0.009937 | 0.009937 | -0.0015% |
| tov | 16443 | 0.007633 | 0.007633 | +0.0031% |
| stl | 16443 | 0.004218 | 0.004218 | -0.0051% |
| blk | 16443 | 0.002627 | 0.002627 | -0.0066% |
| fg3m | 16443 | 0.005462 | 0.005461 | +0.0184% |
