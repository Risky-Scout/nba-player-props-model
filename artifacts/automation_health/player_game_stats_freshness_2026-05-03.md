# Player game stats freshness — 2026-05-03

_Generated 2026-05-04T17:00:53+00:00._

- backfill window: **2026-04-30 → 2026-05-03**
- status: **FAILED**
- total rows in parquet: **83497**
- min game_date: `2023-10-24`
- max game_date: `2026-04-29`
- duplicate (game_id, player_id) rows: `0`
- rows added by this run: **0**

## Reason

BDL_API_KEY environment variable is not set; refusing to fabricate outcomes. The official refresh script (scripts/refresh_bdl_player_game_stats.py) requires this credential.

## Remediation

Run from CI where BDL_API_KEY is provisioned, or export BDL_API_KEY locally before invoking this script.
