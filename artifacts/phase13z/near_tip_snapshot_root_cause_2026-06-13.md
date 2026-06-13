# Near-tip snapshot root-cause audit — 2026-06-13

Generated 2026-06-13T21:53:06Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Knicks | Spurs | Knicks @ Spurs | T-minus-25 | `2026-06-14T00:40:00Z` | `2026-06-14T00:15:00Z` | Scheduled |
| Knicks | Spurs | Knicks @ Spurs | Close-lock | `2026-06-14T00:40:00Z` | `2026-06-14T00:35:00Z` | Scheduled |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

