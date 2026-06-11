# Near-tip snapshot root-cause audit — 2026-06-10

Generated 2026-06-11T01:41:47Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Spurs | Knicks | Spurs @ Knicks | T-minus-25 | `2026-06-11T00:43:00Z` | `2026-06-11T00:18:00Z` | Missed during setup window; documented, not backfilled |
| Spurs | Knicks | Spurs @ Knicks | Close-lock | `2026-06-11T00:43:00Z` | `2026-06-11T00:37:00Z` | Missed during setup window; documented, not backfilled |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

