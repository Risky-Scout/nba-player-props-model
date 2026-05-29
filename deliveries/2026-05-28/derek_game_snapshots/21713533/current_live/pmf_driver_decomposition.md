# Thunder @ Spurs — PMF driver decomposition

_Snapshot: `current_live` (on_time_or_current_live)._

Per-row contextual deltas from the Phase 13S direct-lineup engine. Constant deltas across players are honest when BDL did not return confirmed lineups (the engine then sees the same lagged-proxy bucket on every row).

## Per-player contextual deltas (top 30)

| player_name | team | exp_mp_contextual | contextual_minutes_delta |
| --- | --- | --- | --- |
| De'Aaron Fox | SAS | 14.451 | 14.451 |
| Jalen Williams | OKC | 14.451 | 14.451 |
| Isaiah Hartenstein | OKC | 14.451 | 14.451 |
| Cason Wallace | OKC | 14.451 | 14.451 |
| Jaylin Williams | OKC | 14.451 | 14.451 |
| Jared McCain | OKC | 14.451 | 14.451 |
| Stephon Castle | SAS | 14.451 | 14.451 |
| Devin Vassell | SAS | 14.451 | 14.451 |
| Shai Gilgeous-Alexander | OKC | 14.451 | 14.451 |
| Luguentz Dort | OKC | 14.451 | 14.451 |
| Julian Champagnie | SAS | 14.451 | 14.451 |
| Chet Holmgren | OKC | 14.451 | 14.451 |
| Dylan Harper | SAS | 14.451 | 14.451 |
| Alex Caruso | OKC | 14.451 | 14.451 |
| Keldon Johnson | SAS | 14.451 | 14.451 |
| Victor Wembanyama | SAS | 14.451 | 14.451 |

## Technical audit details

- Game ID: `21713533`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Contextual engine: **True**
- Contextual applied: **True**
- Direct-lineup driver: **True**
