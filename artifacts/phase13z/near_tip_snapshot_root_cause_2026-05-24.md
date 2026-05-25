# Near-tip snapshot root-cause audit — 2026-05-24

Generated 2026-05-25T01:59:15Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Thunder | Spurs | Thunder @ Spurs | T-minus-25 | `2026-05-25T00:13:00Z` | `2026-05-24T23:48:00Z` | Missed during setup window; documented, not backfilled |
| Thunder | Spurs | Thunder @ Spurs | Close-lock | `2026-05-25T00:13:00Z` | `2026-05-25T00:08:00Z` | Available |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

