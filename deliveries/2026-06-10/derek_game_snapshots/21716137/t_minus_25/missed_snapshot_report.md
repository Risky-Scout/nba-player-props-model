# Spurs @ Knicks — T-minus-25 snapshot

This near-tip snapshot was not generated before tip.

The target time was 25 minutes before tip. By the time the near-tip verification ran, the game had already started, so the system did not create a backfilled pre-tip PMF. That is intentional: creating a pre-tip snapshot after the game starts would risk using information that was not available at the time.

The miss is documented here so the daily index and verifiers show the true status. Going forward, the dispatcher's snapshot state machine fires inside the cron window and recovers any miss before tip; only post-tip misses produce this report.

## Technical audit details

- Game ID: `21716137`
- Away Team: Spurs
- Home Team: Knicks
- Snapshot type: `t_minus_25`
- Target time UTC: `2026-06-11T00:18:00Z`
- Tip time UTC: `2026-06-11T00:43:00Z`
- Documented at UTC: `2026-06-11T01:41:26Z`
- Missed reason: `post_tip_no_pretip_snapshot_was_generated`
- no_fake_pretip_snapshot: **True**
- production_fix_applied: **True**
