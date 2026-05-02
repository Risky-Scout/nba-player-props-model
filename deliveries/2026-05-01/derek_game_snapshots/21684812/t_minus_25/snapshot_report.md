# Derek live snapshot — 2026-05-01 game 21684812 (t_minus_25)

- snapshot_type: **t_minus_25**
- snapshot_mode: **backfill_demo**
- pmf_source: **live_snapshot_reused_canonical**
- pmfs_recomputed: **False**
- champion_model_id: `challenger-2026-04-30`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`
- game_start_time_utc: `None`
- snapshot_target_time_utc: `None`
- actual_run_started_at_utc: `2026-05-02T13:12:39Z`
- actual_run_finished_at_utc: `2026-05-02T13:12:41Z`
- pmf_generated_at_utc: `2026-05-02T13:12:13Z`
- props_emitted: 29
- market_rows: 29
- active_players_projected: 13

## Lineup status

- lineup_source: `None`
- lineup_fetched_at_utc: `2026-05-02T13:12:41Z`
- lineup_confirmed: **False**
- lineup_complete: `unavailable`
- lineup_aware: **False**
- lineup_confirmation_status: `unavailable`
- lineup_blocker: 'no rows returned by BDL lineups endpoint (lineups not posted yet)'
- lineup_hash: ``
- starters_by_team: `{}`
- lineup_context_supplied: **True**
- lineup_affects_pmf_features: **False**
- lineup_feature_blocker: 'predict.py does not yet accept --lineup-context; lineup status is recorded as snapshot metadata and will inform Phase 13M-bis feature engineering, but does not currently change PMF features.'

## Champion model

- champion_metadata_verified: **False**
- no_leakage_champion_cutoff_verified: **False**
- live_snapshot_retrained: **False**
- live_snapshot_recalibrated: **False**

## Files

| File | rows | sha256 |
| --- | ---: | --- |
| prop_summary.parquet | 29 | `3ae4f000b83c11ab` |
| full_pmf_wide.parquet | 29 | `8095175e23dffc1b` |
| outcome_level_probabilities.parquet | 29 | `1fd7352464cb4d54` |
| market_comparison.parquet | 29 | `de6c1fa5dc791bd0` |
