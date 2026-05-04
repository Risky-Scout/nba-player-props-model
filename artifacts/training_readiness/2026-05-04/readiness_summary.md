# Daily Training Readiness — 2026-05-04

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-04T16:39:25+00:00 |
| Code commit | 466c26c5d0f3 |
| Overall pass | yes |
| Blocking failed | 0 |
| Advisory failed | 2 |

## Checks

| Check | Severity | Pass | Detail |
| --- | --- | --- | --- |
| outcomes_through_as_of_date | blocking | yes | rows through 2026-05-04: 83497 |
| future_dates_present_advisory | advisory | yes | 0 rows have date > 2026-05-04; trainer must filter them out |
| required_stat_columns_present | advisory | yes | present=['ast', 'blk', 'fg3m', 'pts', 'reb', 'stl'] missing=['tov'] |
| no_impossible_stat_values | blocking | yes | ok |
| min_training_rows | blocking | yes | 83497 >= 5000 |
| min_per_stat_rows | advisory | yes | enough=['pts', 'reb', 'ast', 'fg3m', 'stl', 'blk'] thin=[] |
| odds_snapshots_for_date | advisory | NO | 0 parquet snapshot(s) for 2026-05-04 |
| freshness_manifest_for_date | advisory | NO | missing |
| no_promotion_lock_held | blocking | yes | ok |

## Counts

```
{
  "player_game_stats_total_rows": 83497,
  "player_game_stats_rows_through_as_of": 83497,
  "player_game_stats_rows_on_as_of_date": 0,
  "player_game_stats_rows_after_as_of": 0,
  "stat_columns_present": {
    "pts": "pts",
    "reb": "reb",
    "ast": "ast",
    "fg3m": "fg3m",
    "stl": "stl",
    "blk": "blk"
  },
  "per_stat_rows_through_as_of": {
    "pts": 83497,
    "reb": 83497,
    "ast": 83497,
    "fg3m": 83497,
    "stl": 83497,
    "blk": 83497
  },
  "odds_snapshot_files_on_date": 0
}
```
