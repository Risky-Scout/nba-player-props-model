# Near-tip snapshot root-cause audit — 2026-05-04

Generated 2026-05-05T01:45:10Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Timberwolves | Spurs | Timberwolves @ Spurs | T-minus-25 | `2026-05-05T01:43:12Z` | `2026-05-05T01:18:12Z` | Pending dispatch |
| Timberwolves | Spurs | Timberwolves @ Spurs | Close-lock | `2026-05-05T01:43:12Z` | `2026-05-05T01:38:12Z` | Missed during setup window; documented, not backfilled |
| 76ers | Knicks | 76ers @ Knicks | T-minus-25 | `2026-05-05T00:13:39Z` | `2026-05-04T23:48:39Z` | Missed during setup window; documented, not backfilled |
| 76ers | Knicks | 76ers @ Knicks | Close-lock | `2026-05-05T00:13:39Z` | `2026-05-05T00:08:39Z` | Missed during setup window; documented, not backfilled |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

