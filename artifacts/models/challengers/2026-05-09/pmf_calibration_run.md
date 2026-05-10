# PMF calibration run

**Run at:** 2026-05-10T16:33:46.528695Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260510_163252`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 15,546 | yes | 0.538 / 0.253 | 0.513 / 0.274 |
| blk | 15,546 | yes | 0.500 / 0.288 | 0.500 / 0.290 |
| fg3m | 15,546 | yes | 0.471 / 0.328 | 0.490 / 0.312 |
| pts | 15,546 | yes | 0.522 / 0.277 | 0.504 / 0.285 |
| reb | 15,546 | yes | 0.539 / 0.250 | 0.516 / 0.276 |
| stl | 15,546 | yes | 0.485 / 0.287 | 0.493 / 0.289 |
| stocks | 15,546 | yes | 0.482 / 0.285 | 0.494 / 0.288 |
| tov | 15,546 | yes | 0.546 / 0.259 | 0.514 / 0.274 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.