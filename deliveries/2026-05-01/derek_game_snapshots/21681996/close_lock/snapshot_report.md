# Derek live snapshot — 2026-05-01 game 21681996 (close_lock)

- snapshot_type: **close_lock**
- snapshot_mode: **backfill_demo**
- pmf_source: **live_snapshot_reused_canonical**
- pmfs_recomputed: **False**
- champion_model_id: `challenger-2026-04-30`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`
- game_start_time_utc: `None`
- snapshot_target_time_utc: `None`
- actual_run_started_at_utc: `2026-05-02T13:43:59Z`
- actual_run_finished_at_utc: `2026-05-02T13:44:00Z`
- pmf_generated_at_utc: `2026-05-02T13:43:25Z`
- props_emitted: 33
- market_rows: 33
- active_players_projected: 13

## Lineup status

- lineup_source: `None`
- lineup_fetched_at_utc: `2026-05-02T13:44:00Z`
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

- champion_metadata_verified: **False**
- no_leakage_champion_cutoff_verified: **False**
- live_snapshot_retrained: **False**
- live_snapshot_recalibrated: **False**

## Files

| File | rows | sha256 |
| --- | ---: | --- |
| prop_summary.parquet | 33 | `67e99629dbdcf062` |
| full_pmf_wide.parquet | 33 | `8b75168f45315515` |
| outcome_level_probabilities.parquet | 33 | `ed55de6be5392388` |
| market_comparison.parquet | 33 | `def0015164e4fd5f` |
