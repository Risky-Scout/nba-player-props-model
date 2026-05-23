# Previous-Day Source Completeness — 2026-05-22

- target_date: 2026-05-22
- yesterday_in_et: 2026-05-22
- passed: **True**
- fail_code: (none)

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| source_refresh_manifest_present | yes | status=skipped_already_fresh finished_at=2026-05-23T19:45:20+00:00 |
| source_parquet_exists | yes | data/player_game_stats.parquet |
| max_game_date_covers_target | yes | max_game_date=2026-05-22 target=2026-05-22 |
| no_rows_after_target_date | yes | rows_after_target=0 |
| rows_on_target_date_above_floor | yes | rows_on_target_date=28 >= floor=1 |
| rows_within_rolling_7day_baseline | yes | rows=28 median7=22 |

## Metrics

```
{
  "row_count_total": 84338,
  "max_game_date": "2026-05-22",
  "rows_on_target_date": 28,
  "rows_after_target_date": 0,
  "source_sha256_prefix": "e4bce5fab094abdd",
  "rolling_7day_median_rows": 22,
  "rolling_7day_dates": [
    "2026-05-13",
    "2026-05-15",
    "2026-05-17",
    "2026-05-18",
    "2026-05-19",
    "2026-05-20",
    "2026-05-21"
  ]
}
```
