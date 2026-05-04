# Training Automation Verification — 2026-05-04

- generated_at_utc: 2026-05-04T16:39:26+00:00
- mode: **unknown**
- overall_pass: **False**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| readiness_report_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/training_readiness/2026-05-04/readiness_report.json |
| challenger_dir_exists | NO | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-05-04 |
| train_manifest_exists | NO | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-05-04/train_manifest.json |
| calibration_manifest_exists | NO | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-05-04/calibration_manifest.json |
| validation_report_exists | NO | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-05-04/validation_report.json |
| promotion_decision_exists | NO | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/challengers/2026-05-04/promotion_decision.json |
| champion_pointer_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/registry/champion_pointer.json |
| model_registry_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/registry/model_registry.json |
| promotion_log_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/models/registry/promotion_log.csv |
| nightly_run_manifest_exists | yes | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/nightly_training/2026-05-04/run_manifest.json |
| smoke_test_report_exists | NO | /Users/josephshackelford/woo_models/Gen3_DARKO_Model/artifacts/nightly_training/2026-05-04/smoke_test_report.json |
| champion_pointer_unchanged_when_promote_false | yes | pointer model_version present and unchanged (promote was false) |
| pmf_validity_passed | NO | validation_report.json missing |
| derek_compat_smoke_passed | NO | smoke_test_report.json missing |
| woo_compat_smoke_passed | NO | smoke_test_report.json missing |
| no_secrets_in_manifests | yes | hits=[] |
| no_phase10d_overlays_in_manifests | yes | hits=[] |
| no_raw_dir_referenced_in_manifests | yes | manifests do not name artifacts/raw/ |
| training_run_reproducible | NO | manifests missing |
| workflow_file_exists | yes | .github/workflows/nightly_training_calibration.yml |
| workflow_calls_orchestrator | yes |  |
| workflow_has_safe_cron | yes | expected cron '30 9 * * *' present |
| workflow_has_timeout_protection | yes |  |
| workflow_uses_required_secrets | yes |  |
| workflow_uses_correct_authorship | yes |  |
| workflow_no_phase10d_overlays | yes | hits=[] |
| no_delivery_references_challenger_dir | yes | violations=[] |
| promotion_uses_atomic_pointer_update | yes |  |
| failure_mode_keeps_champion_unchanged | yes | pre=125eb260dc64 post=125eb260dc64 |
| no_forbidden_files_staged | yes | staged_violations=[] |

## Mode details

```
{
  "train_manifest_dry_run": null,
  "calibration_manifest_dry_run": null,
  "challenger_pickle_count": 0,
  "run_manifest_halted_reason": "previous_day_data_not_ready",
  "run_manifest_final_status": "halted_pending_upstream_data",
  "train_manifest_status": null
}
```

## Failure-mode simulation

```
{
  "pre_pointer_sha256": "125eb260dc642bd3b26878f8e407bffd716a210a2727e6cbdc815dea9191fff3",
  "post_pointer_sha256": "125eb260dc642bd3b26878f8e407bffd716a210a2727e6cbdc815dea9191fff3",
  "pointer_unchanged": true,
  "promotion_marker_promoted_field": false,
  "promote_script_exit_code": 0
}
```
