# Training Automation Verification — 2026-05-17

- generated_at_utc: 2026-05-18T12:56:11+00:00
- mode: **real_training**
- overall_pass: **False**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| readiness_report_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/training_readiness/2026-05-17/readiness_report.json |
| challenger_dir_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/models/challengers/2026-05-17 |
| train_manifest_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/models/challengers/2026-05-17/train_manifest.json |
| calibration_manifest_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/models/challengers/2026-05-17/calibration_manifest.json |
| validation_report_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/models/challengers/2026-05-17/validation_report.json |
| promotion_decision_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/models/challengers/2026-05-17/promotion_decision.json |
| champion_pointer_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/models/registry/champion_pointer.json |
| model_registry_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/models/registry/model_registry.json |
| promotion_log_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/models/registry/promotion_log.csv |
| nightly_run_manifest_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/nightly_training/2026-05-17/run_manifest.json |
| smoke_test_report_exists | yes | /home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/nightly_training/2026-05-17/smoke_test_report.json |
| champion_pointer_unchanged_when_promote_false | yes | pointer model_version present and unchanged (promote was false) |
| pmf_validity_passed | yes | issues=[] |
| derek_compat_smoke_passed | yes | {"build_derek_forward_feed.py_present": true, "challenger_dir_referenced": false, "champion_pointer_used_only": true} |
| woo_compat_smoke_passed | yes | {"build_wizard_of_odds_public_export.py_present": true, "challenger_dir_referenced": false, "champion_pointer_used_only": true} |
| no_secrets_in_manifests | yes | hits=[] |
| no_phase10d_overlays_in_manifests | yes | hits=[] |
| no_raw_dir_referenced_in_manifests | yes | manifests do not name artifacts/raw/ |
| training_run_reproducible | yes | missing_train=set() missing_cal=set() |
| workflow_file_exists | yes | .github/workflows/nightly_training_calibration.yml |
| workflow_calls_orchestrator | yes |  |
| workflow_has_safe_cron | yes | expected cron '30 9 * * *' present |
| workflow_has_timeout_protection | yes |  |
| workflow_uses_required_secrets | yes |  |
| workflow_uses_correct_authorship | yes |  |
| workflow_no_phase10d_overlays | yes | hits=[] |
| no_delivery_references_challenger_dir | yes | violations=[] |
| promotion_uses_atomic_pointer_update | yes |  |
| failure_mode_keeps_champion_unchanged | NO | pre=fe5f8f1db44e post=f5ab19b3999c |
| no_forbidden_files_staged | yes | staged_violations=[] |
| real_training_challenger_pickles_present | yes | challenger_pickles=8 (must be > 0 when dry_run=false) |
| real_training_validation_scored_real_artifacts | yes | validation_report.challenger.dry_run=False |
| real_training_metrics_computed | yes | challenger_has_metric=True champion_has_metric=True |

## Mode details

```
{
  "train_manifest_dry_run": false,
  "calibration_manifest_dry_run": false,
  "challenger_pickle_count": 8,
  "run_manifest_halted_reason": null,
  "run_manifest_final_status": "ok",
  "train_manifest_status": "ok",
  "manifest_recorded_pickle_count": 8,
  "pickles_source": "on_disk"
}
```

## Failure-mode simulation

```
{
  "pre_pointer_sha256": "fe5f8f1db44e71d791b6cca8d99537cb893029acad9d6e92ef0bc92e446c853f",
  "post_pointer_sha256": "f5ab19b3999cccbd0264f35d9dcdba5662a04bfd8c21bee61781740cd4ae7c0d",
  "pointer_unchanged": false,
  "promotion_marker_promoted_field": true,
  "promote_script_exit_code": 0
}
```
