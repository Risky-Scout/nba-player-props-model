# Spurs @ Knicks — Direct lineup impact

## Summary

- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Direct-lineup PMF driver: **True**
- Direct-lineup features consumed: **True**
- Lineup confirmed: **False**

Without confirmed lineups, the direct-lineup features fall back to lagged starter proxies. Treat the deltas as a best-available baseline, not a confirmed projection.

## Direct-lineup metrics

- Rows scored: **30**
- Confirmed starters: **0**
- Confirmed bench: **30**
- Starter changed from projection: **0**
- Bench changed from projection: **30**
- Minutes-projection conflicts: **0**
- Minutes-delta abs mean: **14.4450**
- Minutes-delta abs max: **14.4450**

## Per-stat rate-delta summary

| stat | abs_mean | abs_max | n |
| --- | ---: | ---: | ---: |
| ast | 0.0086 | 0.0086 | 30 |
| blk | 0.0006 | 0.0006 | 30 |
| fg3m | 0.0015 | 0.0015 | 30 |
| pts | 0.0290 | 0.0290 | 30 |
| reb | 0.0080 | 0.0080 | 30 |
| stl | 0.0020 | 0.0020 | 30 |
| tov | 0.0048 | 0.0048 | 30 |

## Technical audit details

- Game ID: `21716136`
- Champion model ID: `challenger-2026-06-06`
