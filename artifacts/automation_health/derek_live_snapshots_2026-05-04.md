# Derek Live Snapshots — 2026-05-04

- generated_at_utc: 2026-05-05T01:44:29+00:00
- passed: **True**
- snapshot_count: 1 across 2 game folders

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| derek_game_snapshots_dir_present | yes | deliveries/2026-05-04/derek_game_snapshots |
| 21707972/current_live/required_outputs_present | yes | ok |
| 21707972/current_live/run_timestamps_recorded | yes | started=2026-05-05T01:40:47Z finished=2026-05-05T01:40:47Z |
| 21707972/current_live/snapshot_mode_valid | yes | snapshot_mode='backfill_demo' |
| 21707972/current_live/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='backfill_demo' allow_backfill_test=True |
| 21707972/current_live/backfill_demo_pmf_source_is_reused_canonical | yes | pmf_source='live_snapshot_reused_canonical' pmfs_recomputed=False |
| 21707972/current_live/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-current_live-21707972-20260505T014047' |
| 21707972/current_live/manifest_field_present:prediction_code_commit | yes | value='84cade383e5a48f94e1665eafc837e1a3a239bff' |
| 21707972/current_live/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-04T15:13:49Z' |
| 21707972/current_live/manifest_field_present:pmf_output_hash | yes | value='cf783b37715341ee' |
| 21707972/current_live/pmf_row_count_positive | yes | rows=32 |
| 21707972/current_live/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21707972/current_live/market_comparison_present | yes | rows=32 |
| 21707972/current_live/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-04-30' pointer='challenger-2026-04-30' |
| 21707972/current_live/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no confirmed lineup source wired' |
| 21707972/current_live/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21707972/current_live/lineup_blocker_documented | yes | lineup_blocker='no confirmed lineup source wired' |
| 21707972/current_live/no_post_tip_data_used | yes | =True |
| 21707972/current_live/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21707972/current_live/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21707972/current_live/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
