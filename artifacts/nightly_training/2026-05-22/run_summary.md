# Nightly Training/Calibration Run — 2026-05-22

- final_status: **ok**
- halted_reason: (none)
- dry_run: False
- no_promote: False
- promoted: False

## Steps

- **source_data_refresh**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/source_data_refresh.log
- **previous_day_source_completeness**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/previous_day_source_completeness.log
- **readiness**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/readiness.log
- **training_input_preflight**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/training_input_preflight.log
- **prepare_training_inputs**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/prepare_training_inputs.log
- **train_challenger**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/train_challenger.log
- **calibrate_challenger**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/calibrate_challenger.log
- **rolling_market_benchmark**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/rolling_market_benchmark.log
- **validate**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/validate.log
- **promote**: exit_code=1 log=artifacts/nightly_training/2026-05-22/logs/promote.log
- **verify_champion_pointer_contextual_contract**: exit_code=0 log=artifacts/nightly_training/2026-05-22/logs/verify_champion_pointer_contextual_contract.log

## Smoke Tests

- champion_pointer_smoke: passed=True
- derek_compat_smoke: passed=True
- woo_compat_smoke: passed=True
