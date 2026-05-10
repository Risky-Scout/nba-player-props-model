# Previous-Day No-Leakage Verification — 2026-05-09

- target_date_et: 2026-05-09
- resolved_training_cutoff_date: 2026-05-09
- stale_fallback_used: False
- leakage_checks_passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| fold_aggregate_max_game_date | yes | max=2026-05-09 cutoff=2026-05-09 source=fold_aggregate.parquet |
| train_manifest_max_date | yes | max=2026-05-09 cutoff=2026-05-09 |
| train_manifest_real_run | yes | dry_run=False |
| train_manifest_future_rows_excluded_recorded | yes | future_rows_excluded=0 |
| calibration_validation_window_end | yes | validation_window_end=2026-05-09 cutoff=2026-05-09 |
| calibration_training_window_end | yes | training_window_end=2026-04-11 cutoff=2026-05-09 |
| calibration_manifest_real_run | yes | dry_run=False |
| validation_challenger_holdout_window_end | yes | end=2026-05-09 cutoff=2026-05-09 |
| validation_champion_holdout_window_end | yes | end=2026-05-09 cutoff=2026-05-09 |
| validation_challenger_dry_run_false | yes | validation.challenger.dry_run=False |
| training_inputs_no_future_rows | yes | rows_after_cutoff=153664 future_rows_excluded=0 |

## Max dates seen

```
{
  "fold_aggregate": "2026-05-09",
  "training_summary_max_date": "2026-05-09",
  "future_rows_excluded": 0,
  "calibration_validation_window_end": "2026-05-09",
  "calibration_training_window_end": "2026-04-11",
  "challenger_holdout_window_end": "2026-05-09",
  "champion_holdout_window_end": "2026-05-09",
  "prepare_fold_aggregate_rows_after_cutoff": 153664,
  "prepare_fold_aggregate_future_rows_excluded": 0
}
```
