# Daily PMF delivery stat-count mismatch — `2026-05-06`

## Sources
- stat_grid: `predictions/stat_grid_2026-05-06.parquet` exists=True
- canonical MODEL_ONLY: `deliveries/2026-05-06/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet` exists=True
- all_props: `predictions/all_props_2026-05-06.parquet` exists=True
- backtest report (optional): `artifacts/model_diagnostics/backtest_delivery_range_2026-05-06_2026-05-06.json` exists=True

## Per-stat row counts
| stat | stat_grid | all_props | canonical |
|------|-----------|-----------|-----------|
| ast | 70 | 7 | 68 |
| blk | 70 | 1 | 68 |
| fg3m | 68 | 4 | 68 |
| pa | 70 | — | 68 |
| pr | 70 | — | 68 |
| pra | 70 | — | 68 |
| pts | 70 | 7 | 68 |
| ra | 70 | — | 68 |
| reb | 70 | 6 | 68 |
| stl | 70 | 2 | 68 |
| stocks | 70 | — | 68 |
| tov | 70 | — | 68 |

## stat_grid: keys with `pts` but no `fg3m`: 2
- `21707973|1028112004`
- `21707973|1057397172`

## stat_grid: keys with `pts` but no `tov`: 0

## Likely root cause
If canonical is uneven while stat_grid is rectangular, the usual cause is `build_daily_pmf_delivery.py --rebuild-canonical`, which merges `all_props` (sparse per-stat) with stat_grid append-only dedupe, producing unequal `stat` value_counts. Fix: use stat_grid-built canonical without `--rebuild-canonical`, and/or run `_enforce_complete_stat_grid` after `build_canonical_from_predictions`.

