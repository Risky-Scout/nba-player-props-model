# Near-tip snapshot root-cause audit — 2026-05-08

Generated 2026-05-08T23:31:07Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Knicks | 76ers | Knicks @ 76ers | T-minus-25 | `2026-05-08T23:10:00Z` | `2026-05-08T22:45:00Z` | Missed during setup window; documented, not backfilled |
| Knicks | 76ers | Knicks @ 76ers | Close-lock | `2026-05-08T23:10:00Z` | `2026-05-08T23:05:00Z` | Missed during setup window; documented, not backfilled |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

