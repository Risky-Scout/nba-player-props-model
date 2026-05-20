# Champion vs Challenger Validation — 2026-05-19

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-20T17:29:18+00:00 |
| Promote | no |
| Reason | gate_failed:nll_improves_or_non_worse |
| Champion model_version | challenger-2026-04-30 |
| Challenger dry_run | True |
| PMF validity issues | 0 |
| Gates passed | 7 |
| Gates failed | 14 |

## Gates passed

- pmf_validity: ok
- no_future_leakage: dry_run future_rows_excluded=0 error=None
- sufficient_calibration_samples: total_samples_in_calibration_window=177324
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok
- market_benchmark_available: rows_total=5625 dates_included=10

## Gates failed

- nll_improves_or_non_worse: dry_run challenger == champion; no improvement to demonstrate
- rps_improves_or_non_worse: dry_run challenger == champion; no improvement to demonstrate
- calibration_error_improves: dry_run challenger == champion; no improvement to demonstrate
- p0_error_improves_or_non_worse: dry_run challenger == champion; no improvement to demonstrate
- mean_bias_does_not_worsen: dry_run challenger == champion; no improvement to demonstrate
- tov_does_not_regress: dry_run challenger == champion; no improvement to demonstrate
- starter_core_role_buckets_do_not_regress: dry_run challenger == champion; no improvement to demonstrate
- bench_fringe_role_buckets_do_not_regress_materially: dry_run challenger == champion; no improvement to demonstrate
- no_severe_stat_bucket_regression: dry_run challenger == champion; no improvement to demonstrate
- m6_3_stat_role_matrix_valid: expected 66 rows, found 66; stat mismatch missing=['ra'] extra=[]; missing_cells=['ra|bench', 'ra|core', 'ra|fringe', 'ra|inactive_risk', 'ra|rotation', 'ra|starter']
- m6_3_review_cells_guarded: review_cells=18 guarded_cells=18
- market_logloss_non_inferior_or_better: delta_logloss=0.036980768653124906 tolerance=0.005 (negative favors model)
- market_brier_non_inferior_or_better: delta_brier=0.012077780653008373 tolerance=0.005 (negative favors model)
- no_severe_market_stat_bucket_regression: severe market regression on reb: delta_logloss=+0.0981
