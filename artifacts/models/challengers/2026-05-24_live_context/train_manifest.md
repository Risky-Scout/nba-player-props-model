# Phase 13P Live-Context Challenger — 2026-05-24

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82010
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
| minutes | 16402 | 57.823904 | 57.183252 | +1.1079% |
| pts | 16402 | 0.095944 | 0.095928 | +0.0172% |
| reb | 16402 | 0.024118 | 0.024118 | -0.0009% |
| ast | 16402 | 0.009931 | 0.009931 | -0.0010% |
| tov | 16402 | 0.007636 | 0.007636 | +0.0032% |
| stl | 16402 | 0.004221 | 0.004222 | -0.0055% |
| blk | 16402 | 0.002617 | 0.002617 | -0.0068% |
| fg3m | 16402 | 0.005465 | 0.005464 | +0.0194% |
