# Derek live snapshot — 2026-05-03 game 21684819 (current_live)

- snapshot_type: **current_live**
- snapshot_mode: **production_live_current**
- pmf_source: **live_snapshot_recomputed_canonical_current**
- pmfs_recomputed: **True**
- champion_model_id: `challenger-2026-04-30`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`
- game_start_time_utc: `2026-05-03T19:40:00Z`
- snapshot_target_time_utc: `2026-05-03T16:21:11Z`
- actual_run_started_at_utc: `2026-05-03T16:21:11Z`
- actual_run_finished_at_utc: `2026-05-03T16:21:13Z`
- pmf_generated_at_utc: `2026-05-03T16:21:02Z`
- props_emitted: 33
- market_rows: 33
- active_players_projected: 14

## Lineup status

- lineup_source: `None`
- lineup_fetched_at_utc: `2026-05-03T16:21:13Z`
- lineup_confirmed: **False**
- lineup_complete: `unavailable`
- lineup_aware: **False**
- lineup_confirmation_status: `unavailable`
- lineup_blocker: 'no rows returned by BDL lineups endpoint (lineups not posted yet)'
- lineup_hash: ``
- starters_by_team: `{}`
- lineup_context_supplied: **True**
- lineup_affects_pmf_features: **False**
- lineup_feature_blocker: 'no lineup rows joined into prediction state for this snapshot — see derek_live_predictions_summary.json for the exact blocker (typical: BDL has not posted lineups yet, or backfill_demo mode bypassed predict.py).'

## Champion model

- champion_metadata_verified: **True**
- no_leakage_champion_cutoff_verified: **True**
- live_snapshot_retrained: **False**
- live_snapshot_recalibrated: **False**

## Files

| File | rows | sha256 |
| --- | ---: | --- |
| prop_summary.parquet | 33 | `0aa0fc1947f59f7b` |
| full_pmf_wide.parquet | 33 | `ca0892f1ea46f93c` |
| outcome_level_probabilities.parquet | 33 | `d9002f7c2f93cfce` |
| market_comparison.parquet | 33 | `f23f89039160ecbf` |
| lineup_context.parquet | 14 | `c40ca398f48a41a2` |
| injury_availability_context.parquet | 14 | `f703cdf64a4f65ba` |
| prediction_input_audit.parquet | 33 | `0aa0fc1947f59f7b` |
| direct_lineup_impact_report.json | 1 | `1641f1cdcba64f05` |
| game_context.parquet | 14 | `57d2af0e891852ca` |
| pmf_driver_decomposition.parquet | 33 | `49e98a311e447118` |
| lineup_injury_impact_report.json | 1 | `394015348926e904` |
| contextual_feature_audit.parquet | 14 | `6b05e5a6859d70e7` |
