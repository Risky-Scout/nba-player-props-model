# PMF calibration run

**Run at:** 2026-05-27T18:13:19.711913Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260527_181245`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 11,400 | yes | 0.549 / 0.256 | 0.509 / 0.273 |
| blk | 11,400 | yes | 0.505 / 0.290 | 0.501 / 0.290 |
| fg3m | 11,400 | yes | 0.471 / 0.329 | 0.489 / 0.313 |
| pts | 11,400 | yes | 0.540 / 0.282 | 0.506 / 0.284 |
| reb | 11,400 | yes | 0.550 / 0.254 | 0.509 / 0.273 |
| stl | 11,400 | yes | 0.489 / 0.289 | 0.489 / 0.288 |
| tov | 11,400 | yes | 0.543 / 0.262 | 0.521 / 0.275 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.