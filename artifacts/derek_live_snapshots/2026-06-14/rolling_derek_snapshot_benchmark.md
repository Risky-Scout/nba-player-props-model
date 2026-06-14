# Rolling Derek snapshot benchmark — as-of 2026-06-14

- window_days: 28
- generated_at_utc: 2026-06-14T20:26:19+00:00
- dates_included: 11
- dates_missing: 17
- rows_total: 372
- minimum_sample_passed (>=200): **True**

## By snapshot type

| snapshot_type | rows | mean_nll | model_logloss | market_logloss | Δ (model−market) |
| --- | ---: | ---: | ---: | ---: | ---: |
| close_lock | 67 | 2.069729708264571 | None | None | None |
| current_live | 228 | 2.3800790473201885 | None | None | None |
| t_minus_25 | 77 | 2.569581445218276 | None | None | None |
