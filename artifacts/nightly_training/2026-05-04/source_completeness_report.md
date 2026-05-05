# Previous-Day Source Completeness — 2026-05-04

- target_date: 2026-05-04
- yesterday_in_et: 2026-05-04
- passed: **True**
- fail_code: (none)

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| source_refresh_manifest_present | yes | status=skipped_already_fresh finished_at=2026-05-05T22:33:40+00:00 |
| source_parquet_exists | yes | data/player_game_stats.parquet |
| max_game_date_covers_target | yes | max_game_date=2026-05-04 target=2026-05-04 |
| no_rows_after_target_date | yes | rows_after_target=0 |
| rows_on_target_date_above_floor | yes | rows_on_target_date=46 >= floor=25 |
| rows_within_rolling_7day_baseline | yes | rows=46 median7=61 |

## Metrics

```
{
  "row_count_total": 83775,
  "max_game_date": "2026-05-04",
  "rows_on_target_date": 46,
  "rows_after_target_date": 0,
  "source_sha256_prefix": "e493ee6f8a936ca6",
  "rolling_7day_median_rows": 61,
  "rolling_7day_dates": [
    "2026-04-27",
    "2026-04-28",
    "2026-04-29",
    "2026-04-30",
    "2026-05-01",
    "2026-05-02",
    "2026-05-03"
  ]
}
```
