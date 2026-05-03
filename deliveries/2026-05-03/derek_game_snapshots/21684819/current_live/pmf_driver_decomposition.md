# Magic @ Pistons — PMF driver decomposition

_Snapshot: `current_live` (post_tip_stale_baseline)._

Per-row contextual deltas from the Phase 13S direct-lineup engine. Constant deltas across players are honest when BDL did not return confirmed lineups (the engine then sees the same lagged-proxy bucket on every row).

## Per-player contextual deltas (top 30)

| player_name | exp_mp_contextual | contextual_minutes_delta | contextual_pmf_mean_baseline | contextual_pmf_mean_post |
| --- | --- | --- | --- | --- |
| Daniss Jenkins | 15.378 | 15.378 | nan | nan |
| Ausar Thompson | 15.378 | 15.378 | nan | nan |
| Anthony Black | 15.378 | 15.378 | nan | nan |
| Isaiah Stewart | 15.378 | 15.378 | nan | nan |
| Jamal Cain | 15.378 | 15.378 | nan | nan |
| Tobias Harris | 15.378 | 15.378 | nan | nan |
| Jalen Suggs | 15.378 | 15.378 | nan | nan |
| Cade Cunningham | 15.378 | 15.378 | nan | nan |
| Duncan Robinson | 15.378 | 15.378 | nan | nan |
| Paolo Banchero | 15.378 | 15.378 | nan | nan |
| Wendell Carter Jr. | 15.378 | 15.378 | nan | nan |
| Desmond Bane | 15.378 | 15.378 | nan | nan |
| Tristan Da Silva | 15.378 | 15.378 | nan | nan |
| Jalen Duren | 15.378 | 15.378 | nan | nan |

## Technical audit details

- Game ID: `21684819`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Contextual engine: **True**
- Contextual applied: **True**
- Direct-lineup driver: **True**
