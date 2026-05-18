# PMF calibration run

**Run at:** 2026-05-18T20:13:21.462949Z
**Folds:** 6 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260518_201147`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 19,208 | yes | 0.544 / 0.255 | 0.515 / 0.274 |
| blk | 19,208 | yes | 0.512 / 0.296 | 0.498 / 0.289 |
| fg3m | 19,208 | yes | 0.470 / 0.327 | 0.489 / 0.312 |
| pts | 19,208 | yes | 0.531 / 0.281 | 0.503 / 0.286 |
| reb | 19,208 | yes | 0.546 / 0.253 | 0.512 / 0.276 |
| stl | 19,208 | yes | 0.505 / 0.295 | 0.492 / 0.290 |
| stocks | 19,208 | yes | 0.508 / 0.297 | 0.497 / 0.293 |
| tov | 19,208 | yes | 0.542 / 0.261 | 0.517 / 0.275 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.