# Daily Automation Health Probe

- generated_at_utc: 2026-05-01T00:29:13+00:00
- code_commit: 3b1b490eb3cd
- latest_delivery_date_seen: 2026-04-30
- overall_pass: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| woo_latest_export_present | yes | all required files present |
| woo_latest_manifest_date_matches_latest_delivery | yes | manifest_date='2026-04-30' latest_delivery_date='2026-04-30' |
| woo_export_verifier_present | yes | candidates=['scripts/verify_wizard_of_odds_public_export.py'] |
| workflow_present_wizard_of_odds_ftp_deploy.yml | yes | WoO FTP deploy workflow |
| workflow_present_daily_pmf_delivery.yml | yes | Daily delivery workflow |
| workflow_present_nightly_training_calibration.yml | yes | Nightly training workflow |
| derek_forward_feed_builder_present | yes | scripts/build_derek_forward_feed.py |
| daily_workflow_references_derek | yes | daily_pmf_delivery.yml references Derek |
| daily_workflow_references_woo_modes | yes | daily_pmf_delivery.yml references both WoO modes |
| champion_pointer_present | yes | well-formed |
| training_cron_no_overlap_with_delivery | yes | overlap_slots=[] cutoff_constants_present=True |
| no_dirty_production_files | yes | clean |
| no_secrets_in_outputs | yes | files_scanned=175 hits=[] |
| latest_derek_for_latest_date | yes | deliveries/2026-04-30/derek_forward_feed exists=True |
| latest_woo_for_latest_date | yes | deliveries/2026-04-30/wizard_of_odds exists=True |
| delivery_does_not_reference_challengers | yes | ok |
