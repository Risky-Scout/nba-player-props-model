# Derek live snapshot — 2026-05-03 game 21684819 (current_live)

- snapshot_type: **current_live**
- snapshot_mode: **production_live_current**
- pmf_source: **live_snapshot_recomputed_canonical_current**
- pmfs_recomputed: **True**
- champion_model_id: `challenger-2026-04-30`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`
- game_start_time_utc: `2026-05-03T19:40:00Z`
- snapshot_target_time_utc: `2026-05-03T16:10:40Z`
- actual_run_started_at_utc: `2026-05-03T16:10:40Z`
- actual_run_finished_at_utc: `2026-05-03T16:10:41Z`
- pmf_generated_at_utc: `2026-05-03T15:58:13Z`
- props_emitted: 33
- market_rows: 33
- active_players_projected: 14

## Lineup status

- lineup_source: `None`
- lineup_fetched_at_utc: `2026-05-03T16:10:41Z`
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
| prop_summary.parquet | 33 | `7eccf72a0c200c25` |
| full_pmf_wide.parquet | 33 | `ec3ba1c9bcfba624` |
| outcome_level_probabilities.parquet | 33 | `f1e9defa598f1d0c` |
| market_comparison.parquet | 33 | `fc636ef87feac491` |
| lineup_context.parquet | 14 | `fca957c3620ea87f` |
| injury_availability_context.parquet | 14 | `0e6c746d82e02043` |
| prediction_input_audit.parquet | 33 | `7eccf72a0c200c25` |
| direct_lineup_impact_report.json | 1 | `1641f1cdcba64f05` |
| game_context.parquet | 14 | `cef478ea358e1e88` |
| pmf_driver_decomposition.parquet | 33 | `34f40c4de5767254` |
| lineup_injury_impact_report.json | 1 | `394015348926e904` |
| contextual_feature_audit.parquet | 14 | `ff215e9da25d99c2` |
