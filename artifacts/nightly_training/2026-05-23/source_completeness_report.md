# Previous-Day Source Completeness — 2026-05-23

- target_date: 2026-05-23
- yesterday_in_et: 2026-05-23
- passed: **True**
- fail_code: (none)

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| source_refresh_manifest_present | yes | status=skipped_already_fresh finished_at=2026-05-24T14:09:40+00:00 |
| source_parquet_exists | yes | data/player_game_stats.parquet |
| max_game_date_covers_target | yes | max_game_date=2026-05-23 target=2026-05-23 |
| no_rows_after_target_date | yes | rows_after_target=0 |
| rows_on_target_date_above_floor | yes | rows_on_target_date=19 >= floor=1 |
| rows_within_rolling_7day_baseline | yes | rows=19 median7=26 |

## Metrics

```
{
  "row_count_total": 84357,
  "max_game_date": "2026-05-23",
  "rows_on_target_date": 19,
  "rows_after_target_date": 0,
  "source_sha256_prefix": "cee9e01d30bf895c",
  "rolling_7day_median_rows": 26,
  "rolling_7day_dates": [
    "2026-05-15",
    "2026-05-17",
    "2026-05-18",
    "2026-05-19",
    "2026-05-20",
    "2026-05-21",
    "2026-05-22"
  ]
}
```
