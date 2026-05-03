# Derek Output Blocker Audit (Phase 13U Part B)

- generated_at_utc: 2026-05-03T15:35:20+00:00Z

## delivery_date = 2026-05-03

- predictions_parquet_present: **True**
- prediction_rows: 69
- unique_games: 2
- game_ids: ['21682000', '21684819']
- game_start_time_column_present: **False**
- game_start_time_non_null_count: 0
- pmf_display_props: 8
- pmf_display_games: ['Orlando Magic @ Detroit Pistons', 'Toronto Raptors @ Cleveland Cavaliers']
- pmf_display_top_level_time_keys: []
- odds_api_processed_dir_present: False
- odds_api_raw_event_count: 0
- derek_snapshot_count: 0
- live_lineups_dir_present: False

## Root cause

predictions/all_props_<date>.parquet has no game_start_time column at all (not just null), so the dispatcher's _load_schedule cannot derive any per-game tip time. Without tip times, the T-25 / close-lock window check always returns due=False with reason=no_game_start_time.

## Files to repair

- `src/nba_props_model/schedule/game_start_times.py (new resolver)`
- `scripts/resolve_game_start_times.py (CLI for live_schedule outputs)`
- `scripts/enrich_predictions_game_start_times.py (metadata-only writer)`
- `scripts/dispatch_derek_live_game_snapshots.py (resolver-aware)`
- `scripts/run_derek_live_game_snapshot.py (current_live mode)`
- `scripts/verify_derek_slate_completeness.py (new)`
- `scripts/verify_derek_production_live_e2e.py (extend with current_live)`
- `.github/workflows/derek_live_game_snapshots.yml (cron + steps)`

