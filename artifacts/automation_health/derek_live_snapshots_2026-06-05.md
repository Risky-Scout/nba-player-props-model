# Derek Live Snapshots — 2026-06-05

- generated_at_utc: 2026-06-06T00:23:18+00:00
- passed: **True**
- snapshot_count: 2 across 1 game folders

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| derek_game_snapshots_dir_present | yes | deliveries/2026-06-05/derek_game_snapshots |
| 21716135/current_live/required_outputs_present | yes | ok |
| 21716135/current_live/current_live_target_pre_tip | yes | target=2026-06-05T21:53:17Z game_start=2026-06-06T00:40:00Z |
| 21716135/current_live/run_timestamps_recorded | yes | started=2026-06-05T21:53:17Z finished=2026-06-05T21:54:00Z |
| 21716135/current_live/snapshot_mode_valid | yes | snapshot_mode='production_live_current' |
| 21716135/current_live/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live_current' allow_backfill_test=False |
| 21716135/current_live/production_live_pmfs_recomputed | yes | pmfs_recomputed=True pmf_source='live_snapshot_recomputed' |
| 21716135/current_live/champion_metadata_verified | yes | value=True |
| 21716135/current_live/no_leakage_champion_cutoff_verified | yes | value=True |
| 21716135/current_live/live_snapshot_did_not_retrain | yes | live_snapshot_retrained=False |
| 21716135/current_live/live_snapshot_did_not_recalibrate | yes | live_snapshot_recalibrated=False |
| 21716135/current_live/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-current_live-21716135-20260605T215317' |
| 21716135/current_live/manifest_field_present:prediction_code_commit | yes | value='905f3847678d6c3cf2a07faa2f25bf0a71ad5750' |
| 21716135/current_live/manifest_field_present:pmf_generated_at_utc | yes | value='2026-06-05T21:54:00Z' |
| 21716135/current_live/manifest_field_present:pmf_output_hash | yes | value='fbd689618eccf097' |
| 21716135/current_live/pmf_row_count_positive | yes | rows=43 |
| 21716135/current_live/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21716135/current_live/market_comparison_present | yes | rows=43 |
| 21716135/current_live/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-06-04' pointer='challenger-2026-06-04' |
| 21716135/current_live/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='confirmed_lineups_not_available_yet' |
| 21716135/current_live/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21716135/current_live/lineup_blocker_documented | yes | lineup_blocker='confirmed_lineups_not_available_yet' |
| 21716135/current_live/no_post_tip_data_used | yes | =True |
| 21716135/current_live/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21716135/current_live/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21716135/current_live/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
| 21716135/t_minus_25/required_outputs_present | yes | ok |
| 21716135/t_minus_25/snapshot_target_offset_ok | yes | expected=25min  observed=25.0min |
| 21716135/t_minus_25/run_timestamps_recorded | yes | started=2026-06-06T00:22:19Z finished=2026-06-06T00:23:05Z |
| 21716135/t_minus_25/snapshot_mode_valid | yes | snapshot_mode='production_live' |
| 21716135/t_minus_25/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live' allow_backfill_test=False |
| 21716135/t_minus_25/production_live_pmfs_recomputed | yes | pmfs_recomputed=True pmf_source='live_snapshot_recomputed' |
| 21716135/t_minus_25/production_live_predict_invocation_proof | yes | predict.py invocation proof must be recorded |
| 21716135/t_minus_25/champion_metadata_verified | yes | value=True |
| 21716135/t_minus_25/no_leakage_champion_cutoff_verified | yes | value=True |
| 21716135/t_minus_25/live_snapshot_did_not_retrain | yes | live_snapshot_retrained=False |
| 21716135/t_minus_25/live_snapshot_did_not_recalibrate | yes | live_snapshot_recalibrated=False |
| 21716135/t_minus_25/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-t_minus_25-21716135-20260606T002219' |
| 21716135/t_minus_25/manifest_field_present:prediction_code_commit | yes | value='663e323d3740d940c4328001fca0b4cd783e8280' |
| 21716135/t_minus_25/manifest_field_present:pmf_generated_at_utc | yes | value='2026-06-06T00:23:04Z' |
| 21716135/t_minus_25/manifest_field_present:pmf_output_hash | yes | value='8c2f91d6f5d3ad5e' |
| 21716135/t_minus_25/pmf_generated_during_run_window | yes | pmf_generated_at=2026-06-06T00:23:04Z started=2026-06-06T00:22:19Z |
| 21716135/t_minus_25/pmf_row_count_positive | yes | rows=35 |
| 21716135/t_minus_25/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21716135/t_minus_25/market_comparison_present | yes | rows=35 |
| 21716135/t_minus_25/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-06-04' pointer='challenger-2026-06-04' |
| 21716135/t_minus_25/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='confirmed_lineups_not_available_yet' |
| 21716135/t_minus_25/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21716135/t_minus_25/lineup_blocker_documented | yes | lineup_blocker='confirmed_lineups_not_available_yet' |
| 21716135/t_minus_25/no_post_tip_data_used | yes | =True |
| 21716135/t_minus_25/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21716135/t_minus_25/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21716135/t_minus_25/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
| 21716135/t_minus_25/lineup_feature_blocker_explains_false | yes | lineup_feature_blocker='lineup parquet missing required columns (player_id/starter); got []' |
