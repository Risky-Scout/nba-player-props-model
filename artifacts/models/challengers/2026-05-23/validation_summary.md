# Champion vs Challenger Validation — 2026-05-23

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-24T14:19:33+00:00 |
| Promote | no |
| Reason | gate_failed:m6_3_stat_role_matrix_valid |
| Champion model_version | challenger-2026-04-30 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 16 |
| Gates failed | 5 |

## Gates passed

- nll_improves_or_non_worse: challenger=1.69826 champion=1.69826 delta=+0 (tol=0.016982608593554646)
- rps_improves_or_non_worse: challenger=0.949547 champion=0.949547 delta=+0 (tol=0.009495474177241557)
- calibration_error_improves: challenger=0.316235 champion=0.316235 delta=+0 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.316235 champion=0.316235 delta=+0 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.0669141 champion=0.0669141 delta=+0 (tol=0.05)
- tov_does_not_regress: challenger=1.28057 champion=1.28057 delta=+0 (tol=0.02561141548757333)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=0.0
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.0
- no_severe_stat_bucket_regression: worst_stat=pts delta=0.0
- pmf_validity: ok
- no_future_leakage: real_train train_manifest.status='ok'; pg_stats_summary.error=None (OOF fold_aggregate cutoff is leakage authority)
- sufficient_calibration_samples: total_samples_in_calibration_window=176562
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok
- market_benchmark_available: rows_total=5625 dates_included=11

## Gates failed

- m6_3_stat_role_matrix_valid: expected 66 rows, found 66; stat mismatch missing=['ra'] extra=[]; missing_cells=['ra|bench', 'ra|core', 'ra|fringe', 'ra|inactive_risk', 'ra|rotation', 'ra|starter']
- m6_3_review_cells_guarded: review_cells=18 guarded_cells=18
- market_logloss_non_inferior_or_better: delta_logloss=0.036980768653124906 tolerance=0.005 (negative favors model)
- market_brier_non_inferior_or_better: delta_brier=0.012077780653008373 tolerance=0.005 (negative favors model)
- no_severe_market_stat_bucket_regression: severe market regression on reb: delta_logloss=+0.0981
