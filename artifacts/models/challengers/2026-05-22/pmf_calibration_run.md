# PMF calibration run

**Run at:** 2026-05-23T22:21:46.286982Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260523_222058`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 11,303 | yes | 0.550 / 0.256 | 0.511 / 0.272 |
| blk | 11,303 | yes | 0.505 / 0.289 | 0.498 / 0.289 |
| fg3m | 11,303 | yes | 0.471 / 0.329 | 0.487 / 0.313 |
| pts | 11,303 | yes | 0.539 / 0.284 | 0.505 / 0.284 |
| reb | 11,303 | yes | 0.549 / 0.255 | 0.506 / 0.274 |
| stl | 11,303 | yes | 0.488 / 0.287 | 0.494 / 0.288 |
| tov | 11,303 | yes | 0.542 / 0.263 | 0.523 / 0.276 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.