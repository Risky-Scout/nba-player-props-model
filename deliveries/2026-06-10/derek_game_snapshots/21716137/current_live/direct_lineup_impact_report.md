# Spurs @ Knicks — Direct lineup impact

## Summary

- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Direct-lineup PMF driver: **True**
- Direct-lineup features consumed: **True**
- Lineup confirmed: **False**

Without confirmed lineups, the direct-lineup features fall back to lagged starter proxies. Treat the deltas as a best-available baseline, not a confirmed projection.

## Direct-lineup metrics

- Rows scored: **35**
- Confirmed starters: **0**
- Confirmed bench: **35**
- Starter changed from projection: **0**
- Bench changed from projection: **35**
- Minutes-projection conflicts: **0**
- Minutes-delta abs mean: **14.4434**
- Minutes-delta abs max: **14.4434**

## Per-stat rate-delta summary

| stat | abs_mean | abs_max | n |
| --- | ---: | ---: | ---: |
| ast | 0.0086 | 0.0086 | 35 |
| blk | 0.0006 | 0.0006 | 35 |
| fg3m | 0.0015 | 0.0015 | 35 |
| pts | 0.0290 | 0.0290 | 35 |
| reb | 0.0080 | 0.0080 | 35 |
| stl | 0.0020 | 0.0020 | 35 |
| tov | 0.0048 | 0.0048 | 35 |

## Technical audit details

- Game ID: `21716137`
- Champion model ID: `challenger-2026-06-09`
