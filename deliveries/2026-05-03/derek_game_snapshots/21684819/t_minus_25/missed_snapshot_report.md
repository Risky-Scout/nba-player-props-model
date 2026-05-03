# Missed snapshot — t_minus_25 (21684819) 2026-05-03

- snapshot_type: **t_minus_25**
- game_id: `21684819`
- delivery_date: 2026-05-03
- game_start_time_utc: `2026-05-03T19:40:00Z`
- snapshot_target_time_utc: `2026-05-03T19:15:00Z`
- now_utc: `2026-05-03T20:10:48Z`
- missed_reason: `post_tip_no_pretip_snapshot_was_generated`

## Why a marker, not a fake snapshot

The game has already tipped. We do **not** fabricate a pre-tip snapshot after the fact — pre-tip lineups, injury status, and odds at this moment in history can no longer be reconstructed without leakage from in-game data. Instead, this marker file records the miss honestly so downstream verifiers and Derek's index can label the snapshot as MISSED_POST_TIP rather than silently treating it as pending.

- `no_fake_pretip_snapshot: true`
- `production_fix_applied: true`
