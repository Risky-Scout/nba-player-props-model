# Near-tip snapshot root-cause audit — 2026-06-03

Generated 2026-06-04T00:24:55Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Knicks | Spurs | Knicks @ Spurs | T-minus-25 | `2026-06-04T00:30:00Z` | `2026-06-04T00:05:00Z` | Available (late but pre-tip) |
| Knicks | Spurs | Knicks @ Spurs | Close-lock | `2026-06-04T00:30:00Z` | `2026-06-04T00:24:00Z` | Available |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

