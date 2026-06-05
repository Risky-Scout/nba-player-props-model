# Knicks @ Spurs — PMF driver decomposition

_Snapshot: `current_live` (on_time_or_current_live)._

Per-row contextual deltas from the Phase 13S direct-lineup engine. Constant deltas across players are honest when BDL did not return confirmed lineups (the engine then sees the same lagged-proxy bucket on every row).

## Per-player contextual deltas (top 30)

| player_name | team | exp_mp_contextual | contextual_minutes_delta | contextual_pmf_mean_baseline | contextual_pmf_mean_post |
| --- | --- | --- | --- | --- | --- |
| De'Aaron Fox | SAS | 14.447 | 14.447 | nan | nan |
| Landry Shamet | NYK | 14.447 | 14.447 | nan | nan |
| Luke Kornet | SAS | 14.447 | 14.447 | nan | nan |
| Jalen Brunson | NYK | 14.447 | 14.447 | nan | nan |
| Josh Hart | NYK | 14.447 | 14.447 | nan | nan |
| Stephon Castle | SAS | 14.447 | 14.447 | nan | nan |
| Devin Vassell | SAS | 14.447 | 14.447 | nan | nan |
| Mitchell Robinson | NYK | 14.447 | 14.447 | nan | nan |
| Julian Champagnie | SAS | 14.447 | 14.447 | nan | nan |
| OG Anunoby | NYK | 14.447 | 14.447 | nan | nan |
| Dylan Harper | SAS | 14.447 | 14.447 | nan | nan |
| Keldon Johnson | SAS | 14.447 | 14.447 | nan | nan |
| Mikal Bridges | NYK | 14.447 | 14.447 | nan | nan |
| Victor Wembanyama | SAS | 14.447 | 14.447 | nan | nan |
| Karl-Anthony Towns | NYK | 14.447 | 14.447 | nan | nan |

## Technical audit details

- Game ID: `21716135`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Contextual engine: **True**
- Contextual applied: **True**
- Direct-lineup driver: **True**
