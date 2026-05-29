# Derek Live Snapshots — 2026-05-28

- generated_at_utc: 2026-05-29T00:01:36+00:00
- passed: **True**
- snapshot_count: 1 across 1 game folders

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| derek_game_snapshots_dir_present | yes | deliveries/2026-05-28/derek_game_snapshots |
| 21713533/current_live/required_outputs_present | yes | ok |
| 21713533/current_live/current_live_target_pre_tip | yes | target=2026-05-28T22:48:40Z game_start=2026-05-29T00:40:00Z |
| 21713533/current_live/run_timestamps_recorded | yes | started=2026-05-28T22:48:40Z finished=2026-05-28T22:49:20Z |
| 21713533/current_live/snapshot_mode_valid | yes | snapshot_mode='production_live_current' |
| 21713533/current_live/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live_current' allow_backfill_test=False |
| 21713533/current_live/production_live_pmfs_recomputed | yes | pmfs_recomputed=True pmf_source='live_snapshot_recomputed' |
| 21713533/current_live/champion_metadata_verified | yes | value=True |
| 21713533/current_live/no_leakage_champion_cutoff_verified | yes | value=True |
| 21713533/current_live/live_snapshot_did_not_retrain | yes | live_snapshot_retrained=False |
| 21713533/current_live/live_snapshot_did_not_recalibrate | yes | live_snapshot_recalibrated=False |
| 21713533/current_live/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-current_live-21713533-20260528T224840' |
| 21713533/current_live/manifest_field_present:prediction_code_commit | yes | value='e261dd5212491cbd5870bee2abfa71a777965590' |
| 21713533/current_live/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-28T22:49:20Z' |
| 21713533/current_live/manifest_field_present:pmf_output_hash | yes | value='a8287d14e8c9018e' |
| 21713533/current_live/pmf_row_count_positive | yes | rows=39 |
| 21713533/current_live/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21713533/current_live/market_comparison_present | yes | rows=39 |
| 21713533/current_live/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-05-27' pointer='challenger-2026-05-27' |
| 21713533/current_live/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='confirmed_lineups_not_available_yet' |
| 21713533/current_live/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21713533/current_live/lineup_blocker_documented | yes | lineup_blocker='confirmed_lineups_not_available_yet' |
| 21713533/current_live/no_post_tip_data_used | yes | =True |
| 21713533/current_live/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21713533/current_live/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21713533/current_live/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
