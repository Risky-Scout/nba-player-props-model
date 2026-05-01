# Champion vs Challenger Validation — 2026-04-28

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-01T10:54:27+00:00 |
| Promote | YES |
| Reason | all_gates_passed |
| Champion model_version | 2026-03-09-v12 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 16 |
| Gates failed | 0 |

## Gates passed

- nll_improves_or_non_worse: challenger=2.01054 champion=2.01054 delta=+0 (tol=0.02010541822286629)
- rps_improves_or_non_worse: challenger=1.21143 champion=1.21143 delta=+0 (tol=0.012114344004962268)
- calibration_error_improves: challenger=0.278306 champion=0.278306 delta=+0 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.278306 champion=0.278306 delta=+0 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.299249 champion=0.299249 delta=+0 (tol=0.05)
- tov_does_not_regress: challenger=1.28738 champion=1.28738 delta=+0 (tol=0.02574768217016353)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=0.0
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.0
- no_severe_stat_bucket_regression: worst_stat=pts delta=0.0
- pmf_validity: ok
- no_future_leakage: future_rows_excluded=17
- sufficient_calibration_samples: total_samples_in_calibration_window=188694
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- promotion_clock_safe: before 14:30 UTC
- no_phase10d_overlays_referenced: ok

## Gates failed

- (none)
