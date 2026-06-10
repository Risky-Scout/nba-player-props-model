# Champion vs Challenger Validation — 2026-06-09

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-06-10T18:27:03+00:00 |
| Promote | no |
| Reason | gate_failed:market_benchmark_available |
| Champion model_version | challenger-2026-06-08 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 17 |
| Gates failed | 1 |

## Gates passed

- nll_improves_or_non_worse: challenger=1.77024 champion=1.77024 delta=+0 (tol=0.017702429447929446)
- rps_improves_or_non_worse: challenger=0.944668 champion=0.944668 delta=+0 (tol=0.009446678915981457)
- calibration_error_improves: challenger=0.317274 champion=0.317274 delta=+0 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.317274 champion=0.317274 delta=+0 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.033144 champion=0.033144 delta=+0 (tol=0.05)
- tov_does_not_regress: challenger=1.30042 champion=1.30042 delta=+0 (tol=0.02600840862620328)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=0.0
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.0
- no_severe_stat_bucket_regression: worst_stat=pts delta=0.0
- pmf_validity: ok
- no_future_leakage: real_train train_manifest.status='ok'; pg_stats_summary.error=None (OOF fold_aggregate cutoff is leakage authority)
- sufficient_calibration_samples: total_samples_in_calibration_window=172872
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok
- m6_3_stat_role_matrix_valid: valid
- m6_3_review_cells_guarded: review_cells=16 guarded_cells=16

## Gates failed

- market_benchmark_available: rolling market benchmark JSON not produced for this date
