# Previous-Day Source Completeness — 2026-04-30

- target_date: 2026-04-30
- yesterday_in_et: 2026-04-30
- passed: **True**
- fail_code: (none)

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| source_refresh_manifest_present | yes | status=ok finished_at=2026-05-01T12:47:04+00:00 |
| source_parquet_exists | yes | data/player_game_stats.parquet |
| max_game_date_covers_target | yes | max_game_date=2026-04-30 target=2026-04-30 |
| no_rows_after_target_date | yes | rows_after_target=0 |
| rows_on_target_date_above_floor | yes | rows_on_target_date=71 >= floor=25 |
| rows_within_rolling_7day_baseline | yes | rows=71 median7=73 |

## Metrics

```
{
  "row_count_total": 83568,
  "max_game_date": "2026-04-30",
  "rows_on_target_date": 71,
  "rows_after_target_date": 0,
  "source_sha256_prefix": "7ae9ec31106c239d",
  "rolling_7day_median_rows": 73,
  "rolling_7day_dates": [
    "2026-04-23",
    "2026-04-24",
    "2026-04-25",
    "2026-04-26",
    "2026-04-27",
    "2026-04-28",
    "2026-04-29"
  ]
}
```
