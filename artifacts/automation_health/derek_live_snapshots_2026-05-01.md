# Derek Live Snapshots — 2026-05-01

- generated_at_utc: 2026-05-02T13:12:54+00:00
- passed: **True**
- snapshot_count: 6 across 3 game folders

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| derek_game_snapshots_dir_present | yes | deliveries/2026-05-01/derek_game_snapshots |
| 21681995/t_minus_25/required_outputs_present | yes | ok |
| 21681995/t_minus_25/run_timestamps_recorded | yes | started=2026-05-02T13:12:34Z finished=2026-05-02T13:12:35Z |
| 21681995/t_minus_25/snapshot_mode_valid | yes | snapshot_mode='backfill_demo' |
| 21681995/t_minus_25/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='backfill_demo' allow_backfill_test=True |
| 21681995/t_minus_25/backfill_demo_pmf_source_is_reused_canonical | yes | pmf_source='live_snapshot_reused_canonical' pmfs_recomputed=False |
| 21681995/t_minus_25/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-t_minus_25-21681995-20260502T131234' |
| 21681995/t_minus_25/manifest_field_present:prediction_code_commit | yes | value='52ca1c80dd5671b33e1a770876198d030dd9b015' |
| 21681995/t_minus_25/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-02T13:12:13Z' |
| 21681995/t_minus_25/manifest_field_present:pmf_output_hash | yes | value='a53b2423e4181720' |
| 21681995/t_minus_25/pmf_row_count_positive | yes | rows=33 |
| 21681995/t_minus_25/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21681995/t_minus_25/market_comparison_present | yes | rows=33 |
| 21681995/t_minus_25/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-04-30' pointer='challenger-2026-04-30' |
| 21681995/t_minus_25/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21681995/t_minus_25/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21681995/t_minus_25/lineup_blocker_documented | yes | lineup_blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21681995/t_minus_25/no_post_tip_data_used | yes | =True |
| 21681995/t_minus_25/no_challenger_artifacts_used | yes | =True |
| 21681995/close_lock/required_outputs_present | yes | ok |
| 21681995/close_lock/run_timestamps_recorded | yes | started=2026-05-02T13:12:43Z finished=2026-05-02T13:12:45Z |
| 21681995/close_lock/snapshot_mode_valid | yes | snapshot_mode='backfill_demo' |
| 21681995/close_lock/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='backfill_demo' allow_backfill_test=True |
| 21681995/close_lock/backfill_demo_pmf_source_is_reused_canonical | yes | pmf_source='live_snapshot_reused_canonical' pmfs_recomputed=False |
| 21681995/close_lock/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-close_lock-21681995-20260502T131243' |
| 21681995/close_lock/manifest_field_present:prediction_code_commit | yes | value='52ca1c80dd5671b33e1a770876198d030dd9b015' |
| 21681995/close_lock/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-02T13:12:13Z' |
| 21681995/close_lock/manifest_field_present:pmf_output_hash | yes | value='a53b2423e4181720' |
| 21681995/close_lock/pmf_row_count_positive | yes | rows=33 |
| 21681995/close_lock/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21681995/close_lock/market_comparison_present | yes | rows=33 |
| 21681995/close_lock/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-04-30' pointer='challenger-2026-04-30' |
| 21681995/close_lock/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21681995/close_lock/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21681995/close_lock/lineup_blocker_documented | yes | lineup_blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21681995/close_lock/no_post_tip_data_used | yes | =True |
| 21681995/close_lock/no_challenger_artifacts_used | yes | =True |
| 21681995/snapshot_comparison_emitted_when_both_present | yes | advisory: comparison emitter is Phase 13L-bis scope; both snapshots present. |
| 21681996/t_minus_25/required_outputs_present | yes | ok |
| 21681996/t_minus_25/run_timestamps_recorded | yes | started=2026-05-02T13:12:37Z finished=2026-05-02T13:12:38Z |
| 21681996/t_minus_25/snapshot_mode_valid | yes | snapshot_mode='backfill_demo' |
| 21681996/t_minus_25/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='backfill_demo' allow_backfill_test=True |
| 21681996/t_minus_25/backfill_demo_pmf_source_is_reused_canonical | yes | pmf_source='live_snapshot_reused_canonical' pmfs_recomputed=False |
| 21681996/t_minus_25/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-t_minus_25-21681996-20260502T131237' |
| 21681996/t_minus_25/manifest_field_present:prediction_code_commit | yes | value='52ca1c80dd5671b33e1a770876198d030dd9b015' |
| 21681996/t_minus_25/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-02T13:12:13Z' |
| 21681996/t_minus_25/manifest_field_present:pmf_output_hash | yes | value='8b75168f45315515' |
| 21681996/t_minus_25/pmf_row_count_positive | yes | rows=33 |
| 21681996/t_minus_25/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21681996/t_minus_25/market_comparison_present | yes | rows=33 |
| 21681996/t_minus_25/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-04-30' pointer='challenger-2026-04-30' |
| 21681996/t_minus_25/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21681996/t_minus_25/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21681996/t_minus_25/lineup_blocker_documented | yes | lineup_blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21681996/t_minus_25/no_post_tip_data_used | yes | =True |
| 21681996/t_minus_25/no_challenger_artifacts_used | yes | =True |
| 21681996/close_lock/required_outputs_present | yes | ok |
| 21681996/close_lock/run_timestamps_recorded | yes | started=2026-05-02T13:12:46Z finished=2026-05-02T13:12:47Z |
| 21681996/close_lock/snapshot_mode_valid | yes | snapshot_mode='backfill_demo' |
| 21681996/close_lock/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='backfill_demo' allow_backfill_test=True |
| 21681996/close_lock/backfill_demo_pmf_source_is_reused_canonical | yes | pmf_source='live_snapshot_reused_canonical' pmfs_recomputed=False |
| 21681996/close_lock/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-close_lock-21681996-20260502T131246' |
| 21681996/close_lock/manifest_field_present:prediction_code_commit | yes | value='52ca1c80dd5671b33e1a770876198d030dd9b015' |
| 21681996/close_lock/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-02T13:12:13Z' |
| 21681996/close_lock/manifest_field_present:pmf_output_hash | yes | value='8b75168f45315515' |
| 21681996/close_lock/pmf_row_count_positive | yes | rows=33 |
| 21681996/close_lock/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21681996/close_lock/market_comparison_present | yes | rows=33 |
| 21681996/close_lock/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-04-30' pointer='challenger-2026-04-30' |
| 21681996/close_lock/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21681996/close_lock/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21681996/close_lock/lineup_blocker_documented | yes | lineup_blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21681996/close_lock/no_post_tip_data_used | yes | =True |
| 21681996/close_lock/no_challenger_artifacts_used | yes | =True |
| 21681996/snapshot_comparison_emitted_when_both_present | yes | advisory: comparison emitter is Phase 13L-bis scope; both snapshots present. |
| 21684812/t_minus_25/required_outputs_present | yes | ok |
| 21684812/t_minus_25/run_timestamps_recorded | yes | started=2026-05-02T13:12:39Z finished=2026-05-02T13:12:41Z |
| 21684812/t_minus_25/snapshot_mode_valid | yes | snapshot_mode='backfill_demo' |
| 21684812/t_minus_25/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='backfill_demo' allow_backfill_test=True |
| 21684812/t_minus_25/backfill_demo_pmf_source_is_reused_canonical | yes | pmf_source='live_snapshot_reused_canonical' pmfs_recomputed=False |
| 21684812/t_minus_25/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-t_minus_25-21684812-20260502T131239' |
| 21684812/t_minus_25/manifest_field_present:prediction_code_commit | yes | value='52ca1c80dd5671b33e1a770876198d030dd9b015' |
| 21684812/t_minus_25/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-02T13:12:13Z' |
| 21684812/t_minus_25/manifest_field_present:pmf_output_hash | yes | value='8095175e23dffc1b' |
| 21684812/t_minus_25/pmf_row_count_positive | yes | rows=29 |
| 21684812/t_minus_25/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21684812/t_minus_25/market_comparison_present | yes | rows=29 |
| 21684812/t_minus_25/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-04-30' pointer='challenger-2026-04-30' |
| 21684812/t_minus_25/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21684812/t_minus_25/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21684812/t_minus_25/lineup_blocker_documented | yes | lineup_blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21684812/t_minus_25/no_post_tip_data_used | yes | =True |
| 21684812/t_minus_25/no_challenger_artifacts_used | yes | =True |
| 21684812/close_lock/required_outputs_present | yes | ok |
| 21684812/close_lock/run_timestamps_recorded | yes | started=2026-05-02T13:12:48Z finished=2026-05-02T13:12:50Z |
| 21684812/close_lock/snapshot_mode_valid | yes | snapshot_mode='backfill_demo' |
| 21684812/close_lock/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='backfill_demo' allow_backfill_test=True |
| 21684812/close_lock/backfill_demo_pmf_source_is_reused_canonical | yes | pmf_source='live_snapshot_reused_canonical' pmfs_recomputed=False |
| 21684812/close_lock/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-close_lock-21684812-20260502T131248' |
| 21684812/close_lock/manifest_field_present:prediction_code_commit | yes | value='52ca1c80dd5671b33e1a770876198d030dd9b015' |
| 21684812/close_lock/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-02T13:12:13Z' |
| 21684812/close_lock/manifest_field_present:pmf_output_hash | yes | value='8095175e23dffc1b' |
| 21684812/close_lock/pmf_row_count_positive | yes | rows=29 |
| 21684812/close_lock/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21684812/close_lock/market_comparison_present | yes | rows=29 |
| 21684812/close_lock/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-04-30' pointer='challenger-2026-04-30' |
| 21684812/close_lock/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21684812/close_lock/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21684812/close_lock/lineup_blocker_documented | yes | lineup_blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21684812/close_lock/no_post_tip_data_used | yes | =True |
| 21684812/close_lock/no_challenger_artifacts_used | yes | =True |
| 21684812/snapshot_comparison_emitted_when_both_present | yes | advisory: comparison emitter is Phase 13L-bis scope; both snapshots present. |
