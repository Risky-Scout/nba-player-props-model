# PMF calibration run

**Run at:** 2026-05-06T22:28:38.192324Z
**Folds:** 15 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260506_222744`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 49,525 | yes | 0.541 / 0.256 | 0.504 / 0.283 |
| fg3m | 49,525 | yes | 0.478 / 0.329 | 0.492 / 0.300 |
| pts | 49,525 | yes | 0.524 / 0.281 | 0.498 / 0.290 |
| reb | 49,525 | yes | 0.537 / 0.252 | 0.497 / 0.287 |
| tov | 49,525 | yes | 0.547 / 0.259 | 0.509 / 0.281 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.