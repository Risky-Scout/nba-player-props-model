# Spurs @ Knicks — PMF driver decomposition

_Snapshot: `current_live` (on_time_or_current_live)._

Per-row contextual deltas from the Phase 13S direct-lineup engine. Constant deltas across players are honest when BDL did not return confirmed lineups (the engine then sees the same lagged-proxy bucket on every row).

## Per-player contextual deltas (top 30)

| player_name | team | exp_mp_contextual | contextual_minutes_delta |
| --- | --- | --- | --- |
| De'Aaron Fox | SAS | 14.445 | 14.445 |
| Landry Shamet | NYK | 14.445 | 14.445 |
| Jalen Brunson | NYK | 14.445 | 14.445 |
| Josh Hart | NYK | 14.445 | 14.445 |
| Stephon Castle | SAS | 14.445 | 14.445 |
| Devin Vassell | SAS | 14.445 | 14.445 |
| Julian Champagnie | SAS | 14.445 | 14.445 |
| Dylan Harper | SAS | 14.445 | 14.445 |
| Keldon Johnson | SAS | 14.445 | 14.445 |
| Mikal Bridges | NYK | 14.445 | 14.445 |
| Victor Wembanyama | SAS | 14.445 | 14.445 |
| Karl-Anthony Towns | NYK | 14.445 | 14.445 |

## Technical audit details

- Game ID: `21716136`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Contextual engine: **True**
- Contextual applied: **True**
- Direct-lineup driver: **True**
