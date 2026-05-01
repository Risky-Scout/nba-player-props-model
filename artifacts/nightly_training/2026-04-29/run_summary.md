# Nightly Training/Calibration Run — 2026-04-29

- final_status: **ok**
- halted_reason: (none)
- dry_run: True
- no_promote: True
- promoted: False

## Steps

- **readiness**: exit_code=0 log=artifacts/nightly_training/2026-04-29/logs/readiness.log
- **train_challenger**: exit_code=0 log=artifacts/nightly_training/2026-04-29/logs/train_challenger.log
- **calibrate_challenger**: exit_code=0 log=artifacts/nightly_training/2026-04-29/logs/calibrate_challenger.log
- **validate**: exit_code=0 log=artifacts/nightly_training/2026-04-29/logs/validate.log
- **promote**: skipped (--no-promote was set)

## Smoke Tests

- champion_pointer_smoke: passed=True
- derek_compat_smoke: passed=True
- woo_compat_smoke: passed=True
