# Derek Live Snapshots — 2026-05-25

- generated_at_utc: 2026-05-25T23:20:08+00:00
- passed: **True**
- snapshot_count: 1 across 1 game folders

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| derek_game_snapshots_dir_present | yes | deliveries/2026-05-25/derek_game_snapshots |
| 21713901/current_live/required_outputs_present | yes | ok |
| 21713901/current_live/run_timestamps_recorded | yes | started=2026-05-25T22:01:03Z finished=2026-05-25T22:01:41Z |
| 21713901/current_live/snapshot_mode_valid | yes | snapshot_mode='production_live_current' |
| 21713901/current_live/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live_current' allow_backfill_test=False |
| 21713901/current_live/production_live_pmfs_recomputed | yes | pmfs_recomputed=True pmf_source='live_snapshot_recomputed' |
| 21713901/current_live/champion_metadata_verified | yes | value=True |
| 21713901/current_live/no_leakage_champion_cutoff_verified | yes | value=True |
| 21713901/current_live/live_snapshot_did_not_retrain | yes | live_snapshot_retrained=False |
| 21713901/current_live/live_snapshot_did_not_recalibrate | yes | live_snapshot_recalibrated=False |
| 21713901/current_live/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-current_live-21713901-20260525T220103' |
| 21713901/current_live/manifest_field_present:prediction_code_commit | yes | value='8d2f7093f96f7653a04673784290cb831bbc07b9' |
| 21713901/current_live/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-25T22:01:40Z' |
| 21713901/current_live/manifest_field_present:pmf_output_hash | yes | value='07ab74e8297ba032' |
| 21713901/current_live/pmf_row_count_positive | yes | rows=32 |
| 21713901/current_live/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21713901/current_live/market_comparison_present | yes | rows=32 |
| 21713901/current_live/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-05-24' pointer='challenger-2026-05-24' |
| 21713901/current_live/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='confirmed_lineups_not_available_yet' |
| 21713901/current_live/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21713901/current_live/lineup_blocker_documented | yes | lineup_blocker='confirmed_lineups_not_available_yet' |
| 21713901/current_live/no_post_tip_data_used | yes | =True |
| 21713901/current_live/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21713901/current_live/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21713901/current_live/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
