# PMF calibration run

**Run at:** 2026-06-08T12:24:22.691742Z
**Folds:** 3 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260608_122357`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 7,953 | yes | 0.548 / 0.260 | 0.509 / 0.280 |
| blk | 7,953 | yes | 0.503 / 0.291 | 0.512 / 0.296 |
| fg3m | 7,953 | yes | 0.473 / 0.329 | 0.484 / 0.317 |
| pts | 7,953 | yes | 0.543 / 0.284 | 0.521 / 0.294 |
| reb | 7,953 | yes | 0.553 / 0.256 | 0.528 / 0.282 |
| stl | 7,953 | yes | 0.490 / 0.291 | 0.497 / 0.290 |
| tov | 7,953 | yes | 0.537 / 0.264 | 0.528 / 0.274 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.