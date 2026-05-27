# Phase 13P Live-Context Challenger — 2026-05-26

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82063
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
| minutes | 16413 | 57.809729 | 57.170111 | +1.1064% |
| pts | 16413 | 0.096052 | 0.096035 | +0.0180% |
| reb | 16413 | 0.024114 | 0.024115 | -0.0008% |
| ast | 16413 | 0.009935 | 0.009935 | -0.0011% |
| tov | 16413 | 0.007637 | 0.007637 | +0.0033% |
| stl | 16413 | 0.004221 | 0.004221 | -0.0054% |
| blk | 16413 | 0.002616 | 0.002616 | -0.0068% |
| fg3m | 16413 | 0.005466 | 0.005465 | +0.0198% |
