# Champion vs Challenger Validation — 2026-06-14

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-06-15T13:42:30+00:00 |
| Promote | no |
| Reason | gate_failed:market_benchmark_available |
| Champion model_version | challenger-2026-06-13 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 17 |
| Gates failed | 1 |

## Gates passed

- nll_improves_or_non_worse: challenger=1.78759 champion=1.78759 delta=+0 (tol=0.017875900903203498)
- rps_improves_or_non_worse: challenger=0.94802 champion=0.94802 delta=+0 (tol=0.009480195964368873)
- calibration_error_improves: challenger=0.312648 champion=0.312648 delta=+0 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.312648 champion=0.312648 delta=+0 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.0510691 champion=0.0510691 delta=+0 (tol=0.05)
- tov_does_not_regress: challenger=1.3222 champion=1.3222 delta=+0 (tol=0.02644394707906244)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=0.0
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.0
- no_severe_stat_bucket_regression: worst_stat=pts delta=0.0
- pmf_validity: ok
- no_future_leakage: real_train train_manifest.status='ok'; pg_stats_summary.error=None (OOF fold_aggregate cutoff is leakage authority)
- sufficient_calibration_samples: total_samples_in_calibration_window=172122
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok
- m6_3_stat_role_matrix_valid: valid
- m6_3_review_cells_guarded: review_cells=16 guarded_cells=16

## Gates failed

- market_benchmark_available: rolling market benchmark JSON not produced for this date
