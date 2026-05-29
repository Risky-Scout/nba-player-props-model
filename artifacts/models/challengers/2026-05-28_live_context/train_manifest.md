# Phase 13P Live-Context Challenger — 2026-05-28

- feature_set_id: `phase13p_lineup_injury_driver_v1`
- rows_used: 82091
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
| minutes | 16419 | 57.790628 | 57.149719 | +1.1090% |
| pts | 16419 | 0.096038 | 0.096021 | +0.0176% |
| reb | 16419 | 0.024113 | 0.024113 | -0.0009% |
| ast | 16419 | 0.009935 | 0.009935 | -0.0013% |
| tov | 16419 | 0.007634 | 0.007634 | +0.0033% |
| stl | 16419 | 0.004221 | 0.004221 | -0.0053% |
| blk | 16419 | 0.002615 | 0.002615 | -0.0067% |
| fg3m | 16419 | 0.005466 | 0.005465 | +0.0193% |
