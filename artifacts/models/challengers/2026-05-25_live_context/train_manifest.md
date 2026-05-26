# Phase 13P Live-Context Challenger — 2026-05-25

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82037
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
| minutes | 16408 | 57.803608 | 57.162807 | +1.1086% |
| pts | 16408 | 0.095988 | 0.095972 | +0.0173% |
| reb | 16408 | 0.024118 | 0.024118 | -0.0009% |
| ast | 16408 | 0.009936 | 0.009936 | -0.0007% |
| tov | 16408 | 0.007638 | 0.007638 | +0.0033% |
| stl | 16408 | 0.004222 | 0.004222 | -0.0053% |
| blk | 16408 | 0.002616 | 0.002616 | -0.0069% |
| fg3m | 16408 | 0.005466 | 0.005465 | +0.0198% |
