# Raptors @ Cavaliers — PMF driver decomposition

_Snapshot: `current_live` (on_time_or_current_live)._

Per-row contextual deltas from the Phase 13S direct-lineup engine. Constant deltas across players are honest when BDL did not return confirmed lineups (the engine then sees the same lagged-proxy bucket on every row).

## Per-player contextual deltas (top 30)

| player_name | exp_mp_contextual | contextual_minutes_delta | contextual_pmf_mean_baseline | contextual_pmf_mean_post |
| --- | --- | --- | --- | --- |
| James Harden | 15.378 | 15.378 | nan | nan |
| Donovan Mitchell | 15.378 | 15.378 | nan | nan |
| Sam Merrill | 15.378 | 15.378 | nan | nan |
| Brandon Ingram | 15.378 | 15.378 | nan | nan |
| Ja'Kobe Walter | 15.378 | 15.378 | nan | nan |
| Jarrett Allen | 15.378 | 15.378 | nan | nan |
| Evan Mobley | 15.378 | 15.378 | nan | nan |
| RJ Barrett | 15.378 | 15.378 | nan | nan |
| Collin Murray-Boyles | 15.378 | 15.378 | nan | nan |
| Jakob Poeltl | 15.378 | 15.378 | nan | nan |
| Scottie Barnes | 15.378 | 15.378 | nan | nan |
| Dennis Schroder | 15.378 | 15.378 | nan | nan |
| Jamal Shead | 15.378 | 15.378 | nan | nan |
| Sandro Mamukelashvili | 15.378 | 15.378 | nan | nan |

## Technical audit details

- Game ID: `21682000`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Contextual engine: **True**
- Contextual applied: **True**
- Direct-lineup driver: **True**
