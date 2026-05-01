# Training Automation Verification — 2026-04-29

- generated_at_utc: 2026-05-01T00:30:22+00:00
- mode: **dry_run**
- overall_pass: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| readiness_report_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/training_readiness/2026-04-29/readiness_report.json |
| challenger_dir_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-04-29 |
| train_manifest_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-04-29/train_manifest.json |
| calibration_manifest_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-04-29/calibration_manifest.json |
| validation_report_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-04-29/validation_report.json |
| promotion_decision_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-04-29/promotion_decision.json |
| champion_pointer_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/registry/champion_pointer.json |
| model_registry_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/registry/model_registry.json |
| promotion_log_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/registry/promotion_log.csv |
| nightly_run_manifest_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/nightly_training/2026-04-29/run_manifest.json |
| smoke_test_report_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/nightly_training/2026-04-29/smoke_test_report.json |
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
| failure_mode_keeps_champion_unchanged | yes | pre=7dd4bbd1c7fc post=7dd4bbd1c7fc |
| no_forbidden_files_staged | yes | staged_violations=[] |

## Mode details

```
{
  "train_manifest_dry_run": true,
  "calibration_manifest_dry_run": true,
  "challenger_pickle_count": 0
}
```

## Failure-mode simulation

```
{
  "pre_pointer_sha256": "7dd4bbd1c7fccdaed7303d6ced3d420f2d230b0d688b8bf699722967ea16916e",
  "post_pointer_sha256": "7dd4bbd1c7fccdaed7303d6ced3d420f2d230b0d688b8bf699722967ea16916e",
  "pointer_unchanged": true,
  "promotion_marker_promoted_field": false,
  "promote_script_exit_code": 0
}
```
