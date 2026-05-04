# Previous-Day Source Completeness — 2026-05-03

- target_date: 2026-05-03
- yesterday_in_et: 2026-05-03
- passed: **True**
- fail_code: (none)

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| source_refresh_manifest_present | yes | status=skipped_already_fresh finished_at=2026-05-04T19:53:46+00:00 |
| source_parquet_exists | yes | data/player_game_stats.parquet |
| max_game_date_covers_target | yes | max_game_date=2026-05-03 target=2026-05-03 |
| no_rows_after_target_date | yes | rows_after_target=0 |
| rows_on_target_date_above_floor | yes | rows_on_target_date=44 >= floor=25 |
| rows_within_rolling_7day_baseline | yes | rows=44 median7=67 |

## Metrics

```
{
  "row_count_total": 83729,
  "max_game_date": "2026-05-03",
  "rows_on_target_date": 44,
  "rows_after_target_date": 0,
  "source_sha256_prefix": "489a130927792022",
  "rolling_7day_median_rows": 67,
  "rolling_7day_dates": [
    "2026-04-26",
    "2026-04-27",
    "2026-04-28",
    "2026-04-29",
    "2026-04-30",
    "2026-05-01",
    "2026-05-02"
  ]
}
```
