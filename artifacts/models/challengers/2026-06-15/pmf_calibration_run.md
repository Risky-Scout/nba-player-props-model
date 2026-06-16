# PMF calibration run

**Run at:** 2026-06-16T19:17:06.145941Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260616_191629`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 8,101 | yes | 0.551 / 0.258 | 0.509 / 0.278 |
| blk | 8,101 | yes | 0.505 / 0.290 | 0.508 / 0.296 |
| fg3m | 8,101 | yes | 0.473 / 0.329 | 0.487 / 0.315 |
| pts | 8,101 | yes | 0.542 / 0.284 | 0.522 / 0.294 |
| reb | 8,101 | yes | 0.552 / 0.256 | 0.526 / 0.281 |
| stl | 8,101 | yes | 0.489 / 0.289 | 0.487 / 0.289 |
| tov | 8,101 | yes | 0.540 / 0.262 | 0.528 / 0.277 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.