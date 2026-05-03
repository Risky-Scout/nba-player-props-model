# Near-tip snapshot root-cause audit — 2026-05-03

- generated_at_utc: 2026-05-03T20:08:23+00:00Z

## Per-(game, snapshot_type) state

| game_id | snapshot_type | tip_utc | target_utc | now_utc | exists | missed_marker | true_state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 21682000 | t_minus_25 | 2026-05-03T23:40:00+00:00Z | 2026-05-03T23:15:00+00:00Z | 2026-05-03T20:08:23+00:00Z | False | False | **NOT_DUE** |
| 21682000 | close_lock | 2026-05-03T23:40:00+00:00Z | 2026-05-03T23:35:00+00:00Z | 2026-05-03T20:08:23+00:00Z | False | False | **NOT_DUE** |
| 21684819 | t_minus_25 | 2026-05-03T19:40:00+00:00Z | 2026-05-03T19:15:00+00:00Z | 2026-05-03T20:08:23+00:00Z | False | False | **MISSED_POST_TIP** |
| 21684819 | close_lock | 2026-05-03T19:40:00+00:00Z | 2026-05-03T19:35:00+00:00Z | 2026-05-03T20:08:23+00:00Z | False | False | **MISSED_POST_TIP** |

## Answers

### 1_why_21684819_t_minus_25_missing

Game 21684819 tipped at 19:40 UTC. The cron-driven dispatcher run that fell inside the T-25 window (19:10-19:22 UTC) either did not generate the snapshot (workflow not triggered, or generated for the other game first and stopped) or the dispatcher classified the game as 'not due' due to game_start_time being absent at the exact moment of the run. The fix must guarantee that any game with a known game_start_time gets evaluated through the explicit state machine on every cron firing.

### 2_workflow_not_triggered

Cron triggers every 10 minutes 16-04 UTC, so the 19:10Z and 19:20Z firings should both have considered the T-25 window. If predictions/all_props_<date>.parquet did not yet have game_start_time enriched at the 19:10Z firing, the dispatcher would have skipped the game with reason=no_game_start_time.

### 3_dispatcher_skipped_due_to_no_game_start_time

Confirmed by inspecting earlier 13T verbose log lines showing 'reason=no_game_start_time'. Phase 13U then added the resolver+enricher, but a future-date dispatch still depends on the resolver having ODDS_API_KEY.

### 4_target_window_tolerance_too_narrow

T_MINUS_25_WINDOW = (-5, +7) min. Cron interval is 10 min. A target landing between two cron ticks could fall outside the window. Phase 13Z widens to ±6 min and adds LATE_BUT_PRE_TIP to recover from any miss before tip.

### 5_force_true_ignored

Force=true in the previous workflow_dispatch was honored for current_live (it overwrote folders) but the T-25/close-lock branches still required the in-window check. The fix routes force=true through LATE_BUT_PRE_TIP if past the window but pre-tip.

### 6_close_lock_pending_not_due_when_now_past_target

verify_derek_production_live_e2e.py classified per-game snapshot states with this logic:
  if present: PASS
  elif overdue (now > target+grace) AND game_start<now: MISSED_POST_TIP
  elif overdue: MISSED
  else: PENDING_NOT_DUE
The 'else' branch fired for CLOSE_LOCK at now=19:38:13 target=19:35:00 because the per-snapshot overdue check used a 12-minute grace and the game_start comparison required game_start <= now. With now=19:38:13 and game_start=19:40:00, neither MISSED branch was hit, so it fell through to PENDING_NOT_DUE — the bug.

### 7_other_games_at_risk

[{'game_id': '21684819', 'snapshot_type': 't_minus_25', 'tip_utc': '2026-05-03T19:40:00+00:00Z', 'target_utc': '2026-05-03T19:15:00+00:00Z', 'now_utc': '2026-05-03T20:08:23+00:00Z', 'snapshot_exists': False, 'missed_marker_present': False, 'true_state': 'MISSED_POST_TIP'}, {'game_id': '21684819', 'snapshot_type': 'close_lock', 'tip_utc': '2026-05-03T19:40:00+00:00Z', 'target_utc': '2026-05-03T19:35:00+00:00Z', 'now_utc': '2026-05-03T20:08:23+00:00Z', 'snapshot_exists': False, 'missed_marker_present': False, 'true_state': 'MISSED_POST_TIP'}]

### 8_files_to_repair

['scripts/dispatch_derek_live_game_snapshots.py — share classify_snapshot_state with the verifier, generate LATE_BUT_PRE_TIP, write MISSED_POST_TIP markers.', 'scripts/verify_derek_production_live_e2e.py — replace the silent PENDING_NOT_DUE fallback with the same state machine; accept missed_post_tip markers as valid.', 'scripts/run_derek_live_game_snapshot.py — manifest stamps actual_run_late, late_seconds, snapshot_validity_status.', 'scripts/build_derek_delivery_readme.py — show explicit per-snapshot status from the state machine.', 'deliveries/<date>/derek_game_snapshots/<gid>/<snap>/missed_snapshot_manifest.json — the new honest miss marker.']

