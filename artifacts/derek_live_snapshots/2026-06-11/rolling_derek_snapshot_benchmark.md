# Rolling Derek snapshot benchmark — as-of 2026-06-11

- window_days: 28
- generated_at_utc: 2026-06-11T18:58:43+00:00
- dates_included: 10
- dates_missing: 18
- rows_total: 289
- minimum_sample_passed (>=200): **True**

## By snapshot type

| snapshot_type | rows | mean_nll | model_logloss | market_logloss | Δ (model−market) |
| --- | ---: | ---: | ---: | ---: | ---: |
| close_lock | 67 | 2.069729708264571 | None | None | None |
| current_live | 187 | 2.4474463372405237 | None | None | None |
| t_minus_25 | 35 | 3.1430827712546057 | None | None | None |
