# PMF calibration run

**Run at:** 2026-06-09T18:05:21.178019Z
**Folds:** 4 walk-forward, 28-day validation, 365-day minimum training window.
**Production artifact backup:** `/home/runner/work/nba-player-props-model/nba-player-props-model/artifacts/archive/aggregate_only_20260609_180445`

## Per-stat result

| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |
|---|---:|---|---|---|
| ast | 8,059 | yes | 0.550 / 0.257 | 0.509 / 0.279 |
| blk | 8,059 | yes | 0.503 / 0.291 | 0.513 / 0.295 |
| fg3m | 8,059 | yes | 0.474 / 0.328 | 0.484 / 0.318 |
| pts | 8,059 | yes | 0.543 / 0.283 | 0.521 / 0.294 |
| reb | 8,059 | yes | 0.552 / 0.255 | 0.528 / 0.280 |
| stl | 8,059 | yes | 0.489 / 0.289 | 0.494 / 0.290 |
| tov | 8,059 | yes | 0.541 / 0.261 | 0.520 / 0.274 |

## Known caveat

training_df's baked-in mp_* feature columns were computed with the full-data minutes model. When per-fold models are refit on data sliced by date from that training_df, those baked-in columns carry a small indirect leakage. The validation outcomes themselves are never seen by the fold's models, so the primary OOF guarantee holds; the effective calibration is slightly optimistic. A strict-regen walk-forward would require rebuilding training_df per fold (~20 min each); this run does not pay that cost.