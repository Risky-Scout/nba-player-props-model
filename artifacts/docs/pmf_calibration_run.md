# PMF calibration run

**Run at:** 2026-05-09T10:37:31.149424Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260509_103729`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 15,546 | no (insufficient data) | - | - |
| blk | 15,546 | no (insufficient data) | - | - |
| fg3m | 15,546 | no (insufficient data) | - | - |
| pts | 15,546 | no (insufficient data) | - | - |
| reb | 15,546 | no (insufficient data) | - | - |
| stl | 15,546 | no (insufficient data) | - | - |
| stocks | 15,546 | no (insufficient data) | - | - |
| tov | 15,546 | no (insufficient data) | - | - |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.