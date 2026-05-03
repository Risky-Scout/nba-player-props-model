# Derek Live Snapshots — 2026-05-03

- generated_at_utc: 2026-05-03T20:29:46+00:00
- passed: **False**
- snapshot_count: 4 across 2 game folders

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| derek_game_snapshots_dir_present | yes | deliveries/2026-05-03/derek_game_snapshots |
| 21682000/current_live/required_outputs_present | yes | ok |
| 21682000/current_live/current_live_target_pre_tip | yes | target=2026-05-03T20:29:27Z game_start=2026-05-03T23:40:00Z |
| 21682000/current_live/run_timestamps_recorded | yes | started=2026-05-03T20:29:27Z finished=2026-05-03T20:29:30Z |
| 21682000/current_live/snapshot_mode_valid | yes | snapshot_mode='production_live_current' |
| 21682000/current_live/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live_current' allow_backfill_test=False |
| 21682000/current_live/production_live_pmfs_recomputed | yes | pmfs_recomputed=True pmf_source='live_snapshot_recomputed_canonical_current' |
| 21682000/current_live/champion_metadata_verified | yes | value=True |
| 21682000/current_live/no_leakage_champion_cutoff_verified | yes | value=True |
| 21682000/current_live/live_snapshot_did_not_retrain | yes | live_snapshot_retrained=False |
| 21682000/current_live/live_snapshot_did_not_recalibrate | yes | live_snapshot_recalibrated=False |
| 21682000/current_live/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-current_live-21682000-20260503T202927' |
| 21682000/current_live/manifest_field_present:prediction_code_commit | yes | value='6a0b8314fbc4bf70f89978e908c0f1d73aac5f41' |
| 21682000/current_live/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-03T20:29:23Z' |
| 21682000/current_live/manifest_field_present:pmf_output_hash | yes | value='0cfe3f67e070543b' |
| 21682000/current_live/pmf_row_count_positive | yes | rows=36 |
| 21682000/current_live/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21682000/current_live/market_comparison_present | yes | rows=36 |
| 21682000/current_live/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-04-30' pointer='challenger-2026-04-30' |
| 21682000/current_live/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21682000/current_live/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21682000/current_live/lineup_blocker_documented | yes | lineup_blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21682000/current_live/no_post_tip_data_used | yes | =True |
| 21682000/current_live/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21682000/current_live/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21682000/current_live/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
| 21684819/current_live/required_outputs_present | yes | ok |
| 21684819/current_live/current_live_target_pre_tip | NO | target=2026-05-03T20:29:31Z game_start=2026-05-03T19:40:00Z |
| 21684819/current_live/run_timestamps_recorded | yes | started=2026-05-03T20:29:31Z finished=2026-05-03T20:29:34Z |
| 21684819/current_live/snapshot_mode_valid | yes | snapshot_mode='production_live_current' |
| 21684819/current_live/snapshot_mode_matches_allow_backfill_test | yes | snapshot_mode='production_live_current' allow_backfill_test=False |
| 21684819/current_live/production_live_pmfs_recomputed | yes | pmfs_recomputed=True pmf_source='live_snapshot_recomputed_canonical_current' |
| 21684819/current_live/champion_metadata_verified | yes | value=True |
| 21684819/current_live/no_leakage_champion_cutoff_verified | yes | value=True |
| 21684819/current_live/live_snapshot_did_not_retrain | yes | live_snapshot_retrained=False |
| 21684819/current_live/live_snapshot_did_not_recalibrate | yes | live_snapshot_recalibrated=False |
| 21684819/current_live/manifest_field_present:prediction_run_id | yes | value='derek-snapshot-current_live-21684819-20260503T202931' |
| 21684819/current_live/manifest_field_present:prediction_code_commit | yes | value='6a0b8314fbc4bf70f89978e908c0f1d73aac5f41' |
| 21684819/current_live/manifest_field_present:pmf_generated_at_utc | yes | value='2026-05-03T20:29:23Z' |
| 21684819/current_live/manifest_field_present:pmf_output_hash | yes | value='ca0892f1ea46f93c' |
| 21684819/current_live/pmf_row_count_positive | yes | rows=33 |
| 21684819/current_live/pmf_validity_sample | yes | sample_n=5 issues=[] |
| 21684819/current_live/market_comparison_present | yes | rows=33 |
| 21684819/current_live/champion_metadata_matches_pointer | yes | manifest_champion='challenger-2026-04-30' pointer='challenger-2026-04-30' |
| 21684819/current_live/lineup_blocker_documented_when_unconfirmed | yes | lineup_confirmed=False blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21684819/current_live/lineup_feature_blocker_documented | yes | lineup_feature_blocker must be documented when lineup_affects_pmf_features=false |
| 21684819/current_live/lineup_blocker_documented | yes | lineup_blocker='no rows returned by BDL lineups endpoint (lineups not posted yet)' |
| 21684819/current_live/no_post_tip_data_used | yes | =True |
| 21684819/current_live/contextual_pmf_engine_recorded | yes | contextual_pmf_engine=True; no_challenger_artifacts_used=False |
| 21684819/current_live/injury_source_recorded | yes | injury_source='data/nba_injury_reports.parquet (downstream of predict.py)' |
| 21684819/current_live/availability_source_recorded | yes | availability_source='data/player_availability_asof.parquet (BDL availability snapshot)' |
| 21684819/t_minus_25/required_outputs_present | NO | missing=['snapshot_manifest.json', 'snapshot_report.md', 'prop_summary.csv', 'prop_summary.parquet', 'full_pmf_wide.csv', 'full_pmf_wide.parquet', 'outcome_level_probabilities.csv', 'outcome_level_probabilities.parquet', 'market_comparison.csv', 'market_comparison.parquet'] |
| 21684819/close_lock/required_outputs_present | NO | missing=['snapshot_manifest.json', 'snapshot_report.md', 'prop_summary.csv', 'prop_summary.parquet', 'full_pmf_wide.csv', 'full_pmf_wide.parquet', 'outcome_level_probabilities.csv', 'outcome_level_probabilities.parquet', 'market_comparison.csv', 'market_comparison.parquet'] |
