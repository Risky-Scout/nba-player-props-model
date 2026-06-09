# Champion vs Challenger Validation — 2026-06-08

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-06-09T10:55:50+00:00 |
| Promote | no |
| Reason | gate_failed:no_severe_market_stat_bucket_regression |
| Champion model_version | challenger-2026-06-06 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 20 |
| Gates failed | 1 |

## Gates passed

- nll_improves_or_non_worse: challenger=1.70963 champion=1.73215 delta=-0.0225138 (tol=0.017321485268945835)
- rps_improves_or_non_worse: challenger=0.935445 champion=0.942705 delta=-0.00726063 (tol=0.009427052866226856)
- calibration_error_improves: challenger=0.310748 champion=0.318073 delta=-0.00732573 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.310748 champion=0.318073 delta=-0.00732573 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.0157288 champion=0.0787003 delta=-0.0629716 (tol=0.05)
- tov_does_not_regress: challenger=1.28105 champion=1.28375 delta=-0.00269927 (tol=0.025674908168695394)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=-0.023808959228654114
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=-0.018559695513246544
- no_severe_stat_bucket_regression: worst_stat=fg3m delta=0.008162416540465678
- pmf_validity: ok
- no_future_leakage: real_train train_manifest.status='ok'; pg_stats_summary.error=None (OOF fold_aggregate cutoff is leakage authority)
- sufficient_calibration_samples: total_samples_in_calibration_window=173154
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok
- m6_3_stat_role_matrix_valid: valid
- m6_3_review_cells_guarded: review_cells=8 guarded_cells=8
- market_benchmark_available: rows_total=1285 dates_included=10
- market_logloss_non_inferior_or_better: delta_logloss=0.00412407433622323 tolerance=0.005 (negative favors model)
- market_brier_non_inferior_or_better: delta_brier=0.0015019138293587016 tolerance=0.005 (negative favors model)

## Gates failed

- no_severe_market_stat_bucket_regression: severe market regression on reb: delta_logloss=+0.1309
