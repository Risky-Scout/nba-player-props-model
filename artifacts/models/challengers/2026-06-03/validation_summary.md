# Champion vs Challenger Validation — 2026-06-03

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-06-04T18:10:21+00:00 |
| Promote | no |
| Reason | gate_failed:market_logloss_non_inferior_or_better |
| Champion model_version | challenger-2026-06-03 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 18 |
| Gates failed | 3 |

## Gates passed

- nll_improves_or_non_worse: challenger=1.70963 champion=1.70963 delta=+0 (tol=0.017096347391233575)
- rps_improves_or_non_worse: challenger=0.935445 champion=0.935445 delta=+0 (tol=0.009354446551171479)
- calibration_error_improves: challenger=0.310748 champion=0.310748 delta=+0 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.310748 champion=0.310748 delta=+0 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.0157288 champion=0.0157288 delta=+0 (tol=0.05)
- tov_does_not_regress: challenger=1.28105 champion=1.28105 delta=+0 (tol=0.02562092273401159)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=0.0
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.0
- no_severe_stat_bucket_regression: worst_stat=pts delta=0.0
- pmf_validity: ok
- no_future_leakage: real_train train_manifest.status='ok'; pg_stats_summary.error=None (OOF fold_aggregate cutoff is leakage authority)
- sufficient_calibration_samples: total_samples_in_calibration_window=174102
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok
- m6_3_stat_role_matrix_valid: valid
- m6_3_review_cells_guarded: review_cells=8 guarded_cells=8
- market_benchmark_available: rows_total=2263 dates_included=10

## Gates failed

- market_logloss_non_inferior_or_better: delta_logloss=0.06994340047031351 tolerance=0.005 (negative favors model)
- market_brier_non_inferior_or_better: delta_brier=0.020500560150660083 tolerance=0.005 (negative favors model)
- no_severe_market_stat_bucket_regression: severe market regression on reb: delta_logloss=+0.1575
