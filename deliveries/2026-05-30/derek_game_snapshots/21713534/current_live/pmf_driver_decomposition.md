# Spurs @ Thunder — PMF driver decomposition

_Snapshot: `current_live` (on_time_or_current_live)._

Per-row contextual deltas from the Phase 13S direct-lineup engine. Constant deltas across players are honest when BDL did not return confirmed lineups (the engine then sees the same lagged-proxy bucket on every row).

## Per-player contextual deltas (top 30)

| player_name | team | exp_mp_contextual | contextual_minutes_delta | contextual_pmf_mean_baseline | contextual_pmf_mean_post |
| --- | --- | --- | --- | --- | --- |
| Isaiah Joe | OKC | 14.451 | 14.451 | nan | nan |
| Chet Holmgren | OKC | 14.451 | 14.451 | nan | nan |
| De'Aaron Fox | SAS | 14.451 | 14.451 | nan | nan |
| Jaylin Williams | OKC | 14.451 | 14.451 | nan | nan |
| Stephon Castle | SAS | 14.451 | 14.451 | nan | nan |
| Luguentz Dort | OKC | 14.451 | 14.451 | nan | nan |
| Shai Gilgeous-Alexander | OKC | 14.451 | 14.451 | nan | nan |
| Dylan Harper | SAS | 14.451 | 14.451 | nan | nan |
| Keldon Johnson | SAS | 14.451 | 14.451 | nan | nan |
| Victor Wembanyama | SAS | 14.451 | 14.451 | nan | nan |
| Cason Wallace | OKC | 14.451 | 14.451 | nan | nan |
| Isaiah Hartenstein | OKC | 14.451 | 14.451 | nan | nan |
| Alex Caruso | OKC | 14.451 | 14.451 | nan | nan |
| Kenrich Williams | OKC | 14.451 | 14.451 | nan | nan |
| Jared McCain | OKC | 14.451 | 14.451 | nan | nan |
| Devin Vassell | SAS | 14.451 | 14.451 | nan | nan |
| Julian Champagnie | SAS | 14.451 | 14.451 | nan | nan |

## Technical audit details

- Game ID: `21713534`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Contextual engine: **True**
- Contextual applied: **True**
- Direct-lineup driver: **True**
