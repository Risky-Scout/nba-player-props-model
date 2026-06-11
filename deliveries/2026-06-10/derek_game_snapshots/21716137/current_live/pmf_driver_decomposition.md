# Spurs @ Knicks — PMF driver decomposition

_Snapshot: `current_live` (on_time_or_current_live)._

Per-row contextual deltas from the Phase 13S direct-lineup engine. Constant deltas across players are honest when BDL did not return confirmed lineups (the engine then sees the same lagged-proxy bucket on every row).

## Per-player contextual deltas (top 30)

| player_name | team | exp_mp_contextual | contextual_minutes_delta |
| --- | --- | --- | --- |
| Mitchell Robinson | NYK | 14.443 | 14.443 |
| OG Anunoby | NYK | 14.443 | 14.443 |
| Landry Shamet | NYK | 14.443 | 14.443 |
| De'Aaron Fox | SAS | 14.443 | 14.443 |
| Stephon Castle | SAS | 14.443 | 14.443 |
| Dylan Harper | SAS | 14.443 | 14.443 |
| Keldon Johnson | SAS | 14.443 | 14.443 |
| Mikal Bridges | NYK | 14.443 | 14.443 |
| Victor Wembanyama | SAS | 14.443 | 14.443 |
| Karl-Anthony Towns | NYK | 14.443 | 14.443 |
| Jalen Brunson | NYK | 14.443 | 14.443 |
| Josh Hart | NYK | 14.443 | 14.443 |
| Miles McBride | NYK | 14.443 | 14.443 |
| Devin Vassell | SAS | 14.443 | 14.443 |
| Julian Champagnie | SAS | 14.443 | 14.443 |

## Technical audit details

- Game ID: `21716137`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Contextual engine: **True**
- Contextual applied: **True**
- Direct-lineup driver: **True**
