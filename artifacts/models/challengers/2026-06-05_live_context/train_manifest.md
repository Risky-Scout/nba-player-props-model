# Phase 13P Live-Context Challenger — 2026-06-05

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82149
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
| minutes | 16430 | 57.773254 | 57.136281 | +1.1025% |
| pts | 16430 | 0.095985 | 0.095968 | +0.0171% |
| reb | 16430 | 0.024106 | 0.024106 | -0.0007% |
| ast | 16430 | 0.009930 | 0.009930 | -0.0014% |
| tov | 16430 | 0.007636 | 0.007636 | +0.0031% |
| stl | 16430 | 0.004218 | 0.004219 | -0.0052% |
| blk | 16430 | 0.002613 | 0.002614 | -0.0066% |
| fg3m | 16430 | 0.005463 | 0.005462 | +0.0186% |
