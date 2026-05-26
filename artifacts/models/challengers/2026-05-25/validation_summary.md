# Champion vs Challenger Validation — 2026-05-25

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-26T18:21:09+00:00 |
| Promote | no |
| Reason | gate_failed:market_logloss_non_inferior_or_better |
| Champion model_version | challenger-2026-05-22 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 18 |
| Gates failed | 3 |

## Gates passed

- nll_improves_or_non_worse: challenger=1.70272 champion=1.70272 delta=+0 (tol=0.017027204021985702)
- rps_improves_or_non_worse: challenger=0.938405 champion=0.938405 delta=+0 (tol=0.009384048385821235)
- calibration_error_improves: challenger=0.315736 champion=0.315736 delta=+0 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.315736 champion=0.315736 delta=+0 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.0791911 champion=0.0791911 delta=+0 (tol=0.05)
- tov_does_not_regress: challenger=1.28875 champion=1.28875 delta=+0 (tol=0.025774914033808317)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=0.0
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.0
- no_severe_stat_bucket_regression: worst_stat=pts delta=0.0
- pmf_validity: ok
- no_future_leakage: real_train train_manifest.status='ok'; pg_stats_summary.error=None (OOF fold_aggregate cutoff is leakage authority)
- sufficient_calibration_samples: total_samples_in_calibration_window=176022
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok
- m6_3_stat_role_matrix_valid: valid
- m6_3_review_cells_guarded: review_cells=1 guarded_cells=1
- market_benchmark_available: rows_total=5625 dates_included=13

## Gates failed

- market_logloss_non_inferior_or_better: delta_logloss=0.036980768653124906 tolerance=0.005 (negative favors model)
- market_brier_non_inferior_or_better: delta_brier=0.012077780653008373 tolerance=0.005 (negative favors model)
- no_severe_market_stat_bucket_regression: severe market regression on reb: delta_logloss=+0.0981
