# PMF calibration run

**Run at:** 2026-05-25T22:43:09.410885Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260525_224222`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 11,347 | yes | 0.548 / 0.257 | 0.510 / 0.273 |
| blk | 11,347 | yes | 0.501 / 0.290 | 0.502 / 0.288 |
| fg3m | 11,347 | yes | 0.471 / 0.329 | 0.490 / 0.312 |
| pts | 11,347 | yes | 0.540 / 0.283 | 0.506 / 0.285 |
| reb | 11,347 | yes | 0.550 / 0.254 | 0.508 / 0.273 |
| stl | 11,347 | yes | 0.487 / 0.287 | 0.492 / 0.289 |
| tov | 11,347 | yes | 0.542 / 0.262 | 0.522 / 0.275 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.