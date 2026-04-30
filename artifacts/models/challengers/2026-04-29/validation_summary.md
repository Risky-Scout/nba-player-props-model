# Champion vs Challenger Validation — 2026-04-29

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-04-30T22:49:24+00:00 |
| Promote | no |
| Reason | gate_failed:nll_improves_or_non_worse |
| Champion model_version | 2026-03-09-v12 |
| Challenger dry_run | True |
| PMF validity issues | 0 |
| Gates passed | 6 |
| Gates failed | 10 |

## Gates passed

- pmf_validity: ok
- no_future_leakage: future_rows_excluded=0
- sufficient_calibration_samples: total_samples_in_calibration_window=187812
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok

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
- promotion_clock_safe: AT OR AFTER 14:30 UTC — too close to WoO run
