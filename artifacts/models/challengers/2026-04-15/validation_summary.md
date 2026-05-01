# Champion vs Challenger Validation — 2026-04-15

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-01T02:43:18+00:00 |
| Promote | YES |
| Reason | all_gates_passed |
| Champion model_version | 2026-03-09-v12 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 16 |
| Gates failed | 0 |

## Gates passed

- nll_improves_or_non_worse: challenger=2.23914 champion=2.23914 delta=+0 (tol=0.02239135518103993)
- rps_improves_or_non_worse: challenger=1.33796 champion=1.33796 delta=+0 (tol=0.013379572548724312)
- calibration_error_improves: challenger=0.269349 champion=0.269349 delta=+0 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.269349 champion=0.269349 delta=+0 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.107833 champion=0.107833 delta=+0 (tol=0.05)
- tov_does_not_regress: challenger=1.4012 champion=1.4012 delta=+0 (tol=0.028023922087598362)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=0.0
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.0
- no_severe_stat_bucket_regression: worst_stat=pts delta=0.0
- pmf_validity: ok
- no_future_leakage: future_rows_excluded=870
- sufficient_calibration_samples: total_samples_in_calibration_window=195732
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- promotion_clock_safe: before 14:30 UTC
- no_phase10d_overlays_referenced: ok

## Gates failed

- (none)
