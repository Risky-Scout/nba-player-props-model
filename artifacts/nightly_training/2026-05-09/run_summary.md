# Nightly Training/Calibration Run — 2026-05-09

- final_status: **halted_no_promotion**
- halted_reason: promotion_clock_cutoff
- dry_run: False
- no_promote: False
- promoted: False

## Steps

- **source_data_refresh**: exit_code=0 log=artifacts/nightly_training/2026-05-09/logs/source_data_refresh.log
- **previous_day_source_completeness**: exit_code=0 log=artifacts/nightly_training/2026-05-09/logs/previous_day_source_completeness.log
- **readiness**: exit_code=0 log=artifacts/nightly_training/2026-05-09/logs/readiness.log
- **training_input_preflight**: exit_code=0 log=artifacts/nightly_training/2026-05-09/logs/training_input_preflight.log
- **prepare_training_inputs**: exit_code=0 log=artifacts/nightly_training/2026-05-09/logs/prepare_training_inputs.log
- **train_challenger**: exit_code=0 log=artifacts/nightly_training/2026-05-09/logs/train_challenger.log
- **calibrate_challenger**: exit_code=0 log=artifacts/nightly_training/2026-05-09/logs/calibrate_challenger.log
- **rolling_market_benchmark**: exit_code=0 log=artifacts/nightly_training/2026-05-09/logs/rolling_market_benchmark.log
- **validate**: exit_code=0 log=artifacts/nightly_training/2026-05-09/logs/validate.log
- **promote**: skipped (promotion_clock_unsafe_at_or_after_14:30_utc)

## Smoke Tests

- champion_pointer_smoke: passed=True
- derek_compat_smoke: passed=True
- woo_compat_smoke: passed=True
