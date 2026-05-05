# Timberwolves @ Spurs — Close-lock snapshot

This near-tip snapshot was not generated before tip.

The target time was 5 minutes before tip. By the time the near-tip verification ran, the game had already started, so the system did not create a backfilled pre-tip PMF. That is intentional: creating a pre-tip snapshot after the game starts would risk using information that was not available at the time.

The miss is documented here so the daily index and verifiers show the true status. Going forward, the dispatcher's snapshot state machine fires inside the cron window and recovers any miss before tip; only post-tip misses produce this report.

## Technical audit details

- Game ID: `21707972`
- Away Team: Timberwolves
- Home Team: Spurs
- Snapshot type: `close_lock`
- Target time UTC: `2026-05-05T01:38:12Z`
- Tip time UTC: `2026-05-05T01:43:12Z`
- Documented at UTC: `2026-05-05T01:44:13Z`
- Missed reason: `post_tip_no_pretip_snapshot_was_generated`
- no_fake_pretip_snapshot: **True**
- production_fix_applied: **True**
