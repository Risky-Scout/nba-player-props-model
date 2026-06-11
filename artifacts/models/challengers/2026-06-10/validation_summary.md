# Champion vs Challenger Validation — 2026-06-10

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-06-11T23:12:11+00:00 |
| Promote | no |
| Reason | gate_failed:market_benchmark_available |
| Champion model_version | challenger-2026-06-10 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 17 |
| Gates failed | 1 |

## Gates passed

- nll_improves_or_non_worse: challenger=1.79609 champion=1.79609 delta=+0 (tol=0.017960875619944774)
- rps_improves_or_non_worse: challenger=0.946597 champion=0.946597 delta=+0 (tol=0.009465969374563324)
- calibration_error_improves: challenger=0.315058 champion=0.315058 delta=+0 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.315058 champion=0.315058 delta=+0 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.0549521 champion=0.0549521 delta=+0 (tol=0.05)
- tov_does_not_regress: challenger=1.30324 champion=1.30324 delta=+0 (tol=0.02606479208654391)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=0.0
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.0
- no_severe_stat_bucket_regression: worst_stat=pts delta=0.0
- pmf_validity: ok
- no_future_leakage: real_train train_manifest.status='ok'; pg_stats_summary.error=None (OOF fold_aggregate cutoff is leakage authority)
- sufficient_calibration_samples: total_samples_in_calibration_window=172770
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok
- m6_3_stat_role_matrix_valid: valid
- m6_3_review_cells_guarded: review_cells=18 guarded_cells=18

## Gates failed

- market_benchmark_available: rolling market benchmark JSON not produced for this date
