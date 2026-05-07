# PMF calibration run

**Run at:** 2026-05-07T17:09:02.520473Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260507_170901`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 14,054 | no (insufficient data) | - | - |
| fg3m | 14,902 | no (insufficient data) | - | - |
| pts | 14,054 | no (insufficient data) | - | - |
| reb | 14,054 | no (insufficient data) | - | - |
| tov | 14,054 | no (insufficient data) | - | - |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.