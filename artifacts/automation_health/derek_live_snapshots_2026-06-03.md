# Derek Live Snapshots — 2026-06-03

- generated_at_utc: 2026-06-04T00:24:47+00:00
- passed: **False**
- snapshot_count: 3 across 1 game folders

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| derek_game_snapshots_dir_present | yes | deliveries/2026-06-03/derek_game_snapshots |
| 21716134/current_live/required_outputs_present | yes | ok |
| 21716134/current_live/current_live_target_pre_tip | yes | target=2026-06-03T22:34:15Z game_start=2026-06-04T00:30:00Z |
| 21716134/current_live/run_timestamps_recorded | yes | started=2026-06-03T22:34:15Z finished=2026-06-03T22:34:54Z |
| 21716134/current_live/snapshot_mode_valid | yes | snapshot_mode='production_live_current' |
| 21716134/current_live/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live_current' allow_backfill_test=False |
| 21716134/current_live/production_live_pmfs_recomputed | yes | pmfs_recomputed=True pmf_source='live_snapshot_recomputed' |
| 21716134/current_live/champion_metadata_verified | yes | value=True |
| 21716134/current_live/no_leakage_champion_cutoff_verified | yes | value=True |
| 21716134/current_live/live_snapshot_did_not_retrain | yes | live_snapshot_retrained=False |
| 21716134/current_live/live_snapshot_did_not_recalibrate | yes | live_snapshot_recalibrated=False |
| 21716134/current_live/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-current_live-21716134-20260603T223415' |
| 21716134/current_live/manifest_field_present:prediction_code_commit | yes | value='c03eb2990efb0473607fea52fa3ec960c809d8d4' |
| 21716134/current_live/manifest_field_present:pmf_generated_at_utc | yes | value='2026-06-03T22:34:53Z' |
| 21716134/current_live/manifest_field_present:pmf_output_hash | yes | value='41c3ae57f5cb4d49' |
| 21716134/current_live/pmf_row_count_positive | yes | rows=29 |
| 21716134/current_live/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21716134/current_live/market_comparison_present | yes | rows=29 |
| 21716134/current_live/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-06-02' pointer='challenger-2026-06-02' |
| 21716134/current_live/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='confirmed_lineups_not_available_yet' |
| 21716134/current_live/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21716134/current_live/lineup_blocker_documented | yes | lineup_blocker='confirmed_lineups_not_available_yet' |
| 21716134/current_live/no_post_tip_data_used | yes | =True |
| 21716134/current_live/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21716134/current_live/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21716134/current_live/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
| 21716134/t_minus_25/required_outputs_present | yes | ok |
| 21716134/t_minus_25/snapshot_target_offset_ok | yes | expected=25min  observed=25.0min |
| 21716134/t_minus_25/run_timestamps_recorded | yes | started=2026-06-04T00:23:15Z finished=2026-06-04T00:23:57Z |
| 21716134/t_minus_25/snapshot_mode_valid | yes | snapshot_mode='production_live' |
| 21716134/t_minus_25/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live' allow_backfill_test=False |
| 21716134/t_minus_25/production_live_pmfs_recomputed | yes | pmfs_recomputed=True pmf_source='live_snapshot_recomputed' |
| 21716134/t_minus_25/production_live_predict_invocation_proof | yes | predict.py invocation proof must be recorded |
| 21716134/t_minus_25/champion_metadata_verified | yes | value=True |
| 21716134/t_minus_25/no_leakage_champion_cutoff_verified | yes | value=True |
| 21716134/t_minus_25/live_snapshot_did_not_retrain | yes | live_snapshot_retrained=False |
| 21716134/t_minus_25/live_snapshot_did_not_recalibrate | yes | live_snapshot_recalibrated=False |
| 21716134/t_minus_25/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-t_minus_25-21716134-20260604T002315' |
| 21716134/t_minus_25/manifest_field_present:prediction_code_commit | yes | value='1219dbc6394af5dfcbe98b5e0703c3e75eb2c885' |
| 21716134/t_minus_25/manifest_field_present:pmf_generated_at_utc | yes | value='2026-06-04T00:23:56Z' |
| 21716134/t_minus_25/manifest_field_present:pmf_output_hash | yes | value='e50d9833f08d1cf2' |
| 21716134/t_minus_25/pmf_generated_during_run_window | yes | pmf_generated_at=2026-06-04T00:23:56Z started=2026-06-04T00:23:15Z |
| 21716134/t_minus_25/pmf_row_count_positive | yes | rows=31 |
| 21716134/t_minus_25/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21716134/t_minus_25/market_comparison_present | yes | rows=31 |
| 21716134/t_minus_25/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-06-02' pointer='challenger-2026-06-02' |
| 21716134/t_minus_25/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='confirmed_lineups_not_available_yet' |
| 21716134/t_minus_25/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21716134/t_minus_25/lineup_blocker_documented | yes | lineup_blocker='confirmed_lineups_not_available_yet' |
| 21716134/t_minus_25/no_post_tip_data_used | yes | =True |
| 21716134/t_minus_25/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21716134/t_minus_25/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21716134/t_minus_25/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
| 21716134/t_minus_25/lineup_feature_blocker_explains_false | yes | lineup_feature_blocker='lineup parquet missing required columns (player_id/starter); got []' |
| 21716134/close_lock/required_outputs_present | yes | ok |
| 21716134/close_lock/snapshot_target_offset_ok | NO | expected=5min  observed=6.0min |
| 21716134/close_lock/run_timestamps_recorded | yes | started=2026-06-04T00:24:00Z finished=2026-06-04T00:24:38Z |
| 21716134/close_lock/snapshot_mode_valid | yes | snapshot_mode='production_live' |
| 21716134/close_lock/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live' allow_backfill_test=False |
| 21716134/close_lock/production_live_pmfs_recomputed | yes | pmfs_recomputed=True pmf_source='live_snapshot_recomputed' |
| 21716134/close_lock/production_live_predict_invocation_proof | yes | predict.py invocation proof must be recorded |
| 21716134/close_lock/champion_metadata_verified | yes | value=True |
| 21716134/close_lock/no_leakage_champion_cutoff_verified | yes | value=True |
| 21716134/close_lock/live_snapshot_did_not_retrain | yes | live_snapshot_retrained=False |
| 21716134/close_lock/live_snapshot_did_not_recalibrate | yes | live_snapshot_recalibrated=False |
| 21716134/close_lock/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-close_lock-21716134-20260604T002400' |
| 21716134/close_lock/manifest_field_present:prediction_code_commit | yes | value='1219dbc6394af5dfcbe98b5e0703c3e75eb2c885' |
| 21716134/close_lock/manifest_field_present:pmf_generated_at_utc | yes | value='2026-06-04T00:24:37Z' |
| 21716134/close_lock/manifest_field_present:pmf_output_hash | yes | value='fd33314f5ab1eed4' |
| 21716134/close_lock/pmf_generated_during_run_window | yes | pmf_generated_at=2026-06-04T00:24:37Z started=2026-06-04T00:24:00Z |
| 21716134/close_lock/pmf_row_count_positive | yes | rows=31 |
| 21716134/close_lock/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21716134/close_lock/market_comparison_present | yes | rows=31 |
| 21716134/close_lock/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-06-02' pointer='challenger-2026-06-02' |
| 21716134/close_lock/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='confirmed_lineups_not_available_yet' |
| 21716134/close_lock/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21716134/close_lock/lineup_blocker_documented | yes | lineup_blocker='confirmed_lineups_not_available_yet' |
| 21716134/close_lock/no_post_tip_data_used | yes | =True |
| 21716134/close_lock/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21716134/close_lock/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21716134/close_lock/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
| 21716134/close_lock/lineup_feature_blocker_explains_false | yes | lineup_feature_blocker='lineup parquet missing required columns (player_id/starter); got []' |
| 21716134/snapshot_comparison_emitted_when_both_present | yes | advisory: comparison emitter is Phase 13L-bis scope; both snapshots present. |
