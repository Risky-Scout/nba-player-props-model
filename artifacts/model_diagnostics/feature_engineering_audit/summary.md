# Player-prop feature engineering audit

- training rows: **511693**
- event market rows: **147142**
- families missing in training: **9**
- families missing in event rows: **14**

## Expected findings
- `lineup_features_insufficient_in_training_table`: `True`
- `event_market_rows_missing_lineup_usage_rest_context`: `True`
- `injury_availability_features_too_sparse`: `True`
