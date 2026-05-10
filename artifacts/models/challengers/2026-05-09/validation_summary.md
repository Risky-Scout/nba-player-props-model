# Champion vs Challenger Validation — 2026-05-09

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-10T19:41:57+00:00 |
| Promote | no |
| Reason | gate_failed:promotion_clock_safe |
| Champion model_version | challenger-2026-04-30 |
| Challenger dry_run | False |
| PMF validity issues | 0 |
| Gates passed | 16 |
| Gates failed | 4 |

## Gates passed

- nll_improves_or_non_worse: challenger=1.86551 champion=1.86674 delta=-0.00123048 (tol=0.018667394024116532)
- rps_improves_or_non_worse: challenger=1.08089 champion=1.08085 delta=+3.61787e-05 (tol=0.010808519988841962)
- calibration_error_improves: challenger=0.310836 champion=0.310884 delta=-4.8074e-05 (tol=0.0)
- p0_error_improves_or_non_worse: challenger=0.310836 champion=0.310884 delta=-4.8074e-05 (tol=0.005)
- mean_bias_does_not_worsen: challenger=0.118846 champion=0.117857 delta=+0.000988534 (tol=0.05)
- tov_does_not_regress: challenger=1.44489 champion=1.44443 delta=+0.000461533 (tol=0.028888554051839196)
- starter_core_role_buckets_do_not_regress: worst_core_nll_delta=-0.001118765258732335
- bench_fringe_role_buckets_do_not_regress_materially: worst_bench_nll_delta=0.000565805524936458
- no_severe_stat_bucket_regression: worst_stat=tov delta=0.0004615327338588493
- pmf_validity: ok
- no_future_leakage: future_rows_excluded=0
- sufficient_calibration_samples: total_samples_in_calibration_window=181266
- derek_feed_compatibility: ok
- woo_export_compatibility: ok
- no_phase10d_overlays_referenced: ok
- market_benchmark_available: rows_total=4340 dates_included=8

## Gates failed

- promotion_clock_safe: AT OR AFTER 14:30 UTC — too close to WoO run
- market_logloss_non_inferior_or_better: delta_logloss=0.046709075611009385 tolerance=0.005 (negative favors model)
- market_brier_non_inferior_or_better: delta_brier=0.015209114493651185 tolerance=0.005 (negative favors model)
- no_severe_market_stat_bucket_regression: severe market regression on reb: delta_logloss=+0.0898
