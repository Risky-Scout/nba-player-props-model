# Derek live snapshot — 2026-05-03 game 21682000 (current_live)

- snapshot_type: **current_live**
- snapshot_mode: **production_live_current**
- pmf_source: **live_snapshot_recomputed_canonical_current**
- pmfs_recomputed: **True**
- champion_model_id: `challenger-2026-04-30`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`
- game_start_time_utc: `2026-05-03T23:40:00Z`
- snapshot_target_time_utc: `2026-05-03T16:10:42Z`
- actual_run_started_at_utc: `2026-05-03T16:10:42Z`
- actual_run_finished_at_utc: `2026-05-03T16:10:43Z`
- pmf_generated_at_utc: `2026-05-03T15:58:13Z`
- props_emitted: 36
- market_rows: 36
- active_players_projected: 14

## Lineup status

- lineup_source: `None`
- lineup_fetched_at_utc: `2026-05-03T16:10:43Z`
- lineup_confirmed: **False**
- lineup_complete: `fetch_failed`
- lineup_aware: **False**
- lineup_confirmation_status: `fetch_failed`
- lineup_blocker: 'BDL_API_KEY not set in runner environment'
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
| prop_summary.parquet | 36 | `30e53c10184e77f3` |
| full_pmf_wide.parquet | 36 | `be0cd7064081a1d1` |
| outcome_level_probabilities.parquet | 36 | `a0725ddea472ff90` |
| market_comparison.parquet | 36 | `6181299bafd7adc9` |
| lineup_context.parquet | 14 | `309684be346dbb08` |
| injury_availability_context.parquet | 14 | `7ed829ff6ceedeac` |
| prediction_input_audit.parquet | 36 | `30e53c10184e77f3` |
| direct_lineup_impact_report.json | 1 | `07b92a094f379a10` |
| game_context.parquet | 14 | `84ba364948262ee2` |
| pmf_driver_decomposition.parquet | 36 | `c8da310d3048bc73` |
| lineup_injury_impact_report.json | 1 | `f23ae18c69b7e9bb` |
| contextual_feature_audit.parquet | 14 | `f4adadd72437a2ab` |
