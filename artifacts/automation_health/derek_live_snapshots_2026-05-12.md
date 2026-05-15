# Derek Live Snapshots — 2026-05-12

- generated_at_utc: 2026-05-14T05:17:55+00:00
- passed: **False**
- snapshot_count: 1 across 1 game folders

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| derek_game_snapshots_dir_present | yes | deliveries/2026-05-12/derek_game_snapshots |
| 21707976/close_lock/required_outputs_present | yes | ok |
| 21707976/close_lock/run_timestamps_recorded | NO | started=None finished=None |
| 21707976/close_lock/snapshot_mode_valid | yes | snapshot_mode='production_live' |
| 21707976/close_lock/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live' allow_backfill_test=False |
| 21707976/close_lock/production_live_pmfs_recomputed | NO | pmfs_recomputed=False pmf_source='corrected_wizard_of_odds_full_pmfs_wide' |
| 21707976/close_lock/production_live_predict_invocation_proof | NO | predict.py invocation proof must be recorded |
| 21707976/close_lock/champion_metadata_verified | NO | value=None |
| 21707976/close_lock/no_leakage_champion_cutoff_verified | NO | value=None |
| 21707976/close_lock/live_snapshot_did_not_retrain | NO | live_snapshot_retrained=None |
| 21707976/close_lock/live_snapshot_did_not_recalibrate | NO | live_snapshot_recalibrated=None |
| 21707976/close_lock/manifest_field_present:prediction_run_id | NO | value=None |
| 21707976/close_lock/manifest_field_present:prediction_code_commit | NO | value=None |
| 21707976/close_lock/manifest_field_present:pmf_generated_at_utc | NO | value=None |
| 21707976/close_lock/manifest_field_present:pmf_output_hash | NO | value=None |
| 21707976/close_lock/pmf_row_count_positive | yes | rows=341 |
| 21707976/close_lock/market_comparison_present | yes | rows=1285 |
| 21707976/close_lock/champion_metadata_matches_pointer | NO | manifest_champion=None pointer='challenger-2026-04-30' |
| 21707976/close_lock/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no confirmed lineup source in corrected delivery' |
| 21707976/close_lock/lineup_blocker_documented | yes | lineup_blocker='no confirmed lineup source in corrected delivery' |
| 21707976/close_lock/no_post_tip_data_used | NO | =None |
| 21707976/close_lock/no_challenger_artifacts_used | NO | =None |
| 21707976/close_lock/injury_source_recorded | yes | injury_source='corrected_pmf_delivery' |
| 21707976/close_lock/availability_source_recorded | yes | availability_source='corrected_pmf_delivery' |
