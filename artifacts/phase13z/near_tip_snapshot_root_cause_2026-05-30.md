# Near-tip snapshot root-cause audit — 2026-05-30

Generated 2026-05-30T21:13:52Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Spurs | Thunder | Spurs @ Thunder | T-minus-25 | `2026-05-31T00:10:00Z` | `2026-05-30T23:45:00Z` | Scheduled |
| Spurs | Thunder | Spurs @ Thunder | Close-lock | `2026-05-31T00:10:00Z` | `2026-05-31T00:05:00Z` | Scheduled |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

