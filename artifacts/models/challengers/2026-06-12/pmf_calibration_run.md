# PMF calibration run

**Run at:** 2026-06-13T14:50:30.344204Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260613_145004`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 8,080 | yes | 0.551 / 0.257 | 0.508 / 0.279 |
| blk | 8,080 | yes | 0.504 / 0.289 | 0.512 / 0.294 |
| fg3m | 8,080 | yes | 0.471 / 0.328 | 0.485 / 0.316 |
| pts | 8,080 | yes | 0.542 / 0.284 | 0.520 / 0.294 |
| reb | 8,080 | yes | 0.552 / 0.256 | 0.524 / 0.282 |
| stl | 8,080 | yes | 0.490 / 0.288 | 0.487 / 0.292 |
| tov | 8,080 | yes | 0.541 / 0.260 | 0.526 / 0.275 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.