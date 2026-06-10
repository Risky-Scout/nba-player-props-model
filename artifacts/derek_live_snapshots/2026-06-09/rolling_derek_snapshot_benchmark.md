# Rolling Derek snapshot benchmark — as-of 2026-06-09

- window_days: 28
- generated_at_utc: 2026-06-10T01:58:42+00:00
- dates_included: 9
- dates_missing: 19
- rows_total: 254
- minimum_sample_passed (>=200): **True**

## By snapshot type

| snapshot_type | rows | mean_nll | model_logloss | market_logloss | Δ (model−market) |
| --- | ---: | ---: | ---: | ---: | ---: |
| close_lock | 67 | 2.069729708264571 | None | None | None |
| current_live | 152 | 2.4968281600315576 | None | None | None |
| t_minus_25 | 35 | 3.1430827712546057 | None | None | None |
