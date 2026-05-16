# Previous-Day Source Completeness — 2026-05-15

- target_date: 2026-05-15
- yesterday_in_et: 2026-05-15
- passed: **True**
- fail_code: (none)

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| source_refresh_manifest_present | yes | status=skipped_already_fresh finished_at=2026-05-16T10:49:13+00:00 |
| source_parquet_exists | yes | data/player_game_stats.parquet |
| max_game_date_covers_target | yes | max_game_date=2026-05-15 target=2026-05-15 |
| no_rows_after_target_date | yes | rows_after_target=0 |
| rows_on_target_date_above_floor | yes | rows_on_target_date=54 >= floor=1 |
| rows_within_rolling_7day_baseline | yes | rows=54 median7=45 |

## Metrics

```
{
  "row_count_total": 84196,
  "max_game_date": "2026-05-15",
  "rows_on_target_date": 54,
  "rows_after_target_date": 0,
  "source_sha256_prefix": "85607cd0fe8c379d",
  "rolling_7day_median_rows": 45,
  "rolling_7day_dates": [
    "2026-05-07",
    "2026-05-08",
    "2026-05-09",
    "2026-05-10",
    "2026-05-11",
    "2026-05-12",
    "2026-05-13"
  ]
}
```
