# Nightly Training/Calibration Run — 2026-04-28

- final_status: **ok**
- halted_reason: (none)
- dry_run: False
- no_promote: True
- promoted: False

## Steps

- **resolve_previous_day_et_target**: exit_code=0 log=artifacts/nightly_training/logs/resolve_previous_day_et_target.log
- **readiness**: exit_code=0 log=artifacts/nightly_training/2026-04-28/logs/readiness.log
- **training_input_preflight**: exit_code=0 log=artifacts/nightly_training/2026-04-28/logs/training_input_preflight.log
- **prepare_training_inputs**: exit_code=0 log=artifacts/nightly_training/2026-04-28/logs/prepare_training_inputs.log
- **train_challenger**: exit_code=0 log=artifacts/nightly_training/2026-04-28/logs/train_challenger.log
- **calibrate_challenger**: exit_code=0 log=artifacts/nightly_training/2026-04-28/logs/calibrate_challenger.log
- **validate**: exit_code=0 log=artifacts/nightly_training/2026-04-28/logs/validate.log
- **promote**: skipped (--no-promote was set)

## Smoke Tests

- champion_pointer_smoke: passed=True
- derek_compat_smoke: passed=True
- woo_compat_smoke: passed=True
