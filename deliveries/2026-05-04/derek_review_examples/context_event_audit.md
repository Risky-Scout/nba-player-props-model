# Context event audit — 2026-05-04

_Generated 2026-05-05T02:43:30+00:00._

This audit shows how late-breaking lineup / injury news is captured by snapshots and propagated to teammates.

## Schema

| field | description |
|---|---|
| `event_type` | `injury_news` / `lineup_change` / `vacated_minutes` |
| `player_id`, `player_name` | subject of the event |
| `event_timestamp_utc` | when BDL injury fetch / lineup feed first reported it |
| `event_source` | `BDL_injury_fetch` / `BDL_lineup_feed` / `manual` |
| `caught_by_snapshot` | `current_live` / `t_minus_25` / `close_lock` |
| `caught_at_snapshot_time_utc` | the snapshot's `generated_at_utc` |
| `propagation_player_ids` | teammates whose vacated-minutes / role context shifted |
| `pmf_mean_delta` | model PMF mean shift (per stat) attributable to the event |
| `lineup_confirmed_post_event` | whether the event lifted the snapshot from projected → confirmed |

## Worked example — Ayo Dosunmu ruled out around 3 PM ET

Hypothetical event format (Bulls 3 PM ET injury report drops):

```
event_type: injury_news
player: Ayo Dosunmu (player_id=…)
event_timestamp_utc: 2026-05-04T19:00:00Z   # 3 PM ET
event_source: BDL_injury_fetch
caught_by_snapshot: t_minus_25
caught_at_snapshot_time_utc: 2026-05-04T22:35:00Z
propagation_player_ids: [Coby White, Lonzo Ball, Patrick Williams]
pmf_mean_delta:
  Coby White / pts:   +1.42 (vacated lead-guard minutes)
  Lonzo Ball  / ast:  +0.58 (assist creation share)
  Patrick Williams / reb: +0.31 (role-bucket lift, smaller)
lineup_confirmed_post_event: True (pre-game lineup matched the news)
```

## Slate matches: **['Ayo Dosunmu', 'Victor Wembanyama']**

These players appear in today's slate; the snapshot folders for their games will carry the audit fields above when an event hits within the snapshot window.

## Where to find this in the production artifacts

- `lineup_injury_impact_report.md` (per snapshot folder) — confirms   whether BDL injury fetch returned data and what the snapshot saw.
- `direct_lineup_impact_report.md` — Phase 13S direct-lineup driver   attribution: starter / bench changes, lineup composition impact.
- `pmf_driver_decomposition.md` — per-row contextual minutes / rate   deltas attributable to the lineup / injury context.

## Hard rule

If a snapshot was generated BEFORE the event timestamp, the snapshot does NOT carry the new context. The dispatcher will not back-rewrite a snapshot to claim it caught later news.

