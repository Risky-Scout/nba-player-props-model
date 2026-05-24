# PMF calibration run

**Run at:** 2026-05-24T16:42:13.921106Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260524_164147`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 11,322 | yes | 0.549 / 0.257 | 0.511 / 0.272 |
| blk | 11,322 | yes | 0.503 / 0.290 | 0.496 / 0.287 |
| fg3m | 11,322 | yes | 0.470 / 0.329 | 0.486 / 0.313 |
| pts | 11,322 | yes | 0.540 / 0.283 | 0.505 / 0.284 |
| reb | 11,322 | yes | 0.549 / 0.255 | 0.508 / 0.273 |
| stl | 11,322 | yes | 0.488 / 0.287 | 0.492 / 0.287 |
| tov | 11,322 | yes | 0.540 / 0.264 | 0.522 / 0.275 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.