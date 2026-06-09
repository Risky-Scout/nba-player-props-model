# Rolling Derek snapshot benchmark — as-of 2026-06-09

- window_days: 28
- generated_at_utc: 2026-06-09T04:23:07+00:00
- dates_included: 8
- dates_missing: 20
- rows_total: 224
- minimum_sample_passed (>=200): **True**

## By snapshot type

| snapshot_type | rows | mean_nll | model_logloss | market_logloss | Δ (model−market) |
| --- | ---: | ---: | ---: | ---: | ---: |
| close_lock | 67 | 2.069729708264571 | None | None | None |
| current_live | 122 | 2.545324750719958 | None | None | None |
| t_minus_25 | 35 | 3.1430827712546057 | None | None | None |
