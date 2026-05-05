# Nightly Training/Calibration Run — 2026-05-03

- final_status: **ok**
- halted_reason: (none)
- dry_run: False
- no_promote: True
- promoted: False

## Steps

- **source_data_refresh**: exit_code=0 log=artifacts/nightly_training/2026-05-03/logs/source_data_refresh.log
- **previous_day_source_completeness**: exit_code=0 log=artifacts/nightly_training/2026-05-03/logs/previous_day_source_completeness.log
- **readiness**: exit_code=0 log=artifacts/nightly_training/2026-05-03/logs/readiness.log
- **training_input_preflight**: exit_code=0 log=artifacts/nightly_training/2026-05-03/logs/training_input_preflight.log
- **prepare_training_inputs**: exit_code=0 log=artifacts/nightly_training/2026-05-03/logs/prepare_training_inputs.log
- **train_challenger**: exit_code=0 log=artifacts/nightly_training/2026-05-03/logs/train_challenger.log
- **calibrate_challenger**: exit_code=0 log=artifacts/nightly_training/2026-05-03/logs/calibrate_challenger.log
- **rolling_market_benchmark**: exit_code=0 log=artifacts/nightly_training/2026-05-03/logs/rolling_market_benchmark.log
- **validate**: exit_code=0 log=artifacts/nightly_training/2026-05-03/logs/validate.log
- **promote**: skipped (--no-promote was set)

## Smoke Tests

- champion_pointer_smoke: passed=True
- derek_compat_smoke: passed=True
- woo_compat_smoke: passed=True
