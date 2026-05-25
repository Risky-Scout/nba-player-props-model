# Near-tip snapshot root-cause audit — 2026-05-25

Generated 2026-05-25T20:50:45Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Knicks | Cavaliers | Knicks @ Cavaliers | T-minus-25 | `` | `` | Pending dispatch |
| Knicks | Cavaliers | Knicks @ Cavaliers | Close-lock | `` | `` | Pending dispatch |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

