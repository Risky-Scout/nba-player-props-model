# Champion vs Challenger Validation — 2026-05-13

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-15T01:34:18+00:00 |
| Promote | no |
| Reason | gate_failed:m6_3_stat_role_matrix_valid |
| Champion model_version | challenger-2026-04-30 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 17 |
| Gates failed | 5 |

## Gates passed

- nll_improves_or_non_worse: challenger=3.93992 champion=3.93992 delta=+0 (tol=0.03939923563146953)
- rps_improves_or_non_worse: challenger=1.1109 champion=1.1109 delta=+0 (tol=0.01110896424181148)
- calibration_error_improves: challenger=0.322082 champion=0.322082 delta=-5.55112e-17 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.322082 champion=0.322082 delta=-5.55112e-17 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.369801 champion=0.369801 delta=+4.996e-16 (tol=0.05)
- tov_does_not_regress: challenger=1.34761 champion=1.34761 delta=+0 (tol=0.026952124611520557)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=0.0
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.0
- no_severe_stat_bucket_regression: worst_stat=fg3m delta=0.0
- pmf_validity: ok
- no_future_leakage: future_rows_excluded=0
- sufficient_calibration_samples: total_samples_in_calibration_window=178344
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- promotion_clock_safe: before 14:30 UTC
- no_phase10d_overlays_referenced: ok
- market_benchmark_available: rows_total=5625 dates_included=9

## Gates failed

- m6_3_stat_role_matrix_valid: expected 66 rows, found 66; stat mismatch missing=['ra'] extra=[]; missing_cells=['ra|bench', 'ra|core', 'ra|fringe', 'ra|inactive_risk', 'ra|rotation', 'ra|starter']
- m6_3_review_cells_guarded: review_cells=18 guarded_cells=18
- market_logloss_non_inferior_or_better: delta_logloss=0.036980768653124906 tolerance=0.005 (negative favors model)
- market_brier_non_inferior_or_better: delta_brier=0.012077780653008373 tolerance=0.005 (negative favors model)
- no_severe_market_stat_bucket_regression: severe market regression on reb: delta_logloss=+0.0981
