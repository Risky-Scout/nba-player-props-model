# Knicks @ Cavaliers — PMF driver decomposition

_Snapshot: `current_live` (on_time_or_current_live)._

Per-row contextual deltas from the Phase 13S direct-lineup engine. Constant deltas across players are honest when BDL did not return confirmed lineups (the engine then sees the same lagged-proxy bucket on every row).

## Per-player contextual deltas (top 30)

| player_name | team | exp_mp_contextual | contextual_minutes_delta | contextual_pmf_mean_baseline | contextual_pmf_mean_post |
| --- | --- | --- | --- | --- | --- |
| James Harden | CLE | 14.452 | 14.452 | nan | nan |
| Donovan Mitchell | CLE | 14.452 | 14.452 | nan | nan |
| Sam Merrill | CLE | 14.452 | 14.452 | nan | nan |
| Jalen Brunson | NYK | 14.452 | 14.452 | nan | nan |
| Josh Hart | NYK | 14.452 | 14.452 | nan | nan |
| Jarrett Allen | CLE | 14.452 | 14.452 | nan | nan |
| Evan Mobley | CLE | 14.452 | 14.452 | nan | nan |
| Max Strus | CLE | 14.452 | 14.452 | nan | nan |
| Mikal Bridges | NYK | 14.452 | 14.452 | nan | nan |
| Karl-Anthony Towns | NYK | 14.452 | 14.452 | nan | nan |

## Technical audit details

- Game ID: `21713901`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Contextual engine: **True**
- Contextual applied: **True**
- Direct-lineup driver: **True**
