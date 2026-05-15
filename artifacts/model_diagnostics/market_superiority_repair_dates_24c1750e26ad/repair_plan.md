# Market superiority repair plan (dates_24c1750e26ad)

- Segments: **84**
- Dominant failure counts:
  - `insufficient_scored_rows`: 42
  - `model_prob_too_high_or_overconfident_side`: 29
  - `mean_too_low`: 6
  - `nan`: 5
  - `model_logloss_not_better`: 1
  - `variance_too_narrow`: 1

## Highest-priority next actions

- `review_segment_diagnostics`: 47 segments
- `fit_event_neutral_probability_scale_repair`: 29 segments
- `fit_pmf_mean_shift_repair`: 6 segments
- `collect_more_oof_data_or_retrain`: 1 segments
- `fit_pmf_variance_temperature_repair`: 1 segments

