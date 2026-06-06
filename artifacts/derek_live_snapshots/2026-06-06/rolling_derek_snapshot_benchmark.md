# Rolling Derek snapshot benchmark — as-of 2026-06-06

- window_days: 28
- generated_at_utc: 2026-06-06T23:46:56+00:00
- dates_included: 9
- dates_missing: 19
- rows_total: 322
- minimum_sample_passed (>=200): **True**

## By snapshot type

| snapshot_type | rows | mean_nll | model_logloss | market_logloss | Δ (model−market) |
| --- | ---: | ---: | ---: | ---: | ---: |
| close_lock | 165 | 2.054341309630842 | None | None | None |
| current_live | 122 | 2.545324750719958 | None | None | None |
| t_minus_25 | 35 | 3.1430827712546057 | None | None | None |
