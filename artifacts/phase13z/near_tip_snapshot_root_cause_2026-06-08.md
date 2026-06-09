# Near-tip snapshot root-cause audit — 2026-06-08

Generated 2026-06-09T00:02:03Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Spurs | Knicks | Spurs @ Knicks | T-minus-25 | `2026-06-09T00:40:00Z` | `2026-06-09T00:15:00Z` | Scheduled |
| Spurs | Knicks | Spurs @ Knicks | Close-lock | `2026-06-09T00:40:00Z` | `2026-06-09T00:35:00Z` | Scheduled |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

