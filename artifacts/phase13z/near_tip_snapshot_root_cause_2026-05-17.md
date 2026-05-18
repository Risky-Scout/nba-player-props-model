# Near-tip snapshot root-cause audit — 2026-05-17

Generated 2026-05-18T03:52:54Z.

## Per-(matchup, snapshot) state

| Away | Home | Matchup | Snapshot | Tip Time UTC | Target Time UTC | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Away (game 21709241) | Home (game 21709241) | Game 21709241 | T-minus-25 | `` | `` | Pending dispatch |
| Away (game 21709241) | Home (game 21709241) | Game 21709241 | Close-lock | `` | `` | Pending dispatch |

## Why missed snapshots are documented, not backfilled

The dispatcher's snapshot state machine refuses to create a pre-tip snapshot after a game has already tipped. That would risk capturing post-tip information into a manifest claimed as pre-tip. Instead, missed near-tip snapshots get a `missed_snapshot_manifest.json` + `missed_snapshot_report.md` marker so the daily index and verifiers can show the true status.

