# Phase 13P Live-Context Challenger — 2026-06-03

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82130
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
| minutes | 16426 | 57.779915 | 57.142218 | +1.1037% |
| pts | 16426 | 0.096000 | 0.095983 | +0.0173% |
| reb | 16426 | 0.024108 | 0.024108 | -0.0008% |
| ast | 16426 | 0.009932 | 0.009932 | -0.0014% |
| tov | 16426 | 0.007633 | 0.007633 | +0.0033% |
| stl | 16426 | 0.004219 | 0.004220 | -0.0052% |
| blk | 16426 | 0.002614 | 0.002614 | -0.0066% |
| fg3m | 16426 | 0.005464 | 0.005463 | +0.0188% |
