# Previous-Day Source Completeness — 2026-05-09

- target_date: 2026-05-09
- yesterday_in_et: 2026-05-09
- passed: **True**
- fail_code: (none)

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| source_refresh_manifest_present | yes | status=skipped_already_fresh finished_at=2026-05-10T22:14:07+00:00 |
| source_parquet_exists | yes | data/player_game_stats.parquet |
| max_game_date_covers_target | yes | max_game_date=2026-05-09 target=2026-05-09 |
| no_rows_after_target_date | yes | rows_after_target=0 |
| rows_on_target_date_above_floor | yes | rows_on_target_date=45 >= floor=25 |
| rows_within_rolling_7day_baseline | yes | rows=45 median7=45 |

## Metrics

```
{
  "row_count_total": 84003,
  "max_game_date": "2026-05-09",
  "rows_on_target_date": 45,
  "rows_after_target_date": 0,
  "source_sha256_prefix": "f7224da10dc03ce7",
  "rolling_7day_median_rows": 45,
  "rolling_7day_dates": [
    "2026-05-02",
    "2026-05-03",
    "2026-05-04",
    "2026-05-05",
    "2026-05-06",
    "2026-05-07",
    "2026-05-08"
  ]
}
```
