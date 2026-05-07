# Near-tip snapshot root-cause audit — 2026-05-06

Generated 2026-05-07T02:31:41Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Timberwolves | Spurs | Timberwolves @ Spurs | T-minus-25 | `2026-05-07T01:48:13Z` | `2026-05-07T01:23:13Z` | Missed during setup window; documented, not backfilled |
| Timberwolves | Spurs | Timberwolves @ Spurs | Close-lock | `2026-05-07T01:48:13Z` | `2026-05-07T01:43:13Z` | Pending dispatch |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

